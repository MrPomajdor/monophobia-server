from modules.variables import *

class Flags:
    connected = 0


class Client:
    def __init__(self,id):
        self.id = id
        self.transform = Transform()
        self.flags = []
        pass