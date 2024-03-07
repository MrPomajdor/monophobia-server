from math import sqrt
from modules.blocks import *
from modules.packet import *
from modules.messages import *
from modules.packet_classes import Vector3
from modules.logging import *
def ReturnError(socket:socket,str:str):
    resp = Packet()
    resp.header = Headers.rejected
    resp.flag = Flags.Response.error
    resp.add_to_payload(str)
    resp.send(socket)

def Distance(a:Vector3, b:Vector3):
    return sqrt((b.x - a.x)**2 + (b.y - a.y)**2 + (b.z - a.z)**2)
class Handling:
    def __init__(self) -> None:
        self.player_class:Player = None
        self.client_socket:socket = None
        self.server_class = None
        pass
    def parse_packet(self, packet:Packet):
        mainLogger.log(f"Parsing packet: {packet.header}:{packet.flag} for player player {self.player_class.id}/{self.player_class.name}",6)
        match packet.header:
            case Headers.data:
                match packet.flag:
                    case Flags.Post.createLobby: #TODO: add a check if player has already a lobby, he cant create one. Please do it please please please
                        #name, max players,bool password,string password
                        mainLogger.log(f"Recieved lobby creation packet...",4)
                        new_name, new_max_players, isProtected, new_password = packet.get_from_payload(['string','int','bool','string'])
                        if next((item for item in self.server_class.lobbies if item.name == new_name), None):
                            ReturnError(self.client_socket,"LOBBY_EXISTS")
                            mainLogger.log(f"Player {self.player_class.name} tried to create a lobby with a name that already exists",4)
                            return
                        if new_max_players < 2:
                            ReturnError(self.client_socket,"LOBBY_MIN_PLAYERS_TWO")
                            mainLogger.log(f"Player {self.player_class.name} tried to create a lobby with less than 2 max players",4)
                            return
                        if next((item for item in self.server_class.lobbies if item.owner == self.player_class), None):
                            ReturnError(self.client_socket,"PLAYER_LOBBY_EXISTS")
                            mainLogger.log(f"Player {self.player_class.name} tried to create a lobby, even tho he has one already. Grumpy fucker...",4)
                            return
                         
                        new_lobby = Lobby(new_name)
                        if "shithead" in new_name.decode("UTF-8"):
                            new_lobby.map = "grid0"
                            mainLogger.log(f"Creating debug lobby")
                        new_lobby.SetOwnership(self.player_class.id)
                        new_lobby.AddPlayer(self.player_class)
                        if isProtected:
                            new_lobby.password = new_password
                            new_lobby.password_protected = True
                        self.server_class.lobbies.append(new_lobby)
                        resp = Packet()
                        resp.header = Headers.data
                        resp.flag = Flags.Response.lobbyInfo
                        resp.add_to_payload(new_lobby.GetInfoJSON())
                        resp.send(self.client_socket)
                        mainLogger.log(f"Player {self.player_class.name} created a lobby: {new_name}/{new_max_players}/{isProtected}({new_password})",4)
                    case Flags.Post.joinLobby: #{"mapName":"grid0","time":300,"players":[{"name":"debil","id":0,"cosmetics":[],"skin":"male01","isHost":false}]}
                        if self.player_class.lobby != None:
                            ReturnError(self.client_socket,"ALREADY_IN_LOBBY")
                            mainLogger.log(f"Player {self.player_class.name} tried to enter a lobby although he was in a lobby already",3)
                            return
                        lobby_id, password = packet.get_from_payload(['int','string'])
                        lobby:Lobby = None
                        lobby = next((item for item in self.server_class.lobbies if item.id == lobby_id), None)
                        if lobby != None:
                            if lobby.id == lobby_id:
                                if len(lobby.players) >= lobby.max_players:
                                    ReturnError(self.client_socket,"LOBBY_FULL")
                                    mainLogger.log(f"Player {self.player_class.name} tried to enter a full lobby",3)
                                    return
                                if lobby.password_protected and lobby.password != password: #check for password
                                    mainLogger.log(f"Wrong password Mr. {self.player_class.name}!",3)
                                    return
                                
                                
                                lobby.AddPlayer(self.player_class)
                                #Everything ok add player to the lobby and send confirmation (lobby info)
                                self.broadcast(lobby,BroadcastTypes.lobbyInfo)
                        else:
                            ReturnError(self.client_socket,"LOBBY_NOT_FOUND")
                            mainLogger.log(f"Player {self.player_class.name} tried to enter a non-existent lobby {lobby_id}",3)
                    case Flags.Request.lobbyList:
                        #lobby_data = self.generate_lobby_data()
                        response_packet = Packet()
                        response_packet.header = Headers.data
                        response_packet.flag = Flags.Response.lobbyList
                        response_packet.add_to_payload(len(self.server_class.lobbies))
                        for lobby in self.server_class.lobbies:
                            response_packet.add_to_payload(lobby.id)
                            response_packet.add_to_payload(lobby.name.decode("UTF-8"))
                            response_packet.add_to_payload(lobby.password_protected)
                            response_packet.add_to_payload(len(lobby.players))
                            response_packet.add_to_payload(lobby.max_players)
                        response_packet.send(self.client_socket)
                    case Flags.Post.transformData: #UDP
                        try:
                            js = json.loads(packet.get_from_payload(['string']))
                        except:
                            mainLogger.log(f"Recieved corrupted json data from {self.player_class.id}!",3)
                            ReturnError(self.client_socket,"JSON_CORRUPTED")
                            return
                        id = js.get("id")
                        if self.player_class.id == id:  #check if id matches
                                #TODO: make the alsgorythm for checking if the client is cheating, eg. check the distance between positions and detect when it jumps then teleport him back
                                self.player_class.player_data = JsonToClass(js,PlayerData)
                                self.broadcast(self.player_class.lobby,BroadcastTypes.transforms,sock=self.server_class.udp_socket)
                        else:
                            mainLogger.log(f"ID doesnt match id (local) {self.player_class.id} id (remote) {id}\n{js}\n",2)
                    case Flags.Post.voice: #UDP! TODO: OPTIMIZE!!! and maybe add something like when 2 players send voice data then it packs both of their packets into one and broadcasts? Think about it bc i think thats not a good idea tbh
                        if not self.player_class.lobby:
                            return
                        vo_data = packet.payload
                        pac = Packet()
                        pac.header = Headers.data
                        pac.flag = Flags.Response.voice
                        pac.add_to_payload(self.player_class.id)
                        pac.add_to_payload(len(vo_data))
                        pac.add_to_payload(vo_data)
                        #print(f"Recieved {len(vo_data)} bytes of voice data")
                        for pla in self.player_class.lobby.players:
                            if pla.id != self.player_class.id:
                                if Distance(pla.player_data.transforms.position,pla.player_data.transforms.position) < self.player_class.lobby.MiscSettings.max_voice_distance: #TODO: Check the actual distance and set it as a variable in lobby settings
                                    pac.send(self.server_class.udp_socket,(pla.ip,pla.udp_port))
                    case _: 
                        mainLogger.log(f"Invialid flag {packet.flag} for player player {self.player_class.id}/{self.player_class.name}",3)
                        ReturnError(self.client_socket,"INVALID_FLAG")

            case Headers.echo:
                #i mean, okay? What do you want me to fucking do with that information. Like I could send you ack i guess?
                xd = Packet()
                xd.header = Headers.ack
                xd.send(self.client_socket)
            case Headers.ack:
                pass
            case _:
                mainLogger.log(f"Invialid heaqder {packet.header} for player player {self.player_class.id}/{self.player_class.name}",3)
                ReturnError(self.client_socket,"INVALID_HEADER")
    def broadcast(self,lobby:Lobby,what:BroadcastTypes,data=None,sock:socket=None):
        match what:
            case BroadcastTypes.transforms:
                if (not lobby) or (not lobby.players):
                    return
                dic = PlayersDataPacket()
                dic.players = [cl.GetDataDic() for cl in self.server_class.clients]
                pack = Packet()
                pack.header = Headers.data
                pack.flag = Flags.Response.transformData
                pack.add_to_payload(ClassToJson(dic))
                for pl in lobby.players:
                    pack.send(sock,(pl.ip,pl.udp_port))
            case BroadcastTypes.voice:
                if not data:
                    return
                
                p = Packet()
                p.header = Headers.data
                p.flag = Flags.Response.voice
                p.add_to_payload(data)
                for pl in lobby.players:
                    p.send()
            case BroadcastTypes.lobbyInfo:
                json_info = lobby.GetInfoJSON()
                resp = Packet()
                resp.header = Headers.data
                resp.flag = Flags.Response.lobbyInfo
                resp.add_to_payload(json_info)
                resp.send(self.client_socket)
                for pl in lobby.players:
                    resp.send(pl.socket)
            case BroadcastTypes.LobbyClosing:
                resp = Packet()
                resp.header = Headers.rejected
                resp.flag = Flags.Response.LobbyClosing
                resp.add_to_payload(data)
                resp.send(self.client_socket)
                for pl in lobby.players:
                    resp.send(pl.socket)
                    
    def createLobby(self,owner:Player,lobbyName:str,max_players:int,password:str=None):
        mainLogger.log(f"Creating lobby {lobbyName}/{max_players}/{password} for {owner.name}",4)
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
        mainLogger.log(f"Player init: name:{pl.name}/id:{pl.id}/addr:{addr}",3)
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
        mainLogger.log(f"Added player {player.id}/{player.name} to lobby {lobbyName}",3)
    def remove_client_from_lobby(self, player:Player):
        lobby = player.lobby
        if not lobby:
            return
        if lobby.owner == player:
            self.broadcast(lobby,BroadcastTypes.LobbyClosing,data="Disconnected by host")
            self.server_class.lobbies.remove(lobby)
            mainLogger.log(f"Removed lobby {lobby.name} (owner left)",3)

        lobby.players.remove(player)
        if len(lobby.players) < 1:
            self.server_class.lobbies.remove(lobby)
            mainLogger.log(f"Removed lobby {lobby.name} (last player left - how?)",3)
        player.lobby = None
        mainLogger.log(f"Removed player {player.id}/{player.name} from lobby",3)
    def disconnect_client(self, client_socket, player:Player):
        # Remove the client from lobbies and global player list
        mainLogger.log(f"Player {player.id}/{player.name} disconnecting...",3)
        if not player:
            mainLogger.log(f"No player class present (just closing connection)",3)
            client_socket.close()
            return
        lb = player.lobby
        if lb:
            self.remove_client_from_lobby(player)
            self.broadcast(lb,BroadcastTypes.transforms) #TODO: why did i decide to type that here?
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

