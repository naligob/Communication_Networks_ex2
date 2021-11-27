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
    clientKey = ''.join(random.choices(
        string.ascii_lowercase + string.ascii_uppercase + string.digits, k=128))
    clientPath = DATADIRNAME + '/' + str(clientsFilesCounter)
    os.mkdir(clientPath)
    clientSet = {client_address}
    utdList = {client_address}
    clientsData[clientKey] = {
        'path': clientPath, 'up_to_date': utdList, 'CS': clientSet}
    return clientKey, clientsData


def sendAllDirFromPath(path, clientSocket):
    allDirs = ''
    # if os.path.isdir(path):
    #     allDirs += path[len(DATADIRNAME):]
    for dirname, dirnames, filenames in os.walk(path):
        for subdirname in dirnames:
            p = dirname[len(path):]
            allDirs += SEPARATOR + p + '/' + subdirname
    if allDirs == '':
        clientSocket.send(b'EMPTY**')
    else:
        clientSocket.send(f'{allDirs}'.encode())
    ack = clientSocket.recv(BUFFER)


def getAllFilesFromPath(path):  # need to send each file in send function
    allFiles = set()
    for dirname, dirnames, filenames in os.walk(path):
        for filename in filenames:
            p = dirname[len(path):]
            allFiles.add(p + '/' + filename)
    if os.path.isfile(path):
        allFiles.add(path[len(DATADIRNAME):])
    return allFiles


def updateCheck(key, client_address, clientsData):
    if client_address in clientsData[key]['CS']:
        if client_address not in clientsData[key]['up_to_date']:
            print('True')
            clientsData[key]['up_to_date'].add(client_address)
            return True
    return False


def sendAllFile(filesSet, client_socket, path):
    all_files = ''
    for file in filesSet:
        with open(path + file, 'rb') as f:
            all_files += SEPARATOR + file + \
                "??" + str(len(f.read(BUFFER)))
    if all_files == '':
        client_socket.send(f'EMPTY'.encode())
    else:
        client_socket.send(f'{all_files}'.encode())
    for file in filesSet:
        fileName = client_socket.recv(BUFFER).decode()
        with open(path + fileName, 'rb') as f:
            while True:
                bytesRead = f.read(BUFFER)
                if len(bytesRead) == 0:
                    break
                client_socket.send(bytesRead)
                if len(bytesRead) < BUFFER:
                    break
                fileName = client_socket.recv(BUFFER).decode()

    ack = client_socket.recv(BUFFER)


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
            print(cmdName)
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


def makeLocalClient(clientsData):
    key = 'RlrVBr0VZk3VIx2YZJfW6L3H5QN7DFkt9dTXlPVAmGuTp2cwweCTiz5Aw6gPJtkZ5pYtpxoSVgNA5cTQdk63Yxq4Ka3RmyzLFnMfROaPtLnIlBGJgXh1TmBQrpNaTfDx'
    clientSet = {'10.0.2.4'}
    utdList = {'10.0.2.4'}
    clientsData[key] = {
        'path': DATADIRNAME + '/1', 'up_to_date': utdList, 'CS': clientSet}
    return clientsData


def main():
    # os.mkdir(DATADIRNAME)  # maybe need to check if exsits
    clientsData = {}
    clientsData = makeLocalClient(clientsData)
    port = int(sys.argv[1])
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
        print(f'client: {client_address}')
        if userCase == 0:
            clientID, clientsData = newClientReg(
                clientsFilesCounter, client_address, clientsData)
            clientsFilesCounter += 1
            key = clientID
            print(f'client key: {key}')
        else:
            clientsData[key]['CS'].add(client_address)
        clientAbsolutePath = clientsData[key]['path']
        if updateCheck(key, client_address, clientsData):  # known user
            print('known user!!')
            print(client_address)
            client_socket.send(f'{key}{SEPARATOR}{YES}'.encode())
            sendAllDirFromPath(clientAbsolutePath, client_socket)
            sendAllFile(getAllFilesFromPath(clientAbsolutePath),
                        client_socket, clientAbsolutePath)
            print('updated!!')
        else:
            client_socket.send(f'{key}{SEPARATOR}{NO}'.encode())
        if runCommands(client_socket, clientAbsolutePath):  # true if have command
            print('entered last_modified')
            newutdList = {client_address}
            print('before update:')
            print(clientsData)
            print()
            clientsData[key]['up_to_date'] = newutdList
            print('after update:')
            print(clientsData)
            print()
        else:
            print('skip last modifid')

        client_socket.close()


if __name__ == '__main__':
    main()
