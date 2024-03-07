class Headers:
    ack = b'\x00\x00'
    echo = b'\x01\x00'
    hello = b'\x02\x00'
    data = b'\x03\x00'
    disconnecting = b'\x04\x00'
    rejected = b'\xFF\xFF'
    imHere = b'\xAA\xAA'

class Flags:
    none = b'\x00'
    
    class Request:
        playerList = b'\x04'
        lobbyList = b'\x07'
        worldState = b'\xD0'
    
    class Post:
        joinLobby = b'\x08'
        createLobby = b'\x11'
        updateLobbyInfo = b'\x10'
        playerTransformData = b'\xA0'
        lobbyInfo = b'\xA1'
        worldState = b'\xA2'
        itemPos = b'\xA3'
        voice = b'\xAC'

    class Response:
        idAssign = b'\x03'
        playerList = b'\x05'
        lobbyList = b'\x06'
        error = b'\xFF'
        closing_con = b'\xF0'
        lobbyListChanged = b'\x0A'
        lobbyClosing = b'\xF1'
        transformData = b'\xB0'
        lobbyInfo = b'\x09'
        worldState = b'\xC2'
        itemPos = b'\xC3'
        voice = b'\x0C'

