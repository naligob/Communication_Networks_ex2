import socket
import time
import sys
import os
import watchdog
import string
import random


def identifyUser(data):
    return 1 if data != 'New User' else 0


def newClientReg(clientsFilesCounter, client_address, clientsData):
    clientID = random.choices(
        string.ascii_lowercase + string.ascii_uppercase + string.digits, 128)
    clientPath = DATADIRNAME + str(clientsFilesCounter)
    os.mkdir(clientPath)
    clientSet = {client_address}
    clientsData[clientID] = {
        'path': clientPath, 'last_modified': client_address, 'CS': clientSet}
    return clientID, clientsData


def sendAllDirFromPath(path, clientSocket):
    allDirs = ''
    for dirname, dirnames, filenames in os.walk(path):
        for subdirname in dirnames:
            p = dirname[len(path):]
            allDirs += p + '\\'+subdirname + SEPARATOR
    clientSocket.send(f'{allDirs}'.encode())


def getAllDirFromPath(path):
    allDirs = ''
    for dirname, dirnames, filenames in os.walk(path):
        for subdirname in dirnames:
            p = dirname[len(path):]
            allDirs += p + '\\'+subdirname + SEPARATOR
    return allDirs


def getAllFilesFromPath(path):  # need to send each file in send function
    allFiles = set()
    for dirname, dirnames, filenames in os.walk(path):
        for filename in filenames:
            p = dirname[len(path):]
            allFiles.add(p + '\\'+filename)
    return allFiles


def updateCheck(key, client_address, clientsData):
    if client_address in clientsData[key]['CS'] and client_address not in clientsData[key]['last_modified']:
        return True
    return False


def sendAllFile(filesSet, client_socket, path):
    for file in filesSet:
        client_socket.send(f'{file}'.encode())
        with open(path + file, 'rb') as f:
            while True:
                bytesRead = f.read(BUFFER)
                if not bytesRead:
                    break
                client_socket.send(bytesRead)  # maybe send all


DATADIRNAME = './ServerData'
SEPARATOR = "#"
BUFFER = 1024
os.mkdir(DATADIRNAME)  # maybe need to check if exsits
clientsData = {}
port = sys.argv[1]
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(('', port))
server.listen(5)

clientsFilesCounter = 1
while True:
    client_socket, client_address = server.accept()
    key = str(client_socket.recv(1024), encoding='utf-8')  # convert to string
    userCase = identifyUser(key)  # 0 is new client 1 is well known
    if userCase != 1:
        clientID, clientsData = newClientReg(
            clientsFilesCounter, client_address, clientsData)
        client_socket.send(f'{clientID}'.encode())
        clientsFilesCounter += 1
    else:
        if updateCheck(key, client_address, clientsData):  # known user
            clientAbsolutePath = clientsData[key]['path']
            sendAllDirFromPath(clientAbsolutePath, client_socket)
            files = getAllFilesFromPath(clientAbsolutePath)
            sendAllFile(files, client_socket, clientAbsolutePath)
            # dirsString = getAllDirFromPath(clientAbsolutePath)
            # client_socket.send(f'{dirsString}'.encode())

    client_socket.close()

# find client in dict
# if client in clientsData[clientID]['clientSet']:
#   make somthing...
