#!/usr/bin/env python

import os
import sys
import operator
import id3
import re

def listid3v2(filename):
    id3v2 = id3.ID3v2()

    if not os.path.isfile(filename):
        print "%s: %s is not a file." % (sys.argv[0], filename)
        return

    track = None
    artist = ''
    album = ''
    title = ''
    
    id3v1 = id3.ID3v1( filename )
    id3v2 = id3.ID3v2( filename )
    
    if id3v1.title:
        title = id3v1.title
    if id3v1.artist:
        artist = id3v1.artist
    if id3v1.album:
        album = id3v1.album
    if id3v1.track:
        track = int(id3v1.track)
    
    for frame in id3v2.frames:
        # print "%s" % frame
        if frame.id == 'TPE1':
            artist = frame.value
        elif frame.id == 'TIT2':
            title = frame.value
        elif frame.id == 'TALB':
            album = frame.value
        elif frame.id == 'TRCK':
            if frame.value.find('/') != -1:
                track = int(frame.value.split('/')[0])
            else:
                track = int(str(frame.value).strip())

    if not track:
        numbers = re.findall(r'[^0-9]([0-9][0-9])[^0-9]', filename)
        if not numbers:
             numbers = re.findall(r'([0-9][0-9])[^0-9]', filename)
        if numbers:
            track = int(numbers[0])

    print "File  : %s" % filename
    print "\tArtist: %s" % artist
    print "\tAlbum : %s" % album
    print "\tTrack : %s" % track
    print "\tTitle : %s" % title

#
# Main program starts here
#
if __name__ == "__main__":
    for ff in sys.argv[1:]:
        listid3v2(ff)
            