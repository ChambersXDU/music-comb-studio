import io,base64,math
from pathlib import Path
import numpy as np
from PIL import Image,ImageFont,ImageDraw
from shapely.geometry import box,Polygon
from shapely.ops import unary_union
from shapely import affinity

def polygons(geom):
 return [geom] if geom.geom_type=='Polygon' else list(geom.geoms) if geom.geom_type=='MultiPolygon' else []

def normalized(geom,bounds=None):
 geom=geom.buffer(0)
 if geom.is_empty:raise ValueError('没有找到可用的实心轮廓，请检查图形或阈值')
 x0,y0,x1,y1=bounds or geom.bounds;w=x1-x0
 geom=affinity.translate(geom,-(x0+x1)/2,-(y0+y1)/2);geom=affinity.scale(geom,1/w,1/w,origin=(0,0))
 contours=[]
 for p in polygons(geom):
  contours.append(list(map(list,p.exterior.coords))[:-1])
  contours.extend(list(map(list,r.coords))[:-1] for r in p.interiors)
 return {'contours':contours,'aspect':(y1-y0)/w}

def mask_geometry(im,threshold=128,invert=False):
 im=im.convert('RGBA');background=Image.new('RGBA',im.size,'white');background.alpha_composite(im);gray=background.convert('L');gray.thumbnail((384,384),Image.Resampling.LANCZOS)
 a=np.asarray(gray);mask=a>threshold if invert else a<threshold;rects=[]
 for y,row in enumerate(mask):
  boundaries=np.flatnonzero(np.diff(np.r_[False,row,False].astype(int)))
  rects.extend(box(int(x0),y,int(x1),y+1) for x0,x1 in zip(boundaries[::2],boundaries[1::2]))
 if not rects:raise ValueError('图片中没有轮廓；可调节阈值或反相')
 return unary_union(rects).simplify(.35,preserve_topology=True)

def svg_geometry(data):
 from svgelements import SVG,Path as SvgPath,Shape,Move,Close
 import manifold3d as m
 if b'<!ENTITY' in data.upper() or b'<!DOCTYPE' in data.upper():raise ValueError('SVG 不支持实体或外部文档')
 svg=SVG.parse(io.BytesIO(data),reify=True);shapes=[];colored=[]
 for element in svg.elements():
  if not isinstance(element,Shape) or str(element.fill) in ['None','none'] or element.values.get('visibility')=='hidden':continue
  if element.fill.red is None:raise ValueError('SVG 渐变请先转成纯色区域')
  path=SvgPath(element);contours=[];points=[]
  for segment in path:
   if isinstance(segment,Move):
    if len(points)>2:contours.append(points)
    points=[[segment.end.x,segment.end.y]]
   elif isinstance(segment,Close):
    if len(points)>2:contours.append(points)
    points=[]
   else:
    length=segment.length(error=1e-3);count=min(128,max(1,math.ceil(length/1.5)))
    points.extend([[segment.point(t/count).x,segment.point(t/count).y] for t in range(1,count+1)])
  if len(points)>2:contours.append(points)
  if contours:
   # Even-odd nesting keeps counters and holes. Overlapping filled elements are unioned.
   rule=m.FillRule.EvenOdd if element.values.get('fill-rule')=='evenodd' else m.FillRule.NonZero
   normalized_paths=m.CrossSection([np.asarray(contour,dtype=float) for contour in contours],rule).to_polygons()
   geom=Polygon()
   for contour in normalized_paths:geom=geom.symmetric_difference(Polygon(contour).buffer(0))
   color=element.fill
   hexcolor=f"#{color.red:02x}{color.green:02x}{color.blue:02x}" if color is not None and color.red is not None else "#000000"
   shapes.append(geom);colored.append((hexcolor,geom))
 if not shapes:raise ValueError('SVG 需要实心路径/形状；文字请先转换为路径，线条请先转轮廓')
 geometry=unary_union(shapes)
 # Later SVG elements paint over earlier elements; remove overlapped material.
 regions=[];covered=Polygon()
 for color,geom in reversed(colored):
  visible=geom-covered;covered=covered.union(geom)
  if not visible.is_empty:regions.append((color,visible))
 merged={}
 for color,geom in regions:merged[color]=merged.get(color,Polygon()).union(geom)
 if len(merged)>16:raise ValueError('SVG 最多支持 16 种纯色；请先简化配色')
 return geometry,[{'color':color,**normalized(geom,geometry.bounds)} for color,geom in merged.items()]

def text_geometry(text):
 if not text or len(text)>80:raise ValueError('文字长度需要 1–80 个字符')
 fontpath=Path('/Library/Fonts/Arial Unicode.ttf')
 if not fontpath.exists():fontpath=Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')
 font=ImageFont.truetype(str(fontpath),120) if fontpath.exists() else ImageFont.load_default(size=120)
 bounds=font.getbbox(text);im=Image.new('L',(bounds[2]-bounds[0]+10,bounds[3]-bounds[1]+10),255);ImageDraw.Draw(im).text((5-bounds[0],5-bounds[1]),text,font=font,fill=0)
 return mask_geometry(im)

def import_art(item):
 kind=item.get('kind','text')
 if kind=='text':result=normalized(text_geometry(item.get('text','')))
 else:
  if item.get('file'):data=Path(item['file']).read_bytes()
  elif item.get('data'):data=base64.b64decode(item['data'].split(',')[-1],validate=True)
  else:raise ValueError('请选择 SVG 或图片文件')
  if len(data)>5*1024*1024:raise ValueError('图形文件最大 5 MB')
  if kind=='svg':geom,regions=svg_geometry(data)
  else:
   Image.MAX_IMAGE_PIXELS=20000000
   with Image.open(io.BytesIO(data)) as im:geom=mask_geometry(im, int(item.get('threshold',128)),bool(item.get('invert',False)))
  result=normalized(geom)
  if kind=='svg':result['regions']=regions
 return {**result,'kind':kind}
