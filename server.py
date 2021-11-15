import socket
import sys
import os
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


def delete(path):
    if os.path.isfile(path):
        os.remove(path)
    if os.path.isdir(path):
        try:
            os.rmdir(path)
        except:
            for root, dirs, files in os.walk(path, topdown=False):
                for name in files:
                    os.remove(os.path.join(root, name))
                for name in dirs:
                    os.rmdir(os.path.join(root, name))
            os.rmdir(path)


def addNewFile(filePath, data):
    with open(filePath, 'wb') as f:
        f.write(data)


def addNewDir(dirPath):
    os.mkdir(dirPath)


def modifiedData(path, isFile, fileData='none'):
    delete(path)
    if isFile:
        addNewFile(path, fileData)
    else:
        addNewDir(path)


DATADIRNAME = './ServerData'
SEPARATOR = "#"
BUFFER = 1024


def main():
    os.mkdir(DATADIRNAME)  # maybe need to check if exsits
    clientsData = {}
    port = sys.argv[1]
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('', port))
    server.listen(5)

    clientsFilesCounter = 1
    while True:
        client_socket, client_address = server.accept()
        key = str(client_socket.recv(1024),
                  encoding='utf-8')  # convert to string
        userCase = identifyUser(key)  # 0 is new client 1 is well known
        if userCase != 1:
            clientID, clientsData = newClientReg(
                clientsFilesCounter, client_address, clientsData)
            client_socket.send(f'{clientID}'.encode())
            clientsFilesCounter += 1
        else:
            clientAbsolutePath = clientsData[key]['path']
            if updateCheck(key, client_address, clientsData):  # known user
                sendAllDirFromPath(clientAbsolutePath, client_socket)
                files = getAllFilesFromPath(clientAbsolutePath)
                sendAllFile(files, client_socket, clientAbsolutePath)
                # dirsString = getAllDirFromPath(clientAbsolutePath)
                # client_socket.send(f'{dirsString}'.encode())
            # accept changes from client
            # get command
            while True:
                command = str(client_socket.recv(1024),
                              encoding='utf-8')
                if not command:
                    break
                while True:
                    data = str(client_socket.recv(1024), encoding='utf-8')
                    if not data:
                        break
                # need to added client path to currect folder
                clientPathByCommand = clientAbsolutePath + \
                    command.path  # need to get clean path
                if command == 'delete':
                    delete(clientPathByCommand)
                elif command == 'newFile':
                    addNewFile(clientPathByCommand, data)
                elif command == 'newDir':
                    addNewDir(clientPathByCommand)
                elif command == 'modified':
                    modifiedData(clientPathByCommand, command.isFile, data)
                # update last change
                clientsData[key]['last_modified'] = client_address
        client_socket.close()


if __name__ == '__main__':
    main()
