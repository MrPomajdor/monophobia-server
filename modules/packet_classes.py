import json

class Vector3:
    def __init__(self,x=0,y=0,z=0):
        self.x = x
        self.y = y
        self.z = z 

class Inputs:
    def __init__(self):
        self.isSprinting = False
        self.isMoving = False
        self.isCrouching = False

class Transforms:
    def __init__(self):
        self.position = Vector3()
        self.rotation = Vector3()
        self.target_velocity = Vector3()
        self.real_velocity = Vector3()

class PlayerData:
    def __init__(self):
        self.type = "PlayerPositionData"
        self.transforms = Transforms()
        self.inputs = Inputs()
        self.id = 0

class PlayersDataPacket:
    def __init__(self):
        self.type = "OtherPlayersPositionData"
        self.players = []

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
        p = data.get('position')
        r = data.get('rotation')
        tv = data.get('target_velocity')
        rv = data.get('real_velocity')
        obj.position = p
        obj.real_velocity = rv
        obj.target_velocity = tv
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
        obj.players = [JsonToClass(json.dumps(player), PlayerData) for player in data.get('players', [])]
        return obj
    else:
        raise ValueError(f"Unsupported class: {cls}")