# Noa Eitan 316222777, Coral Kuta 208649186
import os.path
import socket
import sys
import time
from watchdog.observers import Observer
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

# list of all files and folders in the path
global files_and_folders
# create socket with TCP protocol
global socket_client
global global_path
global global_folder
global global_identifier


def track_data_with_id(ip, port, path, timer, identifier):
    global files_and_folders
    global socket_client
    global global_path
    global global_folder
    global global_identifier
    files_and_folders = []
    # create socket with TCP protocol
    socket_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # save the path to the folder that we want to save and monitor via server
    files_and_folders.append(path)
    global_path = path
    _, global_folder = os.path.split(global_path)
    # connect to server (SYN) - save him the identifier
    socket_client.connect((ip, int(port)))
    # start monitor the data with the server.
    track_data(path, timer, identifier)
    socket_client.send(bytes(identifier, 'UTF-8'))

    # end of talk with server
    socket_client.close()


def track_data_without_id(ip, port, path, timer):
    global files_and_folders
    global socket_client
    global global_path
    global global_folder
    global global_identifier
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
    identifier = str(socket_client.recv(SIZE_ID), 'UTF-8')
    global_identifier = identifier
    # send data to server
    send_data_first_time(path)
    # send 0 to server- means that we finished send the files, start tracking
    socket_client.send(bytes("0", 'UTF-8'))
    # start monitor the data with the server.
    track_data(path, timer, identifier)
    # end of talk with server
    socket_client.close()


def send_data_first_time(path):
    for root, dirs, files in os.walk(path):
        # add the root to the list of fies and folders
        files_and_folders.append(root)
        root_name = os.path.basename(root)
        # only sub-directories
        for directory_name in dirs:
            send_folder_name(directory_name, root_name)
            # add the folder to the list of fies and folders
            files_and_folders.append(os.path.join(root, directory_name))
        # only files
        for file_name in files:
            file_path = os.path.join(root, file_name)
            send_file(file_name, file_path, root_name)
            # add the file to the list of fies and folders
            files_and_folders.append(file_path)


def send_name(name):
    length = len(name)
    socket_client.send(length.to_bytes(8, sys.byteorder))
    socket_client.send(bytes(name, 'UTF-8'))


def send_length(data):
    length = os.path.getsize(data)
    socket_client.send(length.to_bytes(8, sys.byteorder))


def send_folder_name(folder_name, mother_folder):
    # send 2 to server- means that we send a folder in current
    socket_client.send(bytes("2", 'UTF-8'))
    # send size of name file and the name of file
    send_name(folder_name)
    # where the server makes the folder ??
    send_name(mother_folder)


def send_file(file_name, file_path, mother_folder):
    # send 1 to server- means that we send a file
    socket_client.send(bytes("1", 'UTF-8'))
    # send file name
    send_name(file_name)
    # send where the file belongs
    send_name(mother_folder)
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


def send_file_to_remove_or_moved(file_name, file_path, mother_folder):
    # send 1 to server- means that we send a file
    socket_client.send(bytes("1", 'UTF-8'))
    # send file name
    send_name(file_name)
    # send where the file belongs
    send_name(mother_folder)


def track_data(path, timer, identifier):
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
    my_observer = Observer()
    my_observer.schedule(my_event_handler, path, recursive=go_recursively)
    # start monitor changes
    my_observer.start()
    try:
        while True:
            # sleep to some time
            time.sleep(int(timer))
            # send 4 to server- means that we waked up and we want to pull changes
            # socket_client.send(bytes("4", 'UTF-8'))
            # while True:
            #     option = str(socket_client.recv(1), 'UTF-8')
            #     # no more changes
            #     if option == "0":
            #         break
            #     # created new folder/file
            #     elif option == "6":
            #         option = str(socket_client.recv(1), 'UTF-8')
            #         # file
            #         if option == "1":
            #             create_new_file(socket_client)
            #         # create new folder
            #         elif option == "2":
            #             create_new_folder(socket_client)
            #     # file/folder has been deleted
            #     elif option == "7":
            #         option = str(socket_client.recv(1), 'UTF-8')
            #         # delete file
            #         if option == "1":
            #             delete_file(socket_client)
            #         # delete folder
            #         elif option == "2":
            #             delete_folder(socket_client)
            #     # file/folder has been modified
            #     elif option == "8":
            #         option = str(socket_client.recv(1), 'UTF-8')
            #         # modify folder - rename folder name
            #         if option == "2":
            #             rename_folder_name(socket_client)
            #     # file/folder has been moved
            #     elif option == "9":
            #         option = str(socket_client.recv(1), 'UTF-8')
            #         # move file
            #         if option == "1":
            #             move_file(socket_client)
            #         # move folder
            #         elif option == "2":
            #             move_folder(socket_client)

    except KeyboardInterrupt:
        my_observer.stop()
        # send 0 to server- means that we want to stop monitor
        socket_client.send(bytes("0", 'UTF-8'))
    my_observer.join()


def create_new_file():
    # name of a new file
    file_name = get_name()
    # where to create new file ?
    file_mother_path = get_mother_path(files_and_folders)
    # write
    file_to_write = open(os.path.join(file_mother_path, file_name), "wb")
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
    files_and_folders.append(os.path.join(file_mother_path, file_name))


def create_new_folder():
    # name of the new dir
    new_dir_name = get_name()
    # where the new dir needs to be
    dir_mother_dir = get_name()
    # the path to mother
    mother_path = get_dir_path(files_and_folders, dir_mother_dir)
    new_path = os.path.join(mother_path, new_dir_name)
    os.mkdir(new_path)
    # adding the new folder to the list
    files_and_folders.append(new_path)


def delete_file():
    # name of the file to delete
    file_name = get_name()
    # where the new dir needs to be
    dir_mother_file = get_name()
    # the path to mother
    mother_path = get_dir_path(files_and_folders, dir_mother_file)
    # path to remove
    path_to_remove = os.path.join(mother_path, file_name)
    # remove the file
    if os.path.exists(path_to_remove):
        os.remove(path_to_remove)
    files_and_folders.remove(path_to_remove)


def delete_folder():
    # name of the dir to delete
    dir_name = get_name()
    # where the new dir needs to be
    dir_mother_dir = get_name()
    # the path to mother
    mother_path = get_dir_path(files_and_folders, dir_mother_dir)
    # path to remove
    path_to_remove = os.path.join(mother_path, dir_name)
    # delete the files and folders that in the folder
    for root, dirs, files in os.walk(path_to_remove, topdown=False):
        for name in files:
            os.remove(os.path.join(root, name))
            files_and_folders.remove(os.path.join(root, name))
        for name in dirs:
            os.rmdir(os.path.join(root, name))
            files_and_folders.remove(os.path.join(root, name))
    # remove the folder
    os.rmdir(path_to_remove)
    # remove the folder from the list
    files_and_folders.remove(path_to_remove)


def rename_folder_name():
    # name of the dir to rename
    dir_old_name = get_name()
    # where the dir is exist
    dir_mother_dir = get_name()
    # name of the new name dir
    dir_new_name = get_name()
    # where the dir needs to be
    dir_mother_dir2 = get_name()
    # the path to mother
    mother_path = get_dir_path(files_and_folders, dir_mother_dir)
    # path to the folder that we need to rename
    path_to_rename = os.path.join(mother_path, dir_old_name)
    # path to the new folder name
    new_path = os.path.join(mother_path, dir_new_name)
    # rename the folder
    os.rename(path_to_rename, new_path)
    # path to the new folder
    new_path = os.path.join(mother_path, dir_new_name)
    # remove the oldest folder and add the new folder, from the list of folders
    files_and_folders.remove(path_to_rename)
    files_and_folders.append(new_path)


def move_file(directories):
    # name of the file to move
    file_name = get_name()
    # where the file is now
    old_dir_mother_file = get_name()
    # path to to dir where the file is now
    old_mother_path = get_dir_path(directories, old_dir_mother_file)
    # path to the old path of the file
    old_path = os.path.join(old_mother_path, file_name)
    # name of the file to move
    file_name2 = get_name()
    # where the file need to be- name of the new dir
    new_dir_mother_file = get_name()
    # path to the new dir where the file need to be
    new_mother_path = get_dir_path(files_and_folders, new_dir_mother_file)
    # path to the new place that the file need to be
    new_path = os.path.join(new_mother_path, file_name2)
    # replace - put the file in the new path and remove from the oldest
    os.replace(old_path, new_path)
    files_and_folders.remove(old_path)
    files_and_folders.append(new_path)


def move_folder():
    # name of the folder to move
    folder_name = get_name()
    # where the folder is now
    old_dir_mother_folder = get_name()
    # path to to dir where the folder is now
    old_mother_path = get_dir_path(files_and_folders, old_dir_mother_folder)
    # path to the old path of the folder
    old_path = os.path.join(old_mother_path, folder_name)
    # name of the folder to move
    folder_name2 = get_name()
    # where the file need to be- name of the new dir
    new_dir_mother_folder = get_name()
    # path to the new dir where the folder need to be
    new_mother_path = get_dir_path(files_and_folders, new_dir_mother_folder)
    # path to the new place that the folder need to be
    new_path = os.path.join(new_mother_path, folder_name2)
    # replace - put the whole files in the new path
    os.mkdir(new_path)
    #
    # # move the files and folders
    # #create the folders
    # for root, dirs, files in os.walk(old_path, topdown=True):
    #     for name in files:
    #         os.remove(os.path.join(root, name))
    #         files_and_folders.remove(os.path.join(root, name))
    #     for name in dirs:
    #         os.rmdir(os.path.join(root, name))
    #         files_and_folders.remove(os.path.join(root, name))



    # save all paths to files and dirs in the old path
    files = os.listdir(old_path)
    # scan the files and dirs,  and move them from the old path to the new path
    for f in files:
        files_and_folders.remove(os.path.join(old_path, f))
        files_and_folders.append(os.path.join(new_path, f))
        os.replace(os.path.join(old_path, f), os.path.join(new_path, f))
    # remove the old folder
    os.rmdir(old_path)
    # remove old folder from directories
    files_and_folders.remove(old_path)
    # add the new folder to directories
    files_and_folders.append(new_path)


def on_created(event):
    # get the path of the event that created
    path = event.src_path
    files_and_folders.append(path)
    # get the file/folder name and the mother path
    mother_path, name = os.path.split(path)
    # get mother folder name
    _, mother_name = os.path.split(mother_path)
    # if this an temporary file
    if name.endswith('swp'):
        return
    # if this is outputstream file
    # if path.contains('.goutputstream'):
    #     return
    if '.goutputstream' in path:
        return
    print(f"hey, {event.src_path} has been created!")
    # send 5 to server- means that we have an update to send to him
    socket_client.send(bytes("5", 'UTF-8'))
    # send 6 to server- means that the update is file/folder that has been created
    socket_client.send(bytes("6", 'UTF-8'))
    if os.path.isfile(path):
        send_file(name, path, mother_name)
    else:
        send_folder_name(name, mother_name)


def on_deleted(event):
    # get the path of the event that deleted
    path = event.src_path
    # delete from list of files and folders
    files_and_folders.remove(path)
    # get the file/folder name and the mother path
    mother_path, name = os.path.split(path)
    # get mother folder name
    _, mother_name = os.path.split(mother_path)
    if name.endswith('.swp'):
        return
    print(f"what the f**k! Someone deleted {event.src_path}!")
    # send 5 to server- means that we have an update to send to him
    socket_client.send(bytes("5", 'UTF-8'))
    # send 7 to server- means that the update is file/folder that has been deleted
    socket_client.send(bytes("7", 'UTF-8'))
    if os.path.isfile(path):
        # delete file
        send_file_to_remove_or_moved(name, path, mother_name)
    else:
        # delete folder
        send_folder_name(name, mother_name)


def on_modified(event):
    print(f"hey buddy, {event.src_path} has been modified")
    # # send 5 to server- means that we have an update to send to him
    # socket_client.send(bytes("5", 'UTF-8'))
    # # send 8 to server- means that the update is file/folder that has been modified
    # socket_client.send(bytes("8", 'UTF-8'))
    # # check if folder. if folder- send so she can rename. else, send delete and than create


def on_moved(event):
    print(f"ok ok ok, someone moved {event.src_path} to {event.dest_path}")
    # get the old path of the event that moved
    old_path = event.src_path
    # get the file/folder name and the old mother path
    old_mother_path, name = os.path.split(old_path)
    # get old mother folder name
    _, old_mother_name = os.path.split(old_mother_path)
    # get the new path of the event that moved
    new_path = event.dest_path
    # get the file/folder name and the new mother path
    new_mother_path, name2 = os.path.split(new_path)
    # get mother folder name
    _, new_mother_name = os.path.split(new_mother_path)

    # if this is outputstream file
    #if old_path.contains('.goutputstream'):
    if '.goutputstream' in old_path:
        # send 5 to server- means that we have an update to send to him
        socket_client.send(bytes("5", 'UTF-8'))
        # send 7 to server- means that the update is file/folder that has been deleted
        socket_client.send(bytes("7", 'UTF-8'))
        send_file_to_remove_or_moved(name, new_path, new_mother_name)
        # send 5 to server- means that we have an update to send to him
        socket_client.send(bytes("5", 'UTF-8'))
        # send 6 to server- means that the update is file/folder that has been created
        socket_client.send(bytes("6", 'UTF-8'))
        send_file(name, new_path, new_mother_name)
        return

    # if the folder/file has moved from outside
    if not (old_path in files_and_folders):
        # send 5 to server- means that we have an update to send to him
        socket_client.send(bytes("5", 'UTF-8'))
        # send 6 to server- means that the update is file/folder that has been created
        socket_client.send(bytes("6", 'UTF-8'))
        # send to server the folder/file that has created (moved from outside)
        send_folder_name(name2, new_mother_name)
        for root, dirs, files in os.walk(new_path, topdown=True):
            # add the root to the list of fies and folders
            files_and_folders.append(root)
            root_name = os.path.basename(root)
            # only sub-directories
            for directory_name in dirs:
                # send 5 to server- means that we have an update to send to him
                socket_client.send(bytes("5", 'UTF-8'))
                # send 6 to server- means that the update is file/folder that has been created
                socket_client.send(bytes("6", 'UTF-8'))
                send_folder_name(directory_name, root_name)
                # add the folder to the list of fies and folders
                files_and_folders.append(os.path.join(root, directory_name))
            # only files
            for file_name in files:
                # send 5 to server- means that we have an update to send to him
                socket_client.send(bytes("5", 'UTF-8'))
                # send 6 to server- means that the update is file/folder that has been created
                socket_client.send(bytes("6", 'UTF-8'))
                file_path = os.path.join(root, file_name)
                send_file(file_name, file_path, root_name)
                # add the file to the list of fies and folders
                files_and_folders.append(file_path)
        return
    # file/folder has moved from inside. already exist in the server
    # send 5 to server- means that we have an update to send to him
    socket_client.send(bytes("5", 'UTF-8'))
    # send 9 to server- means that the update is file/folder that has been moved
    socket_client.send(bytes("9", 'UTF-8'))

    if os.path.isfile(new_path):
        # file
        send_file_to_remove_or_moved(name, old_path, old_mother_name)
        files_and_folders.remove(old_path)
        files_and_folders.append(new_path)
        send_file_to_remove_or_moved(name2, new_path, new_mother_name)
    else:
        # folder
        send_folder_name(name, old_mother_name)
        files_and_folders.remove(old_path)
        files_and_folders.append(new_path)
        send_folder_name(name2, new_mother_name)


def get_name():
    length = int.from_bytes(socket_client.recv(8), sys.byteorder)
    return str(socket_client.recv(length), 'UTF-8')


def get_mother_path(directories):
    mother = get_name()
    return get_dir_path(directories, mother)


def get_dir_path(directories, wanted_dir):
    for i in range(len(directories)):
        tokens = os.path.split(directories[i])
        if tokens[-1] == wanted_dir:
            # return path to desired directory
            return directories[i]

    return directories[0]


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
