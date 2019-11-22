import socket
import sys
import time
import threading
import datetime as dt

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

#Added some constants for blocking functionality
UNBLOCKED = True
BLOCKED = False

credDict = {}  #Creates a dictionary to store the accounts for the application. Key is username and value is a list [password, loggedIn(bool), blocked(bool)]
connections = [] #List for storing active sockets
users = {}  #Dictionary for matching a socket with their username
addresses = {} #Dictionary for matching socket with IP address and port
loginHistory = {} #Key is username, and value is the datetime for the last login
pendingMessages = {} #Key is recipient and value is a list of tuples of the form (sender, message)
blacklist = {}  #Key is user and value is a list of blacklisted usernames

try:
    f = open('credentials.txt', 'r')
    for line in f:
        account = line.split()
        username, password = account[0], account[1]
        credDict[username] = [password, 0, UNBLOCKED]     #Stores the content of credentials.txt in credDict + info about login and blocking
except:
    print('Cannot find file "credentials.txt"')

#Creates a server socket
serverSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serverSock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
serverSock.bind(serverAddress)  #Binds our server socket to the server address.

'''Lets us accept incoming client connections'''
def accept_connections(serverSock):
    global connections
    global users
    global credDict
    global timeout
    global addresses
    while True:
        clientConn, clientAddr = serverSock.accept()   #Creates a separate connection for communicating with client.
        #print('Connected by', clientAddr)
        clientConn.settimeout(timeout)
        connections.append(clientConn)
        addresses[clientConn] = clientAddr
        client_handler = threading.Thread(target=handle_client, args=[clientConn], daemon=True)  #Starts a new thread to handle the client
        client_handler.start()
        
'''Procedure to successfully log out user. Cleans up connections list and sets user to not active (0) in credDict'''
def logout(conn):
    global users
    global connections
    global credDict
    global addresses

    user = users[conn]
    conn.sendall("You've been logged out.".encode('utf-8'))
    conn.close()
    #print('Connection is closed')
    connections.remove(conn)
    credDict[user][1] = 0
    
'''Function to implement the whoelse command. Goes through currently active connections 
   and matches them with appropriate username (excludes the person who made the command).'''
def whoelse(conn):
    global users
    global connections
    global credDict
    global addresses

    usernames = []
    for user_conns in connections:
        if user_conns != conn:
            usernames.append(users[user_conns])
    if len(usernames) == 0:
        return '[Server]: No other users online at the moment.'
    return '[Server]: Online users: ' + ', '.join(usernames)


'''Function to implement the whoelsesince command. Uses the loginHistory dict and returns all users
   that has logged in in the last seconds_ago seconds.'''       
def whoelsesince(conn, seconds_ago):
    global users
    global connections
    global credDict
    global addresses
    global loginHistory
    now = dt.datetime.now()
    number_of_seconds = dt.timedelta(seconds=seconds_ago)
    since_when = now - number_of_seconds
    myself = users[conn]
    user_was_logged_in = []
    for username in loginHistory.keys():
        if username != myself and loginHistory[username] > since_when:
            user_was_logged_in.append(username)
    if len(user_was_logged_in) == 0:
        return '[Server]: No users has logged in in the last ' + str(seconds_ago) + ' seconds.'
    else:
        return '[Server]: Logged in users in the last ' + str(seconds_ago) + ' seconds: ' + ', '.join(user_was_logged_in)

'''Broadcasts a message to all users who have not blocked the broadcaster.
   Also used to implement the presence notifications'''
def broadcast(conn, message):
    global users
    global connections
    global blacklist
    blocked_broadcast = False
    broadcaster = users[conn]
    broadcast = broadcaster + ' (broadcast): ' + message
    for conns in connections:
        if conns != conn and conns in users.keys():
            other_user = users[conns]
            if other_user in blacklist.keys():
                if broadcaster in blacklist[other_user]:
                    blocked_broadcast = True
                else:
                    conns.sendall(broadcast.encode('utf-8'))
            else:
                conns.sendall(broadcast.encode('utf-8'))
    if blocked_broadcast:
        conn.sendall('[Server]: Some user has blocked you.\n'.encode('utf-8'))

'''Function to implement user blocking. Checks that user is valid and if so adds the user to the blacklist dict'''
def block_user(conn, user_to_block):
    global credDict
    global users
    global blacklist
    myself = users[conn]
    if user_to_block == myself:
        conn.sendall('[Server]: You cannot block yourself.'.encode('utf-8'))
        return
    try:
        if user_to_block in blacklist[myself]:
            conn.sendall('[Server]: User is already blocked.'.encode('utf-8'))
            return
        for usernames in credDict.keys():
            if user_to_block == usernames:
                blacklist[myself].append(user_to_block)
                conn.sendall(('[Server]: ' + user_to_block + ' has been blocked.').encode('utf-8'))
                return
        conn.sendall('[Server]: This user is invalid.'.encode('utf-8'))
        return
        
    except KeyError:
        #Case where blacklist is empty for myself
        blacklist[myself] = [user_to_block]
        conn.sendall(('[Server]: ' + user_to_block + ' has been blocked.').encode('utf-8'))
        return

'''Adds unblocking functionality'''
def unblock_user(conn, user_to_unblock):
    global credDict
    global users
    global blacklist
    myself = users[conn]
    if user_to_unblock not in credDict.keys():
        conn.sendall('[Server]: This user is invalid.'.encode('utf-8'))
        return
    if myself in blacklist.keys():
        if user_to_unblock in blacklist[myself]:
            blacklist[myself].remove(user_to_unblock)
            conn.sendall(('[Server]: ' + user_to_unblock + ' has been unblocked.').encode('utf-8'))
            return
    conn.sendall('[Server]: This user is not blocked.'.encode())

            
'''Subroutine in the message_user function. Allows for the server to store the message in the pendingMessages dict.
   This can then be used to send messages to a user who has received messages when he was offline.'''    
def offline_message_user(sender, recipient, message):
    global pendingMessages
    #pendingMessages[recipient] = []
    try:
        pendingMessages[recipient].append((sender, message))
    except KeyError:
        pendingMessages[recipient] = [(sender, message)]


'''Function to actually send the pending messages to a user when he logs in'''
def send_pending_messages(conn, username):
    global pendingMessages
    if username in pendingMessages.keys():
        conn.sendall('[Server]: Here are your messages from when you were offline:\n'.encode('utf-8'))
        while len(pendingMessages[username]) > 0:
            element = pendingMessages[username].pop(0)
            sender, message = element[0], element[1]
            conn.sendall(('<' + sender +'>: ' + message + '\n').encode('utf-8'))



'''Implements the message functionality. Checks if user is valid and if the user is online.
   If user is offline, the message is sent to be stored in pendingMessages.'''
def message_user(conn, recipient, message):
    global users
    global connections
    global credDict
    global pendingMessages
    global blacklist
    sender = users[conn]
    if recipient == sender:
        conn.sendall('[Server]: Message cannot be sent to self'.encode('utf-8'))
        return
    for username in credDict.keys():
        if recipient == username:
            for sensitive_person in blacklist.keys():
                if recipient == sensitive_person:
                    if sender in blacklist[recipient]:
                        conn.sendall('[Server]: This user has blocked you'.encode('utf-8'))
                        return
            for recipient_socket, user in users.items():
                if recipient == user and recipient_socket in connections:
                    recipient_socket.sendall(('<' + sender +'>: ' + message).encode('utf-8'))
                    return
            conn.sendall('[Server]: User is currently not online.'.encode('utf-8'))
            offline_message_user(sender, recipient, message)
            return
    conn.sendall('[Server]: This is not a valid user.'.encode('utf-8'))


'''Handler for incoming client connections. This function implements the logic part of handling the connected clients'''
def handle_client(conn):
    global users
    global connections
    global credDict
    global addresses
    global loginHistory
    try:
        welcome = '[Server]: Welcome to this messenger service. Please login. \n'
        conn.sendall(welcome.encode('utf-8'))
        if authenticate(conn):    #Checks that the connection is logged in with valid credentials
            conn.sendall('[Server]: Chat and have fun!\n'.encode())
            while True:
                #This loop checks for commands sent by the user. If they correspond to a valid command, then the corresponding
                #subroutine is called. These subroutines are implemented above.
                data = conn.recv(1024).decode('utf-8')
                data = data.split(' ', 1)
                if data[0] == 'logout':   #Logout func
                    broadcast(conn, 'Logged out.')
                    logout(conn)
                    break
                
                elif data[0] == 'whoelse':  #Whoelse functionality
                    result = whoelse(conn)
                    conn.sendall(result.encode('utf-8'))
                
                elif data[0] == 'whoelsesince':  #Whoelsesince functionality
                    try:
                        seconds_ago = int(data[1])
                        result = whoelsesince(conn, seconds_ago)
                        conn.sendall(result.encode('utf-8'))
                    except IndexError:
                        conn.sendall('[Server]: You have to include number of seconds.\n[Server]: Proper command is: "whoelsesince <seconds>"'.encode('utf-8'))
                    except ValueError:
                        conn.sendall('[Server]: Second argument must be a number.'.encode('utf-8'))
                 
                elif data[0] == 'broadcast':  #Broadcasting functionality
                    if data[1] != '':
                        broadcast(conn, data[1])
                    else:
                        conn.sendall('[Server]: Not enough arguments given. \n[Server]: Proper syntax is "broadcast <message>"'.encode('utf-8'))
                
                elif data[0] == 'message': #The message functionality
                    try:
                        args = data[1].split(' ', 1)
                        recipient, msg = args[0], args[1]
                        message_user(conn, recipient, msg)
                    except IndexError:
                        conn.sendall('[Server]: Not enough arguments given. \n[Server]: Proper syntax is "message <user> <message>"'.encode('utf-8'))
                
                elif data[0] == 'block':   #Blocking functionality
                    if data[1] != '':
                        block_user(conn, data[1])
                    else:
                        conn.sendall('[Server]: Not enough arguments given. \n[Server]: Proper syntax is "block <user>"'.encode('utf-8'))
                
                elif data[0] == 'unblock': #Unblocking functionality
                    if data[1] != '':
                        unblock_user(conn, data[1])
                    else:
                        conn.sendall('[Server]: Not enough arguments given. \n[Server]: Proper syntax is "unblock <user>"'.encode('utf-8'))
                else:
                    conn.sendall('[Server]: Not a valid command.'.encode('utf-8'))   #Sent if no proper commands are catched
    except ConnectionError:
        #print('An error occurred while connecting to ' + str(addresses[conn]) + '.')   
        #just an error check if some abrupt connectionerror occurs. The user is then marked as logged out, and other users are notified
        if conn in users.keys():
            username = users[conn]
            credDict[username][1] = 0
            broadcast(conn, 'Logged out.')

        conn.close()
        connections.remove(conn)
    except socket.timeout:     #Uses socket.timeout to implement the timeout functionality of the assignment 
        if conn in users.keys():
            username = users[conn]
            credDict[username][1] = 0
            broadcast(conn, 'Logged out.')
        conn.sendall('[Server]: Your connection has been inactive for too long. '.encode('utf-8'))
        conn.sendall("[Server]: You've been logged out.".encode('utf-8'))
        conn.close()
        connections.remove(conn)

'''Implements a simple authentication process to log in a user. Checks that user is not already logged in,
   for correct credentials and that the user hasn't made too many login attempts. If login is successful
   then a presence notification is broadcasted to the other online users.'''
def authenticate(conn):
    global credDict
    global blockDuration
    global users
    global loginHistory
    usernamePrompt = 'Enter your username here: '
    conn.sendall(usernamePrompt.encode('utf-8'))
    loginUsername = conn.recv(1024).decode('utf-8')

    if (loginUsername in credDict):
        login_attempt = 1
        while login_attempt <= 3:
            passwordPrompt = 'Enter your password here: '
            conn.sendall(passwordPrompt.encode('utf-8'))
            loginPassword = conn.recv(1024).decode('utf-8')
            if credDict[loginUsername][0] == loginPassword:
                if credDict[loginUsername][1] == 0 and credDict[loginUsername][2] == UNBLOCKED:
                    credDict[loginUsername][1] = 1
                    success_msg = 'You have successfully logged in!'
                    conn.sendall(success_msg.encode('utf-8'))
                    users[conn] = loginUsername
                    loginHistory[loginUsername] = dt.datetime.now()
                    broadcast(conn, 'I have logged in!')   #Uses the broadcast function for presence notification
                    send_pending_messages(conn, loginUsername)
                    return True

                elif credDict[loginUsername][1] == 1:
                    conn.sendall('This account is already logged in.'.encode('utf-8'))
                    return authenticate(conn)

                elif credDict[loginUsername][2] == BLOCKED:
                    conn.sendall('This account is currently blocked, try again later.'.encode('utf-8'))
                    return authenticate(conn)

            else:
                conn.sendall('Incorrect password. Try again.'.encode('utf-8'))
                login_attempt += 1

        conn.sendall(('Too many login attempts. The account has been blocked for '+ str(blockDuration) + ' seconds.').encode('utf-8'))
        credDict[loginUsername][2] = BLOCKED
        time.sleep(blockDuration)
        credDict[loginUsername][2] = UNBLOCKED
        return authenticate(conn)
    else:
        conn.sendall(('Cannot find user with that username. Please try again.').encode('utf-8'))
        return authenticate(conn)




try:
    serverSock.listen(5)   #Server starts listening for connections
    accept_connections(serverSock)   #Runs the loop to accept connections.
    serverSock.close()
except KeyboardInterrupt:   #For stopping the server manually
    serverSock.close()
    print('Server manually shutdown.')
