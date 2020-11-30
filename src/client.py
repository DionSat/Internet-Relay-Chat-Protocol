import socket
import select
import errno
import sys
from _thread import *
import signal
import threading
import os
import tqdm

BUFFER_SIZE = 1024 * 4
HOST = "127.0.0.1"
PORT = 1234

def help():
    print("\nHere is a list of commands:")

    print("\n#pm expects a valid user followed by a message.")
    print("\n#room expects a valid room followed by a message.")
    print("\n#create, #leave, #join, and #listroom expect a valid room")
    print("\n#allrooms can be used alone.")
    print("\nType quit to disconnect from IRC session.\n")
    print("\n\nExample: #create funroom")
    print("Example: #join funroom")
    print("Example: #whisper dave Hello")
    print("Example: #room general Hello Everyone!")
    print("Example: #allrooms")
    print("Example: #listroom funroom")
    print("Example: #userlist general")
    print("Example: #leave funroom")
    print("\nYou can also simply type in a message and everyone in your current room/rooms will see your message!\n")


def listener(s):
    while True:
        try:
            idata = s.recv(BUFFER_SIZE)  # receive,interpret and print the data from the host
            if not idata:
                break

            print(idata.decode("utf-8"))

        except socket.error:  # host connection lost
            print("Host connection lost!")
            os.kill(os.getpid(), signal.SIGTERM)
            break
    print("Host connection lost!")
    os.kill(os.getpid(), signal.SIGTERM)


def analyze(msg, server_sock):
    msg = msg.strip()
    data = []  # where the data is stored, after being split
    value = 0

    data.append(msg.split())

    if data[0][0] == "#ftp":
        file_name = data[0][1]
        file_transfer(server_sock, file_name, msg)
        value = 1

    return value


def file_transfer(server_sock, filename, msg):
    params = str.split(msg, ' ')
    if not (len(params) == 3):
        print('\nError: Invalid parameter, see HELP.\n')

    try:
        file_stream = open(filename, 'rb')

        # read file
        file_byte = file_stream.read(BUFFER_SIZE)
        file_stream.close()
    except:
        print('\nError: File doesn\'t exist.\n')
        return 0

    file_size = len(file_byte)
    msg += ' ' + str(file_size)
    server_sock.send(msg.encode('utf-8'))  # send msg

    # receive server response
    try:
        server_response = server_sock.recv(BUFFER_SIZE).decode('utf-8')
    except:
        print('\nError: Failed to send file. server no response\n')
        return 0

    # if server ready to receive the file
    if server_response == 'OK':
        # send file
        server_sock.send(file_byte)


def main():
    BUFFER_SIZE = 1024 * 10
    HOST = "127.0.0.1"
    PORT = 1234

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        s.connect((HOST, PORT))  # try to connect to host
        control = 1
    except socket.error:  # connection failed
        print("\nHost could not be reached on the default port!\n")
        PORT = int(input("Enter a port(-1 to quit):"))
        if PORT == -1:
            os.kill(os.getpid(), signal.SIGTERM)

    username = input("Username: ")

    # send username to server
    s.sendall(username.encode("utf-8"))

    i_thread = threading.Thread(target=listener, args=(s,))
    i_thread.start()

    print("\n\nWelcome to the IRC\n")

    while True:
        sdata = input("> ")  # Capture user message

        if sdata == 'quit':  # If user wants to quit
            break

        if sdata is None or len(sdata) < 3:
            continue

        if sdata == '#help':
            help()

        else:
            try:
                if analyze(sdata, s) == 0:
                    s.sendall(str.encode(sdata))  # send user message to host
            except socket.error:  # handle host disconnect
                print("Host connection lost!")
                break

    # os.kill(os.getpid(), signal.SIGTERM)


if __name__ == '__main__':
    main()