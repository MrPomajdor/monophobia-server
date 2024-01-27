import socket
import time

host = "0.0.0.0"
port = 1337
with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as s:
    s.bind((host,port))
    s.listen()
    con, addr = s.accept()
    with con:
        print(f"Connection from {addr}")
        time.sleep(5)
        con.sendall(bytes("Gowno!".encode()))
        while True:
            data = con.recv(1024)
            if not data:
                break
            #con.sendall(data)