import unittest,struct,io,zipfile,json
import numpy as np
import manifold3d as m
from comb.model import build,parse_notes,stl,three_mf,ROOT
from comb.artwork import import_art

def inspect_stl(data):
 n=struct.unpack_from('<I',data,80)[0];record=np.dtype([('normal','<f4',(3,)),('vertices','<f4',(3,3)),('attribute','<u2')]);tri=np.frombuffer(data,dtype=record,count=n,offset=84)['vertices'];vertices,inverse=np.unique(tri.reshape(-1,3),axis=0,return_inverse=True);faces=inverse.reshape(-1,3);edges=np.sort(np.concatenate([faces[:,[0,1]],faces[:,[1,2]],faces[:,[2,0]]]),axis=1);_,counts=np.unique(edges,axis=0,return_counts=True);return vertices,faces,counts
class ModelTests(unittest.TestCase):
 def test_notes(self):
  self.assertEqual(parse_notes('F# G# A# C#1 D#1 F#1 G#1 A#1'),['Gb','Ab','Bb','Db1','Eb1','Gb1','Ab1','Bb1'])
  for value in ['F '*7,'F '*34,'F F F F F F F Z']:
   with self.assertRaises(ValueError):parse_notes(value)
 def test_pause_geometry(self):
  sequence='C1 E1 · F1 G1 A1 · B1'
  self.assertEqual(parse_notes(sequence),['C1','E1','·','F1','G1','A1','·','B1'])
  *_,meta=self.verify({'notes':sequence})
  self.assertEqual(meta['count'],8)
  self.assertEqual([t['note'] for t in meta['teeth']].count('·'),2)
 def verify(self,config):
  c,parts,placed,layout,meta=build(config);self.assertEqual(layout.status(),m.Error.NoError);self.assertEqual(len(parts),3)
  for p in parts.values():self.assertEqual(len([q for q in p.decompose() if q.volume()>.001]),1)
  v,f,edges=inspect_stl(stl(layout));self.assertTrue(np.all(edges==2),f'Unclosed or nonmanifold STL: {np.unique(edges,return_counts=True)}');self.assertGreater(len(f),100);self.assertAlmostEqual(v[:,2].min(),0,places=5);return c,parts,placed,layout,meta
 def test_extremes(self):
  for n in [8,9,25,33]:
   for note in ['F','C2','·']:
    with self.subTest(n=n,note=note):
     *_,meta=self.verify({'notes':[note]*n});self.assertAlmostEqual(meta['width'],2.25*n+24)
 def test_extension_and_tuning(self):
  for extension in [-5,10]:self.verify({'notes':['F','C2','·','C1']*4,'extension':extension,'offsets':[2,-2,0,1]*4})
 def test_reference(self):
  c,parts,_,_,meta=self.verify({})
  for name in ['front','back']:
   d=np.load(ROOT/'assets'/f'reference_{name}.npz');orig=m.Manifold(m.Mesh64(d['vertices'].astype(np.float64),d['faces'].astype(np.uint64)));diff=((orig-parts[name])+(parts[name]-orig)).volume();self.assertLess(diff/orig.volume(),.001,'More than 0.1% reference geometry difference')
 def test_text(self):
  for text,mode in [('TEST','engrave'),('你好','engrave'),('LILT','emboss')]:self.verify({'notes':['C1','G1']*6,'layers':[{'kind':'text','text':text,'mode':mode,'target':'both','width':16,'y':40}]})
 def test_svg_and_bitmap(self):
  import base64
  from PIL import Image,ImageDraw
  svg=b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><path fill-rule="evenodd" d="M0 0H100V100H0Z M25 25H75V75H25Z"/></svg>'
  art=import_art({'kind':'svg','data':base64.b64encode(svg).decode()});self.assertEqual(len(art['contours']),2)
  self.verify({'layers':[dict(art,x=0,y=40,width=5,target='both',mode='emboss')]})
  im=Image.new('RGB',(64,64),'white');ImageDraw.Draw(im).ellipse((8,8,56,56),fill='black');b=io.BytesIO();im.save(b,format='PNG');art=import_art({'kind':'image','data':base64.b64encode(b.getvalue()).decode()});self.verify({'layers':[dict(art,y=40,width=4)]})
 def test_flush_multicolor(self):
  c,parts,placed,layout,meta=self.verify({'layers':[{'kind':'svg','file':str(ROOT/'examples'/'multicolor.svg'),'width':22,'y':40,'mode':'inlay','target':'both'}]})
  original=build({})[1]
  self.assertEqual(len(placed.regions),11)
  for name in ['front','back']:
   self.assertAlmostEqual(parts[name].bounding_box()[2],original[name].bounding_box()[2],places=5)
   self.assertAlmostEqual(parts[name].bounding_box()[5],original[name].bounding_box()[5],places=5)
   diff=((parts[name]-original[name])+(original[name]-parts[name])).volume();self.assertLess(diff,.05)
  for region in placed.regions:
   v,f,edges=inspect_stl(stl(region['mesh']));self.assertTrue(np.all(edges==2),region['name'])
  self.assertEqual(len({region['color'] for region in placed.regions}),7)
 def test_three_mf(self):
  _,_,placed,_,_=self.verify({});z=zipfile.ZipFile(io.BytesIO(three_mf(placed)));self.assertIn('3D/3dmodel.model',z.namelist())
  import xml.etree.ElementTree as ET
  root=ET.fromstring(z.read('3D/3dmodel.model'));ns={'m':'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'};self.assertEqual(len(root.findall('m:build/m:item',ns)),3)
  colors={'front':'#123456','back':'#abcdef','clip':'#fedcba'};z=zipfile.ZipFile(io.BytesIO(three_mf(placed,colors)));root=ET.fromstring(z.read('3D/3dmodel.model'));bases=root.findall('m:resources/m:basematerials/m:base',ns);self.assertEqual([b.attrib['displaycolor'] for b in bases],['#123456FF','#ABCDEFFF','#FEDCBAFF'])
  ns['c']='http://schemas.microsoft.com/3dmanufacturing/material/2015/02';self.assertEqual(len(root.findall('m:resources/c:colorgroup/c:color',ns)),3)
if __name__=='__main__':unittest.main()
