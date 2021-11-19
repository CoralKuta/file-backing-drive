# Noa Eitan 316222777, Coral Kuta 208649186
import os.path
import socket
import sys

MAX_PORT = 65545
MIN_PORT = 0
ARGUMENTS_WITH_ID = 6
ARGUMENTS_WITHOUT_IS = 5
NUMBER_IN_IP = 4
MAX_IP_NUM = 255
MIN_IP_NUM = 0
SIZE_ID = 128


def track_data_with_id(ip, port, path, timer, identifier):
    print(ip, port, path, timer, identifier)


def track_data_without_id(ip, port, path, timer):
    # connect to server (SYN) and get identifier
    # create socket with TCP protocol
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # connect to server
    s.connect((ip, int(port)))
    # ask the server for identifier
    id_str = "ID".zfill(SIZE_ID)
    s.send(bytes(id_str, 'UTF-8'))
    identifier = s.recv(SIZE_ID)
    # send data to server
    send_data_first_time(s, path)
    # send 0 to server- means that we finished send the files, start tracking
    s.send(bytes("0", 'UTF-8'))
    # end of talk with server
    s.close()


def send_data_first_time(socket_client, path):
    for root, dirs, files in os.walk(path):

        root_name = os.path.basename(root)

        # only sub-directories
        for directory_name in dirs:
            send_folder_name(socket_client, directory_name, root_name)

        # only files
        for file_name in files:
            file_path = os.path.join(root, file_name)
            send_file(socket_client, file_name, file_path, root_name)


def send_name(s, name):
    length = len(name)
    s.send(length.to_bytes(8, sys.byteorder))
    s.send(bytes(name, 'UTF-8'))


def send_length(s, data):
    length = os.path.getsize(data)
    s.send(length.to_bytes(8, sys.byteorder))


def send_folder_name(socket_client, folder_name, mother_folder):
    # send 2 to server- means that we send a folder in current
    socket_client.send(bytes("2", 'UTF-8'))

    # send size of name file and the name of file
    send_name(socket_client, folder_name)

    # where the server makes the folder ??
    send_name(socket_client, mother_folder)


def send_file(socket_client, file_name, file_data, mother_folder):
    # send 1 to server- means that we send a file
    socket_client.send(bytes("1", 'UTF-8'))

    # send file name
    send_name(socket_client, file_name)

    # send where the file belongs
    send_name(socket_client, mother_folder)

    # send the size of the file
    send_length(socket_client, file_data)

    # start send the data that in the file
    file = open(file_data, "rb")
    data = file.read(1024)
    # send the bytes in the file
    while data:
        socket_client.send(data)
        data = file.read(1024)
    file.close()



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
