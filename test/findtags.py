#!/usr/bin/env python

import os, sys

nametag = 'default'
counter = 0

def findtags(arg, dirname, names):
    global counter
    if not nametag:
        pass
    print "In %r..." % dirname
    
    for name in names:
        try:
            fullname = os.path.join(dirname, name)
            if not os.path.isfile(fullname):
                continue
            
            print "Looking at %r...." % name
            ff = file(fullname, 'r')
            if ff.read(3) != 'ID3':
                print "No id3v2 tag"
                continue 
                
            verinfo = ff.read(2)
            version_minor = ord(verinfo[0])
            version_rev = ord(verinfo[1])
            
            #skip over flags
            ff.read(1)
            
            tag_size = synchsafe2dec(ff.read(4))
            if tag_size > 3*1024*1024:
                print "Tag says it's much bigger than it should"
                continue
                
            ff.seek(0)
            whole_tag = ff.read(3 + 2 + 1 + 4 + tag_size)
            
            out_name = '%s-%07d.tag' % (nametag, counter,)
            counter = counter + 1
            print "Writing out %r..." % out_name
            out_file = file(os.path.join('sample-tags', out_name), 'w')
            out_file.write(whole_tag)
            out_file.close()
            
            ff.close()
        except:
            (exctype, value,) = sys.exc_info()[:2]
            print "got error %r %r" % (exctype, str(value),)
            continue        

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
    i = 0;
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

def synchsafe2bin(x):
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
    return out

def byte2bitlist(x):
    bitlist = []
    for ii in range(0, 8):
        bitlist.append(x & (1 << ii))
    return bitlist

def bitlist2int(x):
    return x        

def synchsafe2dec(string):
    # chop our string into a list of bytes
    bytelist = list(string)
    # chop our list of bytes into a list of bits
    bitlist = []
    for byte in bytelist:
        bitlist += dec2bin(ord(byte), 8)
    bitlist = synchsafe2bin(bitlist)
    x = bin2dec(bitlist)
    return x


def synchsafe2int(string):
    bytelist = list(string)
    val = 0
    BITSUSED = 7;
    MAXVAL = mask(BITSUSED * 4);
    # For each byte of the first 4 bytes in the string...
    for ii in range(0, 4):
        # ...append the last 7 bits to the end of the temp integer...
        val = (val << BITSUSED) | ord(bytelist[ii]) & mask(BITSUSED);

    # We should always parse 4 characters
    return min(val, MAXVAL)

def mask(bits):
        return ((1 << (bits)) - 1)
    
def fourbytes2int(string):
    ll = map(lambda x:x, string)
    out = 0
    for ii in range(len(ll)):
        out += (pow(256,(3-ii)) * ord(ll[ii]))
    return out

def bin2synchsafe(x):
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


if __name__ == '__main__':
    if len(sys.argv) != 3:
        raise SystemExit, "Useage: findtag.py <your-name> <dir-with-tagged-files>"
    nametag = sys.argv[1]
    if not os.path.exists('sample-tags'):
        os.makedirs('sample-tags')
    os.path.walk(sys.argv[2], findtags, None)
    