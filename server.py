# Noa Eitan 316222777, Coral Kuta 208649186
import os
import socket
import sys
import random
import string
import watchdog

# consts
BYTES_FOR_COUNTER = 3
BYTES_TO_READ = 100
MAX_PORT = 65545
MIN_PORT = 0
ARGUMENTS_NUMBER = 2
CHARACTERS = 128
NEW_ID = "ID".zfill(CHARACTERS)
# SERVER_PATH = "/home/coral/Desktop/Communication Network/"
SERVER_PATH = os.getcwd() + "/"


# class Handler(watchdog.events.PatternMatchingEventHandler):
#     def __init__(self):
#         watchdog.events.PatternMatchingEventHandler(self, patterns={}, ignore_patterns=None,
#                                                     ignore_directiries=False, case_sensitive=True)

'''
The function creates a new identifier for a new client.
'''
def create_id():
    # allowing letter (upper and lower case) and digits.
    characters = string.ascii_letters + string.digits
    # creating a 128 characters string and return it as the new id.
    identifier = ''.join(random.choice(characters) for _ in range(CHARACTERS))
    return identifier


'''
The server function. Once the server is open, he never closes.
'''
def server(port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('', port))
    s.listen(5)

    # new client dictionary
    clients = {}

    while True:
        client_socket, client_address = s.accept()
        data = client_socket.recv(CHARACTERS)
        str_data = str(data, 'UTF-8')

        # new client - create random identifier
        if str_data == NEW_ID:
            identifier = create_id()
            client_socket.send(bytes(identifier, 'UTF-8'))
            clients[identifier] = SERVER_PATH + identifier
            # create the folder with the name of the new client
            path = os.path.join(SERVER_PATH, identifier)
            os.mkdir(path)

            while True:
                name_size = int.from_bytes(client_socket.recv(4), sys.byteorder)
                name = str(client_socket.recv(name_size), 'UTF-8')
                file_to_write = open(path + '/' + name, "wb")
                file_data = client_socket.recv(1024)
                while file_data:
                    file_to_write.write(file_data)
                    file_data = client_socket.recv(1024)
                print("Download Completed")
                file_to_write.close()
                break



        # existing client
        else:
            identifier = str_data
            # doing the logic of the client
            pass


            



        client_socket.send(data.upper())
        # client_socket.close()
        print("Client disconnected.")


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
    server(int(sys.argv[1]))


if __name__ == '__main__':
    main()