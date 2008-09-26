#!/usr/bin/env python

import os
import sys
import string
import exceptions
import operator
import id3
import re
from PIL import Image 
from wxPython.wx import *
import StringIO

class Frame( wxFrame ):
    def __init__( self ):
        image = None
        wxInitAllImageHandlers()
        wxFrame.__init__( self, NULL, -1, "Test")
        panel = wxPanel(self, -1)

        filename = sys.argv[1]
        
        if not os.path.isfile(filename):
            print "%s: %s is not a file." % (sys.argv[0], filename)
            return

        tag = id3.ID3v2( filename )
        
                
        for frame in tag.frames:
            if isinstance(frame, id3.ID3v2Frames.AttachedPicture):
                print len(frame.image)
                source = Image.open(StringIO.StringIO(frame.image))
                image = apply(wxEmptyImage, source.size )
                image.SetData(source.convert("RGB").tostring() )
                image.ConvertToBitmap()
                
        if image:
            bm = wxStaticBitmap(panel, -1, image.ConvertToBitmap() )
        else:
            raise SystemExit, "id3v2 tag has no image"

        self.SetSize(bm.GetSize())
        self.Layout()
    
    

if __name__ == "__main__":
    class App( wxPySimpleApp):
        def OnInit( self ):
            Frame().Show( 1)
            return 1
    App().MainLoop()

