#includes all server-only classes


import json
import random
from typing import List
from modules.packet_classes import *
class BroadcastTypes:
    transforms = 0
    voice = 1
    playersInLobby = 2
    lobbyList = 3
    lobbyInfo = 4
    LobbyClosing = 5
    LobbyListChanged = 6

class Maps:
    gridmap = "grid0"
    lobby = "lobby0"

class MiscSettings: #TODO: Add more settings
    def __init__(self) -> None:
        self.max_voice_distance = 9999999
        


class Player:
    def __init__(self) -> None:
        self.id = 0
        self.name = "PLAYER_NAME"
        self.ip = None
        self.udp_port = None
        self.tcp_port = None
        self.player_data = PlayerData()
        self.cosmetics: list[str] = []
        self.skin = ""
        self.isHost = False
        self.lobby:Lobby = None
        self.socket = None
        self.handler = None
    def GetDataDic(self,string=False) -> dict:
        if not string:
            return self.player_data.to_dict()
        return json.dumps(self.player_data.to_dict())
        
    

  

class Lobby: 
    def __init__(self,name:str):  
        self.owner = None
        self.name = name
        self.players: List[Player] = []
        self.map = Maps.lobby
        self.mapSeed = 0
        self.max_players = 4
        self.password_protected = False
        self.password = ""
        self.id = 0
        self.started = False
        self.MiscSettings = MiscSettings()
        self.WorldState = WorldState()
    def SetOwnership(self,new_owner):
        if new_owner == None:
            self.owner = random.choice(self.players)
        self.owner = new_owner
    def AddPlayer(self,player:Player):
        if len(self.players) < self.max_players:
            self.players.append(player)
            player.lobby = self
        else:
            print(f"Player '{player.name}' tried to enter full lobby.")
    def GetInfoJSON(self) -> str:
        respDic = {}
        respDic["mapName"] = self.map
        respDic["time"] = 300
        respDic["players"] = []
        for pl in self.players:
            respDic["players"].append({"name":pl.name.decode("UTF-8"),"id":pl.id,"cosmetics":pl.cosmetics,"skin":pl.skin,"isHost":(self.owner == pl.id)})
        return json.dumps(respDic)
        

        