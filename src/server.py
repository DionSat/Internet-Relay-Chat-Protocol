import socket
import sys
import threading
import user
import os
import signal
import tqdm

HOST = "127.0.0.1"
PORT = 1234
BUFFER_SIZE = 1024 * 4
clients = []  # list of clients
rooms = ['general']
SEPARATOR = "<SEPARATOR>"


# this method sends the data/msg to all clients except the sending user
def broadcast(data, exclude_user, type):
    if type == 'all-users':
        for client in clients:
            if client.name == exclude_user.name:
                continue
            client.socket.sendall(data)

    if type == 'all-rooms':
        for i in exclude_user.room:
            if i in rooms:
                for client in clients:
                    if client.room == i:
                        if client.name == exclude_user.name:
                            continue
                        client.socket.sendall(data)


def roomcast(data, exclude_user, room):
    if room in rooms:
        for client in clients:
            if room in client.room:
                if client.name == exclude_user.name:
                    continue
                client.socket.sendall(data)


# this method checks the client message for commands begining with a # and executes the valid command
def analyze(msg, new_user):
    msg = msg.strip()
    data = []  # where the data is stored, after being split
    value = 0  # value returned at end -- 1 - a command, 0 - not a command

    data.append(msg.split())

    if data[0][0] == "#create":
        if len(data[0]) == 2:
            room_name = data[0][1]
            create_room(room_name, new_user)
            value = 1
        elif len(data[0]) == 1:
            new_user.socket.send("Room not specified invalid parameters. Please try again.".encode("utf-8"))
            value = 1
        elif len(data[0]) > 2:
            new_user.socket.send("Should only have one room name, too many listed refer to the #help.".encode("utf-8"))
            value = 1

    elif data[0][0] == "#join":
        if len(data[0]) == 2:
            room_name = data[0][1]
            join_room(room_name, new_user)
            value = 1
        elif len(data[0]) == 1:
            new_user.socket.send("Room not specified invalid parameters. Please try again.".encode("utf-8"))
            value = 1
        elif len(data[0]) > 2:
            new_user.socket.send("Should only have one room name, too many listed refer to the #help.".encode("utf-8"))
            value = 1

    elif data[0][0] == "#leave":
        if len(data[0]) == 2:
            room_name = data[0][1]
            leave_room(room_name, new_user)
            value = 1
        elif len(data[0]) == 1:
            new_user.socket.send("Room not specified invalid parameters. Please try again.".encode("utf-8"))
            value = 1
        elif len(data[0]) > 2:
            new_user.socket.send("Should only have one room name, too many listed refer to the #help.".encode("utf-8"))
            value = 1

    elif data[0][0] == "#room":
        if len(data[0]) == 3:
            room_name = data[0][1]
            new_msg = data[0][2]
            message_room(room_name, new_user, new_msg)
            value = 1
        elif len(data[0]) == 1:
            new_user.socket.send("Room not specified invalid parameters. Please try again.".encode("utf-8"))
            value = 1
        elif len(data[0]) > 2:
            new_user.socket.send("Should only have one room name, too many listed refer to the #help.".encode("utf-8"))
            value = 1

    elif data[0][0] == "#allrooms":
        list_all_rooms(new_user)
        value = 1

    elif data[0][0] == "#pm":
        if len(data[0]) == 3:
            other_user = data[0][1]
            new_msg = data[0][2]
            private_message(new_user, other_user, new_msg)
            value = 1
        elif len(data[0]) == 1:
            new_user.socket.send("Client not specified invalid parameters. Please try again.".encode("utf-8"))
            value = 1
        elif len(data[0]) > 2:
            new_user.socket.send("Should only have one client listed, too many listed refer to the #help.".encode("utf-8"))
            value = 1

    elif data[0][0] == "#ftp":
        if len(data[0]) == 3 or len(data[0]) == 4:
            file_name = data[0][1]
            receiving_user = data[0][2]
            file_transfer(new_user, receiving_user, file_name, data)
            value = 1
        else:
            new_user.socket.send("Invalid parameters. Please try again.".encode("utf-8"))
            value = 1

    elif data[0][0] == "#listroom":
        if len(data[0]) == 2:
            room_name = data[0][1]
            list_room_members(new_user, room_name)
            value = 1
        else:
            new_user.socket.send("Invalid parameters. Please try again.".encode("utf-8"))

    return value


def join_room(room_name, _user):
    if len(rooms) >= 10:
        _user.socket.sendall("sorry room limit reached for the server")
    else:
        if room_name not in rooms:
            msg = "room does not exist".encode("utf-8")
            _user.socket.send(msg)

        if len(str.split(room_name, ' ')) > 1 or len(room_name) == 0:
            _user.socket.sendall("Invalid room name.".encode("utf-8"))

            # add to _users room list
        if room_name not in _user.room:
            _user.room.append(room_name)

        join_msg = (_user.name + " has joined %s" % room_name).encode("utf-8")
        roomcast(join_msg, _user, room_name)


def create_room(room_name, _user):
    if len(rooms) >= 10:
        _user.socket.sendall("sorry room limit reached for the server")
    else:
        if len(str.split(room_name, ' ')) > 1 or len(room_name) == 0:
            _user.socket.sendall("Invalid room name.".encode("utf-8"))
        if room_name not in rooms:
            msg = f"User: [{_user.name}] created new room: {room_name}".encode("utf-8")
            broadcast(msg, _user, 'all-users')
            rooms.append(room_name)

            # add to _users room list
            if room_name not in _user.room:
                _user.room.append(room_name)


def leave_room(room_name, _user):
    if room_name not in rooms:
        _user.socket.sendall("Room does not exist")
    else:
        if room_name not in _user.room:
            _user.socket.sendall("Can't leave a room your not in")
        else:
            _user.room.remove(room_name)
            msg = f"{_user.name} has left the room".encode("utf-8")
            roomcast(msg, _user, room_name)

            _user.socket.sendall(("You have been removed from the room: %s" % room_name).encode("utf-8"))


def message_room(room_name, _user, data):
    if room_name not in rooms:
        _user.socket.sendall("Room does not exist")
    else:
        if room_name not in _user.room:
            _user.socket.sendall("Can't message a room you are not in")
        else:
            msg = ("[" + _user.name + "]: " + data).encode("utf-8")
            roomcast(msg, _user, room_name)


def list_all_rooms(_user):
    if len(rooms) > 0:
        title_msg = ("=============  All Rooms  =============").encode("utf-8")
        _user.socket.sendall(title_msg)
        for room in rooms:
            msg = ("Room: " + room).encode("utf-8")
            _user.socket.sendall(msg)


def list_room_members(_user, room_name):
    if len(rooms) > 0:
        if room_name in rooms:
                title_msg = ("=============  Room Members  =============").encode("utf-8")
                _user.socket.sendall(title_msg)
                for client in clients:
                    for room in client.room:
                        if room == room_name:
                            msg = ("member: " + client.name + "\n").encode("utf-8")
                            _user.socket.sendall(msg)
        else:
            _user.socket.sendall("Room does not exist".encode("utf-8"))
    else:
        _user.socket.sendall("There are no rooms".encode("utf-8"))


def private_message(_user, ouser, msg):
    try:
        for person in clients:
            if person.name == ouser:
                person.socket.sendall(("[" + _user.name + "] Private Message: " + msg).encode("utf-8"))
                return 1
        _user.socket.sendall("Sorry user does not exist. Cannot send message".encode("utf-8"))
    except:
        _user.socket.sendall("Sorry user does not exist. Cannot send message".encode("utf-8"))


def file_transfer(_user, ouser, filename, data):
    if not (len(data[0]) == 4 and len(data[0][0]) > 0 and len(data[0][1]) > 0 and len(data[0][2]) > 0 and len(data[0][3]) > 0):
        _user.socket.sendall('Invalid parameter, see HELP.'.encode("utf-8"))

    filename = data[0][1]
    file_size = data[0][3]

    for client in clients:
        if ouser == client.name:
            receiver = client

            # let sender send the file here
            _user.socket.sendall('OK'.encode('utf-8'))

            # receive file from sender
            try:
                file_byte = _user.socket.recv(BUFFER_SIZE)
                while len(file_byte) < int(file_size):
                    file_byte += _user.socket.recv(BUFFER_SIZE)
            except:
                _user.socket.sendall('Failed to send file.'.encode("utf-8"))

            # send msg to receiver for preparation
            receiver_filename = 'receive_' + os.path.basename(filename)
            data = f'{receiver_filename} {file_size} \nClient "[{_user.name}]" send you a file "{receiver_filename}"'
            receiver.socket.sendall(data.encode('utf-8'))

            # receive receiver's response
            try:
                receiver_response = receiver.socket.recv(BUFFER_SIZE)
            except:
                _user.socket.sendall('Failed to send file.'.encode("utf-8"))

            # if receiver ready to receive the file
            if receiver_response.decode('utf-8') == 'OK':
                # send file
                receiver.socket.sendall(file_byte)
            else:
                _user.socket.sendall('Failed to send file.'.encode("utf-8"))

            # send msg to current user
            data = f'You sent a file "{filename}" to user "{receiver.name}"'
            _user.socket.send(data.encode('utf-8'))



def listener(s):
    while True:
        try:
            s.listen()  # listen for socket connections
            conn, addr = s.accept()  # accept the connection, get a conn socket and grab the address
            new_user = user.user()  # create a user object
            new_user.socket = conn  # store the connection info
            new_user.address = addr
            new_user.name = None

            # Start a new thread and return its identifier
            # start_new_thread(threaded, (client_socket,))
            l = threading.Thread(target=threaded, args=(new_user,))  # start thread
            l.start()

        except socket.error:  # when the socket failed or is disconnected break the loop
            break


# thread function
def threaded(new_user):
    if 'general' not in new_user.room:  # put the new user in the general room
        new_user.room.append(rooms[0])

    while new_user.name is None:
        username = new_user.socket.recv(BUFFER_SIZE)  # get the username first thing
        new_user.name = username.decode("utf-8")

        if new_user.name.isspace() or new_user.name == '':
            new_user.socket.sendall("Please enter a valid user name!".encode("utf-8"))
            new_user.name = None

        else:
            for client in clients:
                if client.name == new_user.name:
                    new_user.socket.sendall(
                        (new_user.name + " is already in use, please enter a different name!").encode("utf-8"))
                    new_user.name = None

    clients.append(new_user)

    data = ("Server Message: " + new_user.name + " has joined the IRC session\n").encode("utf-8")
    broadcast(data, new_user, 'all-users')
    data = ("Message: " + new_user.name + " has joined the room").encode("utf-8")
    broadcast(data, new_user, 'all-rooms')

    with new_user.socket:
        try:
            while True:

                # data received from client
                data = new_user.socket.recv(BUFFER_SIZE)
                data = data.decode("utf-8")

                if not data:
                    break
                if data:
                    if analyze(data, new_user) == 0:
                        for room in new_user.room:
                            roomcast(("[" + new_user.name + "]: " + data).encode("utf-8"), new_user, room)

                print("Client sent %s" % data)
        except socket.error:  # When a client disconnects let other users know and break the loop
            for i in clients:
                if i.name == new_user.name:
                    clients.remove(i)

                    data = (new_user.name + " has left the IRC session").encode("utf-8")

                    broadcast(data, new_user, 'all-users')

                    break
        for i in clients:
            if i.name == new_user.name:
                clients.remove(i)

                data = (new_user.name + " has left the IRC session").encode("utf-8")

                broadcast(data, new_user, 'all-users')

                break
        os.kill(os.getpid(), signal.SIGTERM)  # kill the process and running threads


def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    """  
    binds the server to an entered IP address and at the  
    specified port number.  
    The client must be aware of these parameters  
    """

    try:
        server_socket.bind((HOST, PORT))
    except:
        print("Bind failed. Error : " + str(sys.exc_info()))
        sys.exit()

    l = threading.Thread(target=listener, args=(server_socket,))  # start thread
    l.start()


    while True:
        msg = input(">")
        data = str.split(msg, ' ')
        if msg == 'quit':
            os.kill(os.getpid(), signal.SIGTERM)  # kill the process and running threads
            sys.exit()


if __name__ == '__main__':
    main()
