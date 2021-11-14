import socket
import time
import sys
import os
import watchdog
import string
import random


def identifyUser(data):
    return 1 if data != 'New User' else 0


def newClientReg(dataDirName, clientCount, client_address, clientsData):
    clientID = random.choices(
        string.ascii_lowercase + string.ascii_uppercase + string.digits, 128)
    clientPath = dataDirName + str(clientCount)
    os.mkdir(clientPath)
    clientSet = {client_address}
    clientsData[clientID] = {
        'path': clientPath, 'last_modified': client_address, 'clientSet': clientSet}

    return clientID, clientsData


# clients data dictionery {key=user_id , values: path ot file
#                                                , addr of the last modifier client
#                                                   , list of computers}
dataDirName = './ServerData'
os.mkdir(dataDirName)  # maybe need to check if exsits
clientsData = {}
port = sys.argv[1]
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(('', port))
server.listen(5)

clientCount = 1
while True:
    client_socket, client_address = server.accept()
    # print('Connection from: ', client_address)
    data = str(client_socket.recv(1024), encoding='utf-8')  # convert to string
    # print('Received: ', data)
    userCase = identifyUser(data)  # 0 is new client 1 is well known
    # need to generate new id, new client registration and new file to uploud
    if userCase != 1:
        clientID, clientsData = newClientReg(
            dataDirName, clientCount, client_address, clientsData)
        client_socket.send(bytes(clientID, 'utf-8'))
        clientCount += 1

    # client_socket.send(data.upper())
    client_socket.close()

# find client in dict
# if client in clientsData[clientID]['clientSet']:
#   make somthing...
