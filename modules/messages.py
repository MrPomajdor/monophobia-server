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
        itemList = b'\x1A'
    
    class Post:
        joinLobby = b'\x08'
        createLobby = b'\x11'
        updateLobbyInfo = b'\x10'

        playerTransformData = b'\xA0'
        lobbyInfo = b'\xA1'
        worldState = b'\xA2'

        itemPickup = b'\xA5'
        itemDrop = b'\xA6'
        inventorySwitch = b'\xA7'
        startMap = b'\xA8'
        itemIntInf = b'\xA4'
        voice = b'\xAC'

        interactableMessage  = b'\xAD'
        codeInteractionMessage  = b'\xAE'

        transform = b'\xAF'
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

        itemIntInf = b'\xC5'
        itemList = b'\xA1'
        itemPickup = b'\xC6'
        itemDrop = b'\xC7'
        inventorySwitch = b'\xC8'
        startMap = b'\xC9'

        interactableMessage  = b'\x0D'
        codeInteractionMessage  = b'\x0E'

        playerData = b'\xC4'  # warning: contents explosive
        voice = b'\x0C'

        transform = b'\x0F'

        fragment_received = b'\xDF'