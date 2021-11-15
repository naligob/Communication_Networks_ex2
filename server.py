import socket
import sys
import os
import string
import random

DATADIRNAME = './ServerData'
SEPARATOR = "#"
BUFFER = 1024
YES = 'Y'
NO = 'N'


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


def sendAllFile(client_socket, path):
    filesSet = getAllFilesFromPath(path)
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


def creatAllDir(dirList, path):
    for dir in dirList:
        os.mkdir(path + dir)


def create(path, socket):
    dirList = str(socket.recv(BUFFER), encoding='utf-8').split('#')
    if len(dirList):
        creatAllDir(dirList, path)
    while True:
        fileName = socket.recv(BUFFER).decode()
        if not fileName:
            break
        with open(path+fileName, 'wb') as f:
            while True:
                data = socket.recv(BUFFER)
                if not data:
                    break
                f.write(data)


def modified(path, socket):
    delete(path)
    create(path, socket)


def move(srcPath, destPath, socket):
    delete(srcPath)
    create(destPath, socket)


def runCommands(client_socket, clientAbsolutePath):
    commandOccru = False
    while True:
        command = str(client_socket.recv(1024),
                      encoding='utf-8').split('#')
        if not command:
            break
        commandOccru = True
        cmdName = command[0]
        # client location & command path
        cmdSrcPath = clientAbsolutePath + command[1]
        if cmdName == 'on_deleted':
            delete(cmdSrcPath)
        elif cmdName == 'on_created':
            create(cmdSrcPath, client_socket)
        elif cmdName == 'on_modified':
            modified(cmdSrcPath, client_socket)
        elif cmdName == 'on_moved':
            cmdDestPath = clientAbsolutePath + command[2]
            move(cmdSrcPath, cmdDestPath, client_socket)
    return commandOccru


def main():
    os.mkdir(DATADIRNAME)  # maybe need to check if exsits
    clientsData = {}
    port = sys.argv[1]
    try:
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind(('', int(port)))
    except:
        sys.exit()

    server.listen(5)

    clientsFilesCounter = 1
    while True:
        client_socket, client_address = server.accept()
        key = str(client_socket.recv(1024),
                  encoding='utf-8')
        userCase = identifyUser(key)  # 0 is new client 1 is well known
        if userCase != 1:
            clientID, clientsData = newClientReg(
                clientsFilesCounter, client_address, clientsData)
            clientsFilesCounter += 1

        clientAbsolutePath = clientsData[key]['path']
        if updateCheck(key, client_address, clientsData):  # known user
            client_socket.send(f'{clientID}{SEPARATOR}{YES}'.encode())
            sendAllDirFromPath(clientAbsolutePath, client_socket)
            sendAllFile(client_socket, clientAbsolutePath)
        else:
            client_socket.send(f'{clientID}{SEPARATOR}{NO}'.encode())
        if runCommands(client_socket, clientAbsolutePath):  # true if have command
            clientsData[key]['last_modified'] = client_address

        client_socket.close()


if __name__ == '__main__':
    main()
