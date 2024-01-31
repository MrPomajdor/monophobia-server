import json
from typing import List
from modules.packet_classes import *
class BroadcastTypes:
    transforms = 0
    voice = 1

class Maps:
    gridmap = "grid0"

class Player:
    def __init__(self) -> None:
        self.id = 0
        self.name = "PLAYER_NAME"
        self.ip = None
        self.udp_port = None
        self.tcp_port = None
        self.player_data = PlayerData()
        self.cosmetics = []
        self.skin = ""
        self.isHost = False
        self.lobby:Lobby = None
        self.socket = None
    def GetDataDic(self,s=False) -> dict:
        if s:
            return ClassToJson(self.player_data)
        return json.dumps(ClassToJson(self.player_data))
        
    


class Lobby:
    def __init__(self,name:str) -> None:
        self.owner = None
        self.name = name
        self.players: List[Player] = []
        self.map = Maps.gridmap
        self.mapSeed = 0
        self.max_players = 4
        self.password_protected = False
        self.password = ""
        self.id = 0
    def SetOwnership(self,new_owner):
        self.owner = new_owner
    def AddPlayer(self,player:Player):
        if len(self.players) < self.max_players:
            self.players.append(player)
        else:
            print(f"Player '{player.name}' tried to enter full lobby.")
    def GetInfoJSON(self) -> str:
        respDic = {}
        respDic["mapName"] = self.map
        respDic["time"] = 300
        respDic["players"] = []
        for pl in self.players:
            respDic["players"].append({"name":pl.name.decode("UTF-8"),"id":pl.id,"cosmetics":pl.cosmetics,"skin":pl.skin,"isHost":pl.isHost})
        return json.dumps(respDic)
        