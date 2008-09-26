def synchsafe2dec(string):
    """
    Convert a 4 byte string encoded with the synchsafe scheme into a C{int}
    """
    # chop our string into a list of bytes
    bytelist = list(string)
    # chop our list of bytes into a list of bits
    bitlist = []
    for byte in bytelist:
        bitlist += dec2bin(ord(byte), 8)
    bitlist = synchsafe2bin(bitlist)
    x = bin2dec(bitlist)
    return x

def dec2synchsafe(xx):
    """
    Convert an C{int} into a 4 byte string encoded with the synchsafe scheme
    """

    #bin2byte(bin2synchsafe(dec2bin(len(data), 28)))
    xx = bin2byte(bin2synchsafe(dec2bin(xx, 28)))
    assert len(xx) == 4
    return xx


def synchsafe2bin(x):
    assert len(x) == 32
    out = []
    c = 0
    while len(x) > 0:
        c += 1
        y = x.pop()
        if c == 8:
            c = 0
        else:
            out.append(y)
    out.reverse()
    assert len(out) == 28
    return out


def synchsafe2int(xx):
    assert len(xx) == 4
    bytelist = list(xx)
    val = 0
    BITSUSED = 7;
    MAXVAL = mask(BITSUSED * 4);
    # For each byte of the first 4 bytes in the string...
    for ii in range(0, 4):
        # ...append the last 7 bits to the end of the temp integer...
        val = (val << BITSUSED) | ord(bytelist[ii]) & mask(BITSUSED);

    # We should always parse 4 characters
    return min(val, MAXVAL)

def fourbytes2int(yy):
    ll = map(lambda x:x, yy)
    out = 0
    for ii in range(len(ll)):
        out += (pow(256,(3-ii)) * ord(ll[ii]))
    return out

def int2fourbytes(yy):
    ary = dec2bin(yy, 32)
    return bin2byte(ary)

def byte2bin(y, p=0):
    res2 = []
    for x in y:
        z = x
        res = []
        x = ord(x)
        while x > 0:
            res.append(x & 1)
            x = x >> 1
        if p > 0:
            res.extend([0] * (p - len(res)))
        res.reverse()
        res2.extend(res)
    return res2

def bin2byte(x):
    i = 0
    out = ''
    x.reverse()
    b = 1
    ttl = 0
    for y in x:
        i += 1
        ttl += y * b
        b *= 2
        if i == 8:
            i = 0
            out += chr(ttl)
            b = 1
            ttl = 0
    if b > 1:
        out += chr(ttl)
    out = list(out)
    out.reverse()
    out = ''.join(out)
    return out

def bin2dec(x):
    x.reverse()
    b = 1
    ttl = 0
    for y in x:
        ttl += y * b
        b *= 2
    return ttl

def dec2bin(x, p=0):
    res = []
    while x > 0:
        res.append(x & 1)
        x = x >> 1
    if p > 0:
        res.extend([0] * (p - len(res)))
    res.reverse()
    return res

def byte2bitlist(x):
    bitlist = []
    for ii in range(0, 8):
        bitlist.append(x & (1 << ii))
    return bitlist

def bitlist2int(x):
    raise Error
    return x        

def mask(bits):
    return ((1 << (bits)) - 1)
    

def bin2synchsafe(x):
    assert len(x) == 28
    x.reverse()
    out = []
    c = 0
    while len(x) > 0:
        c += 1
        if c == 1:
            out.append(0)
        y = x.pop()
        out.append(y)
        if c == 7:
            c = 0
    return out

def unsynchstr(bytes):
    lastfound = -1
    while 1:
        lastfound = bytes.find('\xff', lastfound + 1)
        if lastfound == -1:
            break
        if (lastfound + 1) == len(bytes):
            bytes = bytes + '\x00'
        elif ((ord(bytes[lastfound+1]) & ord('\xe0')) == ord('\xe0')) or (bytes[lastfound+1] == '\x00'):
            bytes = bytes[:lastfound+1] + '\x00' + bytes[lastfound+1:]
                
    return bytes
                                                                                                                                                                                                        
def deunsynchstr(bytes):
    # print bytes.count('\xff\x00')
    return bytes.replace('\xff\x00', '\xff')

