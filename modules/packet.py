from io import BytesIO
import json
import socket
import struct
from modules.formats import DataFormats
from modules.messages import *
from modules.logging import *
import math
from hashlib import sha256
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
    def assemble_message(header=Headers.data, flag=Flags.none, payload=b''):
        #try:
            return header + flag + struct.pack('I',len(payload)+7)+ payload
        #except:
        #    print(header,type(header))
        #    print(flag,type(flag))
        #    print(payload,type(payload))


class FragmentResult:
    def __init__(self):
        self.hash = ""
        self.isDone = False
        self.payload = b''

class Fragmentator:
    FInitHeader = b'\x12\xFF\x34\xFF'
    FCHHeader = b'\xFF\x99\xFF\x99'
    @staticmethod
    def Fragment(data:bytes):
        if len(data) < 1536:
            return

        chunkNum = math.ceil(len(data) / 512)
        chunkLen = math.floor(len(data) / chunkNum)
        hash = sha256(data).hexdigest().encode("UTF-8")
        chunks = []

        chunks.append(Fragmentator.FInitHeader+struct.pack('I',chunkNum)+struct.pack('I',len(data))+hash)

        for chunkNumber in range(chunkNum):
            curr_chunk = data[(chunkLen*chunkNumber):(chunkLen*(chunkNumber+1))]
            chunks.append(Fragmentator.FCHHeader+struct.pack('I',chunkNumber)+hash+curr_chunk)
        return chunks



class Defragmentator:
    # Fragment Init:
    # 12 FF 34 FF (int - number of fragments) (int total payload len) (payload hash)
    #
    # Fragment Packet:
    # FF 99 FF 99 (int - fragment number) (payload hash) (payload)
    # For now it's only for TCP bc it's a stream and with udp i would need to know what packets are from whom?? Idk what I am thinking anymore
    #
    def __init__(self):
        #
        #             {str:{"total_len":int,"total_fragments":int,"chunks":list[str]}}
        self.memory = {}
        
    def PushData(self,data):
        res = FragmentResult()
        if data.startswith(b'\x12\xFF\x34\xFF'):
            with BytesIO(data) as stream:
                stream.seek(4)
                num_fragments = struct.unpack('I',stream.read(4))[0]
                total_len = struct.unpack('I',stream.read(4))[0]
                hash = stream.read(64)
                self.memory[hash] = {"total_len":total_len,"total_fragments":num_fragments,"chunks":[]}
                res.hash = hash
        elif data.startswith(b'\xFF\x99\xFF\x99'):
            with BytesIO(data) as stream:
                stream.seek(4)
                frag_number = struct.unpack('I',stream.read(4))[0]
                hash = stream.read(64)
                mainLogger.log(f"Received hh {hash}")
                payload = stream.read()
                res.hash = hash
                if hash in self.memory:
                    self.memory[hash]["chunks"].append(payload)
                    if self.memory[hash]["total_fragments"]-1 == frag_number:
                        payload = b''.join(self.memory[hash]["chunks"])
                        del self.memory[hash]
                        res.hash = hash
                        res.isDone = True
                        res.payload = payload
                        return res
                    #mainLogger.log(f"Received packet fragment is not last one! {hash}")
                #else:
                    #mainLogger.log(f"Received packet fragment is not in memory! hash : {hash}")
        return res


class Packet:
    def __init__(self):
        self.header = b'\x00\x00'
        self.flag = Flags.none
        self.payload = b''
        self.port = 0
        self.ip = "0.0.0.0"
    def digest_data(self, data:bytes) -> bool:
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

                self.msg_len = stream.read(4)

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
                    if 0:#  len(buf) > 512*3:
                        mainLogger.log("Sending fragmented packets!")
                        frags = Fragmentator.Fragment(buf)
                        for frag in frags:
                            client_socket.sendall(frag)
                    else:
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
                except Exception as e:
                    print(f"Failed to send packet! {str(e)}")
                    return 0
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
        else:
            mainLogger.log("Unable to add payload to packet due to unknown value type.")

    def get_from_payload(self,formats:list):
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
