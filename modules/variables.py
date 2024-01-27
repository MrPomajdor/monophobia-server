class Position:
    def __init__(self,x,y,z):
        self.x=x
        self.y=x
        self.z=x

class Rotation:
    def __init__(self,x,y,z):
        self.x=x
        self.y=x
        self.z=x

class Movement:
    def __init__(self,x,y,z):
        self.x=x
        self.y=x
        self.z=x

class Transform:
    def __init__(self):
        self.position = Position()
        self.position = Rotation()
        self.position = Movement()

