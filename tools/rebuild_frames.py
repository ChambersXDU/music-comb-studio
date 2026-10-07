"""Rebuild mechanical frames from the checked-in normalized reference meshes.
Run from the project root: .venv/bin/python tools/rebuild_frames.py
"""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from comb.model import *
for name in ['front','back']:
 d=np.load(ROOT/'assets'/f'reference_{name}.npz');orig=m.Manifold(m.Mesh64(np.round(d['vertices'],4),d['faces'].astype(np.uint64)));cutters=m.Manifold()
 for j in range(0 if name=='back' else 1,25,2):
  x=-40.125+12.75+j//2*4.5 if name=='back' else 40.125-15-j//2*4.5;v=VALUES[j] if j<20 else 1
  # Expansion avoids zero-thickness remnants from coplanar reference surfaces.
  t=tooth(x,v,80.25).translate([-x,-20,-2.25]).scale([1.004,1.0004,1.004]).translate([x,20,2.25])
  cutters+=t
 cutters=cutters ^ m.Manifold.cube([100,40,10]).translate([-50,3.01,-1])
 cutters-=m.Manifold.cube([100,10,1.005]).translate([-50,35.8,0])
 shell=orig-cutters;shell=max(shell.decompose(),key=lambda p:p.volume()).simplify(.00001);mesh=shell.to_mesh64();vv=mesh.vert_properties[:,:3];ff=mesh.tri_verts;t=vv[ff];print(name,shell.status(),len(ff),'min',np.linalg.norm(np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]),axis=1).min());np.savez_compressed(ROOT/'assets'/f'{name}_frame.npz',vertices=vv,faces=ff)
