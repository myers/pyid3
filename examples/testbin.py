#!/usr/bin/env python

from id3.binfuncs import * 


#
# Main program starts here
#
if __name__ == "__main__":
    mystr = '\xff\x00\xff\xe0abcedefalkdfjkasd;lfkl\xff\xe1asdj;lfjlasdf\xff'
    mystr2 = str2synchsafe(mystr)
    mystr3 = synchsafe2str(mystr2)

    print "       in: %r" % mystr
    print "synchsafe: %r" % mystr2
    print "      out: %r" % mystr3

    if mystr == mystr3:
        print "passed"
    else:
        print "failed"
   
               