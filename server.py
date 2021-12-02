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

global directories
directories = {}
# directories dictionary.
# Each element has: KEY = identifier
#                   VALUE = list of all paths of client's directory, starting with his base folder.

global current_client_identifier



def serve_clients(port):
    global current_client_identifier
    global directories
    global clients

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('', port))
    s.listen(5)

    while True:
        client_socket, client_address = s.accept()
        print("New client connected.")
        data = client_socket.recv(CHARACTERS)
        # get ID
        str_data = str(data, 'UTF-8')

        if str_data == NEW_ID:
            seq_num = new_client(client_socket)
            clone(client_socket)
            print("done cloning")
        else:
            current_client_identifier = str_data
            print("existing id: " + str_data)
            seq_num = existing_client(client_socket)

        # anyways - track data
        track_data(client_socket, seq_num)
        print("Client disconnected.")



'''
New client
'''
def new_client(client_socket):
    global current_client_identifier
    global directories
    global clients

    # new client - create random identifier, clone and then track
    identifier = create_id()
    current_client_identifier = identifier
    print("new id: " + identifier)
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
    directories[identifier] = client_dir_paths

    return seq_num


'''
Old client
'''
def existing_client(client_socket):
    global current_client_identifier
    global directories
    global clients

    seq_num = int.from_bytes(client_socket.recv(8), sys.byteorder)
    print("existing client sent: " + str(seq_num) + " as seq_num")

    # the computer is not new. we return to track
    if seq_num != 0:
        return seq_num

    # the computer is new - the sequence number of this new computer is the next one available
    client_computers = clients[current_client_identifier]
    new_seq_num = len(client_computers) + 1

    print("new seq num for existing client: " + str(new_seq_num))

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
    new_path = directories[current_client_identifier][0]
    iterations = int.from_bytes(client_socket.recv(8), sys.byteorder)

    for i in range(iterations):
        path_part = get_name(client_socket)
        new_path = os.path.join(new_path, path_part)

    return new_path

def send_full_path(client_socket, path):
    relative_path = os.path.relpath(path, directories[current_client_identifier][0])
    print("rp: " + relative_path)
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
    global directories
    for root, dirs, files in os.walk(directories[current_client_identifier][0]):
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
        option = str(client_socket.recv(1), 'UTF-8')

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
            directories[current_client_identifier].append(full_path)
            os.mkdir(full_path)
            # adding the new folder to the list


def track_data(client_socket, seq_num):
    print("tracking...")
    option = str(client_socket.recv(1), 'UTF-8')

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
            #change_type = str(client_socket.recv(1), 'UTF-8')


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
    directories[current_client_identifier].append(file_full_path)
    return file_full_path


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


# CHANGE = (change type, is_dir, relevant_full_path, old_full_path)
#               0          1              2                3
# client_path = os.path.join(SERVER_PATH, client_identifier)


def create_change(client_socket,change_type, seq_num):
    print("creating a change")
    # creating a change
    change = (change_type, )

    # CREATE
    if change_type == "6":
        # 1 (file), 2 (folder)
        file_or_folder = str(client_socket.recv(1), 'UTF-8')

        # create FILE
        if file_or_folder == "1":
            print("create file")
            new_path = create_file(client_socket)
            if not new_path:
                return
            change = change + (file_or_folder, new_path)
            add_change(seq_num, change)
            print("done creating a file")

        # create FOLDER
        else:
            print("create dir")
            new_path = get_full_path(client_socket)
            if os.path.exists(new_path):
                return
            directories[current_client_identifier].append(new_path)
            os.mkdir(new_path)
            change = change + (file_or_folder, new_path)
            add_change(seq_num, change)
            print("done creating a folder")

    # DELETE
    elif change_type == "7":
        # 1 (file), 2 (folder)
        file_or_folder = str(client_socket.recv(1), 'UTF-8')

        # # making a copy because we delete
        # directories_copy = directories[current_client_identifier].copy()

        # delete FILE
        if file_or_folder == "1":
            print("delete file")
            _ = get_name(client_socket)
            path = get_full_path(client_socket)
            directories[current_client_identifier].remove(path)
            os.remove(path)
            change = change + (file_or_folder, path)
            add_change(seq_num, change)

            # for i in range(len(directories_copy)):
            #     _, directory = os.path.split(directories_copy[i])
            #     if directory == file_name:
            #         path_to_remove = directories_copy[i]
            #         directories[current_client_identifier].remove(path_to_remove)
            #         os.remove(path_to_remove)
            #         change = change + (file_or_folder, path_to_remove, mother_name, data_name)

            print("file deleted")

        # delete FOLDER
        else:
            path = get_full_path(client_socket)
            print("delete dir")
            remove_dir(path)
            change = change + (file_or_folder, path)
            add_change(seq_num, change)
            print("folder deleted")

    # MOVE
    elif change_type == "8":
        # 1 (file), 2 (folder)
        file_or_folder = str(client_socket.recv(1), 'UTF-8')

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
                directories[current_client_identifier].remove(old_path)
                directories[current_client_identifier].append(new_path)
                # change type "9" of renaming
                change = ("9", file_or_folder, new_path, old_path)
                add_change(seq_num, change)
                return

            # if the old path doesn't exist and the new path does exist we update "directories"
            if (not os.path.exists(old_path)) and (os.path.exists(new_path)):
                if old_path in directories[current_client_identifier]:
                    directories[current_client_identifier].remove(old_path)
                if not new_path in directories[current_client_identifier]:
                    directories[current_client_identifier].append(new_path)
                return

            # if we didn't return until now - it's a location replace
            os.replace(old_path, new_path)
            directories[current_client_identifier].remove(old_path)
            directories[current_client_identifier].append(new_path)
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

            # TODO rename not just to mother
            # deal the case that it's not a move, but a name change of folder
            if old_mother == new_mother:
                files = os.listdir(old_path)
                for file in files:
                    directories[current_client_identifier].remove(os.path.join(old_path, file))
                    directories[current_client_identifier].append(os.path.join(new_path, file))
                directories[current_client_identifier].remove(old_path)
                directories[current_client_identifier].append(new_path)
                # change type "9" of renaming
                change = ("9", file_or_folder, new_path, old_path)
                add_change(seq_num, change)
                # change the name of the folder
                os.rename(old_path, new_path)
                return

            # if the new path doesn't exist the folder has moved to new location and we need to create it
            if not os.path.exists(new_path):
                os.mkdir(new_path)
                # make a change ONLY for the folder (not it's content)
                change = change + (file_or_folder, new_path, old_path)
                add_change(seq_num, change)

            # move all the folder's content and don't inform changes
            if os.path.exists(old_path):
                files = os.listdir(old_path)
                for file in files:
                    os.replace(os.path.join(old_path, file), os.path.join(new_path, file))
                    directories[current_client_identifier].remove(os.path.join(old_path, file))
                    directories[current_client_identifier].append(os.path.join(new_path, file))
                directories[current_client_identifier].remove(old_path)
                directories[current_client_identifier].append(new_path)
                os.rmdir(old_path)


def add_change(seq_num, change):
    print("change: ")
    print(change)
    # add change to all computers of clients, but the client's ip itself
    for num in clients[current_client_identifier]:
        if num != seq_num:
            clients[current_client_identifier][num].append(change)



'''
An existing client has connected and the sever needs to update him about the changes that has been made
in his other computers
'''
def update_client(client_socket, seq_num):
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
        print("file name: " + file_name)

        # send old path
        send_file_name(client_socket, file_name)
        send_full_path(client_socket, old_path)
        # send new path
        send_file_name(client_socket, file_name)
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