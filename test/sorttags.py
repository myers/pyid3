#!/usr/bin/env python

import os, sys

from id3 import binfuncs


counter = 0

def sorttags(arg, dirname, names):
    global counter
    print "In %r..." % dirname
    
    for name in names:
        try:
            fullname = os.path.join(dirname, name)
            if not os.path.isfile(fullname):
                continue
            
            print "Looking at %r...." % name
            ff = file(fullname, 'r')
            if ff.read(3) != 'ID3':
                continue 
                
            verinfo = ff.read(2)
            version_minor = ord(verinfo[0])
            version_rev = ord(verinfo[1])
            
            newdir = os.path.join(dirname, "2.%d.%d") % (version_minor, version_rev,)
            if not os.path.exists(newdir):
                os.makedirs(newdir)
            ff.close()
            
            os.rename(fullname, os.path.join(newdir, name))

        except:
            continue        

if __name__ == '__main__':
    # just do this one dir deep
    sorttags(None, sys.argv[1], os.listdir(sys.argv[1]))
    