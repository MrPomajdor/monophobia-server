from io import BytesIO
import json
import socket
import struct
from modules.formats import DataFormats
from modules.messages import *
from modules.logging import *


def is_socket_connected(sock:socket):
    try:
        match sock.getsockopt(socket.SOL_SOCKET, socket.SO_TYPE):
            case socket.SOCK_STREAM:
                # Sending 0 bytes does not actually send data but will check for a closed socket
                sock.sendall(b'')
                return True
            case socket.SOCK_DGRAM:
                return True
    except:
        return False


class PacketParser:
    @staticmethod
    def assemble_message(header, flag, payload):
        return header + flag + payload
    
class Packet:
    def __init__(self):
        self.header = b'\x00\x00'
        self.flag = Flags.none
        self.payload = b''
        self.port = 0
        self.ip = "0.0.0.0"
    def digest_data(self, data) -> bool:
        if len(data)<3:
            print("Packet length too short! Discarding")
            return False
        try:
            mainLogger.log(f"Digesting packet data:\n\n{data}\n\n",10)
            with BytesIO(data) as stream:
                # Read the header (2 bytes)
                self.header = stream.read(2)

                # Read the flag (1 byte)
                self.flag = stream.read(1)

                # Read the payload (the rest of the bytes)
                self.payload = stream.read()
        except:
            return False
        finally:
            return True

    def send(self, client_socket:socket,addr:tuple=None) -> int:
        if not is_socket_connected(client_socket):
            return 0
        match client_socket.getsockopt(socket.SOL_SOCKET, socket.SO_TYPE):
            case socket.SOCK_STREAM:
                buf = PacketParser.assemble_message(self.header, self.flag, self.payload)
                try:
                    mainLogger.log(f"Sending packet via TCP:\n\n{buf}\n\n",10)
                    client_socket.sendall(buf)
                    return len(buf)
                except:
                    print("Failed to send packet!")
                    return 0
            case socket.SOCK_DGRAM:
                buf = PacketParser.assemble_message(self.header, self.flag, self.payload)
                try:
                    mainLogger.log(f"Sending packet via UDP:\n\n{buf}\n\n",10)
                    client_socket.sendto(buf,addr)
                    return len(buf)
                except:
                    print("Failed to send packet!")
                    return 0

    def add_to_payload(self, value):
        if isinstance(value, float):
            self.payload += struct.pack('f', value)
        elif isinstance(value, str):
            value_bytes = value.encode('utf-8')
            self.payload += struct.pack('I',len(value_bytes)) + value_bytes
        elif isinstance(value, bool):
            self.payload += struct.pack('?', value)
        elif isinstance(value, int):
            self.payload += struct.pack('I', value)
        elif isinstance(value, bytes):
            self.payload += value

    def get_from_payload(self,formats:list) -> tuple:
        _pay = self.payload
        result = []
        try:
            if formats == ['json']:
                s = self.payload.decode("UTF-8")
                return json.loads(s)
            else:
                for format in formats:
                    if format == 'string':
                        l = struct.unpack('i',_pay[:4])[0]
                        data = _pay[4:][:l]
                        result.append(data)
                        _pay = _pay[4+l:]
                    else:
                        data = struct.unpack(DataFormats.formats_dict[format],_pay[:DataFormats.formats_len_dict[format]])[0]
                        _pay = _pay[DataFormats.formats_len_dict[format]:]
                        result.append(data)
                
        except Exception as e:
            print(f"Invalid packet payload format {e}")
            return ()
        if len(formats) > 1:
            return tuple(result)
        return result[0]
