import socket
import sys
import time

'''This is a simple server socket, that echoes the message from a client, using TCP'''

# checks whether sufficient arguments have been provided 
if len(sys.argv) != 4: 
    print('The program takes 4 arguments: scriptname, server port, block duration and timeout duration.')
    exit() 


#Allows for command line arguments
serverPort = int(sys.argv[1])
blockDuration = int(sys.argv[2])
timeout = int(sys.argv[3])

serverAddress = ('localhost', serverPort)

credDict = {}  #Creates a dictionary to store the accounts for the application
connections = {} #Dictionary for storing sockets and their corresponding address
users = {}  #Dictionary for matching a socket with their username

try:
    f = open('credentials.txt', 'r')
    for line in f:
        account = line.split()
        username, password = account[0], account[1]
        credDict[username] = [password, 0]                  #Saves the account in the dictionary
except:
    print('Cannot find file "credentials.txt"')

#Creates a server socket
serverSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serverSock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
serverSock.bind(serverAddress)  #Binds our server socket to the server address.

'''Lets us accept incoming client connections'''
def accept_connections(serverSock):
    global connections
    while True:
        clientConn, clientAddr = serverSock.accept()   #Creates a separate connection for communicating with client.
        print('Connected by', clientAddr)
        connections[clientConn] = clientAddr
        handle_client(clientConn)

'''Handler for incoming client connections'''
def handle_client(conn):
    global users
    global credDict
    welcome = 'Welcome to this messenger service. Please login. \n'
    conn.sendall(welcome.encode('utf-8'))
    if authenticate(conn):
        conn.sendall('Chat and have fun!'.encode())
        while True:
            data = conn.recv(1024).decode('utf-8')
            if data == 'logout':
                user = users[conn]
                conn.sendall("You've been logged out.".encode('utf-8'))
                conn.close()
                print('connection is closed')
                credDict[user][1] = 0
                break
            else:
                conn.sendall(('echo: ' + data).encode('utf-8'))
        

'''Lets only authenticated users log in'''
def authenticate(conn):
    global credDict
    global blockDuration
    global users
    usernamePrompt = 'Enter your username here: '
    conn.sendall(usernamePrompt.encode('utf-8'))
    loginUsername = conn.recv(1024).decode('utf-8')

    if (loginUsername in credDict):
        login_attempt = 1
        while login_attempt <= 3:
            passwordPrompt = 'Enter your password here: '
            conn.sendall(passwordPrompt.encode('utf-8'))
            loginPassword = conn.recv(1024).decode('utf-8')
            if (credDict[loginUsername][0] == loginPassword) and (credDict[loginUsername][1] == 0):
                credDict[loginUsername][1] = 1
                success_msg = 'You have successfully logged in!'
                conn.sendall(success_msg.encode('utf-8'))
                users[conn] = loginUsername
                return True
            elif (credDict[loginUsername][0] == loginPassword) and (credDict[loginUsername][1] == 1):
                conn.sendall('This account is already logged in.'.encode('utf-8'))
                return authenticate(conn)
            else:
                conn.sendall('Incorrect password. Try again.'.encode('utf-8'))
                login_attempt += 1
        conn.sendall(('Too many login attempts. You have been blocked for '+ str(blockDuration) + ' seconds.').encode('utf-8'))
        time.sleep(blockDuration)
        authenticate(conn)
    else:
        conn.sendall(('Cannot find user with that username. Please try again.').encode('utf-8'))
        authenticate(conn)





serverSock.listen()   #Server starts listening for connections
accept_connections(serverSock)
serverSock.close()