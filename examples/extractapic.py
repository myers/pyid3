#!/usr/bin/env python

import os
import sys
import string
import exceptions
import operator
import id3
import re

def extractapic(filename):
    print "Extracting pictures from %r" % filename
    imagenum = 1
    if not os.path.isfile(filename):
        print "%s: %s is not a file." % (sys.argv[0], filename)
        return

    id3v2 = id3.ID3v2( filename )

    for frame in id3v2.frames:
        if frame.id == 'APIC':
            imgf = file("image-%0i.jpg" % imagenum, 'w')
            imgf.write(frame.image)
            imgf.close()

#
# Main program starts here
#
if __name__ == "__main__":
    for ff in sys.argv[1:]:
        extractapic(ff)
