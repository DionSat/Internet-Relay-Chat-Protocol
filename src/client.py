import socket

# establish type of connection as IPV4 and TCP
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# connect to the server
client_socket.connect((socket.gethostname(), 29))

full_msg = ''
while True:
    # receive message from the server in a buffer
    msg = client_socket.recv(8)
    if len(msg) <= 0:
        break
    full_msg += msg.decode("utf-8")
print(full_msg)