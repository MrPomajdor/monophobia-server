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
from modules.logging import *
import argparse



argparser = argparse.ArgumentParser()
argparser.add_argument("-i","--ip",type=str,default='0.0.0.0',help='Set ip that the server will bind to')
argparser.add_argument("-p","--port",type=int,default=1338,help='Set the port for the sevrer')
argparser.add_argument("-d","--debug",type=int,default=0,help='Set a minimum level for printing debug messages (0-6)')
argparser.add_argument("-l","--log",action='store_true',default=False,help='Enable/disable storing log in a log file')

class GameServer:
    def __init__(self, host='0.0.0.0', port=1338):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_socket.bind((host, port))
        self.udp_socket.bind((host, port))
        self.server_socket.listen(5)
        self.echo_interval = 2
        self.clients: List[Player] = []
        self.lobbies: List[Lobby] = []
        self.host = host
        self.port = port
    def echo_handler(self,sock:socket):
        while 1:
            time.sleep(5)
            echo = Packet()
            echo.header = Headers.echo
            echo.flag = Flags.none
            if not echo.send(sock):
                break
    #this code was written by ChatGPT because i was lazy to write something like that xd
    def wait_for_packet(self, client_socket, expected_header):
        max_attempts = 50 
        sleep_interval = 0.05

        for attempt in range(1, max_attempts + 1):
            try:
                data = client_socket.recv(1024) 
                if data:
                    received_packet = Packet() 
                    received_packet.digest_data(data)
                    if received_packet.header == expected_header:
                        return received_packet
            except socket.timeout:

                pass  # Continue the loop if a timeout occurs

            # Wait for a short interval before the next attempt
            time.sleep(sleep_interval)

        return None
    def udp_handler(self):
        try:
            while 1:
                try:
                    data, addr = self.udp_socket.recvfrom(4096)
                except Exception as e:
                    mainLogger.log(f"{e} UDP")
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
                                    mainLogger.log(f"player with id {id} initialized udp port to {addr[1]}",3)
                                    break
                        continue
                player_class = next((plc for plc in self.clients if plc.udp_port == addr[1] and plc.ip == addr[0]), None)
                if not data or not player_class or player_class.ip != addr[0] or player_class.udp_port != addr[1]:
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
        except KeyboardInterrupt:
            mainLogger.log("Server shitting down (UDP)")
        finally:
            self.udp_socket.close()
                
    def HandleClientTCP(self, client_socket:socket.socket, address):
        player_id = None
        mainLogger.log(f"Accepted connection from {address}",1)
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
                mainLogger.log("hello packet not recieved. Disconnecting.",2)
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
            mainLogger.log(f"Client initialized: {name} id {player_class.id}")
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
                    mainLogger.log("No data - client disconnected",3)
                    break
                packet = Packet()
                packet.digest_data(data)
                hand.parse_packet(packet)
            raise AllGoodEnding("disconnecting")
            
                


        except socket.timeout:
            mainLogger.log("Timeout waiting for packet. Disconnecting client.",3)
        except ConnectionException as e:
            mainLogger.log(f"{e}",3)
        except AllGoodEnding as e:
            mainLogger.log(f"Session closed!",3)
        except Exception as e:
            resp = Packet()
            resp.header = Headers.rejected
            resp.flag = Flags.Response.closing_con
            resp.add_to_payload(str(e))
            resp.send(client_socket)
            mainLogger.log(f"{e}")
            traceback.print_exc()
        finally:
            # Disconnect client and clean up
            if player_class and client_socket:
                mainLogger.log(f"Client {player_class.id}/{player_class.name} disconnected.")
                hand.disconnect_client(client_socket, player_class)
            else:
                mainLogger.log(f"Some client disconnected.")

        
        
    def tcp_recv(self):
        mainLogger.log("Server is listening for connections...")
        try:
            while True:
                client_socket, addr = self.server_socket.accept()
                client_socket.settimeout(10)
                client_thread = threading.Thread(target=self.HandleClientTCP, args=(client_socket, addr))
                client_thread.start()
        except KeyboardInterrupt:
            mainLogger.log("Server shutting down (TCP).")
        finally:
            self.server_socket.close()

    
    def start(self):
        mainLogger.log(f"Starting Monophobia server on {self.host}:{self.port}")
        print(f"          Close server using CTRL+Break")
        tcp = threading.Thread(target=self.tcp_recv)
        tcp.start()
        udp = threading.Thread(target=self.udp_handler)
        udp.start()

args = argparser.parse_args()
# Instantiate and start the server
game_server = GameServer(args.ip,args.port)
mainLogger.log(f"Set log level: {args.debug}")
mainLogger.log_level = args.debug
game_server.start()