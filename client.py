import socket
import time
import sys
import os
from watchdog.observers import Observer
from watchdog.events import LoggingEventHandler

BUFFER = 4096
SEPARATOR = "**"
EMPTY = "EMPTY"
events_list = []
file = "data"

def on_created(event):
    events_list.append("on_created**" + str(event.src_path)[len(file):])


def on_deleted(event):
    events_list.append("on_deleted**" + str(event.src_path)[len(file):])


def on_modified(event):
    events_list.append("on_modified**" + str(event.src_path)[len(file):])


def on_moved(event):
    events_list.append("on_moved**" + str(event.src_path)[len(file):] +
                       "**" + str(event.dest_path)[len(file):])


def get_all_files_from_path(path):  # need to send each file in send function
    allFiles = set()
    for dirname, dirnames, filenames in os.walk(path):
        for filename in filenames:
            p = dirname[len(path):]
            allFiles.add(p + '\\' + filename)
    return allFiles


def send_all_files(filesSet, client_socket, path):
    all_files = ''
    for file in filesSet:
        all_files += SEPARATOR + file
    client_socket.send(f'{all_files}'.encode())
    for file in filesSet:
        fileName = client_socket.recv(BUFFER).decode()
        with open(path + fileName, 'rb') as f:
            while True:
                bytesRead = f.read(BUFFER)
                if len(bytesRead) == 0:
                    break
                client_socket.send(bytesRead)

def send_all_dir_from_path(path, clientSocket):
    allDirs = ''
    for dirname, dirnames, filenames in os.walk(path):
        for subdirname in dirnames:
            p = dirname[len(path):]
            allDirs += p + '\\' + subdirname + SEPARATOR
    if allDirs == '':
        clientSocket.send(b'EMPTY')
    else:
        clientSocket.send(f'{allDirs}'.encode())


def creatAllDir(dirList, path):
        for dir in dirList[:-1]:

            os.mkdir(path + dir)


def creatAllFiles(fileList, path, socket):
    for file in fileList[1:]:
        print("file sent:" + file + str(len(fileList[1:])))
        socket.send(f'{file}'.encode())
        print("file sent:" + file)
        with open(path+file, 'wb') as f:
            while True:
                data = socket.recv(BUFFER)
                f.write(data)
                if len(data) < BUFFER:
                    break


def create(path, socket):
    dirList = str(socket.recv(BUFFER), encoding='utf-8').split(SEPARATOR)
    if dirList[0] != EMPTY:
        creatAllDir(dirList, path)
    fileList = str(socket.recv(BUFFER), encoding='utf-8').split(SEPARATOR)
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
    ip = "127.0.0.1" #"89.138.213.122"
    port = 33333
    waiting_time = float(10)
    user_name = 'New User'
    if len(sys.argv) > 5:
        user_name = sys.argv[5]
    event_handler = LoggingEventHandler()
    event_handler.on_created = on_created
    event_handler.on_deleted = on_deleted
    event_handler.on_modified = on_modified
    event_handler.on_moved = on_moved
    observer = Observer()
    observer.schedule(event_handler, file, recursive=True)
    observer.start()
    flag = 0
    while True:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((ip, port))
        s.send(bytes(user_name, 'utf-8'))
        data = str(s.recv(BUFFER), encoding='utf-8')
        user_name = data.split(SEPARATOR)[0]
        if str(data).split(SEPARATOR)[1] == 'Y':
            delete(file)
            os.mkdir(file)
            create(file, s)

        if len(sys.argv) <= 5 and flag == 0:
            s.send(bytes("on_created**", 'utf-8'))
            send_all_dir_from_path(file, s)
            send_all_files(get_all_files_from_path(file), s, file)
            flag = 1

        else:
            for event in events_list:
                s.send(bytes(event, 'utf-8'))
                event_tipe = str(event).split(SEPARATOR)[0]
                event_path = str(event).split(SEPARATOR)[1]
                if event_tipe == "on_created":
                    send_all_dir_from_path(event_path, s)
                    send_all_files(get_all_files_from_path(event_path), s, event_path)
                if event_tipe == "on_modified":
                    send_all_dir_from_path(event_path, s)
                    send_all_files(get_all_files_from_path(event_path), s, event_path)
                if event_tipe == "on_moved":
                    send_all_dir_from_path(str(event).split(SEPARATOR)[2], s)
                    send_all_files(get_all_files_from_path(str(event).split(SEPARATOR)[2]), s, event_path.rpartition(SEPARATOR)[1])
                events_list.remove(event)

        s.close()
        time.sleep(waiting_time)

    observer.stop()
    observer.join()



if __name__ == '__main__':
    main()
