import json
import numpy as np
from .model import ROOT,NOTES,VALUES,load_frame

def encode(v):return json.dumps(v,ensure_ascii=False,separators=(',',':'))

def rgb(color):return [round(int(color[i:i+2],16)/255,6) for i in (1,3,5)]

def export(c):
 out=['// LILT music comb. Units: mm. Derived from the user-provided notext.stl.\n// Edit notes, offsets, extension and artwork settings below; F# aliases should be replaced by Gb.\n',f'notes = {encode(c["notes"])};',f'offsets = {encode(c["offsets"])};',f'extension = {c["extension"]}; // changes every free tooth length and pitch', 'part = "all"; // [all,front,back,clip]',f'note_names = {encode(NOTES)};',f'note_roots = {encode(VALUES)};','$fn=48;',f'baked_art = {encode([[a["target"],a["x"],a["y"],a["width"],a["rotation"],a["depth"],a["mode"]] for a in c["layers"]])}; // target, x, y, width, rotation, depth, mode']
 out.extend(['extra_text = ""; // Editable native OpenSCAD text', 'extra_svg = ""; // Path to a replacement SVG, e.g. logo.svg', 'extra_font = "Arial Unicode MS";', 'extra_target = "back";', 'extra_x = 0; extra_y = 40;', 'extra_width = 18; extra_rotation = 0;', 'extra_depth = 0.4; extra_mode = "engrave";', 'art = concat(baked_art,[[extra_target,extra_x,extra_y,extra_width,extra_rotation,extra_depth,extra_mode],[extra_target,extra_x,extra_y,extra_width,extra_rotation,extra_depth,extra_mode]]);'])
 for name in ['front','back','clip']:
  color=c['colors'][name]
  out.append(f'{name}_color = {encode([round(int(color[i:i+2],16)/255,6) for i in (1,3,5)])};')
 patches=[]
 for a in c['layers']:
  patches.append((a.get('regions') if a.get('preserveColors',True) else None) or [{'color':a['color'],'contours':a['contours']}])
 out.append('extra_color = [0.71,0.36,0.18];')
 out.append('art_colors=concat('+encode([[rgb(r['color']) for r in regions] for regions in patches])+',[[extra_color],[extra_color]]);')
 for i,a in enumerate(c['layers']):
  points=[];paths=[]
  for contour in a['contours']:
   paths.append(list(range(len(points),len(points)+len(contour))));points.extend(contour)
  out.append(f'module art_{i}() {{polygon(points={encode(points)},paths={encode(paths)});}}')
 for i,regions in enumerate(patches):
  for j,region in enumerate(regions):
   points=[];paths=[]
   for contour in region['contours']:
    paths.append(list(range(len(points),len(points)+len(contour))));points.extend(contour)
   out.append(f'module region_{i}_{j}() {{polygon(points={encode(points)},paths={encode(paths)});}}')
 out.append('module artwork_region(i,r) {')
 for i,regions in enumerate(patches):
  for j in range(len(regions)):out.append(f'if(i=={i}&&r=={j})region_{i}_{j}();')
 out.append('if(i>=len(baked_art)) artwork(i);}')
 out.append('module artwork(i) {')
 for i in range(len(c['layers'])):out.append(f'if(i=={i}) art_{i}();')
 out.append('if(i==len(baked_art) && extra_text!="") mirror([0,1]) resize([1,0],auto=true) text(extra_text,size=10,font=extra_font,halign="center",valign="center");')
 out.append('if(i==len(baked_art)+1 && extra_svg!="") mirror([0,1]) resize([1,0],auto=true) import(extra_svg,center=true);')
 out.append('}')
 for name in ['front_frame','back_frame','clip']:
  data=np.load(ROOT/'assets'/f'{name}.npz');points=data['vertices'].tolist();faces=data['faces'][:,::-1].tolist()
  out.extend([f'{name}_points={encode(points)};',f'{name}_faces={encode(faces)};'])
 for name in ['front','back']:
  contours=load_frame(name+'_frame').slice(.02).to_polygons();points=[];paths=[]
  for contour in contours:
   paths.append(list(range(len(points),len(points)+len(contour))));points.extend(contour.tolist())
  out.append(f'{name}_base_points={encode(points)};{name}_base_paths={encode(paths)};')
 out.append('''
assert(len(notes)>=8 && len(notes)<=33,"Use 8 to 33 notes including blanks");
assert(extension>=-5 && extension<=10,"Extension range -5 to 10 mm");
width=2.25*len(notes)+24;
function root(note)=note=="·" ? 1 : let(matches=search([note],note_names)) assert(is_num(matches[0]),str("Unknown note: ",note)) note_roots[matches[0]];
function offset(i)=i<len(offsets) ? offsets[i] : 0;
function resize_point(p)=[abs(p[0])>=28.125 ? p[0]+sign(p[0])*(width-80.25)/2 : p[0]*(28.125+(width-80.25)/2)/28.125,p[1]+(p[1]>25?extension:0),p[2]];
module frame(name){
 if(name=="front") polyhedron([for(p=front_frame_points) resize_point(p)],front_frame_faces,convexity=10);
 if(name=="back") polyhedron([for(p=back_frame_points) resize_point(p)],back_frame_faces,convexity=10);
}
module yz(points){multmatrix([[0,0,1,-(width+10)/2],[1,0,0,0],[0,1,0,0],[0,0,0,1]]) linear_extrude(width+10) polygon(points);}
module tooth(x,value){
 tip=37+extension;r=2.5+value;
 difference(){
  translate([0,0,.005]) linear_extrude(4.5) union(){
   polygon([[x-.5,3],[x+.5,3],[x+.5,tip],[x-.5,tip]]);
   if(value>1)polygon([[x-2.5,3],[x+2.5,3],[x+2.5,r-2],[x,r+.5],[x-2.5,r-2]]);
  }
  yz([[3,-.005],[3,4.495],[8.2,-.005]]);
  yz([[tip-3,.005],[tip,.005],[tip,3.005]]);
 }
}
module plain(name){union(){
 frame(name);
 for(i=[name=="back"?0:1:2:len(notes)-1]){
  x=name=="back"?-width/2+12.75+floor(i/2)*4.5:width/2-15-floor(i/2)*4.5;
  tooth(x,root(notes[i])+(notes[i]=="·"?0:offset(i)));
 }
}}
module art2d(i){a=art[i];translate([a[1],a[2]]) rotate(a[4]) scale(a[3]) artwork(i);}
module art_region2d(i,r){a=art[i];translate([a[1],a[2]])rotate(a[4])scale(a[3])artwork_region(i,r);}
module tooth_footprint(x,value){
 r=2.5+value;tip=37+extension;
 intersection(){
  union(){polygon([[x-.5,3],[x+.5,3],[x+.5,tip],[x-.5,tip]]);if(value>1)polygon([[x-2.5,3],[x+2.5,3],[x+2.5,r-2],[x,r+.5],[x-2.5,r-2]]);}
  translate([-width,8.171111])square([width*2,tip-2.985-8.171111]);
 }
}
module footprint(name){union(){
 points=name=="front"?front_base_points:back_base_points;
 paths=name=="front"?front_base_paths:back_base_paths;
 polygon([for(p=points)let(q=resize_point([p[0],p[1],0]))[q[0],q[1]]],paths);
 for(i=[name=="back"?0:1:2:len(notes)-1]){
  x=name=="back"?-width/2+12.75+floor(i/2)*4.5:width/2-15-floor(i/2)*4.5;
  tooth_footprint(x,root(notes[i])+(notes[i]=="·"?0:offset(i)));
 }
}}
module decorated(name){union(){
 difference(){
  plain(name);
  if(len(art)>0)for(i=[0:len(art)-1])if((art[i][0]==name||art[i][0]=="both")&&(art[i][6]=="engrave"||art[i][6]=="inlay"))translate([0,0,-.02])linear_extrude(art[i][5]+.02)art2d(i);
 }
 if(len(art)>0)for(i=[0:len(art)-1])if(art[i][0]==name||art[i][0]=="both")for(r=[0:len(art_colors[i])-1]){
  if(art[i][6]=="emboss")color(art_colors[i][r])translate([0,0,-art[i][5]])linear_extrude(art[i][5]+.04)intersection(){art_region2d(i,r);footprint(name);}
  if(art[i][6]=="inlay")color(art_colors[i][r])intersection(){plain(name);translate([0,0,-.02])linear_extrude(art[i][5]+.02)art_region2d(i,r);}
 }
}}
max_emboss=len(art)==0?0:max([for(a=art)a[6]=="emboss"?a[5]:0]);
translate([0,0,max_emboss]){
 if(part=="all"||part=="front")color(front_color)decorated("front");
 if(part=="all"||part=="back")translate([0,part=="all"?50+extension:0,0])color(back_color)decorated("back");
 if(part=="all"||part=="clip")translate([0,part=="all"?-16.729:0,0])color(clip_color)polyhedron(clip_points,clip_faces,convexity=10);
}
''')
 return '\n'.join(out).encode('utf-8')
