import socket
import time
import sys
import os
from watchdog.observers import Observer
from watchdog.events import LoggingEventHandler
import string
import random


BUFFER = 1024
events_list = []
ip, port = sys.argv[1], int(sys.argv[2])
file = sys.argv[3]
time = sys.argv[4]
user_name = ''
if len(sys.argv) > 5:
    print(len(sys.argv))
    user_name = sys.argv[5]


def on_created(event):
    events_list.append("on_created#" + str(event.src_path))

def on_deleted(event):
    events_list.append("on_deleted#" + str(event.src_path))

def on_modified(event):
    events_list.append("on_modified#" + str(event.src_path))

def on_moved(event):
    events_list.append("on_moved#" + str(event.src_path) + "#" + str(event.dest_path))

def getAllFilesFromPath(path):  # need to send each file in send function
    allFiles = set()
    for dirname, dirnames, filenames in os.walk(path):
        for filename in filenames:
            p = dirname[len(path):]
            allFiles.add(p + '\\'+filename)
    return allFiles

def sendAllFile(filesSet, client_socket, path):
    for file in filesSet:
        client_socket.send(f'{file}'.encode())
        with open(path + file, 'rb') as f:
            while True:
                bytesRead = f.read(BUFFER)
                if not bytesRead:
                    break
                client_socket.send(bytesRead)  # maybe send all

def sendAllDirFromPath(path, clientSocket):
    allDirs = ''
    for dirname, dirnames, filenames in os.walk(path):
        for subdirname in dirnames:
            p = dirname[len(path):]
            allDirs += p + '\\'+subdirname + SEPARATOR
    clientSocket.send(f'{allDirs}'.encode())

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
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
    s.connect((ip, port))
    if len(sys.argv) < 5 and flag == 0:
        s.send(bytes('New User','utf-8'))
    else: s.send(bytes(user_name, 'utf-8'))

    data = str(s.recv(1024), encoding='utf-8')
    user_name = str(data).rpartition("#")[0]
    if str(data).rpartition("#")[1] == 'Y':
        new_folder = s.recv()

        #get the folder

    if len(sys.argv) < 5 and flag == 0:
        sendAllDirFromPath(file, s)
        sendAllFile(getAllFilesFromPath(file), s, file)
        flag = 1

    else:
        for event in events_list:
            s.send(bytes(event,'utf-8'))
            event_tipe = str(event).rpartition("#")[0]
            event_path = str(event).rpartition("#")[1]
            if event_tipe == "on_created":
                sendAllDirFromPath(event_path,s)
                sendAllFile(getAllFilesFromPath(event_path), s, event_path)
            if event_tipe == "on_modified":
                sendAllDirFromPath(event_path, s)
                sendAllFile(getAllFilesFromPath(event_path), s, event_path)
            if event_tipe == "on_moved":
                sendAllDirFromPath(event_path.rpartition("#")[1], s)
                sendAllFile(getAllFilesFromPath(event_path.rpartition("#")[1]), s, event_path.rpartition("#")[1])
            events_list.remove(event)


    time.sleep(time)
