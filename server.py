import socket
import time
import sys
import os
import watchdog
import string
import random

os.mkdir('./ServerData')

port = sys.argv[1]
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(('', port))
server.listen(5)

# socket.timeout(20)

while True:
    client_socket, client_address = server.accept()
    print('Connection from: ', client_address)

    data = client_socket.recv(100)
    print('Received: ', data)

    client_socket.send(data.upper())
    client_socket.close()

    print('Client disconnected')
