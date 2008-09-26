# @(#) $Id: __init__.py,v 1.5 2004/03/02 05:26:07 myers_carpenter Exp $
__revision__ = "$Revision: 1.5 $"

import sys, re, os, warnings, struct
import cStringIO as StringIO

from id3 import ID3v2Frames

DEBUG_LEVEL = 0

__version__ = '0.5.5'

class Error(RuntimeError):
    """
    Exception raised for all parse errors.
    """
    pass

class NoTagError(Error):
    """
    No tag found in the file
    """
    pass
                        
class BrokenFrameError(Error):
    """
    Tag has a broken frame
    """
    pass
                        
class ID3v2(object):
    """
    ID3v2 parsing/writing class
    """
    def __init__(self, filename = None, broken_frames='error', internal_checks = False):
        self.filename = None
        self.internal_checks = internal_checks
        self.version = (2,3,0,)

        self.tag_size = None
        self.broken_frames = broken_frames

        self.padding_size = 0

        self._unsync = False
        self._set_data_length = False
        self.extended_header = False
        self.experimental = False
        self.footer = False

        self.frames = []

        if filename:
            self.load(filename)

    def set_unsync(self, value):
        # need to do this so that silly tags that are read in can
        # be written out exactly as they were.
        if self.version[1] >= 4:
            self._set_data_length = True
        self._unsync = value            
    def get_unsync(self):
        return self._unsync
    unsync = property(get_unsync, set_unsync)
        

    def get_text_frame(self, frameid, create=True):
        """
        Get the copy of the right frame object or make a new one to 
        fit the bill
        """
        
        try:
            frametype = ID3v2Frames.frameTypes[self.version[1]][frameid][1]
            if frametype != ID3v2Frames.TextInfo:
                raise Error, "%r is not a TextInfo frame type" % (frameid,)
        except KeyError:
            raise Error, "%r is not a TextInfo frame type" % (frameid,)
        
        for frame in self.frames:
            if frame.id == frameid:
                return frame
        
        if create:
            return self.new_frame(frameid)
        else:
            return None            

    def get_usertext_frame(self, description, create=True):
        """
        Get the copy of the right frame object or make a new one to 
        fit the bill
        """
        
        for frame in self.frames:
            if frame.id == 'TXXX' and frame.description == description:
                return frame
        
        if create:
            ret = self.new_frame('TXXX')
            ret.description = description
            return ret
        else:
            return None

    def get_apic_frame(self, description, create=True):
        """
        Get the copy of the right frame object or make a new one to 
        fit the bill
        """
        
        for frame in self.frames:
            if frame.id == 'APIC' and frame.description == description:
                return frame
        
        if create:
            ret = self.new_frame('APIC')
            ret.description = description
            return ret
        
        return None

    def get_ufid_frame(self, owner, create=True):
        """
        Get the copy of the right frame object or make a new one to 
        fit the bill
        """
        
        for frame in self.frames:
            if frame.id == 'UFID' and frame.owner == owner:
                return frame
        
        if create:
            ret = self.new_frame('UFID')
            ret.owner = owner
            return ret
        else:
            return None
            

    def new_frame(self, frameid, data = None):
        try:
            frame_info = ID3v2Frames.frameTypes[self.version[1]][frameid]
            newframe = frame_info[1](frameid, self.version, data)
        except KeyError, err:
            warnings.warn("Unknown frame type %r in file %r" % (frameid, self.filename,))
            newframe = ID3v2Frames.UnknownFrame(frameid, self.version, data)
            
        self.frames.append(newframe)
        return newframe
        
    def load(self, filename):
        """
        Load a file and extract ID3v2 data
        """
        self.filename = filename 
        fh = open(self.filename, 'rb')
        fh.seek(0)
        if fh.read(3) != 'ID3':
            return

        verinfo = fh.read(2)
        self.version = (2,ord(verinfo[0]),ord(verinfo[1]),)
        if(self.version[1] < 3):
            raise Error, "Cannot process tags with version less than 2.3.0 (This tag's version is 2.%s.%s)" % (self.version[1],self.version[2],)
        if(self.version[1] > 4) or (self.version[2] > 0):
            raise Error, "Cannot process tags with version greater than 2.4.0 (This tag's version is 2.%s.%s)" % (self.version[1], self.version[2],)

        tag_flags = binfuncs.byte2bin(fh.read(1), 8)
        
        self._unsync = tag_flags[0]
        self.extended_header = tag_flags[1]
        self.experimental = tag_flags[2]
        self.footer = tag_flags[3]
        assert tag_flags[4] == 0
        assert tag_flags[5] == 0
        assert tag_flags[6] == 0
        assert tag_flags[7] == 0

        if self.extended_header:
            raise Error("Don't know what to do with an extended header")
        
        self.tag_size = binfuncs.synchsafe2dec(fh.read(4))
        if DEBUG_LEVEL >= 1:
            print "tag version: %d.%d.%d" % self.version
            print "tag size:", self.tag_size
            print "unsync:", self.unsync

        if self.version[1] == 3 and self.unsync:
            # print self.tag_size
            tag = fh.read(self.tag_size)
            fh.close()
            tag = binfuncs.deunsynchstr(tag)
            self.tag_size = len(tag)
            fh = StringIO.StringIO(tag)
        
        sizeleft = self.tag_size

        # 11 == frame header + 1 byte frame, smallest legal frame
        while sizeleft >= 11:
            frameid = fh.read(4)
            if re.match(r'[A-Z0-9]{4}', frameid) or ID3v2Frames.frameTypes[self.version[1]].has_key(frameid):
                rawframesize = fh.read(4)
                if self.version[1] >= 4 and frameid != 'COM ':
                    framesize = binfuncs.synchsafe2dec(rawframesize)
                    (framesize23,) = struct.unpack('!I', rawframesize)
                    print "2.4: %d vs 2.3: %d" % (framesize, framesize23,)
                else:
                    (framesize,) = struct.unpack('!I', rawframesize)
                    
                    
                
                if framesize > sizeleft + 2:
                    if self.broken_frames == 'drop':
                        warnings.warn("Broken frame size in %r. Dropping rest of tag." % self.filename)
                        self.padding_size = sizeleft
                        sizeleft = 0
                        break
                    else:
                        raise BrokenFrameError("Invalid frame size %r (raw: %r).  Frame type was %r. Corrupt tag." % (framesize,rawframesize,frameid,))
                data = fh.read(framesize + 2)
                if DEBUG_LEVEL >= 2:
                    print "Raw frame: %r" % (data,)
            elif frameid == '\x00\x00\x00\x00' or frameid == 'MP3e':
                # MP3ext http://www.mutschler.de/mp3ext/ puts "MP3ext " over and over in the padding
                sizeleft -= 4
                break
            else:
                try:
                    lastframeid = self.frames[-1].id
                except IndexError:
                    lastframeid = None
                    
                raise Error("Found garbage where I expected a Frame Id %r. Last frame was %r" % (frameid, lastframeid,))

            try:
                self.new_frame(frameid, data)
            except BrokenFrameError, err:
                if self.broken_frames == 'drop':
                    warnings.warn("Broken frame in %r. Dropping frame." % self.filename)
                    pass
                else:
                    raise
            sizeleft -= (framesize + 2 + 4 + 4)            
            
        if sizeleft:
            # TODO: perhaps detect mp3 frames?  that would be nice to know.
            data = fh.read(sizeleft)
            if frameid != 'MP3e' and data != '\x00' * sizeleft:
                warnings.warn("Not all padding is NULLed out in %r.  Perhaps this tag was written by buggy software, or I didn't parsed it correctly. padding = %r" % (self.filename, frameid + data,))
            self.padding_size = sizeleft
        fh.close()

    def read_frame(self, fh, sizeleft):
        oldpos = fh.tell()
        
    


    def save(self):
        """
        Save the current set of ID3v2 data to file
        """
        old_tag_size = None
        if os.path.isfile(self.filename):
            fh = open(self.filename, 'rb+')
            fh.seek(0)
            if fh.read(3) == 'ID3':
                verinfo = fh.read(2)
                version_minor = ord(verinfo[0])
                version_rev = ord(verinfo[1])
                (
                  unsync,
                  extended,
                  experimental,
                  footer,
                  foo,
                  foo,
                  foo,
                  foo
                ) = binfuncs.byte2bin(fh.read(1), 8)
                old_tag_size = binfuncs.synchsafe2dec(fh.read(4))
            else:
                old_tag_size = 0
        else:
            fh = open(self.filename, 'wb')

        if self.version[1] == 4 and self.unsync:
            if self._set_data_length:
                for ii in self.frames:
                    ii.unsynchronisation = True
            else:
                for ii in self.frames:
                    ii._unsynchronisation = True

        out = StringIO.StringIO()
        for ii in self.frames:
            out.write(ii.write_frame())

        if self.version[1] == 3 and self.unsync:
            tmp = StringIO.StringIO()
            tmp.write(binfuncs.unsynchstr(out.getvalue()))
            out = tmp

        if len(out.getvalue()) > old_tag_size:
            expand_file = 1
            # out += '\x00' * 2048
        else:
            expand_file = 0
            out.write('\x00' * (old_tag_size - len(out.getvalue())))

        newheader = 'ID3'
        # set the version
        newheader += chr(self.version[1])
        newheader += chr(self.version[2])
        # flags 
        newheader += binfuncs.bin2byte([
            self.unsync,
            self.extended_header,
            self.experimental,
            self.footer,
            0,
            0,
            0,
            0
        ])

        tagsize = binfuncs.dec2synchsafe(len(out.getvalue()))
        newheader += tagsize
        
        newtag = newheader + out.getvalue()

        if expand_file == 1:
            if old_tag_size:
                fh.seek(old_tag_size + 10)
            else:
                fh.seek(0)
            fh2 = open(self.filename + '.temp', 'wb')
            fh2.write(newtag)
            fh2.write(fh.read())
            fh2.close()
            fh.close()
            os.rename(self.filename + '.temp', self.filename)
        else:
            fh.seek(0)
            fh.write(newtag)
            fh.close()
        return

    def from_id3v1(self, id3v1tag):
        if (self.version[0], self.version[1],) == (2, 2,):
            raise NotImplementedError, "Cannot convert id3v1 tags to id3v2.2.x"
        if not isinstance(id3v1tag, ID3v1):
            raise TypeError, "Must be a ID3v1 object"
        if id3v1tag.artist:
            self.frames = filter(lambda frame: frame.id != 'TPE1', self.frames)
            f = self.new_frame('TPE1')
            f.value = id3v1tag.artist
        if id3v1tag.album:
            self.frames = filter(lambda frame: frame.id != 'TALB', self.frames)
            f = self.new_frame('TALB')
            f.value = id3v1tag.album
        if id3v1tag.title:
            self.frames = filter(lambda frame: frame.id != 'TIT2', self.frames)
            f = self.new_frame('TIT2')
            f.value = id3v1tag.title
        if id3v1tag.track:
            self.frames = filter(lambda frame: frame.id != 'TRCK', self.frames)
            f = self.new_frame('TRCK')
            f.value = id3v1tag.track
        if id3v1tag.comment:
            f = self.new_frame('COMM')
            f.comment = id3v1tag.comment
        if id3v1tag.genre:
            self.frames = filter(lambda frame: frame.id != 'TCON', self.frames)
            f = self.new_frame('TCON')
            f.value = '(%i)' % id3v1tag.genre
                                    


class ID3v1:
    """
    ID3v1 parsing/writing class
    """  
    def __init__(self, filename = None, error_if_no_tag = False):
        self.filename = None
        self.title = ''
        self.artist = ''
        self.album = ''
        self.year = ''
        self.comment = ''
        self.genre = 0
        self.genre_str = ''
        self.track = None
        self.error_if_no_tag = error_if_no_tag
        if filename:
            self.load(filename)
    
    def remove(self):
        fh = file(self.filename, 'rb+')
        fh.seek(0, 2)
        filesize = fh.tell()
        if filesize < 127:
            return
        fh.seek(-128, 2)
        id3tag = fh.read(128)
        if id3tag[0:3] != 'TAG':
            return
        fh.truncate(filesize - 128)
    
    def load(self, filename):
        """
        Load a file and extract ID3v1 data

        """
        self.filename = filename
        fh = open(filename, 'rb')
        fh.seek(0, 2)
        if fh.tell() < 127:
            if self.error_if_no_tag:
                raise NoTagError
            fh.close()    
            return
        fh.seek(-128, 2)
        id3tag = fh.read(128)
        if id3tag[0:3] != 'TAG':
            if self.error_if_no_tag:
                raise NoTagError
            fh.close()    
            return
        self.title = re.sub('\x00+$', '', id3tag[3:33].rstrip())
        self.artist = re.sub('\x00+$', '', id3tag[33:63].rstrip())
        self.album = re.sub('\x00+$', '', id3tag[63:93].rstrip())
        self.year = re.sub('\x00+$', '', id3tag[93:97].rstrip())
        self.comment = re.sub('\x00+$', '', id3tag[97:127].rstrip())
        self.genre = ord(id3tag[127:128])
        if self.genre in genres:
            self.genre_str = "%s (%d)" % (genres[self.genre], self.genre,)
        else:
            self.genre_str = "unknown (%d)" % self.genre
        if self.comment[28:29] == '\x00':
            self.track = ord(self.comment[29:30])
            self.comment = re.sub('\x00+$', '', self.comment[0:28].rstrip())
        else:
            self.track = None
            
        fh.close()

    def save(self):
        """
        Save the current set of ID3v1 data to file
        """
        fh = open(self.filename, 'rb+')
        self.title = self.title[0:30]
        self.artist = self.artist[0:30]
        self.album = self.album[0:30]
        self.year = self.year[0:4]
        if self.track != None:
            self.comment = self.comment[0:28]
        else:
            self.comment = self.comment[0:30]
        id3tag = 'TAG'
        id3tag += self.title + ('\x00' * (30 - len(self.title)))
        id3tag += self.artist + ('\x00' * (30 - len(self.artist)))
        id3tag += self.album + ('\x00' * (30 - len(self.album)))
        id3tag += self.year + ('\x00' * (4 - len(self.year)))
        if self.track != None:
            id3tag += self.comment + ('\x00' * (29 - len(self.comment)))
            id3tag += chr(self.track)
        else:
            id3tag += self.comment + ('\x00' * (30 - len(self.comment)))
        id3tag += chr(self.genre)
        fh.seek(0, 2)
        if fh.tell() > 127:
            fh.seek(-128, 2)
            oldid3tag = fh.read(3)
            if oldid3tag == 'TAG':
                fh.seek(-128, 2)
                fh.write(id3tag)
            else:
                fh.seek(0, 2)
                fh.write(id3tag)
        else:
            fh.write(id3tag)
        fh.close()

genres = {
    0: 'Blues',
    1: 'Classic Rock',
    2: 'Country',
    3: 'Dance',
    4: 'Disco',
    5: 'Funk',
    6: 'Grunge',
    7: 'Hip - Hop',
    8: 'Jazz',
    9: 'Metal',
    10: 'New Age',
    11: 'Oldies',
    12: 'Other',
    13: 'Pop',
    14: 'R&B',
    15: 'Rap',
    16: 'Reggae',
    17: 'Rock',
    18: 'Techno',
    19: 'Industrial',
    20: 'Alternative',
    21: 'Ska',
    22: 'Death Metal',
    23: 'Pranks',
    24: 'Soundtrack',
    25: 'Euro - Techno',
    26: 'Ambient',
    27: 'Trip - Hop',
    28: 'Vocal',
    29: 'Jazz + Funk',
    30: 'Fusion',
    31: 'Trance',
    32: 'Classical',
    33: 'Instrumental',
    34: 'Acid',
    35: 'House',
    36: 'Game',
    37: 'Sound Clip',
    38: 'Gospel',
    39: 'Noise',
    40: 'Alt Rock',
    41: 'Bass',
    42: 'Soul',
    43: 'Punk',
    44: 'Space',
    45: 'Meditative',
    46: 'Instrumental Pop',
    47: 'Instrumental Rock',
    48: 'Ethnic',
    49: 'Gothic',
    50: 'Darkwave',
    51: 'Techno - Industrial',
    52: 'Electronic',
    53: 'Pop - Folk',
    54: 'Eurodance',
    55: 'Dream',
    56: 'Southern Rock',
    57: 'Comedy',
    58: 'Cult',
    59: 'Gangsta Rap',
    60: 'Top 40',
    61: 'Christian Rap',
    62: 'Pop / Funk',
    63: 'Jungle',
    64: 'Native American',
    65: 'Cabaret',
    66: 'New Wave',
    67: 'Psychedelic',
    68: 'Rave',
    69: 'Showtunes',
    70: 'Trailer',
    71: 'Lo - Fi',
    72: 'Tribal',
    73: 'Acid Punk',
    74: 'Acid Jazz',
    75: 'Polka',
    76: 'Retro',
    77: 'Musical',
    78: 'Rock & Roll',
    79: 'Hard Rock',
    80: 'Folk',
    81: 'Folk / Rock',
    82: 'National Folk',
    83: 'Swing',
    84: 'Fast - Fusion',
    85: 'Bebob',
    86: 'Latin',
    87: 'Revival',
    88: 'Celtic',
    89: 'Bluegrass',
    90: 'Avantgarde',
    91: 'Gothic Rock',
    92: 'Progressive Rock',
    93: 'Psychedelic Rock',
    94: 'Symphonic Rock',
    95: 'Slow Rock',
    96: 'Big Band',
    97: 'Chorus',
    98: 'Easy Listening',
    99: 'Acoustic',
    100: 'Humour',
    101: 'Speech',
    102: 'Chanson',
    103: 'Opera',
    104: 'Chamber Music',
    105: 'Sonata',
    106: 'Symphony',
    107: 'Booty Bass',
    108: 'Primus',
    109: 'Porn Groove',
    110: 'Satire',
    111: 'Slow Jam',
    112: 'Club',
    113: 'Tango',
    114: 'Samba',
    115: 'Folklore',
    116: 'Ballad',
    117: 'Power Ballad',
    118: 'Rhythmic Soul',
    119: 'Freestyle',
    120: 'Duet',
    121: 'Punk Rock',
    122: 'Drum Solo',
    123: 'A Cappella',
    124: 'Euro - House',
    125: 'Dance Hall',
    126: 'Goa',
    127: 'Drum & Bass',
    128: 'Club - House',
    129: 'Hardcore',
    130: 'Terror',
    131: 'Indie',
    132: 'BritPop',
    133: 'Negerpunk',
    134: 'Polsk Punk',
    135: 'Beat',
    136: 'Christian Gangsta Rap',
    137: 'Heavy Metal',
    138: 'Black Metal',
    139: 'Crossover',
    140: 'Contemporary Christian',
    141: 'Christian Rock',
    142: 'Merengue',
    143: 'Salsa',
    144: 'Thrash Metal',
    145: 'Anime',
    146: 'JPop',
    147: 'Synthpop'
}
