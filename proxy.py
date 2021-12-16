# 1- display the communication between the local and remote machines to the console ( hexdump ).
# 2- receive data from an incoming socket from either the local or remote machine ( receive_from ).
# 3- manage the traffic direction between remote and local machines ( proxy_handler ).
# 4- set up a listening socket and pass it to our proxy_handler ( server_loop ).
import sys
import socket
import threading

# ASCII printable characters
# if one exists, or a dot (.) if such a representation doesn’t exist.
# if the length of the corresponding character equals 3, we get the character ( chr(i) ). Otherwise, we get a dot ( . ).
HEX_FILTER = ''.join(
    [(len(repr(chr(i))) == 3) and chr(i) or '.' for i in range(256)])
# provides us with a way to watch the communication going through the proxy in real time.


def hexdump(src, length=16, show=True):
    if isinstance(src, bytes):
        src = src.decode()
    results = list()
    # grab a piece of the string to dump and put it into the word variable
    for i in range(0, len(src), length):
        word = str(src[i:i+length])
        # substitute the string representation of each character for the corresponding character in the raw string ( printable )
        printable = word.translate(HEX_FILTER)
	# substitute the hex representation of the integer value of every character in the raw string ( hexa ).
        hexa = ' '.join([f'{ord(c):02X}' for c in word])
        hexwidth = length*3
        # create a new array to hold the strings, result ,
        # that contains the hex value of the index of the first byte in the word,
        # the hex value of the word, and its printable representation
        results.append(f'{i:04X} {hexa:<{hexwidth}}  {printable}')
    if show:
        for line in results:
            print(line)
        else:
            return results

# create a function that the 2 ends of the proxy will use to receive data
# For receiving both local and remote data, we pass in the socket object to be used.

def receive_from(connection):
    buffer = b""
    # 5 sec timeout
    # might be aggressive if you’re proxying traffic to other countries or over lossy networks,
    # so increase the time-out as necessary.
    connection.settimeout(5)
    try:
        while True:
            data = connection.recv(4096)
            if not data:
                break
            buffer += data
    except Exception as e:
        pass
    return buffer
    # return the buffer byte string to the caller, which could be either the local or remote machine.

# modify the response or request packets before the proxy sends them on their way.
# for request_handler and response_handler.
# fuzzing tasks, test for authentication issues, or do whatever else your heart desires.
# if you find plaintext user credentials being sent and want to try to elevate privileges
# on an application by passing in admin instead of your own username.


def request_handler(buffer):
    # modif
    return buffer


def response_handler(buffer):
    # modif
    return buffer

# the bulk of the logic for our proxy.


def proxy_handler(client_socket, remote_host, remote_port, receive_first):
    remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    remote_socket.connect((remote_host, remote_port))

    if receive_first:
	# accepts a connected socket object and performs a receive.
        remote_buffer = receive_from(remote_socket)
	# dump the contents of the pacjet so that we can inspect it.
        hexdump(remote_buffer)
    
    remote_buffer = response_handler(remote_buffer)
    if len(remote_buffer):
        print("[<==] Sending %d bytes to localhost." % len(remote_buffer))
        client_socket.send(remote_buffer)

    while True:
        local_buffer = receive_from(client_socket)
        if len(local_buffer):
            line = "[==>] Received %d bytes from localhost." % len(local_buffer)
            print(line)
            hexdump(local_buffer)

            local_buffer = request_handler(local_buffer)
            remote_socket.send(local_buffer)
            print("[==>] Sent to remote.")

        remote_buffer = receive_from(remote_socket)
        if len(remote_buffer):
            print("[<==] Received %d bytes from remote." % len(remote_buffer))
            hexdump(remote_buffer)

            remote_buffer = response_handler(remote_buffer)
            client_socket.send(remote_buffer)
            print("[<==] Sent to localhost.")

        if not len(local_buffer) or not len(remote_buffer):
            client_socket.close()
            remote_socket.close()
            print("[*] No more data. Closing connections.")
            break


def server_loop(local_host, local_port, remote_host, remote_port, receive_first):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server.bind((local_host, local_port))
    except Exception as e:
        print('Problem on bind: %r' % e)
        print("[!!] Failed to listen on %s:%d" % (local_host, local_port))
        print("[!!] Check for other listening sockets or correct permissions.")
        sys.exit(0)

    print("[*] Listening on %s:%d" % (local_host, local_port))
    server.listen(5)
    while True:
        client_socket, addr = server.accept()
        # print out the local connection information
        line = "> Received incoming connection from %s:%d" % (addr[0], addr[1])
        print(line)
        # start a thread to talk to the remote host
        proxy_thread = threading.Thread(target=proxy_handler, args=(
            client_socket, remote_host, remote_port, receive_first))
        proxy_thread.start()


def main():
    if len(sys.argv[1:]) != 5:
        print("Usage: ./proxy.py [localhost] [localport]", end='')
        print("[remotehost] [remoteport] [receive_first]")
        print("Example: ./proxy.py 127.0.0.1 9000 123.123.124.124 9000 True")
        sys.exit(0)
    local_host = sys.argv[1]
    local_port = int(sys.argv[2])

    remote_host = sys.argv[3]
    remote_port = int(sys.argv[4])

    receive_first = sys.argv[5]

    if "True" in receive_first:
        receive_first = True
    else:
        receive_first = False

    server_loop(local_host, local_port, remote_host,
                remote_port, receive_first)


if __name__ == '__main__':
    main()
