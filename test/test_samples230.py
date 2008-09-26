#!/usr/bin/env python

__author__   = 'John Shamo'
__revision__ = "$Id: test_samples230.py,v 1.4 2004/04/29 21:06:46 myers_carpenter Exp $"

import unittest

import os, tempfile, shutil, filecmp

import id3

class Samples230TestCase(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def testReadNWrite(self):
        """
        Open the tag, read, then save and see if we have the same thing
        """
        mydir = os.path.join('sample-tags', '2.3.0')
        brokendir = os.path.join('sample-tags', 'broken-frames')
        if not os.path.isdir(mydir):
            raise RuntimeError, "No samples to look over"
        tag_list = os.listdir(mydir)
        tag_list.sort()
        for fn in tag_list:
            tag_file = os.path.join(mydir, fn)
            tfn = tempfile.mktemp('id3v2.tag')
            shutil.copyfile(tag_file, tfn)
            
            try:
                tag = id3.ID3v2(tfn)
            except:
                print "%r" % (tag_file,)
                raise
        
            try:
                tag.save()
            except:
                print "%r" % (tag_file,)
                raise
            
            # EVIL HACK
            # don't check files that have a TXXX 'CT_GAPLESS_DATA' frame
            # these were written by some buggy software that didn't put the
            # unicode BOM on the COMM comment 
            if tag.get_usertext_frame('CT_GAPLESS_DATA', create=False):
                print "Skipping known broken file... %r" % tag_file
                os.rename(tag_file, os.path.join(brokendir, fn))
                os.unlink(tfn)
                continue
            
            
            self.failUnless(self.helper_tagcmp(tag_file, tfn), "rewriting  %r failed. output at %r " % (tag_file, tfn,))
            os.unlink(tfn)

    def helper_tagcmp(self, tagfile1, tagfile2):
        """
        Compare the two files
        """
        tag = id3.ID3v2(tagfile1)
        size = tag.tag_size - tag.padding_size
        
        fdata1 = file(tagfile1).read(size)
        fdata2 = file(tagfile2).read(size)
        
        if fdata1 != fdata2:
            print "%r" % fdata1
            print "%r" % fdata2
        
        return fdata1 == fdata2

    def disable_testRead(self):
        """
        Not needed as the other covers this as well
        """ 
        mydir = os.path.join('sample-tags', '2.3.0')
        tag_list = os.listdir(mydir)
        tag_list.sort()
        for tag_file in tag_list:
            tag_file = os.path.join(mydir, tag_file)
            try:
                tag = id3.ID3v2(tag_file)
            except id3.Error, err:
                print "file was: %s, %s" % (tag_file, err.__str__(),)
            except:
                print "%r" % (tag_file,)
                raise
                
            #self.failUnless(tag.frames != [])


def suite():
    suite = unittest.makeSuite(Samples230TestCase, 'test')

    # suite2 = module2.TheTestSuite()
    # return unittest.TestSuite((suite1, suite2))

    return suite

if __name__ == "__main__":
    unittest.main()
