import socket
import sys
import time
import threading

serverIP = sys.argv[1]
serverPort = int(sys.argv[2])

OPEN = True

clientSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

def recv_handler():
    global clientSock
    global OPEN
    try:
        while True:
            recv_message = clientSock.recv(1024)
            if recv_message:
                print(recv_message.decode('utf-8'))
                if recv_message.decode('utf-8') == "You've been logged out.":
                    clientSock.shutdown(socket.SHUT_WR)
                    OPEN = False
                    break
    except ConnectionError:
        print('Server not available.')
        OPEN = False
    except:
        OPEN = False
        

def send_handler():
    global clientSock
    global OPEN
    try:
        while OPEN:
            send_message = input()
            clientSock.sendall(send_message.encode('utf-8'))
            if send_message == 'logout':
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

    recv_thread = threading.Thread(target=recv_handler, daemon=True)
    recv_thread.start()
    send_thread = threading.Thread(target=send_handler, daemon=True)
    send_thread.start()

    while True:
        time.sleep(0.1)
        if not OPEN:
            break

    clientSock.close()

except KeyboardInterrupt:
    print('User shut down connection.')
    clientSock.close()
except ConnectionError:
    print('Server not available.')
    clientSock.close()


