import socket
import time
import sys
import os
from watchdog.observers import Observer
from watchdog.events import EVENT_TYPE_DELETED, LoggingEventHandler

BUFFER = 100000
SEPARATOR = "**"
EMPTY = "EMPTY"
FLAG = False
events_list = []
# file = "data"
ip = sys.argv[1]
port = int(sys.argv[2])
file = sys.argv[3]


def on_created(event):
    print(event)
    temp = str(event.src_path)[len(file):]
    events_list.append("on_created**" + temp)


def on_deleted(event):
    print(EVENT_TYPE_DELETED)
    events_list.append("on_deleted**" + str(event.src_path)[len(file):])


def on_modified(event):
    print(event)
    temp = str(event.src_path)[len(file):]
    events_list.append("on_modified**" + temp)


def on_moved(event):
    print(event)
    src = str(event.src_path)[len(file):]
    dest = str(event.dest_path)[len(file):]
    events_list.append("on_moved**" + src +
                       "**" + dest)


def get_all_files_from_path(path):  # need to send each file in send function
    allFiles = set()
    for dirname, dirnames, filenames in os.walk(path):
        for filename in filenames:
            p = dirname[len(file):]
            allFiles.add(p + '/' + filename)
    if os.path.isfile(path):
        allFiles.add(path[len(file):])
    return allFiles


def send_all_files(filesSet, client_socket, path):
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


def send_all_dir_from_path(path, clientSocket):
    allDirs = ''
    if os.path.isdir(path):
        allDirs += path[len(file):]
    for dirname, dirnames, filenames in os.walk(path):
        for subdirname in dirnames:
            p = dirname[len(file):]
            allDirs += SEPARATOR + p + '/' + subdirname
    if allDirs == '':
        clientSocket.send(b'EMPTY**')
    else:
        clientSocket.send(f'{allDirs}'.encode())
    ack = clientSocket.recv(BUFFER)


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
    # print(fileList)
    if fileList[0] == '':
        fileList.pop(0)
    if fileList[0] == 'EMPTY':
        socket.send(f'ACK'.encode())
    else:
        creatAllFiles(fileList, path, socket)


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


def main():
    event_handler = LoggingEventHandler()
    event_handler.on_created = on_created
    event_handler.on_deleted = on_deleted
    event_handler.on_modified = on_modified
    event_handler.on_moved = on_moved
    observer = Observer()
    observer.schedule(event_handler, file, recursive=True)
    observer.start()
    waiting_time = int(sys.argv[4])
    user_name = 'New User'
    if len(sys.argv) > 5:
        user_name = sys.argv[5]
    flag = 0
    while True:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((ip, port))
        s.send(bytes(user_name, 'utf-8'))
        data = str(s.recv(BUFFER), encoding='utf-8')
        user_name = data.split(SEPARATOR)[0]
        if str(data).split(SEPARATOR)[1] == 'Y':
            # print('rigth data making copy!')
            delete(file)
            # print('after delete')
            os.mkdir(file)
            create(file, s)
            # print(f'len of events after update: {len(events_list)}')
            events_list.clear()  # all events deleted!
        if len(sys.argv) <= 5 and flag == 0:
            s.send(bytes("on_created**", 'utf-8'))
            ack = s.recv(BUFFER)
            send_all_dir_from_path(file, s)
            send_all_files(get_all_files_from_path(file), s, file)
            flag = 1
        # print('events_list length: ')
        # print(len(events_list))
        for event in events_list:
            print(event)
            s.send(bytes(event, 'utf-8'))
            ack = s.recv(BUFFER)
            event_tipe = str(event).split(SEPARATOR)[0]
            event_path = str(event).split(SEPARATOR)[1]
            if event_tipe == "on_created":
                send_all_dir_from_path(file + event_path, s)
                send_all_files(get_all_files_from_path(
                    file + event_path), s, file)
            elif event_tipe == "on_modified":
                send_all_dir_from_path(file + event_path, s)
                send_all_files(get_all_files_from_path(
                    file + event_path), s, file)
            elif event_tipe == "on_moved":
                send_all_dir_from_path(
                    file + str(event).split(SEPARATOR)[2], s)
                send_all_files(get_all_files_from_path(
                    file + str(event).split(SEPARATOR)[2]), s, file)
            events_list.remove(event)

        s.close()
        time.sleep(waiting_time)

    observer.stop()
    observer.join()


if __name__ == '__main__':
    main()
