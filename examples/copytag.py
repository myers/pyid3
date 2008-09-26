#!/usr/bin/env python

import os
import sys
import string
import exceptions
import operator
import id3
import re

def listid3v2(filename):
    id3v2 = id3.ID3v2()

    if not os.path.isfile(filename):
        print "%s: %s is not a file." % (sys.argv[0], filename)
        return

    id3v2 = id3.ID3v2( filename )
    for frame in id3v2.frames:
        print "%r" % frame
    
    id3v2.filename = "test.tag"
    id3v2.save() 

# Main program starts here
#
if __name__ == "__main__":
    for ff in sys.argv[1:]:
        listid3v2(ff)
            