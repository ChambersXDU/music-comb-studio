from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from pathlib import Path
import json,base64,mimetypes,threading,traceback,time,secrets
from urllib.parse import urlsplit
from .model import ROOT,NOTES,VALUES,DEFAULT,build,stl,three_mf
from .scad import export
from .artwork import import_art
LOCK=threading.Lock()
DOWNLOADS={}
class Handler(BaseHTTPRequestHandler):
 def send(self,status,data,content_type='application/json',filename=None):
  self.send_response(status);self.send_header('Content-Type',content_type);self.send_header('Content-Length',str(len(data)));self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff')
  if filename:self.send_header('Content-Disposition',f'attachment; filename="{filename}"')
  self.end_headers();self.wfile.write(data)
 def do_GET(self):
  path=urlsplit(self.path).path
  if path.startswith('/downloads/'):
   with LOCK: item=DOWNLOADS.get(path.rsplit('/',1)[-1])
   if not item or item[0]<time.time():self.send(404,b'Download expired','text/plain');return
   self.send(200,item[1],'application/octet-stream',item[2]);return
  if path=='/api/catalog':self.send(200,json.dumps({'notes':NOTES,'roots':VALUES,'default':DEFAULT}).encode());return
  file=(ROOT/'web'/('index.html' if path=='/' else path.lstrip('/'))).resolve()
  if not file.is_relative_to((ROOT/'web').resolve()) or not file.is_file():self.send(404,b'Not found','text/plain');return
  mime=mimetypes.guess_type(str(file))[0] or 'application/octet-stream';self.send(200,file.read_bytes(),mime)
 def do_POST(self):
  if self.headers.get('Origin') and self.headers['Origin'] not in [f'http://127.0.0.1:{self.server.server_port}',f'http://localhost:{self.server.server_port}']:self.send(403,b'{}');return
  try:
   length=int(self.headers.get('Content-Length',0))
   if not 0<length<=12*1024*1024:raise ValueError('请求大小超过限制')
   payload=json.loads(self.rfile.read(length));path=urlsplit(self.path).path
   with LOCK:
    if path=='/api/artwork':
     payload.pop('file',None);self.send(200,json.dumps(import_art(payload),ensure_ascii=False).encode());return
    if path=='/api/download' and payload.get('format')=='json':
     self.download(json.dumps(payload['config'],ensure_ascii=False,indent=2).encode(),'music-comb-plan.json');return
    if path not in ['/api/generate','/api/export','/api/download']:self.send(404,b'{}');return
    config=payload.get('config',payload)
    for layer in config.get('layers',[]):layer.pop('file',None)
    c,parts,placed,layout,meta=build(config)
    if path in ['/api/export','/api/download']:
     fmt=payload['format'];data={'stl':lambda:stl(layout),'scad':lambda:export(c),'3mf':lambda:three_mf(placed,c["colors"]),'json':lambda:json.dumps(c,ensure_ascii=False,indent=2).encode()}[fmt]()
     if path=='/api/download':self.download(data,'music-comb.'+fmt)
     else:self.send(200,data,'application/octet-stream','music-comb.'+fmt)
     return
    result={'config':c,'metadata':meta,'stl':base64.b64encode(stl(layout)).decode(),'meshes':[{**{k:v for k,v in region.items() if k!='mesh'},'stl':base64.b64encode(stl(region['mesh'])).decode()} for region in placed.regions]}
    self.send(200,json.dumps(result,ensure_ascii=False).encode())
  except (ValueError,KeyError,TypeError,OSError) as e:self.send(400,json.dumps({'error':str(e)},ensure_ascii=False).encode())
  except (BrokenPipeError,ConnectionResetError):pass
  except Exception as e:traceback.print_exc();self.send(500,json.dumps({'error':f'生成失败：{e}'},ensure_ascii=False).encode())
 def log_message(self,format,*args):
  if '400' in args or '500' in args:super().log_message(format,*args)
 def download(self,data,filename):
  now=time.time()
  for key in list(DOWNLOADS):
   if DOWNLOADS[key][0]<now:del DOWNLOADS[key]
  while len(DOWNLOADS)>=12:del DOWNLOADS[next(iter(DOWNLOADS))]
  key=secrets.token_urlsafe(24);DOWNLOADS[key]=(now+600,data,filename)
  self.send(200,json.dumps({'url':'/downloads/'+key,'filename':filename}).encode())
def serve(port):
 server=ThreadingHTTPServer(('127.0.0.1',port),Handler);print(f'LILT music comb studio: http://127.0.0.1:{port}',flush=True)
 try:server.serve_forever()
 except KeyboardInterrupt:server.server_close()
