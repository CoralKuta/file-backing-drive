# Noa Eitan 316222777, Coral Kuta 208649186
import os.path
import socket
import sys
import time
from watchdog.observers import polling
from watchdog.events import PatternMatchingEventHandler

MAX_PORT = 65545
MIN_PORT = 0
ARGUMENTS_WITH_ID = 6
ARGUMENTS_WITHOUT_IS = 5
NUMBER_IN_IP = 4
MAX_IP_NUM = 255
MIN_IP_NUM = 0
SIZE_ID = 128
BYTES_TO_READ = 1024
NO_SEQUENCE_NUMBER = 0

# list of all files and folders in the path
global files_and_folders
# create socket with TCP protocol
global socket_client
global global_path
global global_folder
global global_identifier
global global_sequence_number
global global_ip
global global_port


def track_data_with_id(ip, port, path, timer, identifier):
    global files_and_folders
    global socket_client
    global global_path
    global global_folder
    global global_identifier
    global global_sequence_number
    global global_ip
    global global_port
    global_ip = ip
    global_port = int(port)
    global_identifier = identifier
    files_and_folders = []
    # create socket with TCP protocol
    socket_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # save the path to the folder that we want to save and monitor via server
    files_and_folders.append(path)
    global_path = path
    _, global_folder = os.path.split(global_path)
    # connect to server (SYN) - save him the identifier
    socket_client.connect((ip, int(port)))
    # send the identifier to the server
    socket_client.send(bytes(identifier, 'UTF-8'))
    # send the server that we dont have sequence number now
    socket_client.send(NO_SEQUENCE_NUMBER.to_bytes(8, sys.byteorder))
    # save the sequence number of this number
    global_sequence_number = int.from_bytes(socket_client.recv(8), sys.byteorder)
    # pull the data from the server
    pull_data()
    # disconnect from server
    socket_client.close()
    # start monitor the data with the server.
    track_data(path, timer)


def pull_data():
    while True:
        option = socket_client.recv(1).decode('UTF-8', "ignore")
        # no more data to pull
        if option == "0":
            break
        # create new file
        elif option == "1":
            create_new_file()
        # create new folder
        elif option == "2":
            create_new_folder()


def track_data_without_id(ip, port, path, timer):
    global files_and_folders
    global socket_client
    global global_path
    global global_folder
    global global_identifier
    global global_sequence_number
    global global_ip
    global global_port
    global_ip = ip
    global_port = int(port)
    files_and_folders = []
    # create socket with TCP protocol
    socket_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # save the path to the folder that we want to save and monitor via server
    files_and_folders.append(path)
    global_path = path
    _, global_folder = os.path.split(global_path)
    # connect to server (SYN) and get identifier
    socket_client.connect((ip, int(port)))
    # ask the server for identifier
    id_str = "ID".zfill(SIZE_ID)
    socket_client.send(bytes(id_str, 'UTF-8'))
    identifier = socket_client.recv(SIZE_ID).decode('UTF-8', "ignore")
    print(identifier)
    global_identifier = identifier
    # save the sequence number of this number
    global_sequence_number = int.from_bytes(socket_client.recv(8), sys.byteorder)
    # send data to server
    send_data_first_time()
    # send 0 to server- means that we finished send the files, start tracking
    socket_client.send(bytes("0", 'UTF-8'))
    # end of talk with server
    socket_client.close()
    # start monitor the data with the server.
    track_data(path, timer)


def send_data_first_time():
    for root, dirs, files in os.walk(global_path):
        # only sub-directories
        for directory_name in dirs:
            directory_path = os.path.join(root, directory_name)
            send_folder_relative_path(directory_path)
            # add the folder to the list of fies and folders
            files_and_folders.append(directory_path)
        # only files
        for file_name in files:
            file_path = os.path.join(root, file_name)
            send_file(file_name, file_path)
            # add the file to the list of fies and folders
            files_and_folders.append(file_path)


def send_name(name):
    length = len(name)
    socket_client.send(length.to_bytes(8, sys.byteorder))
    socket_client.send(bytes(name, 'UTF-8'))


def send_length(data):
    length = os.path.getsize(data)
    socket_client.send(length.to_bytes(8, sys.byteorder))


def send_folder_relative_path(folder_path):
    # send 2 to server- means that we send a folder in current
    socket_client.send(bytes("2", 'UTF-8'))
    # send to server the relative path
    send_relative_path(folder_path)


def send_relative_path(path):
    relative_path = os.path.relpath(path, global_path)
    mother_path, name = os.path.split(relative_path)
    list_split_path = [name]
    while mother_path != "":
        mother_path, name = os.path.split(mother_path)
        list_split_path.append(name)
    list_split_path.reverse()
    # send the size of the split objects in the relative path to server
    socket_client.send(len(list_split_path).to_bytes(8, sys.byteorder))
    for name in list_split_path:
        send_name(name)


def send_file(file_name, file_path):
    # send 1 to server- means that we send a file
    socket_client.send(bytes("1", 'UTF-8'))
    # send file name
    send_name(file_name)
    # send the server the relative path
    send_relative_path(file_path)
    # send the size of the file
    send_length(file_path)
    # start send the data that in the file
    file = open(file_path, "rb")
    data = file.read(BYTES_TO_READ)
    # send the bytes in the file
    while data:
        socket_client.send(data)
        data = file.read(BYTES_TO_READ)
    file.close()


def send_file_to_remove_or_moved(file_name, file_path):
    # send 1 to server- means that we send a file
    socket_client.send(bytes("1", 'UTF-8'))
    # send file name
    send_name(file_name)
    # send where the file belongs (the relative path)
    send_relative_path(file_path)


def get_full_path():
    new_path = global_path
    iterations = int.from_bytes(socket_client.recv(8), sys.byteorder)
    print(iterations)
    for i in range(iterations):
        path_part = get_name()
        new_path = os.path.join(new_path, path_part)
    new_path = os.path.normpath(new_path)
    print(new_path)
    return new_path


def track_data(path, timer):
    global socket_client
    # initial the event handler
    patterns = ["*"]
    ignore_patterns = None
    ignore_directories = False
    case_sensitive = True
    my_event_handler = PatternMatchingEventHandler(patterns, ignore_patterns, ignore_directories, case_sensitive)
    my_event_handler.on_created = on_created
    my_event_handler.on_deleted = on_deleted
    my_event_handler.on_modified = on_modified
    my_event_handler.on_moved = on_moved
    go_recursively = True
    # initial observer, that monitor after changes
    my_observer = polling.PollingObserver()
    my_observer.schedule(my_event_handler, path, recursive=go_recursively)
    # start monitor changes
    my_observer.start()
    try:
        while True:
            # sleep to some time
            time.sleep(int(timer))
            # create socket with TCP protocol
            socket_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # connect to server (SYN) and get identifier
            socket_client.connect((global_ip, global_port))
            # send the server the id
            socket_client.send(bytes(global_identifier, 'UTF-8'))
            # send the server out seq number
            socket_client.send(global_sequence_number.to_bytes(8, sys.byteorder))
            # send 4 to server- means that we waked up, and we want to pull changes
            socket_client.send(bytes("4", 'UTF-8'))
            while True:
                option = socket_client.recv(1).decode('UTF-8', "ignore")
                # no more changes
                if option == "0":
                    # end of talk with server
                    break
                # created new folder/file
                elif option == "6":
                    option = socket_client.recv(1).decode('UTF-8', "ignore")
                    # file
                    if option == "1":
                        create_new_file()
                    # create new folder
                    elif option == "2":
                        create_new_folder()
                # file/folder has been deleted
                elif option == "7":
                    option = socket_client.recv(1).decode('UTF-8', "ignore")
                    # delete file
                    if option == "1":
                        delete_file()
                    # delete folder
                    elif option == "2":
                        delete_folder()
                # file/folder has been moved
                elif option == "8":
                    option = socket_client.recv(1).decode('UTF-8', "ignore")
                    # move file
                    if option == "1":
                        move_file()
                    # move folder
                    elif option == "2":
                        move_folder()
                # file/folder has been modified
                elif option == "9":
                    option = socket_client.recv(1).decode('UTF-8', "ignore")
                    # modify folder - rename file name
                    if option == "1":
                        rename_file_name()
                    # modify folder - rename folder name
                    elif option == "2":
                        rename_folder_name()
            socket_client.close()

    except KeyboardInterrupt:
        my_observer.stop()
        socket_client.close()
    my_observer.join()


def create_new_file():
    print("creating new file")
    # name of a new file
    file_name = get_name()
    # the path of the new file (where to create)
    new_path = get_full_path()
    if os.path.exists(new_path):
        return
    # write
    file_to_write = open(new_path, "wb")
    # getting the size of file
    file_len = int.from_bytes(socket_client.recv(8), sys.byteorder)
    counter = file_len

    if file_len < BYTES_TO_READ:
        file = socket_client.recv(file_len)
    else:
        file = socket_client.recv(BYTES_TO_READ)

    while file:
        file_to_write.write(file)
        counter = counter - len(file)
        if counter <= 0:
            break
        elif counter < BYTES_TO_READ:
            file = socket_client.recv(counter)
        else:
            file = socket_client.recv(BYTES_TO_READ)
    print("Download Completed")
    file_to_write.close()
    files_and_folders.append(new_path)


def create_new_folder():
    print("create new folder")
    # the path of the new folder (where to create)
    new_path = get_full_path()
    if os.path.exists(new_path):
        return
    os.mkdir(new_path)
    # adding the new folder to the list
    files_and_folders.append(new_path)


def delete_file():
    print("delete file")
    # name of a new file
    file_name = get_name()
    # the path of the file
    path_to_remove = get_full_path()
    if not os.path.exists(path_to_remove):
        return
    # remove the file
    if os.path.exists(path_to_remove):
        os.remove(path_to_remove)
    files_and_folders.remove(path_to_remove)


def delete_folder():
    print("delete folder")
    # the path of the folder
    path_to_remove = get_full_path()
    if not os.path.exists(path_to_remove):
        return
    # initial list - the paths to delete at the end of the function (the init files and folders in this path)
    to_delete = []
    # delete the files and folders that in the folder
    for root, dirs, files in os.walk(path_to_remove, topdown=False):
        for name in files:
            os.remove(os.path.join(root, name))
            to_delete.append(os.path.join(root, name))
        for name in dirs:
            os.rmdir(os.path.join(root, name))
            to_delete.append(os.path.join(root, name))
    # remove the folder
    os.rmdir(path_to_remove)
    # remove the folder from the list
    files_and_folders.remove(path_to_remove)
    # remove the init files and folders from the list
    for path in to_delete:
        files_and_folders.remove(path)


def rename_file_name():
    print("rename file")
    # save the old path
    old_path = get_full_path()
    # save the new path
    new_path = get_full_path()
    # if the new path is already exist
    if os.path.exists(new_path):
        return
    # rename the folder
    os.rename(old_path, new_path)
    # remove the oldest folder and add the new folder, from the list of folders
    files_and_folders.remove(old_path)
    files_and_folders.append(new_path)


def rename_folder_name():
    print("rename folder")
    # save the old path
    old_path = get_full_path()
    # save the new path
    new_path = get_full_path()
    # if the new path is already exist
    if os.path.exists(new_path):
        return
    # scan files and folders of the new path and remove them to files_and_folders
    for root, dirs, files in os.walk(old_path, topdown=False):
        for name in files:
            files_and_folders.remove(os.path.join(root, name))
        for name in dirs:
            files_and_folders.remove(os.path.join(root, name))
    # rename the name of the folder
    os.rename(old_path, new_path)
    # append and remove the folder from the files_and_folders
    files_and_folders.remove(old_path)
    files_and_folders.append(new_path)
    # remove the oldest paths that into old_path
    for root, dirs, files in os.walk(new_path, topdown=False):
        for name in files:
            files_and_folders.append(os.path.join(root, name))
        for name in dirs:
            files_and_folders.append(os.path.join(root, name))


def move_file():
    print("move file")
    # name of a new file
    file_name = get_name()
    # the path of the file
    old_path = get_full_path()
    # name of a new file
    file_name = get_name()
    # the path of the file
    new_path = get_full_path()
    print(new_path)
    # replace - put the file in the new path and remove from the oldest
    os.replace(old_path, new_path)
    files_and_folders.remove(old_path)
    files_and_folders.append(new_path)


def move_folder():
    print("move folder")
    # save the old path
    old_path = get_full_path()
    # save the new path
    new_path = get_full_path()
    # replace - put the whole files in the new path
    os.mkdir(new_path)
    # list of folders to delete (the init folders)
    init_files = []
    # scan all files and folders that in the old path and put them into the new path
    for root, dirs, files in os.walk(old_path, topdown=True):
        for name in dirs:
            relative_path = os.path.relpath(os.path.join(root, name), old_path)
            # move to the new folder
            os.mkdir(os.path.join(new_path, relative_path))
            init_files.append(os.path.join(old_path, relative_path))
            # remove and append from the files_and_folders
            files_and_folders.append(os.path.join(new_path, relative_path))
            files_and_folders.remove(os.path.join(old_path, relative_path))
        for name in files:
            relative_path = os.path.relpath(os.path.join(root, name), old_path)
            # move to the new folder
            os.replace(os.path.join(old_path, relative_path), os.path.join(new_path, relative_path))
            # remove and append from the files_and_folders
            files_and_folders.append(os.path.join(new_path, relative_path))
            files_and_folders.remove(os.path.join(old_path, relative_path))
    init_files.reverse()
    for folder in init_files:
        os.rmdir(folder)
    # remove the old folder
    os.rmdir(old_path)
    # remove old folder from files and folders
    files_and_folders.remove(old_path)
    # add the new folder to files and folders
    files_and_folders.append(new_path)


def on_created(event):
    global socket_client
    print(f"hey, {event.src_path} has been created!")
    # get the path of the event that created
    path = event.src_path
    # if the file or folder is already exist
    if path in files_and_folders:
        return
    # get the file/folder name
    _, name = os.path.split(path)
    # if this an temporary file - do not create
    if path.endswith('swp'):
        return
    # if this is outputstream file - do not create
    if '.goutputstream' in path:
        return
    # get the mother path of the new path
    mother_path, _ = os.path.split(path)
    # if the mother path does not exist- so do not send, because this is an init file/folder
    if mother_path not in files_and_folders:
        print("it's not an existing folder return")
        return
    # create socket with TCP protocol
    socket_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # connect to server (SYN)
    socket_client.connect((global_ip, global_port))
    # send the server the id
    socket_client.send(bytes(global_identifier, 'UTF-8'))
    # send the server out seq number
    socket_client.send(global_sequence_number.to_bytes(8, sys.byteorder))
    # send 5 to server- means that we have an update to send to him
    socket_client.send(bytes("5", 'UTF-8'))
    # send 6 to server- means that the update is file/folder that has been created
    socket_client.send(bytes("6", 'UTF-8'))
    if not event.is_directory:
        # send the new file to the server
        send_file(name, path)
        # add the new path to the files_and_folders
        files_and_folders.append(path)
    else:
        # send the folder that has been created
        send_folder_relative_path(path)
        # add the new path to the files_and_folders
        files_and_folders.append(path)
        for root, dirs, files in os.walk(path, topdown=True):
            # only sub-directories
            for directory_name in dirs:
                # send 5 to server- means that we have an update to send to him
                socket_client.send(bytes("5", 'UTF-8'))
                # send 6 to server- means that the update is file/folder that has been created
                socket_client.send(bytes("6", 'UTF-8'))
                send_folder_relative_path(os.path.join(root, directory_name))
                # add the folder to the list of fies and folders
                files_and_folders.append(os.path.join(root, directory_name))
            # only files
            for file_name in files:
                # send 5 to server- means that we have an update to send to him
                socket_client.send(bytes("5", 'UTF-8'))
                # send 6 to server- means that the update is file/folder that has been created
                socket_client.send(bytes("6", 'UTF-8'))
                file_path = os.path.join(root, file_name)
                send_file(file_name, file_path)
                # add the file to the list of fies and folders
                files_and_folders.append(file_path)
    # send 0 to server- means that we ended this connection
    socket_client.send(bytes("0", 'UTF-8'))
    socket_client.close()


def on_deleted(event):
    global socket_client
    print(f"what the f**k! Someone deleted {event.src_path}!")
    # get the path of the event that deleted
    path = event.src_path
    # get the file/folder name and the mother path
    _, name = os.path.split(path)
    # if the path has already deleted
    if path not in files_and_folders:
        return
    # if this is a temporary file
    if name.endswith('.swp'):
        return
    # delete from list of files and folders
    files_and_folders.remove(path)
    # create socket with TCP protocol
    socket_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # connect to server (SYN)
    socket_client.connect((global_ip, global_port))
    # send the server the id
    socket_client.send(bytes(global_identifier, 'UTF-8'))
    # send the server out seq number
    socket_client.send(global_sequence_number.to_bytes(8, sys.byteorder))
    # send 5 to server- means that we have an update to send to him
    socket_client.send(bytes("5", 'UTF-8'))
    # send 7 to server- means that the update is file/folder that has been deleted
    socket_client.send(bytes("7", 'UTF-8'))
    if not event.is_directory:
        # delete file
        print("delete file")
        send_file_to_remove_or_moved(name, path)
    else:
        # delete folder
        print("delete folder")
        send_folder_relative_path(path)
        # delete from files and folders the init files and folders
        copy_files_and_folders = files_and_folders.copy()
        for name in copy_files_and_folders:
            if name.startswith(path):
                files_and_folders.remove(name)
    # send 0 to server- means that we ended this connection
    socket_client.send(bytes("0", 'UTF-8'))
    socket_client.close()


def on_modified(event):
    print(f"hey buddy, {event.src_path} has been modified")


def on_moved(event):
    global socket_client
    print(f"ok ok ok, someone moved {event.src_path} to {event.dest_path}")
    # get the old path of the event that moved
    old_path = event.src_path
    # get the file/folder name of the source
    _, old_name = os.path.split(old_path)
    # get the new path of the event that moved
    new_path = event.dest_path
    # get the file/folder name of the destination
    _, new_name = os.path.split(new_path)

    # if this is outputstream file
    if '.goutputstream' in old_path:
        # create socket with TCP protocol
        socket_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # connect to server (SYN)
        socket_client.connect((global_ip, global_port))
        # send the server the id
        socket_client.send(bytes(global_identifier, 'UTF-8'))
        # send the server out seq number
        socket_client.send(global_sequence_number.to_bytes(8, sys.byteorder))
        # send 5 to server- means that we have an update to send to him
        socket_client.send(bytes("5", 'UTF-8'))
        # send 7 to server- means that the update is file/folder that has been deleted
        socket_client.send(bytes("7", 'UTF-8'))
        send_file_to_remove_or_moved(new_name, new_path)
        # send 5 to server- means that we have an update to send to him
        socket_client.send(bytes("5", 'UTF-8'))
        # send 6 to server- means that the update is file/folder that has been created
        socket_client.send(bytes("6", 'UTF-8'))
        send_file(new_name, new_path)
        # send 0 to server- means that we ended this connection
        socket_client.send(bytes("0", 'UTF-8'))
        socket_client.close()
        return

    # if the new_path is already exist: out
    if new_path in files_and_folders and old_path not in files_and_folders:
        return

    # get the mother path of the new path
    mother_path, _ = os.path.split(new_path)
    # if the mother path does not exist- so do not send, because this is an init file/folder
    if mother_path not in files_and_folders:
        return

    # if the folder/file has moved from outside
    if not (old_path in files_and_folders):
        # create socket with TCP protocol
        socket_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # connect to server (SYN)
        socket_client.connect((global_ip, global_port))
        # send the server the id
        socket_client.send(bytes(global_identifier, 'UTF-8'))
        # send the server out seq number
        socket_client.send(global_sequence_number.to_bytes(8, sys.byteorder))
        # send 5 to server- means that we have an update to send to him
        socket_client.send(bytes("5", 'UTF-8'))
        # send 6 to server- means that the update is file/folder that has been created
        socket_client.send(bytes("6", 'UTF-8'))
        # the source is file
        if not event.is_directory:
            send_file(new_name, new_path)
            # add the new path to the files_and_folders
            files_and_folders.append(new_path)
            # send 0 to server- means that we ended this connection
            socket_client.send(bytes("0", 'UTF-8'))
            socket_client.close()
            return
        # send to server the folder that has created (moved from outside)
        send_folder_relative_path(new_path)
        # add the new path to the files_and_folders
        files_and_folders.append(new_path)
        for root, dirs, files in os.walk(new_path, topdown=True):
            # only sub-directories
            for directory_name in dirs:
                # send 5 to server- means that we have an update to send to him
                socket_client.send(bytes("5", 'UTF-8'))
                # send 6 to server- means that the update is file/folder that has been created
                socket_client.send(bytes("6", 'UTF-8'))
                send_folder_relative_path(directory_name)
                # add the folder to the list of fies and folders
                files_and_folders.append(os.path.join(root, directory_name))
            # only files
            for file_name in files:
                # send 5 to server- means that we have an update to send to him
                socket_client.send(bytes("5", 'UTF-8'))
                # send 6 to server- means that the update is file/folder that has been created
                socket_client.send(bytes("6", 'UTF-8'))
                file_path = os.path.join(root, file_name)
                send_file(file_name, file_path)
                # add the file to the list of fies and folders
                files_and_folders.append(file_path)
        # send 0 to server- means that we ended this connection
        socket_client.send(bytes("0", 'UTF-8'))
        socket_client.close()
        return
    # file/folder has moved from inside. already exist in the server
    # create socket with TCP protocol
    socket_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # connect to server (SYN)
    socket_client.connect((global_ip, global_port))
    # send the server the id
    socket_client.send(bytes(global_identifier, 'UTF-8'))
    # send the server out seq number
    socket_client.send(global_sequence_number.to_bytes(8, sys.byteorder))
    # send 5 to server- means that we have an update to send to him
    socket_client.send(bytes("5", 'UTF-8'))
    # send 9 to server- means that the update is file/folder that has been moved
    socket_client.send(bytes("8", 'UTF-8'))
    if not event.is_directory:
        # file
        send_file_to_remove_or_moved(old_name, old_path)
        files_and_folders.remove(old_path)
        files_and_folders.append(new_path)
        send_file_to_remove_or_moved(new_name, new_path)
    else:
        # folder
        send_folder_relative_path(old_path)
        files_and_folders.remove(old_path)
        files_and_folders.append(new_path)
        send_folder_relative_path(new_path)
        for root, dirs, files in os.walk(new_path, topdown=True):
            for name in dirs:
                # calculate the relative path
                relative_path = os.path.relpath(os.path.join(root, name), new_path)
                # remove and append from the files_and_folders
                files_and_folders.append(os.path.join(new_path, relative_path))
                files_and_folders.remove(os.path.join(old_path, relative_path))
            for name in files:
                # calculate the relative path
                relative_path = os.path.relpath(os.path.join(root, name), new_path)
                # remove and append from the files_and_folders
                files_and_folders.append(os.path.join(new_path, relative_path))
                files_and_folders.remove(os.path.join(old_path, relative_path))
    # send 0 to server- means that we ended this connection
    socket_client.send(bytes("0", 'UTF-8'))
    socket_client.close()


def get_name():
    length = int.from_bytes(socket_client.recv(8), sys.byteorder)
    name = socket_client.recv(length).decode('UTF-8', "ignore")
    return name


def check_arguments(arr):
    # check if the number of arguments valid
    if len(arr) != ARGUMENTS_WITHOUT_IS and len(arr) != ARGUMENTS_WITH_ID:
        return False
    # check if the port is valid
    if (int(arr[2]) > MAX_PORT) or (int(arr[2]) < MIN_PORT):
        return False
    # check if the ip is valid -contains 4 numbers with 3 dots
    numbers = arr[1].split('.')
    if len(numbers) != NUMBER_IN_IP:
        return False
    # check if every number in the IP contains only digits and is valid
    for number in numbers:
        if (not number.isdigit()) or (int(number) < MIN_IP_NUM) or (int(number) > MAX_IP_NUM):
            return False
    # check if timer valid - check if not non negative
    if int(arr[4]) <= 0:
        return False

    # if we have identifier - check if valid
    # if len(arr) == 6:
    #     if len(arr[5])
    return True


def main():
    # check if arguments valid
    if not check_arguments(sys.argv):
        sys.exit(-1)
    # call track_data function, with or without identifier
    if len(sys.argv) == ARGUMENTS_WITH_ID:
        track_data_with_id(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])
    else:
        track_data_without_id(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])


if __name__ == '__main__':
    main()