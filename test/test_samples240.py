#!/usr/bin/env python

__author__   = 'John Shamo'
__revision__ = "$Id: test_samples240.py,v 1.2 2003/09/10 05:45:02 myers_carpenter Exp $"

import unittest

import os
import filecmp
import shutil
import tempfile

import id3

class ID3v240TestCase(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def testReadNWrite(self):
        """
        Open the tag, read, then save and see if we have the same thing
        """
        mydir = os.path.join('sample-tags', '2.4.0')
        tag_list = os.listdir(mydir)
        tag_list.sort()
        for tag_file in tag_list:
            print tag_file
            tag_file = os.path.join(mydir, tag_file)
            tfn = tempfile.mktemp('id3v2.tag')
            shutil.copyfile(tag_file, tfn)
            
            try:
                tag = id3.ID3v2(tfn)
            except id3.Error, err:
                print "read failure. file was: %s, %s" % (tag_file, err.__str__(),)
                raise
            except:
                print "%r" % (tag_file,)
                raise
        
            tag.save()
            
            self.failUnless(filecmp.cmp(tag_file, tfn), "rewriting  %r failed. output at %r " % (tag_file, tfn,))
            os.unlink(tfn)

def suite():
    suite = unittest.makeSuite(ID3v240TestCase, 'test')

    # suite2 = module2.TheTestSuite()
    # return unittest.TestSuite((suite1, suite2))

    return suite

if __name__ == "__main__":
    unittest.main()
