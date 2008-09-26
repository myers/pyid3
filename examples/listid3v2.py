#!/usr/bin/env python

import os
import sys
import string
import exceptions
import operator
import id3
import re

def listid3v2(filename):
    if not os.path.isfile(filename):
        print "%s: %s is not a file." % (sys.argv[0], filename)
        return

    id3v2 = id3.ID3v2( filename )
    
    print "Tag size: ", id3v2.tag_size
    
    maxsize = 0
    for frame in id3v2.frames:
        if len(frame.name) > maxsize:
            maxsize = len(frame.name)

    for frame in id3v2.frames:
        out = u"%s (%s): %s" % (frame.name.rjust(maxsize), frame.id, unicode(frame),)
        print out.encode('utf-8')


#
# Main program starts here
#
if __name__ == "__main__":
    for ff in sys.argv[1:]:
        listid3v2(ff)
            