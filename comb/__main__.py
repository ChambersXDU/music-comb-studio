import argparse,json,sys
from pathlib import Path
from .model import DEFAULT,build,stl,three_mf
from .scad import export

def main():
 parser=argparse.ArgumentParser(description='Local music comb generator, millimeters');sub=parser.add_subparsers(dest='command',required=True)
 gen=sub.add_parser('generate');gen.add_argument('--notes',default=None);gen.add_argument('--config',type=Path);gen.add_argument('--out',type=Path,default=Path('outputs/comb'));gen.add_argument('--extension',type=float);gen.add_argument('--text');gen.add_argument('--svg',type=Path);gen.add_argument('--image',type=Path);gen.add_argument('--x',type=float,default=0);gen.add_argument('--y',type=float,default=40);gen.add_argument('--width',type=float,default=18);gen.add_argument('--target',choices=['front','back','both'],default='back');gen.add_argument('--mode',choices=['engrave','emboss','inlay'],default='engrave');gen.add_argument('--art-color',default='#b65c2f');gen.add_argument('--depth',type=float,default=.4);gen.add_argument('--format',choices=['all','stl','scad','3mf'],default='all')
 serve=sub.add_parser('serve');serve.add_argument('--port',type=int,default=8818)
 args=parser.parse_args()
 if args.command=='serve':
  from .server import serve
  serve(args.port);return
 try:
  config=json.loads(args.config.read_text()) if args.config else {}
  if args.notes is not None:config['notes']=args.notes
  if args.extension is not None:config['extension']=args.extension
  for kind,value in [('text',args.text),('svg',args.svg),('image',args.image)]:
   if value:config.setdefault('layers',[]).append({'kind':kind,**({'text':value} if kind=='text' else {'file':str(value)}),'x':args.x,'y':args.y,'width':args.width,'target':args.target,'mode':args.mode,'depth':args.depth,'color':args.art_color})
  c,parts,placed,layout,meta=build(config);args.out.parent.mkdir(parents=True,exist_ok=True)
  outputs={'stl':lambda:stl(layout),'scad':lambda:export(c),'3mf':lambda:three_mf(placed,c["colors"])}
  for fmt,fn in outputs.items():
   if args.format in ['all',fmt]:
    path=args.out.with_suffix('.'+fmt);path.write_bytes(fn());print(path.resolve())
  args.out.with_suffix('.json').write_text(json.dumps(c,ensure_ascii=False,indent=2));args.out.with_suffix('.manifest.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2))
  print(f'{meta["count"]} notes | {meta["width"]:.2f} × {meta["depth"]:.2f} mm per panel | {meta["triangles"]} triangles')
 except (ValueError,OSError,KeyError) as e:print(f'Error: {e}',file=sys.stderr);sys.exit(2)
if __name__=='__main__':main()
