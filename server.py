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
clients = {}
# new CLIENTS dictionary.
# Each client has: KEY = identifier
#                  VALUE = dictionary of all of his computers.
#                  this dictionary has: KEY = sequence number
#                                       VALUE = A list of changes that this computer needs to get updated.

global files_and_folders
files_and_folders = {}
# directories dictionary.
# Each element has: KEY = identifier
#                   VALUE = list of all paths of client's directory, starting with his base folder.

global current_client_identifier


def serve_clients(port):
    global current_client_identifier
    global files_and_folders
    global clients

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('', port))
    s.listen(5)

    while True:
        client_socket, client_address = s.accept()
        data = client_socket.recv(CHARACTERS)
        # get ID
        str_data = str(data, 'UTF-8')

        if str_data == NEW_ID:
            seq_num = new_client(client_socket)
            clone(client_socket)
        else:
            current_client_identifier = str_data
            seq_num = existing_client(client_socket)

        # anyways - track data
        track_data(client_socket, seq_num)



'''
New client
'''
def new_client(client_socket):
    global current_client_identifier
    global files_and_folders
    global clients

    # new client - create random identifier, clone and then track
    identifier = create_id()
    current_client_identifier = identifier
    client_socket.send(bytes(identifier, 'UTF-8'))

    # the client is new. this is clearly his first computer. thus, seq_num = 1
    seq_num = 1
    client_socket.send(seq_num.to_bytes(8, sys.byteorder))

    # create a new dictionary for this client's computers, seq_num as the first one. his list of changes is empty.
    client_computers = {seq_num: []}
    clients[identifier] = client_computers

    # create the folder with the name of the new client
    client_path = os.path.join(SERVER_PATH, identifier)
    os.mkdir(client_path)

    # base dir of client
    client_dir_paths = [client_path]
    files_and_folders[identifier] = client_dir_paths

    return seq_num


'''
Old client
'''
def existing_client(client_socket):
    global current_client_identifier
    global files_and_folders
    global clients

    seq_num = int.from_bytes(client_socket.recv(8), sys.byteorder)

    # the computer is not new. we return to track
    if seq_num != 0:
        return seq_num

    # the computer is new - the sequence number of this new computer is the next one available
    client_computers = clients[current_client_identifier]
    new_seq_num = len(client_computers) + 1

    # send the client his new sequence number
    client_socket.send(new_seq_num.to_bytes(8, sys.byteorder))

    # adding a new computer to the client's list
    clients[current_client_identifier][new_seq_num] = []


    # send the client his directory so he clones it to the new computer
    send_data(client_socket)

    return seq_num


'''
The function creates a new identifier for a new client.
'''
def create_id():
    # allowing letter (upper and lower case) and digits.
    characters = string.ascii_letters + string.digits
    # creating a 128 characters string and return it as the new id.
    identifier = ''.join(random.choice(characters) for _ in range(CHARACTERS))
    return identifier


def get_name(client_socket):
    length = int.from_bytes(client_socket.recv(8), sys.byteorder)
    return str(client_socket.recv(length), 'UTF-8')


def get_full_path(client_socket):
    new_path = files_and_folders[current_client_identifier][0]
    iterations = int.from_bytes(client_socket.recv(8), sys.byteorder)

    for i in range(iterations):
        path_part = get_name(client_socket)
        new_path = os.path.join(new_path, path_part)

    norm_path = os.path.normpath(new_path)
    print("norm path: " + norm_path)
    return norm_path


def send_full_path(client_socket, path):
    relative_path = os.path.relpath(path, files_and_folders[current_client_identifier][0])
    mother_path, name = os.path.split(relative_path)
    list_split_path = [name]
    while mother_path != "":
        mother_path, name = os.path.split(mother_path)
        list_split_path.append(name)
    list_split_path.reverse()
    # send the size of the split objects in the relative path to server
    client_socket.send(len(list_split_path).to_bytes(8, sys.byteorder))
    for name in list_split_path:
        send_name(client_socket, name)



def send_data(client_socket):
    global files_and_folders
    for root, dirs, files in os.walk(files_and_folders[current_client_identifier][0]):
        # only sub-directories
        for directory_name in dirs:
            directory_path = os.path.join(root, directory_name)
            send_folder_path(client_socket, directory_path)

        # only files
        for file_name in files:
            file_path = os.path.join(root, file_name)
            send_file(client_socket, file_name, file_path)

    # tell client there is no more data
    client_socket.send(bytes("0", 'UTF-8'))


def clone(client_socket):
    while True:
        option = client_socket.recv(1).decode("utf-8", "ignore")

        # no more
        if option == "0":
            break

        # file
        elif option == "1":
            create_file(client_socket)

        # create new folder
        elif option == "2":
            # where the new dir needs to be
            full_path = get_full_path(client_socket)
            files_and_folders[current_client_identifier].append(full_path)
            os.mkdir(full_path)
            # adding the new folder to the list



def track_data(client_socket, seq_num):
    print("tracking...")
    option = client_socket.recv(1).decode("utf-8", "ignore")

    # Client woke up and needs to be notified on changes
    if option == "4":
        print("wake up !")
        update_client(client_socket, seq_num)

    # Watchdog connected. Server need to get updates
    elif option == "5":
        change_type = client_socket.recv(1).decode("utf-8", "ignore")
        while change_type != "0":
            print("watchdog")
            create_change(client_socket,change_type, seq_num)
            change_type = client_socket.recv(1).decode("utf-8", "ignore")
            # change_type = str(client_socket.recv(1), 'UTF-8')


def create_file(client_socket):
    # name of new file
    _ = get_name(client_socket)
    # where to create new file ?
    file_full_path = get_full_path(client_socket)

    if os.path.exists(file_full_path):
        return False

    # write
    file_to_write = open(file_full_path, "wb")
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
    file_to_write.close()
    files_and_folders[current_client_identifier].append(file_full_path)
    return file_full_path


def remove_dir(path_to_remove):
    to_delete = []
    if path_to_remove != files_and_folders[current_client_identifier][0]:
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
        files_and_folders[current_client_identifier].remove(path)


def create_change(client_socket,change_type, seq_num):
    print("creating a change, seq num is " + str(seq_num))
    # creating a change
    change = (change_type, )

    # CREATE
    if change_type == "6":
        # 1 (file), 2 (folder)
        file_or_folder = client_socket.recv(1).decode("utf-8", "ignore")

        # create FILE
        if file_or_folder == "1":
            new_path = create_file(client_socket)
            if not new_path:
                return
            change = change + (file_or_folder, new_path)
            add_change(seq_num, change)

        # create FOLDER
        else:
            new_path = get_full_path(client_socket)
            if os.path.exists(new_path):
                return
            files_and_folders[current_client_identifier].append(new_path)
            os.mkdir(new_path)
            change = change + (file_or_folder, new_path)
            add_change(seq_num, change)

    # DELETE
    elif change_type == "7":
        # 1 (file), 2 (folder)
        file_or_folder = client_socket.recv(1).decode("utf-8", "ignore")

        # delete FILE
        if file_or_folder == "1":
            _ = get_name(client_socket)
            path = get_full_path(client_socket)

            # if the server got a path that is no longer watched, we return
            if path not in files_and_folders:
                return
            files_and_folders[current_client_identifier].remove(path)
            os.remove(path)
            change = change + (file_or_folder, path)
            add_change(seq_num, change)

        # delete FOLDER
        else:
            path = get_full_path(client_socket)
            #
            # # if the server got a path that is no longer watched, we return
            # if path not in files_and_folders:
            #     return
            remove_dir(path)
            change = change + (file_or_folder, path)
            add_change(seq_num, change)

    # MOVE
    elif change_type == "8":
        # 1 (file), 2 (folder)
        file_or_folder = client_socket.recv(1).decode("utf-8", "ignore")

        if file_or_folder == "1":
            # old data
            _ = get_name(client_socket)
            old_path = get_full_path(client_socket)
            # new data
            _ = str(client_socket.recv(1), 'UTF-8')
            _ = get_name(client_socket)
            new_path = get_full_path(client_socket)

            old_mother,_ = os.path.split(old_path)
            new_mother,_ = os.path.split(new_path)

            # deal the case that it's not a move, but a name change of file
            if old_mother == new_mother:
                os.rename(old_path, new_path)
                files_and_folders[current_client_identifier].remove(old_path)
                files_and_folders[current_client_identifier].append(new_path)
                # change type "9" of renaming
                change = ("9", file_or_folder, new_path, old_path)
                add_change(seq_num, change)
                return

            # if the old path doesn't exist and the new path does exist we update "directories"
            if (not os.path.exists(old_path)) and (os.path.exists(new_path)):
                if old_path in files_and_folders[current_client_identifier]:
                    files_and_folders[current_client_identifier].remove(old_path)
                if not new_path in files_and_folders[current_client_identifier]:
                    files_and_folders[current_client_identifier].append(new_path)
                return

            # if we didn't return until now - it's a location replace
            os.replace(old_path, new_path)
            files_and_folders[current_client_identifier].remove(old_path)
            files_and_folders[current_client_identifier].append(new_path)
            change = change + (file_or_folder, new_path, old_path)
            add_change(seq_num, change)


        elif file_or_folder == "2":
            # old data
            old_path = get_full_path(client_socket)
            # new data
            _ = str(client_socket.recv(1), 'UTF-8')
            new_path = get_full_path(client_socket)

            old_mother, _ = os.path.split(old_path)
            new_mother, _ = os.path.split(new_path)

            # deal the case that it's not a move, but a name change of folder
            if old_mother == new_mother:
                for root, dirs, files in os.walk(old_path, topdown=True):
                    for name in dirs:
                        relative_path = os.path.relpath(os.path.join(root, name), old_path)
                        files_and_folders[current_client_identifier].remove(os.path.join(old_path, relative_path))
                    for name in files:
                        relative_path = os.path.relpath(os.path.join(root, name), old_path)
                        files_and_folders[current_client_identifier].remove(os.path.join(old_path, relative_path))

                os.rename(old_path, new_path)

                for root, dirs, files in os.walk(new_path, topdown=True):
                    for name in dirs:
                        relative_path = os.path.relpath(os.path.join(root, name), new_path)
                        files_and_folders[current_client_identifier].append(os.path.join(new_path, relative_path))
                    for name in files:
                        relative_path = os.path.relpath(os.path.join(root, name), new_path)
                        files_and_folders[current_client_identifier].append(os.path.join(new_path, relative_path))
                files_and_folders[current_client_identifier].remove(old_path)
                files_and_folders[current_client_identifier].append(new_path)
                # change type "9" of renaming
                change = ("9", file_or_folder, new_path, old_path)
                add_change(seq_num, change)
                return

            # if we didn't return by now, it's a move ! first, we create the new folder
            os.mkdir(new_path)
            # folders to remove so we don't harm the recursion
            recursive_folders_to_delete = []
            for root, dirs, files in os.walk(old_path, topdown=True):
                for name in dirs:
                    relative_path = os.path.relpath(os.path.join(root, name), old_path)
                    # move to the new folder
                    os.mkdir(os.path.join(new_path, relative_path))
                    recursive_folders_to_delete.append(os.path.join(old_path, relative_path))
                    # remove and append from the files_and_folders
                    files_and_folders[current_client_identifier].append(os.path.join(new_path, relative_path))
                    files_and_folders[current_client_identifier].remove(os.path.join(old_path, relative_path))
                for name in files:
                    relative_path = os.path.relpath(os.path.join(root, name), old_path)
                    # move to the new folder
                    os.replace(os.path.join(old_path, relative_path), os.path.join(new_path, relative_path))
                    # remove and append from the files_and_folders
                    files_and_folders[current_client_identifier].append(os.path.join(new_path, relative_path))
                    files_and_folders[current_client_identifier].remove(os.path.join(old_path, relative_path))

            files_and_folders[current_client_identifier].remove(old_path)
            files_and_folders[current_client_identifier].append(new_path)
            change = ("8", file_or_folder, new_path, old_path)
            add_change(seq_num, change)

            # delete all init empty folders in reverse ways
            recursive_folders_to_delete.reverse()
            for folder in recursive_folders_to_delete:
                os.rmdir(folder)
            # finally, we delete the original file that has moved
            os.rmdir(old_path)


def add_change(seq_num, change):
    # add change to all computers of clients, but the client's ip itself
    for num in clients[current_client_identifier]:
        if num != seq_num:
            clients[current_client_identifier][num].append(change)


'''
An existing client has connected and the sever needs to update him about the changes that has been made
in his other computers
'''
def update_client(client_socket, seq_num):
    print("update client number: " + str(seq_num))
    # list of changes. each change is a tuple.
    changes_list = clients[current_client_identifier][seq_num]

    for change in changes_list:
        change_type = change[0]

        if change_type == "6":
            update_create(change, client_socket)

        elif change_type == "7":
            update_delete(change, client_socket)

        elif change_type == "8":
            update_move(change, client_socket)

        elif change_type == "9":
            update_rename(change, client_socket)

     # This specific computer fo the client has been updated. We can delete his list.
    clients[current_client_identifier][seq_num] = []

    # send client there is no more changes.
    client_socket.send(bytes("0", 'UTF-8'))


# CHANGE = (change type, is_dir, relevant_full_path, old_full_path)
#               0          1              2                3
# client_path = os.path.join(SERVER_PATH, client_identifier)

def update_create(change, client_socket):
    file_or_folder = change[1]             # 1 if file, 2 if folder
    full_path = change[2]                  # full path of file/directory
    mother_path, name = os.path.split(full_path)

    # send 6 to the client - something has been CREATED.
    client_socket.send(bytes("6", 'UTF-8'))

    # FILE
    if file_or_folder == "1":
        file_name = name
        # FILE has been created.
        send_file(client_socket, file_name, full_path)

    # FOLDER
    else:
        # DIRECTORY has been created.
        send_folder_path(client_socket, full_path)


def update_delete(change, client_socket):
    file_or_folder = change[1]        # 1 if file, 2 if folder
    full_path = change[2]             # full path of file/directory

    # send 8 to the client - something has been DELETED
    client_socket.send(bytes("7", 'UTF-8'))

    # FILE
    if file_or_folder == "1":
        _, file_name = os.path.split(full_path)
        # FILE has been deleted.
        send_file_name(client_socket, file_name)
        send_full_path(client_socket, full_path)

    # FOLDER
    else:
        # DIRECTORY has been deleted.
        send_folder_path(client_socket, full_path)


def update_move(change, client_socket):
    file_or_folder = change[1]        # 1 if file, 2 if folder
    full_path = change[2]             # full path of file/directory
    old_path = change[3]              # old path of file/directory

    # send 8 to the client - something has been MOVED.
    client_socket.send(bytes("8", 'UTF-8'))

    # FILE
    if file_or_folder == "1":
        _, file_name = os.path.split(full_path)

        # send old path
        send_file_name(client_socket, file_name)
        send_full_path(client_socket, old_path)
        # send new path
        send_name(client_socket, file_name)
        send_full_path(client_socket, full_path)

    # FOLDER
    else:
        # send 2 to the client - DIRECTORY has been moved.
        client_socket.send(bytes("2", 'UTF-8'))
        # send old location
        send_full_path(client_socket, old_path)
        # send new location
        send_full_path(client_socket, full_path)


def update_rename(change, client_socket):
    file_or_folder = change[1]
    full_path = change[2]  # full path of directory
    old_path = change[3]   # old path of directory

    # send 9 to the client - a folder has been RENAMED.
    client_socket.send(bytes("9", 'UTF-8'))

    # FILE
    if file_or_folder == "1":
        # FILE has been created.
        client_socket.send(bytes("1", 'UTF-8'))
        send_full_path(client_socket, old_path)
        send_full_path(client_socket, full_path)

    # FOLDER
    else:
        client_socket.send(bytes("2", 'UTF-8'))
        send_full_path(client_socket, old_path)
        send_full_path(client_socket, full_path)


def send_name(s, name):
    length = len(name)
    s.send(length.to_bytes(8, sys.byteorder))
    s.send(bytes(name, 'UTF-8'))


def send_length(s, data):
    length = os.path.getsize(data)
    s.send(length.to_bytes(8, sys.byteorder))


def send_folder_path(client_socket, path):
    # send 2 to client - folder
    client_socket.send(bytes("2", 'UTF-8'))

    _, name = os.path.split(path)

    # send path to folder
    send_full_path(client_socket, path)


def send_file_name(client_socket, file_name):
    # send 1 to client - file
    client_socket.send(bytes("1", 'UTF-8'))
    # send file name
    send_name(client_socket, file_name)


def send_file(client_socket, file_name, full_path):
    send_file_name(client_socket, file_name)

    # send the path to the file
    send_full_path(client_socket, full_path)

    # send the size of the file
    send_length(client_socket, full_path)

    # start send the data that in the file
    file = open(full_path, "rb")
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
        serve_clients(int(sys.argv[1]))



if __name__ == '__main__':
    main()