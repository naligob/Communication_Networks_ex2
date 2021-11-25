import socket
import sys
import os
import string
import random

DATADIRNAME = './ServerData'
SEPARATOR = "**"
BUFFER = 100000
YES = 'Y'
NO = 'N'
NEWUSER = 'New User'
EMPTY = "EMPTY"


def identifyUser(data):
    return 1 if data != 'New User' else 0


def newClientReg(clientsFilesCounter, client_address, clientsData):
    clientID = ''.join(random.choices(
        string.ascii_lowercase + string.ascii_uppercase + string.digits, k=128))
    clientPath = DATADIRNAME + '\\' + str(clientsFilesCounter)
    os.mkdir(clientPath)
    clientSet = {client_address}
    clientsData[clientID] = {
        'path': clientPath, 'last_modified': client_address, 'CS': clientSet}
    return clientID, clientsData


def sendAllDirFromPath(path, clientSocket):
    allDirs = ""
    for dirname, dirnames, filenames in os.walk(path):
        for subdirname in dirnames:
            p = dirname[len(path):]
            allDirs += p + '\\'+subdirname + SEPARATOR
    if allDirs == '':
        clientSocket.send(b'EMPTY')
    else:
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
                if bytesRead:
                    break
                client_socket.send(bytesRead)


def delete(path, clientAbsolutePath):
    if os.path.isfile(path):
        os.remove(path)
    if os.path.isdir(path):
        try:
            os.rmdir(path)
        except:
            for root, dirs, files in os.walk(path, topdown=False):
                for fileName in files:
                    os.remove(os.path.join(root, fileName))
                for dirName in dirs:
                    os.rmdir(os.path.join(root, dirName))
            if path != clientAbsolutePath:
                os.rmdir(path)


def creatAllDir(dirList, path):
    for dir in dirList:
        try:    # try new
            os.mkdir(path + dir)  # old ver
        except:  # new
            x = 0   # new, what is x


def creatAllFiles(fileList, path, socket):
    for file in fileList:
        socket.send(f'{file.split("??")[0]}'.encode())
        if int(file.split("??")[1]) > 0:
            with open(path+file.split("??")[0], 'wb') as f:
                while True:
                    data = socket.recv(BUFFER)
                    f.write(data)
                    if len(data) < BUFFER:
                        break
                    socket.send(f'{file.split("??")[0]}'.encode())
        else:
            with open(path + file.split("??")[0], 'wb') as f:
                f.write(b'')
    socket.send(f'ACK'.encode())


def create(path, socket):
    dirList = str(socket.recv(BUFFER),
                  encoding='utf-8').split(SEPARATOR)
    if dirList[0] == '':
        dirList.pop(0)
    socket.send(f'ACK'.encode())
    if dirList[0] != EMPTY:
        creatAllDir(dirList, path)
    fileList = str(socket.recv(BUFFER), encoding='utf-8')
    fileList = fileList.split(SEPARATOR)
    if fileList[0] == '':
        fileList.pop(0)
    if fileList[0] == 'EMPTY':
        socket.send(f'ACK'.encode())
    else:
        creatAllFiles(fileList, path, socket)


def modified(path, socket, clientAbsolutePath):
    delete(path, clientAbsolutePath)
    create(clientAbsolutePath, socket)


def move(srcPath, destPath, socket, clientAbsolutePath):
    delete(srcPath, clientAbsolutePath)
    create(clientAbsolutePath, socket)


def runCommands(client_socket, clientAbsolutePath):
    commandOccru = False
    while True:
        command = str(client_socket.recv(BUFFER),
                      encoding='utf-8')
        client_socket.send(f'ACK'.encode())
        if not command:
            break
        if command != 'EMPTY':
            command = command.split(SEPARATOR)
            commandOccru = True
            cmdName = command[0]
            cmdSrcPath = clientAbsolutePath + command[1]
            if cmdName == 'on_deleted':
                delete(cmdSrcPath, clientAbsolutePath)
            elif cmdName == 'on_created':
                create(clientAbsolutePath, client_socket)
            elif cmdName == 'on_modified':
                modified(cmdSrcPath, client_socket, clientAbsolutePath)
            elif cmdName == 'on_moved':
                cmdDestPath = clientAbsolutePath + command[2]
                move(cmdSrcPath, cmdDestPath, client_socket, clientAbsolutePath)
    return commandOccru


def main():
    os.mkdir(DATADIRNAME)  # maybe need to check if exsits
    clientsData = {}
    port = 33333
    # sys.argv[1]
    try:
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind(('', int(port)))
    except:
        sys.exit()

    server.listen(5)
    clientsFilesCounter = 1
    while True:
        client_socket, client_address = server.accept()
        client_address = client_address[0]
        key = str(client_socket.recv(BUFFER),
                  encoding='utf-8')
        userCase = identifyUser(key)  # 0 is new client 1 is well known
        if userCase != 1:
            clientID, clientsData = newClientReg(
                clientsFilesCounter, client_address, clientsData)
            clientsFilesCounter += 1
            key = clientID
            print(f'client key: {key}')
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
