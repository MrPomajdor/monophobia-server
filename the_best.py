from io import BytesIO
import json
import socket
import threading
import time
import struct
from modules.messages import *
from typing import List
from modules.formats import DataFormats
from modules.blocks import *




class Packet:
    def __init__(self):
        self.header = b'\x00\x00'
        self.flag = Flags.none
        self.payload = b''

    def digest_data(self, data):
        with BytesIO(data) as stream:
            # Read the header (2 bytes)
            self.header = stream.read(2)

            # Read the flag (1 byte)
            self.flag = stream.read(1)

            # Read the payload (the rest of the bytes)
            self.payload = stream.read()

    def send(self, client_socket) -> int:
        buf = PacketParser.assemble_message(self.header, self.flag, self.payload)
        try:
            client_socket.sendall(buf)
            return len(buf)
        except:
            print("Failed to send packet!")
            return 0

    def add_to_payload(self, value):
        if isinstance(value, float):
            self.payload += struct.pack('f', value)
        elif isinstance(value, str):
            value_bytes = value.encode('utf-8')
            self.payload += struct.pack('I',len(value_bytes)) + value_bytes
        elif isinstance(value, bool):
            self.payload += struct.pack('?', value)
        elif isinstance(value, int):
            self.payload += struct.pack('I', value)

    def get_from_payload(self,formats:list) -> tuple:
        _pay = self.payload
        result = []
        try:
            for format in formats:
                if format == 'string':
                    l = struct.unpack('i',_pay[:4])[0]
                    data = _pay[4:][:l]
                    result.append(data)
                    _pay = _pay[4+l:]
                else:
                    data = struct.unpack(DataFormats.formats_dict[format],_pay[:DataFormats.formats_len_dict[format]])[0]
                    _pay = _pay[DataFormats.formats_len_dict[format]:]
                    result.append(data)
                
        except Exception as e:
            print(f"Invalid packet payload format {e}")
            return ()
        if len(formats) > 1:
            return tuple(result)
        return result[0]

class PacketParser:
    @staticmethod
    def assemble_message(header, flag, payload):
        return header + flag + payload


        


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

    def handle_client(self, client_socket:socket.socket, address):
        player_id = None
        print(f"Accepted connection from {address}")
        #client_socket.settimeout(5)  # Set a timeout for the hello packet
        try:
            # create the hello packet to send
            print("Sending hello")
            hello = Packet()
            hello.header = Headers.hello
            hello.flag = Flags.none
            hello.send(client_socket)
            
            packet = self.wait_for_packet(client_socket,Headers.hello)
            if not packet:
                print("hello packet not recieved. Disconnecting.")
                self.disconnect_client(client_socket, player_id)
                return
            print("Recieved hello!")
            # Receive player name from the client
            name = packet.get_from_payload(['string'])
            print(f"Recieved player name {name}")
            # Assign a new player ID
            # Add the player to the global players dictionary
            player_class = self.init_player(name,address)
            player_class.socket = client_socket
            print("Sending id")
            id = Packet()
            id.header = Headers.data
            id.flag = Flags.Response.idAssign
            id.add_to_payload(player_class.id)
            id.send(client_socket)
            echo = threading.Thread(target=self.echo_handler, args=(client_socket,))
            echo.start()
            while 1:
                data = client_socket.recv(1024)
                if not data:
                    print("No data - client disconnected")
                    break
                packet = Packet()
                packet.digest_data(data)

                match packet.header:
                    case Headers.data:
                        match packet.flag:
                            case Flags.Post.joinLobby: #{"mapName":"grid0","time":300,"players":[{"name":"debil","id":0,"cosmetics":[],"skin":"male01","isHost":false}]}
                                lobby_id, password = packet.get_from_payload(['int','string'])
                                lobby = next((item for item in self.lobbies if item.id == lobby_id), None)

                                if lobby != None:
                                    if lobby.id == lobby_id:
                                        if len(lobby.players) >= lobby.max_players:
                                            resp = Packet()
                                            resp.header = Headers.rejected
                                            resp.flag = Flags.Response.error
                                            resp.add_to_payload("LOBBY_FULL")
                                            resp.send(client_socket)
                                            return
                                        if lobby.password_protected and lobby.password != password: #check for password
                                            resp = Packet()
                                            resp.header = Headers.rejected
                                            resp.flag = Flags.Response.error
                                            resp.add_to_payload("BAD_PASSWORD")
                                            resp.send(client_socket)
                                            return
                                        
                                        #Everything ok add player to the lobby and send confirmation (lobby info)
                                        json_info = lobby.GetInfoJSON()


                                        resp = Packet()
                                        resp.header = Headers.data
                                        resp.flag = Flags.Response.lobbyInfo
                                        resp.add_to_payload(json_info)
                                        resp.send(client_socket)
                                        for pl in lobby.players:
                                            resp.send(pl.socket)
                                        lobby.AddPlayer(player_class)
                                        player_class.lobby = lobby
                                        resp.send(client_socket)
                                       
                                else:
                                    resp = Packet()
                                    resp.header = Headers.rejected
                                    resp.flag = Flags.Response.error
                                    resp.add_to_payload("LOBBY_NOT_FOUND")
                                    resp.send(client_socket)
                            case Flags.Request.lobbyList:
                                #lobby_data = self.generate_lobby_data()
                                
                                response_packet = Packet()
                                response_packet.header = Headers.data
                                response_packet.flag = Flags.Response.lobbyList
                                print(response_packet.payload)
                                response_packet.add_to_payload(len(self.lobbies))
                                print(response_packet.payload)
                                for lobby in self.lobbies:
                                    response_packet.add_to_payload(lobby.id)
                                    response_packet.add_to_payload(lobby.name)
                                    response_packet.add_to_payload(lobby.password_protected)
                                    response_packet.add_to_payload(len(lobby.players))
                                    response_packet.add_to_payload(lobby.max_players)
                                response_packet.send(client_socket)
                            case Flags.Post.createLobby:
                                payload_tuple = packet.get_from_payload(['string','string','int'])
                                if not payload_tuple:
                                    return
                                lobby_name,password,max_players = payload_tuple
                                self.createLobby(player_id,lobby_name,)
                                self.add_client_to_lobby(player_id, lobby_name)
                            case Flags.Post.transformData:
                                try:
                                    js = json.loads(packet.get_from_payload(['string']))
                                except:
                                    print(f"[!] Recieved corrupted json data from {player_class.id}!")
                                    resp = Packet()
                                    resp.header = Headers.rejected
                                    resp.flag = Flags.Response.closing_con
                                    resp.add_to_payload("JSON_CORRUPTED")
                                    resp.send(client_socket)
                                    return
                                id = js.get("id")
                                if player_class.id == id:  #check if id matches
                                        #TODO: make the alsgorythm for checking if the client is cheating, eg. check the distance between positions and detect when it jumps then teleport him back
                                        transforms = js.get("transforms")
                                        pos = transforms.get("position")
                                        rot = transforms.get("rotation")
                                        vel = transforms.get("velocity")
                                        player_class.position = (pos.get("x"),pos.get("y"),pos.get("z"))
                                        player_class.rotation = (rot.get("x"),rot.get("y"),rot.get("z"))
                                        player_class.velocity = (vel.get("x"),vel.get("y"),vel.get("z"))
                                        self.broadcast(player_class.lobby,BroadcastTypes.transforms)
                                else:
                                    print(f"ID doesnt match id (local) {player_class.id} id (remote) {id}")
                    case Headers.echo:
                        #i mean, okay? What do you want me to fucking do with that information. Like I could send you ack i guess?
                        xd = Packet()
                        xd.header = Headers.ack
                        xd.send(client_socket)
        except socket.timeout:
            print("Timeout waiting for packet. Disconnecting client.")
        except Exception as e:
            resp = Packet()
            resp.header = Headers.rejected
            resp.flag = Flags.Response.closing_con
            resp.add_to_payload(str(e))
            resp.send(client_socket)
            print(f"{e} 271")
        finally:
            # Disconnect client and clean up
            print("Client disconnected.")
            self.disconnect_client(client_socket, player_class)
    def broadcast(self,lobby:Lobby,what):
        match what:
            case BroadcastTypes.transforms:
                dic = {}
                dic["type"] = "OtherPlayersPositionData"
                dic["players"] = [cl.GetDataDic() for cl in self.clients]
                pack = Packet()
                pack.header = Headers.data
                pack.flag = Flags.Response.transformData
                pack.add_to_payload(json.dumps(dic))
                for pl in lobby.players:
                    pack.send(pl.socket)
                    
                    
    def createLobby(self,owner:Player,lobbyName:str,max_players:int,password:str=None):
        for lobby in self.lobbies:
            if lobby.name == lobbyName:
                return
        lb = Lobby()
        lb.name = lobbyName
        lb.max_players = max_players
        lb.owner = owner
        if password != None:
            lb.password = password
            lb.password_protected = True
        self.lobbies.append(lb)

    def assign_player_id(self):
        new_id = len(self.clients) + 1
        ids = []
        for pl in self.clients:
            ids.append(pl.id)
        while new_id in ids:
            new_id += 1
        return new_id
    def init_player(self,name,addr) -> Player:
        pl = Player()
        pl.name = name
        pl.id = self.assign_player_id()
        pl.ip = addr[0]
        pl.tcp_port = addr[1]
        self.clients.append(pl)
        return pl

    def add_client_to_lobby(self, player:Player, lobbyName):
        for lb in self.lobbies:
            if lb.name == lobbyName:
                lb.AddPlayer(player)
                return

    def remove_client_from_lobby(self, player:Player):
        lobby = next((item for item in self.lobbies if player in item.players), None)
        lobby.players.remove(player)
        player.lobby = None
        


    def disconnect_client(self, client_socket, player:Player):
        # Remove the client from lobbies and global player list
        lb = player.lobby
        self.remove_client_from_lobby(player)

        i = 0
        if self.clients:
            for cli in self.clients:
                if cli.id == player.id:
                    self.clients.pop(i)
                    break
                i+=1
                
        js = lb.GetInfoJSON()
        json_info = json.dumps(js)
        resp = Packet()
        resp.header = Headers.data
        resp.flag = Flags.Response.lobbyInfo
        resp.add_to_payload(json_info)
        resp.send(client_socket)
        for pl in lb.players:
            resp.send(pl.socket)
        dscP = Packet()
        dscP.header = Headers.disconnecting

        # Close the client socket
        client_socket.close()
    def start(self):
        tcp = threading.Thread(target=self.tcp_recv)
        tcp.start()
        
    def tcp_recv(self):
        print("Server is listening for connections...")
        try:
            while True:
                client_socket, addr = self.server_socket.accept()
                client_socket.settimeout(10)
                client_thread = threading.Thread(target=self.handle_client, args=(client_socket, addr))
                client_thread.start()
        except KeyboardInterrupt:
            print("Server shutting down.")
        finally:
            self.server_socket.close()




# Instantiate and start the server
game_server = GameServer('0.0.0.0')
game_server.start()