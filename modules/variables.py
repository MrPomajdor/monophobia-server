class Position:
    def __init__(self,x,y,z):
        self.x=x
        self.y=y
        self.z=z

class Rotation:
    def __init__(self,x,y,z):
        self.x=x
        self.y=y
        self.z=z

class Movement:
    def __init__(self,x,y,z):
        self.x=x
        self.y=y
        self.z=z

class Transform:
    def __init__(self):
        self.position = Position()
        self.rotation = Rotation()
        self.movement = Movement()




