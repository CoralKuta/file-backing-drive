# Noa Eitan 316222777, Coral Kuta 208649186
import os
import socket
import sys
import random
import string

# consts
BYTES_FOR_COUNTER = 3
BYTES_TO_READ = 1024
MAX_PORT = 65545
MIN_PORT = 0
ARGUMENTS_NUMBER = 2
CHARACTERS = 128
NEW_ID = "ID".zfill(CHARACTERS)
SERVER_PATH = os.getcwd()

# GLOBAL VARIABLES
global clients
# new CLIENTS dictionary.
# Each client has: KEY = identifier
#                  VALUE = dictionary of all of his computers.
#                  this dictionary has: KEY = Ip address
#                                       VALUE = A list of changes that this computer needs to get updated.

global directories
# directories dictionary.
# Each element has: KEY = identifier
#                   VALUE = list of all paths of client's directory, starting with his base folder.

global current_client_identifier



'''
The server function. Once the server is open, he never closes.
'''
def first_time_client(port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('', port))
    s.listen(5)

    while True:
        client_socket, client_address = s.accept()
        data = client_socket.recv(CHARACTERS)
        str_data = str(data, 'UTF-8')

        # new client - create random identifier
        if str_data == NEW_ID:
            identifier = create_id()
            global current_client_identifier
            current_client_identifier = identifier
            client_socket.send(bytes(identifier, 'UTF-8'))

            # create a new dictionary for this client's computers, and add his ip as the first one.
            client_computers = {}
            client_ip = client_address[0]
            # this is the first time the client connected. his list of changes is empty.
            client_computers[client_ip] = []
            global clients
            clients = {identifier: client_computers}

            # create the folder with the name of the new client
            client_path = os.path.join(SERVER_PATH, identifier)
            os.mkdir(client_path)

            # base dir of client
            global directories
            client_dir_paths = [client_path]
            directories = {identifier: client_dir_paths}
            clone(client_socket)
            print("done cloning")

            # TRACK
            track_data(client_socket,identifier, client_ip)

        # existing client
        else:
            client_id = str_data
            # # client_path = os.path.join(SERVER_PATH, client_id)
            # client_ip = client_address[0]
            #
            # track_data(client_socket, client_id, client_ip, directories)

        # client_socket.close()
        print("Client disconnected.")


def clone(client_socket):
    while True:
        option = str(client_socket.recv(1), 'UTF-8')

        # no more
        if option == "0":
            break
        # file
        elif option == "1":
            create_file(client_socket)


        # create new folder
        elif option == "2":
            # name of the new dir
            new_dir_name = get_name(client_socket)
            # where the new dir needs to be
            dir_mother_dir = get_name(client_socket)
            # the path to mother
            mother_path = get_dir_path(dir_mother_dir)
            new_dir_path = os.path.join(mother_path, new_dir_name)
            os.mkdir(new_dir_path)
            # adding the new folder to the list
            directories[current_client_identifier].append(new_dir_path)


def track_data(client_socket, client_identifier, client_ip):
    while True:
        print("tracking...")
        option = str(client_socket.recv(1), 'UTF-8')
        if option == "0":
            break

        # Client woke up and needs to be notified on changes
        if option == "4":
            update_client(client_socket, client_identifier, client_ip)

        # Watchdog connected. Server need to get updates
        elif option == "5":
            print("watchdog")
            create_change(client_socket, client_identifier, client_ip)
            pass


'''
The function creates a new identifier for a new client.
'''
def create_id():
    # allowing letter (upper and lower case) and digits.
    characters = string.ascii_letters + string.digits
    # creating a 128 characters string and return it as the new id.
    identifier = ''.join(random.choice(characters) for _ in range(CHARACTERS))
    return identifier


def create_file(client_socket):
    # name of new file
    file_name = get_name(client_socket)
    # where to create new file ?
    file_mother_path = get_mother_path(client_socket)
    _, mother_name = os.path.split(file_mother_path)
    # write
    new_file_path = os.path.join(file_mother_path, file_name)
    file_to_write = open(new_file_path, "wb")
    # getting the size of file
    file_len = int.from_bytes(client_socket.recv(8), sys.byteorder)
    counter = file_len

    if file_len < BYTES_TO_READ:
        file = client_socket.recv(file_len)
    else:
        file = client_socket.recv(BYTES_TO_READ)

    while file:
        file_to_write.write(file)
        counter = counter - len(file)
        if counter <= 0:
            break
        elif counter < BYTES_TO_READ:
            file = client_socket.recv(counter)
        else:
            file = client_socket.recv(BYTES_TO_READ)
    print("Download Completed")
    file_to_write.close()
    directories[current_client_identifier].append(new_file_path)
    return new_file_path, mother_name, file_name


def remove_dir(path_to_remove):
    to_delete = []
    if path_to_remove != directories[current_client_identifier][0]:
        to_delete.append(path_to_remove)

    for root, dirs, files in os.walk(path_to_remove, topdown=False):
        for name in files:
            os.remove(os.path.join(root, name))
            to_delete.append(os.path.join(root, name))
        for name in dirs:
            os.rmdir(os.path.join(root, name))
            to_delete.append(os.path.join(root, name))
    os.rmdir(path_to_remove)


    for path in to_delete:
        directories[current_client_identifier].remove(path)


def get_name(client_socket):
    length = int.from_bytes(client_socket.recv(8), sys.byteorder)
    return str(client_socket.recv(length), 'UTF-8')


def get_mother_path(client_socket):
    mother = get_name(client_socket)
    return get_dir_path(mother)

# TODO: to handle two files/folders with the same name. need to know mother.
def get_dir_path(wanted_dir):
    dirs = directories[current_client_identifier]
    for i in range(len(dirs)):
        _, directory = os.path.split(dirs[i])
        if directory == wanted_dir:
            # return path to desired directory
            return dirs[i]
    return dirs[0]

# def get_dir_path(wanted_dir, mother_dir):
#     dirs = directories[current_client_identifier]
#     for i in range(len(dirs)):
#         _, directory = os.path.split(dirs[i])
#         if directory == wanted_dir:
#             # return path to desired directory
#             return dirs[i]
#     return dirs[0]


def create_change(client_socket, client_identifier, client_ip):
    print("creating a change")
    # 6 (create), 7 (delete), 8 (modify), 9 (move)
    change_type = str(client_socket.recv(1), 'UTF-8')
    # creating a change
    change = (change_type, )

    # CREATE
    if change_type == "6":
        # 1 (file), 2 (folder)
        file_or_folder = str(client_socket.recv(1), 'UTF-8')

        # create FILE
        if file_or_folder == "1":
            print("create file")
            path, mother_name, file_name = create_file(client_socket)
            change = change + (file_or_folder, path, mother_name, file_name)
            print("done creating a file")

        # create FOLDER
        else:
            print("create dir")
            # name of file or folder
            folder_name = get_name(client_socket)
            path = get_dir_path(folder_name)
            mother_name = get_name(client_socket)
            # name of the new dir
            folder_mother_path = get_dir_path(mother_name)
            new_path = os.path.join(folder_mother_path, folder_name)
            os.mkdir(new_path)
            # adding the new folder to the client's directories
            directories[current_client_identifier].append(new_path)
            change = change + (file_or_folder, path, mother_name, folder_name)
            print("done creating a folder")

    # DELETE
    elif change_type == "7":
        # 1 (file), 2 (folder)
        file_or_folder = str(client_socket.recv(1), 'UTF-8')
        data_name = get_name(client_socket)
        path = get_dir_path(data_name)
        mother_name = get_name(client_socket)

        # making a copy because we delete
        directories_copy = directories[current_client_identifier].copy()

        # delete FILE
        if file_or_folder == "1":
            print("delete file")
            for i in range(len(directories_copy)):
                _, directory = os.path.split(directories_copy[i])
                if directory == data_name:
                    path_to_remove = directories_copy[i]
                    directories[current_client_identifier].remove(path_to_remove)
                    os.remove(path_to_remove)
                    change = change + (file_or_folder, path_to_remove, mother_name, data_name)
            print("file deleted")

        # delete FOLDER
        else:
            print("delete dir")
            for i in range(len(directories_copy)):
                _, directory = os.path.split(directories_copy[i])
                if directory == data_name:
                    remove_dir(directories[current_client_identifier][i])
            change = change + (file_or_folder, path, mother_name, data_name)
            print("folder deleted")

    # MODIFY
    elif change_type == "8":
        pass
        # 1 (file), 2 (folder)
        # file_or_folder = str(client_socket.recv(1), 'UTF-8')
        # if file_or_folder == "1":
        #     pass
        # elif file_or_folder == "2":
        #     pass

    # MOVE
    elif change_type == "9":
        # 1 (file), 2 (folder)
        file_or_folder = str(client_socket.recv(1), 'UTF-8')
        # old data
        old_name = get_name(client_socket)
        old_mother = get_name(client_socket)
        print("old mother:" + old_mother)
        old_mother_path = get_dir_path(old_mother)
        print(old_name)
        old_path = get_dir_path(old_name)
        # new data
        _ = str(client_socket.recv(1), 'UTF-8')
        new_name = get_name(client_socket)
        new_mother = get_name(client_socket)
        print("new mother:" + new_mother)
        new_mother_path = get_dir_path(new_mother)
        # new paths
        new_path = os.path.join(new_mother_path, new_name)

        # deal the case that it's not a move, but a name change of folder or file
        if new_mother_path == old_mother_path:
            print(new_mother_path + "\n" + old_mother_path)
            print(old_name + "\n" + new_name)
            os.rename(old_path, new_path)
            directories[current_client_identifier].remove(old_path)
            directories[current_client_identifier].append(new_path)
            return

        if file_or_folder == "1":
            if old_path == new_path:
                return
            # replacing location
            os.replace(old_path, new_path)
            directories[current_client_identifier].remove(old_path)
            directories[current_client_identifier].append(new_path)

        elif file_or_folder == "2":
            if not os.path.exists(new_path):
                os.mkdir(new_path)

            files = os.listdir(old_path)
            for file in files:
                os.replace(os.path.join(old_path, file), os.path.join(new_path, file))
                directories[current_client_identifier].remove(os.path.join(old_path, file))
                directories[current_client_identifier].append(os.path.join(new_path, file))
            directories[current_client_identifier].remove(old_path)
            directories[current_client_identifier].append(new_path)
            os.rmdir(old_path)


    # add change to all computers of clients, but the client's ip itself
    for ip in clients[client_identifier]:
        if ip != client_ip:
            clients[client_identifier][ip].appand(change)


'''
An existing client has connected and the sever needs to update him about the changes that has been made
in his other computers
'''
def update_client(client_socket, client_identifier, client_ip):
    # list of changes. each change is a tuple.
    changes_list = clients[client_identifier][client_ip]

    for change in changes_list:
        change_type = change[0]

        # a computer of the client created a new file or directory.
        if change_type == "6":
            create(change, client_socket)

        elif change_type == "7":
            delete(change, client_socket)

        elif change_type == "8":
            modify(change, client_socket)

        elif change_type == "9":
            move(change, client_socket)

        # This specific computer fo the client has been updated. We can delete his list.
        clients[client_identifier][client_ip] = []


def create(change, client_socket):
    file_or_folder = change[1]    # 1 if file, 2 if folder
    path = change[2]              # path of file/directory
    mother_name = change[3]       # mother name

    # send 6 to the client - something has been CREATED.
    client_socket.send(bytes("6", 'UTF-8'))

    # FILE
    if file_or_folder == "1":
        file_name = change[4]
        # send 1 to the client - FILE has been created.
        client_socket.send(bytes("1", 'UTF-8'))
        send_file(client_socket, file_name, path, mother_name)

    # FOLDER
    else:
        folder_name = change[4]
        # send 2 to the client - DIRECTORY has been created.
        client_socket.send(bytes("2", 'UTF-8'))
        send_folder_name(client_socket, folder_name, mother_name)


def delete(change, client_socket):
    file_or_folder = change[1]   # 1 if file, 2 if folder
    path = change[2]             # path of file/directory
    mother_name = change[3]      # name of mother

    # send 8 to the client - something has been DELETED
    client_socket.send(bytes("7", 'UTF-8'))

    # FILE
    if file_or_folder == "1":
        file_name = change[4]
        # send 1 to the client - FILE has been deleted.
        client_socket.send(bytes("1", 'UTF-8'))
        send_file_name(client_socket, file_name, mother_name)

    # FOLDER
    else:
        folder_name = change[4]
        # send 2 to the client - DIRECTORY has been deleted.
        client_socket.send(bytes("2", 'UTF-8'))
        send_folder_name(client_socket, folder_name, mother_name)


def modify(change, client_socket):
    file_or_folder = change[1]    # 1 if file, 2 if folder
    mother_name = change[3]
    new_name = change[4]         # new name of file\directory
    old_name = change[5]         # old name of file\directory

    # send 8 to the client - something has been MODIFIED.
    client_socket.send(bytes("8", 'UTF-8'))

    # FILE
    if file_or_folder == "1":
        to_delete_change = ()
        to_create_change = ()
        # TODO it's not working!!! how do i save both old and new ?????
        # if a file has been modified, I send the client to delete the file and then to create it.
        delete(change, client_socket)
        create(change, client_socket)

    # FOLDER
    else:
        # send 2 to the client - a folder's name has changed
        client_socket.send(bytes("2", 'UTF-8'))

        # sending the old name of the dir
        send_folder_name(client_socket, old_name, mother_name)

        # sending the new name of the dir
        send_folder_name(client_socket, new_name, mother_name)


def move(change, client_socket):
    file_or_folder = change[1]     # 1 if file, 2 if folder
    path = change[2]               # path of file/directory
    new_mother = change[3]
    old_mother = change[6]
    old_path = change[7]

    # send 9 to the client - something has been MOVED.
    client_socket.send(bytes("9", 'UTF-8'))

    # FILE
    if file_or_folder == "1":
        file_name = change[4]
        client_socket.send(bytes("1", 'UTF-8'))
        # send old location
        send_file_name(client_socket, file_name, old_mother)
        # send new location
        send_file_name(client_socket, file_name, new_mother)

    # FOLDER
    else:
        folder_name = change[4]  # name of file\directory
        # send 2 to the client - DIRECTORY has been moved.
        client_socket.send(bytes("2", 'UTF-8'))
        # send old location
        send_folder_name(client_socket, folder_name, old_mother)
        # send new location
        send_folder_name(client_socket, folder_name, new_mother)


def send_name(s, name):
    length = len(name)
    s.send(length.to_bytes(8, sys.byteorder))
    s.send(bytes(name, 'UTF-8'))


def send_length(s, data):
    length = os.path.getsize(data)
    s.send(length.to_bytes(8, sys.byteorder))


def send_folder_name(client_socket, folder_name, mother_folder):
    # send 2 to client - new folder
    client_socket.send(bytes("2", 'UTF-8'))

    # send size of name file and the name of file
    send_name(client_socket, folder_name)

    # where the client makes the folder ??
    send_name(client_socket, mother_folder)


def send_file_name(client_socket, file_name, mother_folder):
    # send 1 to client - new file
    client_socket.send(bytes("1", 'UTF-8'))

    # send file name
    send_name(client_socket, file_name)

    # send where the file belongs
    send_name(client_socket, mother_folder)


def send_file(client_socket, file_name, file_data, mother_folder):
    send_file_name(client_socket, file_name, mother_folder)

    # send the size of the file
    send_length(client_socket, file_data)

    # start send the data that in the file
    file = open(file_data, "rb")
    data = file.read(BYTES_TO_READ)
    # send the bytes in the file
    while data:
        client_socket.send(data)
        data = file.read(BYTES_TO_READ)
    file.close()


'''
Function that checks validation of arguments.
'''
def check_argument_input(argv):
    # check number of arguments
    if len(argv) != ARGUMENTS_NUMBER:
        sys.exit(-1)

    # check validation of port number
    elif (not argv[1].isdigit()) or ((int(argv[1]) > MAX_PORT) or (int(argv[1]) < MIN_PORT)):
        sys.exit(-1)


def main():
    check_argument_input(sys.argv)
    while True:
        first_time_client(int(sys.argv[1]))



if __name__ == '__main__':
    main()