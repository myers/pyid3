#!/usr/bin/env python

__author__   = 'John Shamo'
__revision__ = "$Id: test_xsop.py,v 1.1 2003/09/09 18:15:46 myers_carpenter Exp $"

import unittest

import os, tempfile

import id3 

class XSOPTestCase(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_apic(self):
        FILESIZE = 1024 
        DATA = 'monkey monkey, monkey'
        tfn = tempfile.mktemp('id3v2.tag')
        fh = file(tfn, 'wb+')
        
        fh.write('\xff' * FILESIZE)
        
        fh.close()
        
        id3v2 = id3.ID3v2(tfn)
        frame = id3v2.get_text_frame('XSOP')
        frame.value = DATA
        id3v2.save()
        
        del id3v2
        
        id3v2 = id3.ID3v2(tfn)
        frame = id3v2.get_text_frame('XSOP', create=False)
        assert frame.value == DATA

        os.unlink(tfn)



def suite():
    suite = unittest.makeSuite(XSOPTestCase, 'test')

    # suite2 = module2.TheTestSuite()
    # return unittest.TestSuite((suite1, suite2))

    return suite

if __name__ == "__main__":
    unittest.main()
