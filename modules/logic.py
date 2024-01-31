from modules.messages import *
from modules.packet import *
from modules.blocks import *

class Logic:
    def handle_logic(serverClass, packet,player_class:Player,client_socket):
        match packet.header:
            case Headers.data:
                match packet.flag:
                    case Flags.Post.joinLobby: #{"mapName":"grid0","time":300,"players":[{"name":"debil","id":0,"cosmetics":[],"skin":"male01","isHost":false}]}
                        lobby_id, password = packet.get_from_payload(['int','string'])
                        lobby = next((item for item in serverClass.lobbies if item.id == lobby_id), None)
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
                                
                                
                                lobby.AddPlayer(player_class)
                                #Everything ok add player to the lobby and send confirmation (lobby info)
                                json_info = lobby.GetInfoJSON()
                                resp = Packet()
                                resp.header = Headers.data
                                resp.flag = Flags.Response.lobbyInfo
                                resp.add_to_payload(json_info)
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
                        response_packet.add_to_payload(len(serverClass.lobbies))
                        for lobby in serverClass.lobbies:
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
                        serverClass.createLobby(player_class.id,lobby_name,)
                        serverClass.add_client_to_lobby(player_class.id, lobby_name)
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
                                player_class.player_data = JsonToClass(js,PlayerData)
                                serverClass.broadcast(player_class.lobby,BroadcastTypes.transforms)
                        else:
                            print(f"ID doesnt match id (local) {player_class.id} id (remote) {id}")
            case Headers.echo:
                #i mean, okay? What do you want me to fucking do with that information. Like I could send you ack i guess?
                xd = Packet()
                xd.header = Headers.ack
                xd.send(client_socket)