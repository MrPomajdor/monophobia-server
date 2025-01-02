#includes all server/client classes

import json

class Vector3:
    def __init__(self,x=0,y=0,z=0):
        self.x = x
        self.y = y
        self.z = z 
    def __str__(self) -> str:
        return f"Vector3({self.x}, {self.y}, {self.z})"
    def to_dict(self):
        return {"x": self.x, "y": self.y, "z": self.z}
class InteractionMessage:
    def __init__(self):
        self.PlayerID = 0
        self.InteractableID = 0
        self.InteractionMessage = ""
    def to_dict(self):
        return {"PlayerID":self.PlayerID,"InteractableID":self.InteractableID,"InteractionMessage":self.InteractionMessage}
class Inputs:
    def __init__(self):
        self.isSprinting = False
        self.isMoving = False
        self.isCrouching = False
        self.MoveDiredction = Vector3()
    def to_dict(self):
        return {"isSprinting": self.isSprinting, "isMoving": self.isMoving, "isCrouching": self.isCrouching,"MoveDirection":self.MoveDiredction.to_dict()}
    
class Transforms:
    def __init__(self):
        self.position = Vector3()
        self.rotation = Vector3()
        #self.target_velocity = Vector3()
        self.real_velocity = Vector3()
        self.real_angular_velocity = Vector3()
    def to_dict(self):
        return {
            "position": self.position.to_dict(),
            "rotation": self.rotation.to_dict(),
            "real_angular_velocity": self.real_angular_velocity.to_dict(),
            "real_velocity": self.real_velocity.to_dict(),
        }
class PlayerData:
    def __init__(self):
        self.type = "PlayerPositionData"
        self.transforms = Transforms()
        self.inputs = Inputs()
        self.id = 0
    def to_dict(self):
        return {
            "type": self.type,
            "transforms": self.transforms.to_dict(),
            "inputs": self.inputs.to_dict(),
            "id": self.id,
        }


class Item:
    def __init__(self) -> None:
        self.id = 0
        self.name = "air"
        self.activated = False
        self.transforms = Transforms()
    def to_dict(self):
        return {
            "id" : self.id,
            "name" : self.name,
            "activated" : self.activated,
            "transforms" : self.transforms.to_dict()
        }

class InteractionInfo:
        def __init__(self) -> None:
            self.itemID = 0
            self.activated = False
        def to_dict(self):
            return {
                "itemID":self.itemID,
                "activated":self.activated
            }



class WorldState:
    def __init__(self):
        self.items = []
        self.itemMap = {}
    def UpdateItemMap(self):
        self.itemMap = {itm.id: itm for itm in self.items}
    def to_dict(self):
        return {
            "items": [x.to_dict() for x in self.items]
        }


class PlayersDataPacket:
    def __init__(self):
        self.type = "OtherPlayersPositionData"
        self.players = []
    def to_dict(self):
        return {
            "type": self.type,
            "players": [player.GetDataDic() for player in self.players]
        }
def ClassToJson(obj):
    return json.dumps(obj, default=lambda o: o.__dict__)


def JsonToClass(json_str, cls):
    """
    Deserialize a JSON string into an instance of the specified class.

    :param json_str: The JSON string to deserialize.
    :param cls: The class to which the JSON string should be deserialized.
    :return: An instance of cls.
    """
    if type(json_str) == str:
        data = json.loads(json_str)
    else:
        data = json_str
    if cls == Inputs:
        obj = Inputs()
        obj.isCrouching = data.get('isCrouching')
        obj.isSprinting = data.get('isSprinting')
        obj.isMoving = data.get('isMoving')
        return obj
    elif cls == Vector3:
        obj = Vector3(data.get('x',0),data.get('y',0),data.get('z',0))
        return obj
    elif cls == Transforms:
        obj = Transforms()
        p = JsonToClass(json.dumps(data.get('position')),Vector3)
        r = JsonToClass(json.dumps(data.get('rotation')),Vector3)
        tv = JsonToClass(json.dumps(data.get('real_angular_velocity')),Vector3)
        rv = JsonToClass(json.dumps(data.get('real_velocity')),Vector3)
        obj.position = p
        obj.real_velocity = rv
        obj.real_angular_velocity = tv
        obj.rotation = r
        return obj
    elif cls == PlayerData:
        obj = PlayerData()
        obj.transforms = JsonToClass(json.dumps(data.get('transforms', {})), Transforms)
        obj.inputs = JsonToClass(json.dumps(data.get('inputs', {})), Inputs)
        obj.id = data.get('id', 0)
        return obj
    elif cls == PlayersDataPacket:
        obj = PlayersDataPacket()
        obj.players = [ ]
        for player in data.get('players', []):
            xd = JsonToClass(player, PlayerData)
            print(type(xd),xd)
            obj.players.append(xd)
        return obj
    elif cls == WorldState:
        obj = WorldState()
        obj.items = [ ]
        for item in data.get('items', []):
            xd = JsonToClass(item, Item)
            obj.items.append(xd)
        return obj
    elif cls == Item:
        obj = Item()
        obj.id = data.get("id",-1)
        obj.name = data.get("name","air")
        obj.activated = data.get("activated",False)
        obj.transforms = JsonToClass(json.dumps(data.get('transforms', {})), Transforms)
        return obj
    elif cls == InteractionInfo:
        obj = InteractionInfo()
        obj.itemID = data.get("itemID")
        obj.pickedUp = data.get("pickedUp")
        obj.pickedUpPlayerID = data.get("pickedUpPlayerID")
        obj.activated = data.get("activated")
        return obj
    else:
        raise ValueError(f"Unsupported class: {cls}")