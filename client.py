import socket
import sys
import time


serverIP = sys.argv[1]
serverPort = int(sys.argv[2])

clientSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

clientSock.connect((serverIP, serverPort))
time.sleep(10)
clientSock.sendall(b'Hello server!')
data = clientSock.recv(1024)

print(data)

clientSock.close()