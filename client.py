import socket
import sys
import time
import threading
import datetime

serverIP = sys.argv[1]
serverPort = int(sys.argv[2])

OPEN = True    #Simple check to see if connection with server is still open (in case of server crashing)

clientSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

'''Function that let's the client print information from the server to the user. Basically allows us to see messages
   and other prompts'''
def recv_handler():
    global clientSock
    global OPEN
    try:
        while True:
            recv_message = clientSock.recv(1024)
            if recv_message:
                print(recv_message.decode('utf-8'))
                if recv_message.decode('utf-8') == "[Server]: You've been logged out.":
                    clientSock.shutdown(socket.SHUT_WR)
                    OPEN = False
                    break
    except ConnectionError:
        print('Server not available.')
        OPEN = False
    except:
        OPEN = False
        

'''Function that lets the user send messages to the server'''
def send_handler():
    global clientSock
    global OPEN
    try:
        while OPEN:
            send_message = input('> ')
            clientSock.sendall(send_message.encode('utf-8'))
            if send_message == 'logout':   #Logout functionality
                clientSock.shutdown(socket.SHUT_WR)
                OPEN = False
                break
    except ConnectionError:
        print('Server not available.')
        OPEN = False
    except:
        OPEN = False


try:
    
    clientSock.connect((serverIP, serverPort))
    #Runs two threads to separately handle receiving messages and sending messages.
    recv_thread = threading.Thread(target=recv_handler, daemon=True) 
    recv_thread.start()
    send_thread = threading.Thread(target=send_handler, daemon=True)
    send_thread.start()

    while True:
        time.sleep(0.1)
        if not OPEN:
            break

    clientSock.close()

#In case of server abruptly stopping or client exiting without logging out.
except KeyboardInterrupt:
    print('User shut down connection.')
    clientSock.close()
except ConnectionError:
    print('Server not available.')
    clientSock.close()


