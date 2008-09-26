#!/usr/bin/env python

__author__   = 'John Shamo'
__revision__ = "$Id: test_brokenframe.py,v 1.1 2004/04/29 21:06:46 myers_carpenter Exp $"

import unittest

import os, tempfile, shutil, filecmp

import id3

class BrokenFrameTestCase(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def testRead(self):
        """
        Try reading tags with broken frames, and see if we survive
        """
        mydir = os.path.join('sample-tags', 'broken-frames')
        if not os.path.isdir(mydir):
            raise RuntimeError, "No samples to look over"
        tag_list = os.listdir(mydir)
        tag_list.sort()

        for tag_file in tag_list:
            tag_file = os.path.join(mydir, tag_file)
            
            tag = id3.ID3v2(tag_file, broken_frames='drop')

def suite():
    suite = unittest.makeSuite(BrokenFrameTestCase, 'test')

    # suite2 = module2.TheTestSuite()
    # return unittest.TestSuite((suite1, suite2))

    return suite

if __name__ == "__main__":
    unittest.main()
