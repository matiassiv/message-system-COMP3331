import socket
import sys
import time
import threading

serverIP = sys.argv[1]
serverPort = int(sys.argv[2])

clientSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)



clientSock.connect((serverIP, serverPort))

open = True

def recv_handler():
    global clientSock
    global open
    while True:
        recv_message = clientSock.recv(1024)
        if recv_message:
            print(recv_message.decode('utf-8'))
            if recv_message.decode('utf-8') == "You've been logged out.":
                print('ok')
                clientSock.shutdown(socket.SHUT_WR)
                clientSock.close()
                open = False
                break

def send_handler():
    global clientSock
    global open
    while open:
        send_message = input()
        clientSock.sendall(send_message.encode('utf-8'))
        if send_message == 'logout':
            clientSock.shutdown(socket.SHUT_WR)
            open = False
            break


recv_thread = threading.Thread(target=recv_handler, daemon=True)
recv_thread.start()
send_thread = threading.Thread(target=send_handler, daemon=True)
send_thread.start()

while True:
    time.sleep(0.1)
    if not open:
        break

clientSock.close()