#!/usr/bin/env python

__author__   = 'John Shamo'
__revision__ = "$Id: test_id3v1.py,v 1.2 2004/03/02 05:26:07 myers_carpenter Exp $"

import unittest

import os, tempfile

import id3 

class id3v1TestCase(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_zero_length_file(self):
        FILESIZE = 0
        tfn = tempfile.mktemp('id3v2.tag')
        fh = file(tfn, 'wb+')
        
        fh.write('\x00' * FILESIZE)
        
        fh.close()

        id3v1 = id3.ID3v1(tfn)
    
        
    def test_remove(self):
        FILESIZE = 1024 
        tfn = tempfile.mktemp('id3v2.tag')
        fh = file(tfn, 'wb+')
        
        fh.write('\x00' * FILESIZE)
        
        fh.close()

        id3v1 = id3.ID3v1(tfn)
        id3v1.title = 'test'
        id3v1.save()
        
        assert os.stat(tfn).st_size == FILESIZE + 128, "size: %d should be %d" % (os.stat(tfn).st_size, FILESIZE + 1024,) 
        
        id3v1.remove()
        
        assert os.stat(tfn).st_size == FILESIZE
        
        os.unlink(tfn)



def suite():
    suite = unittest.makeSuite(id3v1TestCase, 'test')

    # suite2 = module2.TheTestSuite()
    # return unittest.TestSuite((suite1, suite2))

    return suite

if __name__ == "__main__":
    unittest.main()
