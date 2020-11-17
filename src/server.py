import socket

# establish type of connection as IPV4 and TCP
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# bind to your local host on port 29
server_socket.bind((socket.gethostname(), 29))
# listen for connections and leave a queue of 5
server_socket.listen(5)

# listen for connections forever
while True:
    clientsocket, address = server_socket.accept()
    # acknowledge the connection
    print(f"Connection from {address} has been established!")
    # send acknowledgement of connection to client
    clientsocket.send(bytes("Welcome to the server!", "utf-8"))
    # close the connection after sending the message
    clientsocket.close()