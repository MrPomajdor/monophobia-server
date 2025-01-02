import datetime
import os

class Logging:
    def __init__(self):
        self.save_to_file = False
        self.log_file = "auto"  # Could be replaced with a specific filename
        self.log_level = 0
        self.packet= b'\xFF\xFF\xFF'
    def log(self, message: str, level: int=0):
        msg = f"[{datetime.datetime.now().strftime('%H:%M:%S')}][L{level}] {message}"
        if level <= self.log_level:
            print(msg)
        if self.save_to_file:
            if self.log_file == "auto":
                # Generate a log file name based on the current date
                self.log_file = f"log_{datetime.datetime.now().strftime('%Y-%m-%d-%H%M%S')}.txt"
            if not os.path.isdir("logs"):
                os.mkdir("logs")
            with open("logs/"+self.log_file, 'a') as file:
                file.write(msg + "\n")
    def logPacket(self, packet):
        msg = f"[{packet.header}][{packet.flag}]"
        if packet.header+packet.flag==self.packet:
            print(msg)
            if self.save_to_file:
                if self.log_file == "auto":
                    # Generate a log file name based on the current date
                    self.log_file = f"log_{datetime.datetime.now().strftime('%Y-%m-%d-%H%M%S')}.txt"
                if not os.path.isdir("logs"):
                    os.mkdir("logs")
                with open("logs/"+self.log_file, 'a') as file:
                    file.write(msg + "\n")
mainLogger = Logging()