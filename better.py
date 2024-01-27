import random
import struct
import time
from modules.variables import *
from modules.clients import *
from modules.messages import *

import socket
import threading

connectedSockets = []
clientsDict = {}

def handle_receive(client_soc: socket.socket,id):
    try:
        print("Accepted client.")
        while True:
            # Receive data from the client
            data_received = client_soc.recv(1024)  # Adjust the buffer size as needed

            print("data",data_received)
            # Break the loop if no data is received
            if not data_received:
                break

            # Process the received data
            print("Received data from client:", data_received)

            # Send a response back to the client
            client_soc.sendall(Headers.ack)
    except Exception as e:
        print("Error handling client:", e)
    finally:
        client_soc.close()

def handle_send(client_soc: socket.socket,id):
    print("Starting sending handling.")
    packed_data = struct.pack('!i', id)
    client_soc.sendall(Headers.data+b'\x03'+packed_data)
    print("Sent id")
    clientsDict[id]["ackw"] = True

    try:
        while True:
            client_soc.sendall(Headers.echo+b'\x00')
            print("sent echo")
            time.sleep(1)
    except Exception as e:
        print("Error handling client:", e)

with socket.socket() as listening_sock:
    listening_sock.bind(('0.0.0.0', 1337))
    listening_sock.listen()
    while True:
        client_soc, client_address = listening_sock.accept()
        # Send each "client_soc" connection as a parameter to a thread.
        new_id = 0
        if len(clientsDict) > 0:
            new_id = random.randint(0,256)
            while not new_id in clientsDict:
                new_id = random.randint(0,256)
        clientsDict[new_id] = {}
        connectedSockets.append(client_soc)
        threading.Thread(target=handle_receive, args=(client_soc,new_id), daemon=True).start()
        threading.Thread(target=handle_send, args=(client_soc,new_id), daemon=True).start()