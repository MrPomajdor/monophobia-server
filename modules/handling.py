from modules.blocks import *
from modules.packet import *
from modules.messages import *


class Handling:
    def __init__(self) -> None:
        self.player_class = None
        self.client_socket = None
        self.server_class = None
        pass
    def parse_packet(self, packet):
        match packet.header:
            case Headers.data:
                match packet.flag:
                    case Flags.Post.joinLobby: #{"mapName":"grid0","time":300,"players":[{"name":"debil","id":0,"cosmetics":[],"skin":"male01","isHost":false}]}
                        lobby_id, password = packet.get_from_payload(['int','string'])
                        lobby = next((item for item in self.server_class.lobbies if item.id == lobby_id), None)
                        if lobby != None:
                            if lobby.id == lobby_id:
                                if len(lobby.players) >= lobby.max_players:
                                    resp = Packet()
                                    resp.header = Headers.rejected
                                    resp.flag = Flags.Response.error
                                    resp.add_to_payload("LOBBY_FULL")
                                    resp.send(self.client_socket)
                                    return
                                if lobby.password_protected and lobby.password != password: #check for password
                                    resp = Packet()
                                    resp.header = Headers.rejected
                                    resp.flag = Flags.Response.error
                                    resp.add_to_payload("BAD_PASSWORD")
                                    resp.send(self.client_socket)
                                    return
                                
                                
                                lobby.AddPlayer(self.player_class)
                                #Everything ok add player to the lobby and send confirmation (lobby info)
                                json_info = lobby.GetInfoJSON()
                                resp = Packet()
                                resp.header = Headers.data
                                resp.flag = Flags.Response.lobbyInfo
                                resp.add_to_payload(json_info)
                                self.player_class.lobby = lobby
                                resp.send(self.client_socket)
                        else:
                            resp = Packet()
                            resp.header = Headers.rejected
                            resp.flag = Flags.Response.error
                            resp.add_to_payload("LOBBY_NOT_FOUND")
                            resp.send(self.client_socket)
                    case Flags.Request.lobbyList:
                        #lobby_data = self.generate_lobby_data()
                        response_packet = Packet()
                        response_packet.header = Headers.data
                        response_packet.flag = Flags.Response.lobbyList
                        response_packet.add_to_payload(len(self.server_class.lobbies))
                        for lobby in self.server_class.lobbies:
                            response_packet.add_to_payload(lobby.id)
                            response_packet.add_to_payload(lobby.name)
                            response_packet.add_to_payload(lobby.password_protected)
                            response_packet.add_to_payload(len(lobby.players))
                            response_packet.add_to_payload(lobby.max_players)
                        response_packet.send(self.client_socket)
                    case Flags.Post.createLobby:
                        payload_tuple = packet.get_from_payload(['string','string','int'])
                        if not payload_tuple:
                            return
                        lobby_name,password,max_players = payload_tuple
                        self.serverClass.createLobby(self.player_class.id,lobby_name,)
                        self.serverClass.add_client_to_lobby(self.player_class.id, lobby_name)
                    case Flags.Post.transformData:
                        try:
                            js = json.loads(packet.get_from_payload(['string']))
                        except:
                            print(f"[!] Recieved corrupted json data from {self.player_class.id}!")
                            resp = Packet()
                            resp.header = Headers.rejected
                            resp.flag = Flags.Response.closing_con
                            resp.add_to_payload("JSON_CORRUPTED")
                            resp.send(self.client_socket)
                            return
                        id = js.get("id")
                        if self.player_class.id == id:  #check if id matches
                                #TODO: make the alsgorythm for checking if the client is cheating, eg. check the distance between positions and detect when it jumps then teleport him back
                                self.player_class.player_data = JsonToClass(js,PlayerData)
                                self.broadcast(self.player_class.lobby,BroadcastTypes.transforms)
                        else:
                            print(f"ID doesnt match id (local) {self.player_class.id} id (remote) {id}")
                    case _:
                        print(f"Invialid flag {packet.flag}")

            case Headers.echo:
                #i mean, okay? What do you want me to fucking do with that information. Like I could send you ack i guess?
                xd = Packet()
                xd.header = Headers.ack
                xd.send(self.client_socket)
            case Headers.ack:
                pass
            case _:
                print(f"Invialid header {packet.header}")
    def broadcast(self,lobby:Lobby,what:BroadcastTypes,data=None):
        match what:
            case BroadcastTypes.transforms:
                dic = PlayersDataPacket()
                dic.players = [cl.GetDataDic() for cl in self.server_class.clients]
                pack = Packet()
                pack.header = Headers.data
                pack.flag = Flags.Response.transformData
                pack.add_to_payload(ClassToJson(dic))
                for pl in lobby.players:
                    pack.send(pl.socket)
            case BroadcastTypes.voice:
                if not data:
                    return
                
                p = Packet()
                pack.header = Headers.data
                pack.flag = Flags.Response.voice
                pack.add_to_payload(data)
                for pl in lobby.players:
                    pack.send()
                    
                    
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
        self.lobbieself.append(lb)

    def assign_player_id(self):
        new_id = len(self.server_class.clients) + 1
        idsa = []
        for pl in self.server_class.clients:
            idsa.append(pl.id)
        while new_id in idsa:
            new_id += 1
        return new_id
    def init_player(self,name,addr) -> Player:
        pl = Player()
        pl.name = name
        pl.id = self.assign_player_id()
        pl.ip = addr[0]
        pl.tcp_port = addr[1]
        self.server_class.clients.append(pl)
        return pl

    def add_client_to_lobby(self, player:Player, lobbyName):
        for lb in self.lobbies:
            if lb.name == lobbyName:
                lb.AddPlayer(player)
                return
            json_info = lb.GetInfoJSON()
            resp = Packet()
            resp.header = Headers.data
            resp.flag = Flags.Response.lobbyInfo
            resp.add_to_payload(json_info)
            for pl in lb.players:
                resp.send(pl.socket)

    def remove_client_from_lobby(self, player:Player):
        lobby = player.lobby
        if not lobby:
            return
        lobby.players.remove(player)
        player.lobby = None
    def disconnect_client(self, client_socket, player:Player):
        # Remove the client from lobbies and global player list
        if not player:
            client_socket.close()
            return
        lb = player.lobby
        if lb:
            self.remove_client_from_lobby(player)
            self.broadcast(lb,BroadcastTypes.transforms)
        if player:
            i = 0
            if self.server_class.clients:
                for cli in self.server_class.clients:
                    if cli.id == player.id:
                        self.server_class.clients.pop(i)
                        break
                    i+=1
        
        
        # Close the client socket
        client_socket.close()

