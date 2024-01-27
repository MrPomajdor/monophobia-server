from io import BytesIO
import struct
from modules.clients import Flags
from modules.formats import DataFormats
from the_best import PacketParser


class Packet:
    def __init__(self):
        self.header = b'\x00\x00'
        self.flag = Flags.none
        self.payload = b''

    def digest_data(self, data):
        with BytesIO(data) as stream:
            # Read the header (2 bytes)
            self.header = stream.read(2)

            # Read the flag (1 byte)
            self.flag = stream.read(1)

            # Read the payload (the rest of the bytes)
            self.payload = stream.read()

    def send(self, client_socket):
        buf = PacketParser.assemble_message(self.header, self.flag, self.payload)
        try:
            client_socket.sendall(buf)
        except:
            print("Failed to send packet!")

    def add_to_payload(self, value):
        if isinstance(value, float):
            self.payload += struct.pack('!f', value)
        elif isinstance(value, str):
            value_bytes = value.encode('utf-8')
            self.payload += struct.pack('!I',len(value_bytes)) + value_bytes
        elif isinstance(value, int):
            self.payload += struct.pack('!I', value)
        elif isinstance(value, bool):
            self.payload += struct.pack('!?', value)
    def get_from_payload(self,formats:list) -> tuple:
        _pay = self.payload
        result = []
        try:
            for format in formats:
                if format == DataFormats.formats_dict['string']:
                    l = int.from_bytes(_pay[:2],"big")
                    data = struct.unpack(f'!{l}s',_pay[2:][:l:])[0]
                    result.append(data)
                    _pay = _pay[l+1:]
                else:
                    data = struct.unpack('!'+DataFormats.formats_dict[format],_pay[1:][:DataFormats.formats_len_dict[format]:])[0]
                    _pay = _pay[DataFormats.formats_len_dict[format]:]
                    result.append(data)
        except:
            print("Invalid packet payload format")
            return ()
        if len(formats) > 1:
            return tuple(result)
        return result[0]