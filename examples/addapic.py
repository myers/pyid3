#!/usr/bin/env python

import os
import sys
import id3


#
# Main program starts here
#
if __name__ == "__main__":
    if not os.path.isfile(sys.argv[3]):
        print "not such file \"%s\"" % sys.argv[3]
    if not os.path.isfile(sys.argv[2]):
        print "not such file \"%s\"" % sys.argv[2]
                
    id3v2 = id3.ID3v2( sys.argv[3] )
    
    image = file(sys.argv[2], 'r').read()
    newframe = id3v2.new_frame('APIC')
    newframe.image = image
    if sys.argv[1] == '0':
        newframe.picturetype = '\x00'
    else:
        newframe.picturetype = '\x03'
    newframe.mimetype = "image/jpeg"
    id3v2.unsync = 0
    id3v2.save()
            