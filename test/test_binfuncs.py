#!/usr/bin/env python

__author__   = 'John Shamo'
__revision__ = "$Id: test_binfuncs.py,v 1.1 2003/09/09 18:15:46 myers_carpenter Exp $"

import unittest

import os

from id3.binfuncs import * 

class BinTestCase(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def testSynchsafe(self):
        for ii in range(100000,10):
            xx = dec2synchsafe(ii)
            assert len(xx) == 4, "len(xx) = %d , supposed to be 4" % len(xx)
            assert ii == synchsafe2dec(xx)

def suite():
    suite = unittest.makeSuite(BinTestCase, 'test')

    # suite2 = module2.TheTestSuite()
    # return unittest.TestSuite((suite1, suite2))

    return suite

if __name__ == "__main__":
    unittest.main()
