# Noa Eitan 316222777, Coral Kuta 208649186
import os
import socket
import sys
import random
import string

# consts
BYTES_FOR_COUNTER = 3
BYTES_TO_READ = 100
MAX_PORT = 65545
MIN_PORT = 0
ARGUMENTS_NUMBER = 2
CHARACTERS = 128
NEW_ID = "ID".zfill(CHARACTERS)
SERVER_PATH = os.getcwd() + "/"
CURRENT = -1



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

    # new clients dictionary
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

            # base dir of client
            dir_stack = [path]

            while True:
                option = str(client_socket.recv(1), 'UTF-8')

                # no more
                if option == "0":
                    break
                # file
                elif option == "1":
                    # getting the name of the file
                    file_name_len = int.from_bytes(client_socket.recv(8), sys.byteorder)
                    file_name = str(client_socket.recv(file_name_len), 'UTF-8')
                    # file_to_write = open(dir_stack[LAST] + '/' + file_name, "wb")
                    file_to_write = open(os.path.join(dir_stack[CURRENT], file_name), "wb")
                    # getting the size of file
                    file_len = int.from_bytes(client_socket.recv(8), sys.byteorder)
                    counter = file_len

                    if file_len < 1024:
                        file = client_socket.recv(file_len)
                    else:
                        file = client_socket.recv(1024)

                    while file:
                        file_to_write.write(file)
                        counter = counter - len(file)
                        if counter <= 0:
                            break
                        elif counter < 1024:
                            file = client_socket.recv(counter)
                        else:
                            file = client_socket.recv(1024)
                    print("Download Completed")
                    file_to_write.close()

                # create new folder
                elif option == "2":
                    # getting the name of the file
                    dir_name_len = int.from_bytes(client_socket.recv(8), sys.byteorder)
                    dir_name = str(client_socket.recv(dir_name_len), 'UTF-8')
                    dir_stack.append(os.path.join(dir_stack[CURRENT], dir_name))
                    os.mkdir(dir_stack[CURRENT])

                # change dir to " "
                elif option == "3":
                    # getting the name of the file
                    dir_name_len = int.from_bytes(client_socket.recv(8), sys.byteorder)
                    dir_name = str(client_socket.recv(dir_name_len), 'UTF-8')

                    for i in range(len(dir_stack)):
                        tokens = dir_stack[i].split('/')
                        if tokens[-1] == dir_name:
                            temp = dir_stack.pop(i)
                            dir_stack.append(temp)
                            break

                    # result - dir_stack[CURRENT] = desired folder


        # existing client
        else:
            # identifier = str_data
            # doing the logic of the client
            pass

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