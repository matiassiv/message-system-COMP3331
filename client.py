import socket
import sys
import time
import threading

serverIP = sys.argv[1]
serverPort = int(sys.argv[2])

clientSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

clientSock.connect((serverIP, serverPort))

def recv_handler():
    global clientSock
    while True:
        recv_message = clientSock.recv(1024)
        if recv_message:
            print(recv_message.decode('utf-8'))
        if recv_message == "You've been logged out.":
            break

def send_handler():
    global clientSock
    while recv_thread.is_alive():
        send_message = input()
        clientSock.sendall(send_message.encode('utf-8'))


recv_thread = threading.Thread(target=recv_handler, daemon=True)
recv_thread.start()
send_thread = threading.Thread(target=send_handler, daemon=True)
send_thread.start()

while True:
    time.sleep(0.1)
    if not recv_thread.is_alive() or not send_thread.is_alive():
        print('ok')
        time.sleep(1.0)
        break

clientSock.close()