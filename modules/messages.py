class Headers:
    ack = b'\x00\x00'
    echo = b'\x01\x00'
    hello = b'\x02\x00'
    data = b'\x03\x00'
    disconnecting = b'\x04\x00'
    joinRoom = b'\x05\x00'
    createLobby = b'\x06\x00'
    rejected = b'\xFF\xFF'

class Flags:
    none = b'\x00'
    class Request:
        playerList = b'\x04'
        lobbyList = b'\x07'
    class Post:
        joinLobby = b'\x08'
        leaveLobby = b'\x08'
        createLobby = b'\x11'
        updateLobbyInfo = b'\x10'

        transformData = b'\xA0'
        lobbyInfo = b'\xA1'
    class Response:
        transformData = b'\x02'
        idAssign = b'\x03'
        playerList = b'\x05'
        lobbyList = b'\x06'
        lobbyInfo = b'\x09'
        error = b'\xFF'
        closing_con = b'\xF0'

        transformData = b'\xB0'
