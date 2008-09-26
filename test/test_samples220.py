#!/usr/bin/env python

__author__   = 'John Shamo'
__revision__ = "$Id: test_samples220.py,v 1.2 2004/03/02 05:26:07 myers_carpenter Exp $"

import unittest

import os

import id3

class ID3v220SamplesTestCase(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def disable_testRead(self):
        tag_list = os.listdir('sample-tags')
        tag_list.sort()
        for tag_file in tag_list:
            tag_file = os.path.join('sample-tags', tag_file)
            try:
                tag = id3.ID3v2(tag_file)
            except id3.Error, err:
                print "file was: %s, %s" % (tag_file, err.__str__(),)
            except:
                print "%r" % (tag_file,)
                raise
                
            #self.failUnless(tag.frames != [])


def suite():
    suite = unittest.makeSuite(ID3v220SamplesTestCase, 'test')

    # suite2 = module2.TheTestSuite()
    # return unittest.TestSuite((suite1, suite2))

    return suite

if __name__ == "__main__":
    unittest.main()
