from io import BytesIO
from hashlib import sha256
import math
import struct


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
        if data.startswith(b'\x12\xFF\x34\xFF'):
            with BytesIO(data) as stream:
                stream.seek(4)
                num_fragments = struct.unpack('I',stream.read(4))[0]
                total_len = struct.unpack('I',stream.read(4))[0]
                hash = stream.read(64)
                self.memory[hash] = {"total_len":total_len,"total_fragments":num_fragments,"chunks":[]}
        elif data.startswith(b'\xFF\x99\xFF\x99'):
            with BytesIO(data) as stream:
                stream.seek(4)
                frag_number = struct.unpack('I',stream.read(4))[0]
                hash = stream.read(64)
                payload = stream.read()
                if hash in self.memory:
                    self.memory[hash]["chunks"].append(payload)
                    if self.memory[hash]["total_fragments"]-1 == frag_number:
                        payload = b''.join(self.memory[hash]["chunks"])
                        del self.memory[hash]
                        return payload
        return 0
    
f = Fragmentator.Fragment(b'ABCDEF'*1024)
d = Defragmentator()

for frag in f:
    b = d.PushData(frag)
    if b:
        print(b)