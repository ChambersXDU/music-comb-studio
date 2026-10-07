from pathlib import Path
import re, struct, io, zipfile, json, math
import numpy as np
import manifold3d as m
ROOT=Path(__file__).resolve().parent.parent
NOTES=['F','Gb','G','Ab','A','Bb','B','C1','Db1','D1','Eb1','E1','F1','Gb1','G1','Ab1','A1','Bb1','B1','C2']
VALUES=[6.2,7,8.1,8.75,9.45,10.25,10.8,11.5,12.15,12.8,13.4,13.95,14.55,15.1,15.6,16,16.65,17,17.6,18]
DEFAULT=' '.join(NOTES+['·']*5)
DEFAULT_COLORS={'front':'#538d82','back':'#c4cfbe','clip':'#c98c53'}
ALIASES={'F#':'Gb','G#':'Ab','A#':'Bb','C#1':'Db1','D#1':'Eb1','F#1':'Gb1','G#1':'Ab1','A#1':'Bb1','CB1':'B','B#':'C1','CB2':'B1','B#1':'C2'}

def parse_notes(value):
 tokens=re.split(r'[\s,，;；|]+',value.strip()) if isinstance(value,str) else value
 if not isinstance(tokens,list):raise ValueError('音符必须是字符串或列表')
 result=[]
 for raw in tokens:
  if not raw:continue
  token=str(raw).replace('♯','#').replace('♭','b')
  if token in ['·','.','-','_','R','r']:result.append('·');continue
  token=token[0].upper()+token[1:]
  token=ALIASES.get(token.upper(),token)
  if token not in NOTES:raise ValueError(f'不支持的音符：{raw}。可用 F 到 C2，停顿用 ·')
  result.append(token)
 if not 8<=len(result)<=33:raise ValueError(f'需要 8–33 个音符（含空白），当前 {len(result)} 个')
 return result

def number(value,default,low,high,name):
 try:n=float(default if value is None else value)
 except (TypeError,ValueError):raise ValueError(f'{name}必须是数字')
 if not math.isfinite(n) or not low<=n<=high:raise ValueError(f'{name}范围为 {low}–{high}')
 return n

def normalize(config):
 from .artwork import import_art
 notes=parse_notes(config.get('notes',DEFAULT));offsets=config.get('offsets',[])
 if not isinstance(offsets,list) or len(offsets)>len(notes):raise ValueError('逐齿微调列表不能超过音符数量')
 offsets=[number(offsets[i] if i<len(offsets) else 0,0,-2,2,'逐齿微调') for i in range(len(notes))]
 layers=[]
 for raw in config.get('layers',[]):
  if len(layers)>=12:raise ValueError('最多添加 12 个图文图层')
  item=dict(raw)
  if not item.get('contours'):item.update(import_art(item))
  contours=item['contours']
  if sum(len(c) for c in contours)>40000:raise ValueError('图形过于复杂，请简化 SVG 或降低位图分辨率')
  if item.get('target','back') not in ['front','back','both']:raise ValueError('图层面板无效')
  if item.get('mode','engrave') not in ['engrave','emboss','inlay']:raise ValueError('图层方式无效')
  # CrossSection checks closed contour topology; finite values are required before geometry operations.
  for c in contours:
   if len(c)<3 or np.asarray(c).shape!=(len(c),2) or not np.isfinite(np.asarray(c,dtype=float)).all():raise ValueError('图层轮廓无效')
  color=item.get('color','#b65c2f')
  if not isinstance(color,str) or not re.fullmatch(r'#[0-9a-fA-F]{6}',color):raise ValueError('图案颜色无效')
  for region in item.get('regions',[]):
   if not re.fullmatch(r'#[0-9a-fA-F]{6}',region.get('color','')):raise ValueError('SVG 颜色无效')
   for contour in region.get('contours',[]):
    if len(contour)<3 or not np.isfinite(np.asarray(contour,dtype=float)).all():raise ValueError('SVG 轮廓无效')
  layers.append({**item,'color':color.lower(),'x':number(item.get('x'),0,-100,100,'X'),'y':number(item.get('y'),40,-20,70,'Y'),'width':number(item.get('width'),18,1,100,'宽度'),'rotation':number(item.get('rotation'),0,-360,360,'旋转'),'depth':number(item.get('depth'),.4,.1,1.5,'深度'),'target':item.get('target','back'),'mode':item.get('mode','engrave')})
 colors={**DEFAULT_COLORS,**config.get('colors',{})}
 if any(not isinstance(colors[name],str) or not re.fullmatch(r'#[0-9a-fA-F]{6}',colors[name]) for name in DEFAULT_COLORS):raise ValueError('颜色必须是六位十六进制值，如 #538d82')
 return {'colors':{name:colors[name].lower() for name in DEFAULT_COLORS},'notes':notes,'offsets':offsets,'extension':number(config.get('extension'),0,-5,10,'梳齿长度增量'),'layers':layers}

def cs(poly):return m.CrossSection([np.array(poly,dtype=float)],m.FillRule.NonZero)
def yz(poly,width):return cs(poly).extrude(width).transform([[0,0,1,-width/2],[1,0,0,0],[0,1,0,0]])
def tooth(x,v,width,extension=0):
 tip=37+extension
 shape=cs([[x-.5,3],[x+.5,3],[x+.5,tip],[x-.5,tip]]).extrude(4.5).translate([0,0,.005])
 if v>1:
  root=2.5+v
  shape+=cs([[x-2.5,3],[x+2.5,3],[x+2.5,root-2],[x,root+.5],[x-2.5,root-2]]).extrude(4.5).translate([0,0,.005])
 return shape-yz([[3,-.005],[3,4.495],[8.2,-.005]],width+10)-yz([[tip-3,.005],[tip,.005],[tip,3.005]],width+10)

def load_frame(name,width=80.25,extension=0):
 data=np.load(ROOT/'assets'/f'{name}.npz');v=data['vertices'].copy()
 if name!='clip':
  delta=(width-80.25)/2;edge=28.125
  v[:,0]=np.where(abs(v[:,0])>=edge,v[:,0]+np.sign(v[:,0])*delta,v[:,0]*(edge+delta)/edge)
  v[v[:,1]>25,1]+=extension
 result=m.Manifold(m.Mesh64(v.astype(np.float64),data['faces'].astype(np.uint64)))
 if result.status()!=m.Error.NoError:raise ValueError(f'基础框架错误：{result.status()}')
 return result

def layer_cs(layer):
 # SVG/raster coordinates use y-down; the outside view uses the same orientation.
 contours=[np.asarray(c)*layer['width'] for c in layer['contours']]
 shape=m.CrossSection(contours,m.FillRule.EvenOdd)
 return shape.rotate(layer['rotation']).translate([layer['x'],layer['y']])

class PrintParts(list):
 def __init__(self,regions):
  super().__init__(region['mesh'] for region in regions)
  self.regions=regions

def clean_many(body):
 chunks=[clean(chunk) for chunk in body.decompose() if chunk.volume()>1e-7]
 return m.Manifold.compose(chunks) if chunks else m.Manifold()

def build(config):
 c=normalize(config);n=len(c['notes']);width=2.25*n+24;extension=c['extension'];parts={};meta=[];footprints={};regions=[]
 for name,start in [('front',1),('back',0)]:
  body=load_frame(name+'_frame',width,extension)
  for j in range(start,n,2):
   x=-width/2+12.75+j//2*4.5 if name=='back' else width/2-15-j//2*4.5
   v=VALUES[NOTES.index(c['notes'][j])]+c['offsets'][j] if c['notes'][j]!='·' else 1
   body+=tooth(x,v,width,extension)
   meta.append({'index':j,'note':c['notes'][j],'part':name,'x':x,'root':2.5+v,'freeLength':37+extension-(2.5+v)})
  body=clean(body);footprints[name]=[a.tolist() for a in body.slice(.1).to_polygons()];inks=[]
  for index,layer in enumerate(c['layers']):
   if layer['target'] not in [name,'both']:continue
   shape=layer_cs(layer)
   # A later layer replaces earlier colored regions only where it has material.
   if layer['mode']=='engrave':
    cutter=shape.extrude(layer['depth']+.02).translate([0,0,-.02]);body-=cutter
    for ink in inks:ink['mesh']-=cutter
    continue
   patches=layer.get('regions') if layer.get('preserveColors',True) else None
   patches=patches or [{'contours':layer['contours'],'color':layer['color']}]
   for patch_index,patch in enumerate(patches):
    patch_shape=layer_cs({**layer,'contours':patch['contours']})
    if layer['mode']=='inlay':
     cutter=patch_shape.extrude(layer['depth']+.02).translate([0,0,-.02])
     whole=body+m.Manifold.batch_boolean([ink['mesh'] for ink in inks],m.OpType.Add)
     fill=whole^cutter;body-=cutter
     for ink in inks:ink['mesh']-=cutter
    else:
     whole=body+m.Manifold.batch_boolean([ink['mesh'] for ink in inks],m.OpType.Add)
     footprint=whole.slice(.02);fill=(patch_shape^footprint).extrude(layer['depth']+.04).translate([0,0,-layer['depth']])-whole
    if not fill.is_empty():inks.append({'name':f'{name}-art-{index+1}-{patch_index+1}','part':name,'color':patch['color'],'mesh':fill})
  inks=[{**ink,'mesh':clean_many(ink['mesh'])} for ink in inks if not ink['mesh'].is_empty()]
  inks=[ink for ink in inks if not ink['mesh'].is_empty()]
  if body.is_empty():raise ValueError('图案覆盖了整个面板，请减小尺寸或深度')
  base=clean_many(body);complete=base+m.Manifold.batch_boolean([ink['mesh'] for ink in inks],m.OpType.Add)
  parts[name]=clean(complete)
  regions.append({'name':name,'part':name,'color':c['colors'][name],'mesh':base});regions.extend(inks)
 parts['clip']=clean(load_frame('clip'));regions.append({'name':'clip','part':'clip','color':c['colors']['clip'],'mesh':parts['clip']})
 zmin=min(p.bounding_box()[2] for p in parts.values())
 shifts={'front':[0,0,-zmin],'back':[0,50+extension,-zmin],'clip':[0,-16.729,-zmin]}
 placed=PrintParts([{**region,'mesh':clean_many(region['mesh'].translate(shifts[region['part']]))} for region in regions])
 layout=m.Manifold.batch_boolean([clean(parts[name].translate(shifts[name])) for name in ['front','back','clip']],m.OpType.Add)
 metadata={'count':n,'width':width,'depth':44+extension,'parts':3,'volume':layout.volume(),'teeth':sorted(meta,key=lambda v:v['index']),'bounds':layout.bounding_box(),'triangles':layout.num_tri(),'contours':footprints,'materials':[{k:v for k,v in r.items() if k!='mesh'} for r in placed.regions]}
 return c,parts,placed,layout,metadata

def clean(body):
 # Keep the connected outer shell and remove microscopic internal cavities.
 body=max(body.decompose(),key=lambda p:p.volume())
 for tol in [.001,.005,.01]:
  mesh=body.set_tolerance(tol).simplify(tol).to_mesh()
  verts,inv=np.unique(mesh.vert_properties[:,:3],axis=0,return_inverse=True)
  faces=inv[mesh.tri_verts]
  faces=faces[(faces[:,0]!=faces[:,1])&(faces[:,1]!=faces[:,2])&(faces[:,0]!=faces[:,2])]
  mm=m.Mesh(verts,faces.astype(np.uint32));mm.merge();result=m.Manifold(mm)
  if result.status()==m.Error.NoError:return max(result.decompose(),key=lambda p:p.volume())
 raise ValueError('无法生成闭合网格，请调整图文位置或尺寸')

def stl(manifold):
 mesh=manifold.to_mesh();verts=mesh.vert_properties[:,:3];faces=mesh.tri_verts;tri=verts[faces]
 normal=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);length=np.linalg.norm(normal,axis=1);normal/=np.maximum(length[:,None],1e-15)
 dtype=np.dtype([('n','<f4',(3,)),('v','<f4',(3,3)),('a','<u2')]);records=np.zeros(len(faces),dtype=dtype);records['n']=normal;records['v']=tri
 return b'LILT music comb - millimeters'.ljust(80,b'\0')+struct.pack('<I',len(faces))+records.tobytes()

def three_mf(parts,colors=None):
 from xml.etree.ElementTree import Element,SubElement,tostring
 colors=colors or DEFAULT_COLORS
 regions=getattr(parts,'regions',None) or [{'name':name,'part':name,'color':colors[name],'mesh':part} for name,part in zip(['front','back','clip'],parts)]
 regions=[{**region,'color':colors[region['part']] if region['name']==region['part'] else region['color']} for region in regions]
 palette=list(dict.fromkeys(region['color'].lower() for region in regions));material_id=len(regions)+4;color_id=material_id+1
 ns='http://schemas.microsoft.com/3dmanufacturing/core/2015/02';model=Element('model',{'unit':'millimeter','xml:lang':'en-US','xmlns':ns,'xmlns:m':'http://schemas.microsoft.com/3dmanufacturing/material/2015/02'});res=SubElement(model,'resources');buildnode=SubElement(model,'build')
 bases=SubElement(res,'basematerials',{'id':str(material_id)});group=SubElement(res,'m:colorgroup',{'id':str(color_id)})
 for color in palette:
  SubElement(bases,'base',{'name':'Color '+color.upper(),'displaycolor':color.upper()+'FF'});SubElement(group,'m:color',{'color':color.upper()+'FF'})
 for i,region in enumerate(regions,1):
  mesh=region['mesh'].to_mesh();index=str(palette.index(region['color'].lower()));obj=SubElement(res,'object',{'id':str(i),'type':'model','name':region['name'],'pid':str(material_id),'pindex':index});node=SubElement(obj,'mesh');vs=SubElement(node,'vertices');ts=SubElement(node,'triangles')
  for v in mesh.vert_properties[:,:3]:SubElement(vs,'vertex',dict(zip(['x','y','z'],[str(float(x)) for x in v])))
  for f in mesh.tri_verts:SubElement(ts,'triangle',{**dict(zip(['v1','v2','v3'],map(str,f))),'pid':str(color_id),'p1':index,'p2':index,'p3':index})
 for i,name in enumerate(['front','back','clip'],len(regions)+1):
  obj=SubElement(res,'object',{'id':str(i),'type':'model','name':name});components=SubElement(obj,'components')
  for j,region in enumerate(regions,1):
   if region['part']==name:SubElement(components,'component',{'objectid':str(j)})
  SubElement(buildnode,'item',{'objectid':str(i)})
 buff=io.BytesIO()
 with zipfile.ZipFile(buff,'w',zipfile.ZIP_DEFLATED) as z:
  z.writestr('3D/3dmodel.model',tostring(model,encoding='utf-8',xml_declaration=True));z.writestr('[Content_Types].xml','<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>');z.writestr('_rels/.rels','<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
 return buff.getvalue()
