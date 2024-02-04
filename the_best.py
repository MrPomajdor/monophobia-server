from io import BytesIO
import json
import socket
import threading
import time
import struct
import traceback
from modules.messages import *
from typing import List
from modules.formats import DataFormats
from modules.blocks import *
from modules.packet import *
from modules.packet_classes import *
from modules.handling import Handling
from modules.exceptions import *

        


class GameServer:
    def __init__(self, host='127.0.0.1', port=1338):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_socket.bind((host, port))
        self.udp_socket.bind((host, port))
        self.server_socket.listen(5)
        self.echo_interval = 2
        self.clients: List[Player] = []
        xd = Lobby("Xd")
        self.lobbies: List[Lobby] = [xd]
    def echo_handler(self,sock:socket.socket):
        while 1:
            time.sleep(5)
            echo = Packet()
            echo.header = Headers.echo
            echo.flag = Flags.none
            if not echo.send(sock):
                break

    def wait_for_packet(self, client_socket, expected_header):
        max_attempts = 50  # Adjust the maximum number of attempts as needed
        sleep_interval = 0.05  # Adjust the sleep interval in seconds as needed

        for attempt in range(1, max_attempts + 1):
            try:
                data = client_socket.recv(1024)  # Adjust the buffer size as needed
                if data:
                    received_packet = Packet() 
                    received_packet.digest_data(data)
                    if received_packet.header == expected_header:
                        return received_packet  # Return the received packet if it matches the expected header
            except socket.timeout:

                pass  # Continue the loop if a timeout occurs

            # Wait for a short interval before the next attempt
            time.sleep(sleep_interval)

        return None
    def udp_handler(self):
        while 1:
            try:
                data, addr = self.udp_socket.recvfrom(4096)
            except Exception as e:
                print(f"{e} UDP")
            #detect 'I'm here!' packet
            if data:
                if len(data)>2 and data[:2] == Headers.imHere: #that looks ugly as hell. Oh and ImHere packet gets sent in the handshake phase, to tell the server what udp_port im going to send on
                    p = next((plc for plc in self.clients if plc.udp_port == addr[1] and plc.ip == addr[0]), None)
                    if not p:
                        imHerePacket = Packet()
                        imHerePacket.digest_data(data)
                        id = imHerePacket.get_from_payload(['int'])
                        for xd in self.clients:
                            if xd.id == id and xd.udp_port==None:
                                xd.udp_port = addr[1]
                                print(f"player with id {id} initialized udp port to {addr[1]}")
                                continue
            
            player_class = next((plc for plc in self.clients if plc.udp_port == addr[1] and plc.ip == addr[0]), None)
            if not data or not player_class or player_class.ip != addr[0] or player_class.udp_port != addr[1]:
                print(":c")
                continue

            try:
                if data.decode("UTF-8") == "holepunch":
                    continue
            except:
                pass
            player_class.udp_port = addr[1]
            dataPacket = Packet()
            if dataPacket.digest_data(data):
                player_class.handler.parse_packet(dataPacket)
                
    def HandleClientTCP(self, client_socket:socket.socket, address):
        player_id = None
        print(f"Accepted connection from {address}")
        hand = Handling()
        hand.server_class = self
        #client_socket.settimeout(5)  # Set a timeout for the hello packet
        try:
            # create the hello packet to send
            hello = Packet()
            hello.header = Headers.hello
            hello.flag = Flags.none
            hello.send(client_socket)
            
            packet = self.wait_for_packet(client_socket,Headers.hello)
            if not packet:
                print("hello packet not recieved. Disconnecting.")
                raise ConnectionException("Cliend did not respond to hello.")
            # Receive player name from the client
            name = packet.get_from_payload(['string'])
            # Assign a new player ID
            # Add the player to the global players dictionary
            player_class = hand.init_player(name,address)
            player_class.socket = client_socket
            id = Packet()
            id.header = Headers.data
            id.flag = Flags.Response.idAssign
            id.add_to_payload(player_class.id)
            id.send(client_socket)
            echo = threading.Thread(target=self.echo_handler, args=(client_socket,))
            echo.start()
            print(f"Client initialized: {name} id {player_class.id}")
            player_class.handler = hand
            hand.client_socket = client_socket
            hand.player_class = player_class
            hand.server_class = self


            while 1:
                try:
                    data = client_socket.recv(1024)
                except:
                    raise AllGoodEnding(":DD")
                if not data:
                    print("No data - client disconnected")
                    break
                packet = Packet()
                packet.digest_data(data)
                hand.parse_packet(packet)
            raise AllGoodEnding("disconnecting")
            
                


        except socket.timeout:
            print("Timeout waiting for packet. Disconnecting client.")
        except ConnectionException as e:
            print(f"{e}")
        except AllGoodEnding as e:
            print(f"Session closed!")
        except Exception as e:
            resp = Packet()
            resp.header = Headers.rejected
            resp.flag = Flags.Response.closing_con
            resp.add_to_payload(str(e))
            resp.send(client_socket)
            print(f"{e}")
            traceback.print_exc()
        finally:
            # Disconnect client and clean up
            print("Client disconnected.")
            if player_class and client_socket:
                hand.disconnect_client(client_socket, player_class)

        
        
    def tcp_recv(self):
        print("Server is listening for connections...")
        try:
            while True:
                client_socket, addr = self.server_socket.accept()
                client_socket.settimeout(10)
                client_thread = threading.Thread(target=self.HandleClientTCP, args=(client_socket, addr))
                client_thread.start()
        except KeyboardInterrupt:
            print("Server shutting down.")
        finally:
            self.server_socket.close()

    
    def start(self):
        tcp = threading.Thread(target=self.tcp_recv)
        tcp.start()
        udp = threading.Thread(target=self.udp_handler)
        udp.start()


# Instantiate and start the server
game_server = GameServer('0.0.0.0')
game_server.start()