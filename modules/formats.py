
class DataFormats:
    formats_dict = {
        'float': 'f',  # 4 bytes, float
        'double': 'd',  # 8 bytes, double
        'char': 'c',  # 1 byte, char
        'byte': 'B',  # 1 byte, unsigned char
        'short': 'h',  # 2 bytes, short
        'ushort': 'H',  # 2 bytes, unsigned short
        'int': 'i',  # 4 bytes, int
        'uint': 'I',  # 4 bytes, unsigned int
        'long': 'q',  # 8 bytes, long long
        'ulong': 'Q',  # 8 bytes, unsigned long long
        'bool': '?',  # 1 byte, bool
        'string': 's'  # string (byte array)
    }
    formats_len_dict = {
        'float': 4,
        'double': 8,
        'char': 1,
        'byte': 1,
        'short': 2,
        'ushort': 2,
        'int': 4,
        'uint': 4,
        'long': 8,
        'ulong': 8,
        'bool': 1,
        'string': None  # The length of the string is not fixed
    }
    def compile(formats):
        f = '!'
        for i in formats:
            f+=DataFormats.formats_dict[i]