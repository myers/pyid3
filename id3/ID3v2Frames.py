# @(#) $Id: ID3v2Frames.py,v 1.5 2004/03/02 05:26:07 myers_carpenter Exp $
__version__ = "$Revision: 1.5 $"

import sys, re, zlib, warnings, imghdr, struct

from id3 import binfuncs
import id3

class ID3v2Frame(object):
    def __init__(self, id, version = (2,3,0,), data = None):
        self.id = id
        self.version = version
        
        # header flags
        self.tag_alter_preservation = False
        self.file_alter_preservation = False
        self.read_only = False 
        self.grouping_id = False
        self._compression = False
        self.encryption = False 
        self._unsynchronisation = False
        self.data_length_indicator = False
        
        # additional info (depends on value of header flags)
        self.group_id = None
        self.true_size = None
        self.encryption_method = None
        
        # everything that's not part of the header
        self.data = ''

        try:
            self.name = frameTypes[self.version[1]][self.id][0]
        except KeyError:
            self.name = "Unknown Frame Type"
            
        if data:
            self.parse_frame(data)

    def set_unsynchronisation(self, value):
        if value and self.version[1] >= 4:
            raise id3.Error
            self.data_length_indicator = True
        self._unsynchronisation = value
    def get_unsynchronisation(self):
        return self._unsynchronisation
    unsynchronisation = property(get_unsynchronisation, set_unsynchronisation)
        
    def set_compression(self, value):
        if value and self.version[1] >= 4:
            self.data_length_indicator = True
        self._compression = value
    def get_compression(self):
        return self._compression
    compression = property(get_compression, set_compression)
        
    def __str__(self):
        return 'not displaying'

    #def __repr__(self):
    #   return '<ID3v2Frame.%s (%s) compressed: %s dlied: %s encrypted: %s unsynched: %s>' % (self.__class__.__name__, self.id, self.compressed, self.dlied, self.encrypted, self.unsynched)

    def write_frame(self):
        data = self.write_data()
        
        # this gets called after the data for the frame is done
        
        flags = [0] * 16
        if self.version[1] == 3:
            # %abc00000 %ijk00000        
            flags[0] = self.tag_alter_preservation
            flags[1] = self.file_alter_preservation
            flags[2] = self.read_only
            flags[8] = self.compression
            flags[9] = self.encryption
            flags[10] = self.grouping_id
        elif self.version[1] == 4:
            # %0abc0000 %0h00kmnp
            flags[1] = self.tag_alter_preservation
            flags[2] = self.file_alter_preservation
            flags[3] = self.read_only
            flags[9] = self.grouping_id
            flags[12] = self._compression
            flags[13] = self.encryption
            flags[14] = self._unsynchronisation
            flags[15] = self.data_length_indicator

        header = binfuncs.bin2byte(flags)
        ext_header = ''
        # these add bytes to the header
        if self.grouping_id:
            ext_header = ext_header + self.group_id[0]
        if self.encryption:
            ext_header = ext_header + self.encryption_method[0]
        if self.version[1] == 4 and self.data_length_indicator:
            ext_header = ext_header + binfuncs.dec2synchsafe(len(data))
        
        if self.compression:
            if self.version[1] == 4:
                data = zlib.compress(data)
            else:
                oldframesize = struct.pack('!I', len(data))
                data = oldframesize + zlib.compress(data)
        if self.encryption:
            warnings.warn("Encrypted frame (method %r, frameid %r" % (self.encryption_method, self.frameid,))
        if self.unsynchronisation and self.version[1] == 4:
            data = binfuncs.deunsynchstr(data)
        
        id = self.id
        data = ext_header + data 
        if self.version[1] < 4 or self.id == 'COM ':
            size = struct.pack('!I', len(data))
        else:
            size = binfuncs.dec2synchsafe(len(data))
        return "%(id)s%(size)s%(header)s%(data)s" % locals()

    def parse_frame(self, data):
        try:
            self._parse_frame(data)
        except id3.BrokenFrameError:
            raise
        except:
            (exctype, value,) = sys.exc_info()[:2]
            raise id3.BrokenFrameError, "%s: %s" % (exctype, str(value),)
            
                        
    def _parse_frame(self, data):
        flags = binfuncs.byte2bin(data[:2], 8)
        self.data = data[2:]
        
        if self.version[1] == 3:
            # %abc00000 %ijk00000        
            self.tag_alter_preservation = flags[0]
            self.file_alter_preservation = flags[1]
            self.read_only = flags[2]
            assert flags[3] == 0
            assert flags[4] == 0
            assert flags[5] == 0
            assert flags[6] == 0
            assert flags[7] == 0
            self._compression = flags[8]
            self.encryption = flags[9]
            self.grouping_id = flags[10] 
            assert flags[11] == 0
            assert flags[12] == 0
            assert flags[13] == 0
            assert flags[14] == 0
            assert flags[15] == 0
        elif self.version[1] == 4:
            # %0abc0000 %0h00kmnp
            assert flags[0] == 0
            self.tag_alter_preservation = flags[1]
            self.file_alter_preservation = flags[2]
            self.read_only = flags[3]
            assert flags[4] == 0
            assert flags[5] == 0
            assert flags[6] == 0
            assert flags[7] == 0
            assert flags[8] == 0
            self.grouping_id = flags[9] 
            assert flags[10] == 0
            assert flags[11] == 0
            self._compression = flags[12]
            self.encryption = flags[13]
            self._unsynchronisation = flags[14]
            self.data_length_indicator = flags[15]
            if self._compression and not self.data_length_indicator:
                raise id3.BrokenFrameError, "The compression flag was set but not the data_length_indicator"
        else:
            raise Error("Unsupported tag (how did we not catch this before?)")

        # these add bytes to the header
        if self.grouping_id:
            self.group_id = self.data[0]
            self.data = self.data[1:]
        if self.encryption:
            self.encryption_method = self.data[0]
            self.data = self.data[1:]
        if self.version[1] == 3 and self.compression:
            (self.true_size,) = struct.unpack('!I', self.data[:4])
            self.data = self.data[4:]
        if self.version[1] == 4 and self.data_length_indicator:
            self.true_size = binfuncs.synchsafe2dec(self.data[:4])
            self.data = self.data[4:]
        
        # now we post process 
        if self.unsynchronisation:
            self.data = binfuncs.unsynchstr(self.data)
        if self.encryption:
            warnings.warn("Encrypted frame (method %r, frameid %r" % (self.encryption_method, self.frameid,))
        if self.compression:
            self.data = zlib.decompress(self.data)
            
            
        if self.true_size:
            assert len(self.data) == self.true_size, "len(data) == %d should be == %d, and should %r" % (len(self.data), self.true_size, self.__dict__)
            
        # now we run the subclass's data parser
        
        self.parse_data()

    def split_encoded(self, data):
        """
        Figuring out how to do split two encoded strings around a \x00 was tricky
        Here's what helped from http://www.id3.org/id3v2.4.0-structure.txt:
        
        $00   ISO-8859-1 [ISO-8859-1]. Terminated with $00.
        $01   UTF-16 [UTF-16] encoded Unicode [UNICODE] with BOM. All
              strings in the same frame SHALL have the same byteorder.
              Terminated with $00 00.
        $02   UTF-16BE [UTF-16] encoded Unicode [UNICODE] without BOM.
              Terminated with $00 00.
        $03   UTF-8 [UTF-8] encoded Unicode [UNICODE]. Terminated with $00.

        but I don't think 2.3.0 tags terminated ISO-8859-1 strings with a \x00... 
        
        Oh yes it does... but now I think that most tagging libs don't do this.
        
        AHHHH!... 
        
        <icepick> if there are two encoded strings in a frame then the first
        is terminated 
        <icepick> but if only one then no termination
        """
        
        try:
            if self._encoding == '\x00' or self._encoding == '\x03':
                nullindex = data.index('\x00') 
                return (data[:nullindex], data[nullindex+1:],)
            elif self._encoding == '\x01' or self._encoding == '\x02':
                nullindex = 0
                while 1:
                    nullindex = data[nullindex:].index('\x00\x00') + nullindex
                    if nullindex % 2 == 0:
                        break
                    nullindex = nullindex + 1
                    
                return (data[:nullindex], data[nullindex+2:],)
        except ValueError, err:
            raise id3.BrokenFrameError, "Corrupt tag, orig error: " + str(err)
        
    def termination(self):
        if self._encoding == '\x00' or self._encoding == '\x03':
            return '\x00'
        else:
            return '\x00\x00'        
        
    def find_best_encoding(self, value):
        try:
            value.encode('iso-8859-1', 'strict')
            return '\x00'
        except UnicodeEncodeError:
            if self.version[1] < 4:
                return '\x01'
            else:
                return '\x03'
        except:
            print "%r" % type(value)
            raise
            
    def decode(self, value):
        # ISO-8859-1
        if self._encoding == '\x00':
            value = value.decode('iso-8859-1')
        # UTF-16
        elif self._encoding == '\x01':
            if value == '':
                raise id3.BrokenFrameError, "Unicode text doesn't have BOM"
            value = unicode(value, 'utf-16')
        # UTF-16BE
        elif self._encoding == '\x02' and self.version[1] == 4:
            value = unicode(value, 'utf-16-be')
        # UTF-8
        elif self._encoding == '\x03' and self.version[1] == 4:
            value = unicode(value, 'utf-8')
        else:
            raise id3.BrokenFrameError, "Encoding scheme not in spec (%r). Corrupt tag?" % (self._encoding,)
        return value

    def encode(self, value):
        # ISO-8859-1
        if self._encoding == '\x00':
            value = value.encode('iso-8859-1')
        # UTF-16
        elif self._encoding == '\x01':
            value = value.encode('utf-16')
        # UTF-16BE
        elif self._encoding == '\x02' and self.version[1] == 4:
            value = value.encode('utf-16-be')
        # UTF-8
        elif self._encoding == '\x03' and self.version[1] == 4:
            value = value.encode('utf-8')
        else:
            raise id3.BrokenFrameError, "Encoding scheme not in spec (%r). Corrupt tag?" % (self._encoding,)
        return value

class TextInfo(ID3v2Frame):
    def __init__(self, id, version = (2,3,0,), data = None):
        self._value = ''
        ID3v2Frame.__init__(self, id, version, data)

    def __str__(self):
        return self.value

    def set_value(self, value):
        self._encoding = self.find_best_encoding(value)
        self._value = value
    def get_value(self):
        return self._value
    value = property(get_value, set_value)

    def parse_data(self):
        if len(self.data) < 1:
            raise id3.BrokenFrameError("Frame (%s) too short: less than 1" % (self.id,))
        self._encoding = self.data[0]
        self._value = self.decode(self.data[1:])
        
    def write_data(self):
        return "%s%s" % (self._encoding, self.encode(self._value),)
        
class GenreTextInfo(ID3v2Frame):
    # TODO: make 'name' a property
    def __init__(self, id, version = (2,3,0,), data = None):
        self._value = ''
        self.name = ''
        ID3v2Frame.__init__(self, id, version, data)

    def __str__(self):
        if self.name:
            return '%s (%s)' % (self.name, self.value,)
        else:
            return '%s' % (self.value,)

    def set_value(self, value):
        self._encoding = self.find_best_encoding(value)
        self._value = value
    def get_value(self):
        return self._value
    value = property(get_value, set_value)

    def parse_data(self):
        self._encoding = self.data[:1]
        self._value = self.decode(self.data[1:])
        genre_code = re.findall(r'\(([0-9]+)\)', self.value)
        if genre_code:
            self.name = id3.genres.get(int(genre_code[0]), "Unknown")

    def write_data(self):
        return "%s%s" % (self._encoding, self.encode(self._value),)

class URL(ID3v2Frame):
    def __init__(self, id, version = (2,3,0,), data = None):
        self.url = ''
        ID3v2Frame.__init__(self, id, version, data)

    def __str__(self):
        return '%s' % (self.url,) 

    def parse_data(self):
        self.url = self.data.decode('iso-8859-1')

    def write_data(self):
        return self.url.encode('iso-8859-1')

class UserURL(ID3v2Frame):
    def __init__(self, id, version = (2,3,0,), data = None):
        self._description = ''
        self.url = ''
        ID3v2Frame.__init__(self, id, version, data)

    def __str__(self):
        return 'Description: %r, URL: "%s"' % (self.description, self.url,) 

    def set_description(self, description):
        self._encoding = self.find_best_encoding(description)
        self._description = description
    def get_description(self):
        return self._description
    description = property(get_description, set_description)

    def parse_data(self):
        self._encoding = self.data[:1]
        (description, url,) = self.split_encoded(self.data[1:])
        self._description = self.decode(description)
        self.url = url.decode('iso-8859-1')

    def write_data(self):
        return "%s%s%s%s" % (self._encoding, self.encode(self._description), self.termination(), self.url.encode('iso-8859-1'),)

class UserTextInfo(ID3v2Frame):
    def __init__(self, id, version = (2,3,0,), data = None):
        self._description = ''
        self._value = ''
        ID3v2Frame.__init__(self, id, version, data)

    def __str__(self):
        return 'Description: %r, Value: %r' % (self.description, self.value,) 

    def set_description(self, description):
        # we have two encoded strings.  we need to find the encoding that 
        # will work for them both
        self._encoding = self.find_best_encoding(self._description)
        if self._encoding == '\x00':
            self._encoding = self.find_best_encoding(self._value)
        self._description = description
    def get_description(self):
        return self._description
    description = property(get_description, set_description)

    def set_value(self, value):
        # we have two encoded strings.  we need to find the encoding that 
        # will work for them both
        self._encoding = self.find_best_encoding(self._description)
        if self._encoding == '\x00':
            self._encoding = self.find_best_encoding(self._value)
        self._value = value
    def get_value(self):
        return self._value
    value = property(get_value, set_value)

    def parse_data(self):
        self._encoding = self.data[:1]
        (description, value,) = self.split_encoded(self.data[1:])
        self._description = self.decode(description)
        self._value = self.decode(value)

    def write_data(self):
        return "%s%s%s%s" % (self._encoding, self.encode(self.description), self.termination(), self.encode(self.value),)

class Comment(ID3v2Frame):
    def __init__(self, id, version = (2,3,0,), data = None):
        self.language = ''
        self._description = ''
        self._value = ''
        ID3v2Frame.__init__(self, id, version, data)

    def __str__(self):
        return 'Description: %r, Comment: %r' % (self.description, self.value,) 

    def set_description(self, description):
        # we have two encoded strings.  we need to find the encoding that 
        # will work for them both
        self._encoding = self.find_best_encoding(self._description)
        if self._encoding == '\x00':
            self._encoding = self.find_best_encoding(self._value)
        self._description = description
    def get_description(self):
        return self._description
    description = property(get_description, set_description)

    def set_value(self, value):
        # we have two encoded strings.  we need to find the encoding that 
        # will work for them both
        self._encoding = self.find_best_encoding(self._description)
        if self._encoding == '\x00':
            self._encoding = self.find_best_encoding(self._value)
        self._value = value
    def get_value(self):
        return self._value
    value = property(get_value, set_value)

    def set_language(self, language):
        if len(language) > 3:
            raise ValueError, "language can't be more than 3 letters long"
        self._language = language.rjust(3)
    def get_language(self):
        return self._language
    language = property(get_language, set_language)

    def parse_data(self):
        if len(self.data) < 5:
            raise id3.BrokenFrameError("Frame (%s) too short: less than 5 (raw: %r)" % (self.id, self.data,))
        self._encoding = self.data[:1]
        self._language = self.data[1:4]
        (description, value,) = self.split_encoded(self.data[4:])
        self._description = self.decode(description)
        self._value = self.decode(value)

    def write_data(self):
        return "%s%s%s%s%s" % (self._encoding, self._language, self.encode(self._description), self.termination(), self.encode(self._value),)

class AttachedPicture(ID3v2Frame):
    picturetypes = {
        '\x00': 'Other', 
        '\x01': "32x32 pixels 'file icon' (PNG only)", 
        '\x02': 'Other file icon', 
        '\x03': 'Cover (front)', 
        '\x04': 'Cover (back)', 
        '\x05': 'Leaflet page', 
        '\x06': 'Media (e.g. lable side of CD)', 
        '\x07': 'Lead artist/lead performer/soloist', 
        '\x08': 'Artist/performer', 
        '\x09': 'Conductor', 
        '\x10': 'Movie/video screen capture', 
        '\x11': 'A bright coloured fish',
        '\x12': 'Illustration', 
        '\x13': 'Band/artist logotype', 
        '\x14': 'Publisher/Studio logotype', 
        '\x0a': 'Band/Orchestra', 
        '\x0b': 'Composer', 
        '\x0c': 'Lyricist/text writer', 
        '\x0d': 'Recording Location', 
        '\x0e': 'During recording', 
        '\x0f': 'During performance', 
    }    

    def __init__(self, id, version = (2,3,0,), data = None):
        self.mimetype = None
        self.picturetype = '\x03'
        self.picturetype_name = self.picturetypes[self.picturetype]
        self._description = ''
        self._image = None
        ID3v2Frame.__init__(self, id, version, data)

    def __str__(self):
        return 'Description: %r, Type: %s (%r), size: %i bytes' % (self.description, self.picturetype_name, self.picturetype, len(self.image),) 

    def set_description(self, description):
        self._encoding = self.find_best_encoding(description)
        self._description = description
    def get_description(self):
        return self._description
    description = property(get_description, set_description)

    def get_image(self):
        return self._image
    def set_image(self, value):
        type = imghdr.what(None, value)
        if type != 'png' and type != 'jpeg':
            raise id3.Error, "Can't accept images of type %r" % (type,)
        self.mimetype = 'image/%s' % (type,)
        self._image = value
    image = property(get_image, set_image)
    
    def parse_data(self):
        self._encoding = self.data[:1]
        mimetype_end = self.data.find('\x00', 1)
        self.mimetype = self.data[1:mimetype_end].decode('iso-8859-1')
        self.picturetype = self.data[mimetype_end+1]
        if self.picturetypes.has_key(self.picturetype):
            self.picturetype_name = self.picturetypes[self.picturetype]
        (description, self._image,) = self.split_encoded(self.data[mimetype_end+2:])
        self._description = self.decode(description)
       
    def write_data(self):
        return "%s%s\x00%s%s%s%s" % (self._encoding, self.mimetype.encode('iso-8859-1'), self.picturetype, self.encode(self.description), self.termination(), self.image,)

class MusicCDIdentifier(ID3v2Frame):
    def __init__(self, id, version = (2,3,0,), data = None):
        self.toc = ''
        ID3v2Frame.__init__(self, id, version, data)

    def parse_data(self):
        self.toc = self.data

    def write_data(self):
        return self.toc

class UniqueFileIdentifier(ID3v2Frame):
    def __init__(self, id, version = (2,3,0,), data = None):
        self.owner = ''
        self.identifier = ''
        ID3v2Frame.__init__(self, id, version, data)

    def __str__(self):
        return 'Owner: %r, Identifier: %r' % (self.owner, self.identifier,) 

    def parse_data(self):
        (owner, identifier) = self.data.split('\x00', 1)
        self.owner = owner.decode('iso-8859-1')
        self.identifier = identifier.decode('iso-8859-1')

    def write_data(self):
        return "%s\x00%s" % (self.owner.encode('iso-8859-1'), self.identifier.encode('iso-8859-1'),)
        

class UnknownFrame(ID3v2Frame):
    def __init__(self, id, version = (2,3,0,), data = None):
        self.unknown_data = ''
        ID3v2Frame.__init__(self, id, version, data)

    def parse_data(self):
        self.unknown_data = self.data
        
    def write_data(self):
        return self.unknown_data

class CompilationFrame(ID3v2Frame):
    def __init__(self, id, version = (2,3,0,), data = None):
        self.unknown_data = ''
        ID3v2Frame.__init__(self, id, version, data)

    def parse_data(self):
        self.unknown_data = self.data
        
    def write_data(self):
        return self.unknown_data

frameTypes = {
    2:   {'BUF': ('Recommended buffer size', UnknownFrame,),
          'CNT': ('Play counter', UnknownFrame,),
          'COM': ('Comments', UnknownFrame,),
          'CRA': ('Audio encryption', UnknownFrame,),
          'CRM': ('Encrypted meta frame', UnknownFrame,),
          'EQU': ('Equalization', UnknownFrame,),
          'ETC': ('Event timing codes', UnknownFrame,),
          'GEO': ('General encapsulated object', UnknownFrame,),
          'IPL': ('Involved people list', UnknownFrame,),
          'LNK': ('Linked information', UnknownFrame,),
          'MCI': ('Music CD Identifier', UnknownFrame,),
          'MLL': ('MPEG location lookup table', UnknownFrame,),
          'PIC': ('Attached picture', UnknownFrame,),
          'POP': ('Popularimeter', UnknownFrame,),
          'REV': ('Reverb', UnknownFrame,),
          'RVA': ('Relative volume adjustment', UnknownFrame,),
          'SLT': ('Synchronized lyric/text', UnknownFrame,),
          'STC': ('Synced tempo codes', UnknownFrame,),
          'TAL': ('Album/Movie/Show title', TextInfo,),
          'TBP': ('BPM (Beats Per Minute)', TextInfo,),
          'TCM': ('Composer', TextInfo,),
          'TCO': ('Content type', GenreTextInfo,),
          'TCR': ('Copyright message', TextInfo,),
          'TDA': ('Date', TextInfo,),
          'TDY': ('Playlist delay', TextInfo,),
          'TEN': ('Encoded by', TextInfo,),
          'TFT': ('File type', TextInfo,),
          'TIM': ('Time', TextInfo,),
          'TKE': ('Initial key', TextInfo,),
          'TLA': ('Language(s)', TextInfo,),
          'TLE': ('Length', TextInfo,),
          'TMT': ('Media type', TextInfo,),
          'TOA': ('Original artist(s)/performer(s)', TextInfo,),
          'TOF': ('Original filename', TextInfo,),
          'TOL': ('Original Lyricist(s)/text writer(s)', TextInfo,),
          'TOR': ('Original release year', TextInfo,),
          'TOT': ('Original album/Movie/Show title', TextInfo,),
          'TP1': ('Lead artist(s)/Lead performer(s)/Soloist(s)/Performing group', TextInfo,),
          'TP2': ('Band/Orchestra/Accompaniment', TextInfo,),
          'TP3': ('Conductor/Performer refinement', TextInfo,),
          'TP4': ('Interpreted, remixed, or otherwise modified by', TextInfo,),
          'TPA': ('Part of a set', TextInfo,),
          'TPB': ('Publisher', TextInfo,),
          'TRC': ('ISRC (International Standard Recording Code)', TextInfo,),
          'TRD': ('Recording dates', TextInfo,),
          'TRK': ('Track number/Position in set', TextInfo,),
          'TSI': ('Size', TextInfo,),
          'TSS': ('Software/hardware and settings used for encoding', TextInfo,),
          'TT1': ('Content group description', TextInfo,),
          'TT2': ('Title/Songname/Content description', TextInfo,),
          'TT3': ('Subtitle/Description refinement', TextInfo,),
          'TXT': ('Lyricist/text writer', TextInfo,),
          'TXX': ('User defined text information frame', UserTextInfo,),
          'TYE': ('Year', TextInfo,),
          'UFI': ('Unique file identifier', UnknownFrame,),
          'ULT': ('Unsychronized lyric/text transcription', UnknownFrame,),
          'WAF': ('Official audio file webpage', UnknownFrame,),
          'WAR': ('Official artist/performer webpage', UnknownFrame,),
          'WAS': ('Official audio source webpage', UnknownFrame,),
          'WCM': ('Commercial information', UnknownFrame,),
          'WCP': ('Copyright/Legal information', UnknownFrame,),
          'WPB': ('Publishers official webpage', UnknownFrame,),
          'WXX': ('User defined URL link frame', UnknownFrame,),
    }, 

    3:   {'AENC': ('Audio encryption', UnknownFrame,),
          'APIC': ('Attached picture', AttachedPicture,),
          'COMM': ('Comments', Comment,),
          'COMR': ('Commercial frame', UnknownFrame,),
          'ENCR': ('Encryption method registration', UnknownFrame,),
          'EQUA': ('Equalization', UnknownFrame,),
          'ETCO': ('Event timing codes', UnknownFrame,),
          'GEOB': ('General encapsulated object', UnknownFrame,),
          'GRID': ('Group identification registration', UnknownFrame,),
          'IPLS': ('Involved people list', UnknownFrame,),
          'LINK': ('Linked information', UnknownFrame,),
          'MCDI': ('Music CD identifier', MusicCDIdentifier,),
          'MLLT': ('MPEG location lookup table', UnknownFrame,),
          'OWNE': ('Ownership frame', UnknownFrame,),
          'PCNT': ('Play counter', UnknownFrame,),
          'POPM': ('Popularimeter', UnknownFrame,),
          'POSS': ('Position synchronisation frame', UnknownFrame,),
          'PRIV': ('Private frame', UnknownFrame,),
          'RBUF': ('Recommended buffer size', UnknownFrame,),
          'RVAD': ('Relative volume adjustment', UnknownFrame,),
          'RVRB': ('Reverb', UnknownFrame,),
          'SYLT': ('Synchronized lyric/text', UnknownFrame,),
          'SYTC': ('Synchronized tempo codes', UnknownFrame,),
          'TALB': ('Album/Movie/Show title', TextInfo,),
          'TBPM': ('BPM (beats per minute)', TextInfo,),
          'TCOM': ('Composer', TextInfo,),
          'TCON': ('Content type', TextInfo,),
          'TCOP': ('Copyright message', TextInfo,),
          'TDAT': ('Date', TextInfo,),
          'TDLY': ('Playlist delay', TextInfo,),
          'TENC': ('Encoded by', TextInfo,),
          'TEXT': ('Lyricist/Text writer', TextInfo,),
          'TFLT': ('File type', TextInfo,),
          'TIME': ('Time', TextInfo,),
          'TIT1': ('Content group description', TextInfo,),
          'TIT2': ('Title/songname/content description', TextInfo,),
          'TIT3': ('Subtitle/Description refinement', TextInfo,),
          'TKEY': ('Initial key', TextInfo,),
          'TLAN': ('Language(s)', TextInfo,),
          'TLEN': ('Length', TextInfo,),
          'TMED': ('Media type', TextInfo,),
          'TOAL': ('Original album/movie/show title', TextInfo,),
          'TOFN': ('Original filename', TextInfo,),
          'TOLY': ('Original lyricist(s)/text writer(s)', TextInfo,),
          'TOPE': ('Original artist(s)/performer(s)', TextInfo,),
          'TORY': ('Original release year', TextInfo,),
          'TOWN': ('File owner/licensee', TextInfo,),
          'TPE1': ('Lead performer(s)/Soloist(s)', TextInfo,),
          'TPE2': ('Band/orchestra/accompaniment', TextInfo,),
          'TPE3': ('Conductor/performer refinement', TextInfo,),
          'TPE4': ('Interpreted, remixed, or otherwise modified by', TextInfo,),
          'TPOS': ('Part of a set', TextInfo,),
          'TPUB': ('Publisher', TextInfo,),
          'TRCK': ('Track number/Position in set', TextInfo,),
          'TRDA': ('Recording dates', TextInfo,),
          'TRSN': ('Internet radio station name', TextInfo,),
          'TRSO': ('Internet radio station owner', TextInfo,),
          'TSIZ': ('Size', TextInfo,),
          'TSRC': ('ISRC (international standard recording code)', TextInfo,),
          'TSSE': ('Software/Hardware and settings used for encoding', TextInfo,),
          'TXXX': ('User defined text information frame', UserTextInfo,),
          'TYER': ('Year', TextInfo,),
          'UFID': ('Unique file identifier', UniqueFileIdentifier,),
          'USER': ('Terms of use', UnknownFrame,),
          'USLT': ('Unsychronized lyric/text transcription', UnknownFrame,),
          'WCOM': ('Commercial information', URL,),
          'WCOP': ('Copyright/Legal information', URL,),
          'WOAF': ('Official audio file webpage', URL,),
          'WOAR': ('Official artist/performer webpage', URL,),
          'WOAS': ('Official audio source webpage', URL,),
          'WORS': ('Official internet radio station homepage', URL,),
          'WPAY': ('Payment', URL,),
          'WPUB': ('Publishers official webpage', URL,),
          'WXXX': ('User defined URL link frame', UserURL,),
          # Frames to deal with buggy stuff
          'COM ': ('User defined text information frame', UserTextInfo,),
          # MusicBrainz.org extension
          'XSOP': ('Sort order, Performer', TextInfo,),
          # Find it on a lot if files... no idea what it is
          'NCON': ('Unknown', UnknownFrame,),
          # iTune complation flag
          'TCMP': ('Compilation', CompilationFrame,),
    }, 

    4:   {'AENC': ('Audio encryption', UnknownFrame,),
          'APIC': ('Attached picture', AttachedPicture,),
          'ASPI': ('Audio seek point index', UnknownFrame,),
          'COMM': ('Comments', Comment,),
          'COMR': ('Commercial frame', UnknownFrame,),
          'ENCR': ('Encryption method registration', UnknownFrame,),
          'EQU2': ('Equalisation (2)', UnknownFrame,),
          'ETCO': ('Event timing codes', UnknownFrame,),
          'GEOB': ('General encapsulated object', UnknownFrame,),
          'GRID': ('Group identification registration', UnknownFrame,),
          'LINK': ('Linked information', UnknownFrame,),
          'MCDI': ('Music CD identifier', MusicCDIdentifier,),
          'MLLT': ('MPEG location lookup table', UnknownFrame,),
          'OWNE': ('Ownership frame', UnknownFrame,),
          'PCNT': ('Play counter', UnknownFrame,),
          'POPM': ('Popularimeter', UnknownFrame,),
          'POSS': ('Position synchronisation frame', UnknownFrame,),
          'PRIV': ('Private frame', UnknownFrame,),
          'RBUF': ('Recommended buffer size', UnknownFrame,),
          'RVA2': ('Relative volume adjustment (2)', UnknownFrame,),
          'RVRB': ('Reverb', UnknownFrame,),
          'SEEK': ('Seek frame', UnknownFrame,),
          'SIGN': ('Signature frame', UnknownFrame,),
          'SYLT': ('Synchronised lyric/text', UnknownFrame,),
          'SYTC': ('Synchronised tempo codes', UnknownFrame,),
          'TALB': ('Album/Movie/Show title', TextInfo,),
          'TBPM': ('BPM (beats per minute)', TextInfo,),
          'TCOM': ('Composer', TextInfo,),
          'TCON': ('Content type', GenreTextInfo,),
          'TCOP': ('Copyright message', TextInfo,),
          'TDEN': ('Encoding time', TextInfo,),
          'TDLY': ('Playlist delay', TextInfo,),
          'TDOR': ('Original release time', TextInfo,),
          'TDRC': ('Recording time', TextInfo,),
          'TDRL': ('Release time', TextInfo,),
          'TDTG': ('Tagging time', TextInfo,),
          'TENC': ('Encoded by', TextInfo,),
          'TEXT': ('Lyricist/Text writer', TextInfo,),
          'TFLT': ('File type', TextInfo,),
          'TIPL': ('Involved people list', TextInfo,),
          'TIT1': ('Content group description', TextInfo,),
          'TIT2': ('Title/songname/content description', TextInfo,),
          'TIT3': ('Subtitle/Description refinement', TextInfo,),
          'TKEY': ('Initial key', TextInfo,),
          'TLAN': ('Language(s)', TextInfo,),
          'TLEN': ('Length', TextInfo,),
          'TMCL': ('Musician credits list', TextInfo,),
          'TMED': ('Media type', TextInfo,),
          'TMOO': ('Mood', TextInfo,),
          'TOAL': ('Original album/movie/show title', TextInfo,),
          'TOFN': ('Original filename', TextInfo,),
          'TOLY': ('Original lyricist(s)/text writer(s)', TextInfo,),
          'TOPE': ('Original artist(s)/performer(s)', TextInfo,),
          'TOWN': ('File owner/licensee', TextInfo,),
          'TPE1': ('Lead performer(s)/Soloist(s)', TextInfo,),
          'TPE2': ('Band/orchestra/accompaniment', TextInfo,),
          'TPE3': ('Conductor/performer refinement', TextInfo,),
          'TPE4': ('Interpreted, remixed, or otherwise modified by', TextInfo,),
          'TPOS': ('Part of a set', TextInfo,),
          'TPRO': ('Produced notice', TextInfo,),
          'TPUB': ('Publisher', TextInfo,),
          'TRCK': ('Track number/Position in set', TextInfo,),
          'TRSN': ('Internet radio station name', TextInfo,),
          'TRSO': ('Internet radio station owner', TextInfo,),
          'TSOA': ('Album sort order', TextInfo,),
          'TSOP': ('Performer sort order', TextInfo,),
          'TSOT': ('Title sort order', TextInfo,),
          'TSRC': ('ISRC (international standard recording code)', TextInfo,),
          'TSSE': ('Software/Hardware and settings used for encoding', TextInfo,),
          'TSST': ('Set subtitle', TextInfo,),
          'TXXX': ('User defined text information frame', UserTextInfo,),
          'UFID': ('Unique file identifier', UniqueFileIdentifier,),
          'USER': ('Terms of use', UnknownFrame,),
          'USLT': ('Unsynchronised lyric/text transcription', UnknownFrame,),
          'WCOM': ('Commercial information', URL,),
          'WCOP': ('Copyright/Legal information', URL,),
          'WOAF': ('Official audio file webpage', URL,),
          'WOAR': ('Official artist/performer webpage', URL,),
          'WOAS': ('Official audio source webpage', URL,),
          'WORS': ('Official Internet radio station homepage', URL,),
          'WPAY': ('Payment', URL,),
          'WPUB': ('Publishers official webpage', URL,),
          'WXXX': ('User defined URL link frame', UserURL,),
          # Frames to deal with buggy stuff
          'COM ': ('User defined text information frame', UserTextInfo,),
          # iTune complation flag
          'TCMP': ('Compilation', CompilationFrame,),
            
    }
}

encoding_map = {
    '\x00': 'iso-8859-1',
    '\x01': 'utf-16',
    '\x02': 'utf-16-be',
    '\x03': 'utf-8',
}
