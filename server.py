import socket
import sys

'''This is a simple server socket, that echoes the message from a client, using TCP'''


#Allows for command line arguments
serverPort = int(sys.argv[1])
blockDuration = sys.argv[2]
timeout = sys.argv[3]

serverAddress = ('localhost', serverPort)

#Creates a server socket
serverSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serverSock.bind(serverAddress)  #Binds our server socket to the server address.

serverSock.listen()   #Enables our server to accept connections


#Start loop for accepting connections
while True:
    clientConn, clientAddr = serverSock.accept()   #Creates a separate connection for communicating with client.
    print('Connected by', clientAddr)
    while True:
        data = clientConn.recv(1024)
        if not data:
            break
        clientConn.sendall(data)  #Sends data back to client
    
    clientConn.close()

serverSock.close()