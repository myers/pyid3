#!/usr/bin/env python

import os, sys
import distutils.core
import glob

import id3

cmds = {}

setup_args = {
    'name':         'PyID3',
    'version':      id3.__version__,
    'description':  'Reading and writing id3v2 and id3v1 tags (http://id3.org/)',
    'long_description': """\
pyid3 is a pure python library for reading and writing id3 tags (version
1.0, 1.1, 2.3, 2.4, readonly support for 2.2). 

What makes this better than all the others?  Testing!  This library has been
tested against some 200+ MB of just tags.
""",
    'license': 'Python',
    'author':       'Myers Carpenter',
    'author_email': 'icepick@icepick.info',
    'url':          'http://icepick.info/projects/pyid3/',
    'download_url': 'http://icepick.info/projects/pyid3/',
    'classifiers': [
        'Development Status :: 5 - Production/Stable',
        'Environment :: Plugins',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Python License (CNRI Python License)',
        'Programming Language :: Python',
        'Topic :: Multimedia :: Sound/Audio',
    ],
    'license':      'CNRI Python License',
    'packages':     ['id3'],
    'cmdclass':     cmds,
    'scripts':      ['examples/listid3v2.py',],
}

class test(distutils.core.Command):
    """
    Based off of http://mail.python.org/pipermail/distutils-sig/2002-January/002714.html
    """
    description  = "test the distribution prior to install"

    user_options = [
        ('verbosity=', None,
         "Set the verbosity on TestRunner",),
        ('single=', 's',
         "Runs tests from a single file",),]
    
    def initialize_options(self):
        self.single = None
        self.verbosity = 1

    def finalize_options(self):
        build = self.get_finalized_command('build')
        self.build_purelib = build.build_purelib
        self.build_platlib = build.build_platlib

    def run(self):
        import unittest
        # self.run_command('build')

        old_path = sys.path[:]
        sys.path.insert(0, os.path.abspath(os.getcwd()))

        runner = unittest.TextTestRunner(verbosity=self.verbosity)
        
        testFiles = []
        
        if self.single:
            testFiles = [self.single]
        else:
            testFiles.extend(glob.glob(os.path.join('test', 'test_*.py')))

        testSuites = []
        for fileName in testFiles:
            if not os.path.isfile(fileName):
                print '%s is not a file, skipping...' % fileName
                continue
            if fileName[:2] == './':
                fileName = fileName[2:] 
            moduleName = os.path.splitext(fileName)[0].replace(os.sep, '.')
            if self.verbosity > 1:
                print "Importing %r..." % moduleName
            moduleHandle = __import__(moduleName, globals(), locals(), [''])
            if not hasattr(moduleHandle, 'suite'):
                print "Skipping %r as it has no 'suite' function" % fileName
            else:
                testSuites.append(moduleHandle.suite())
            
        runner.run(unittest.TestSuite(tuple(testSuites)))

        sys.path = old_path

cmds['test'] = test

if __name__ == '__main__':
    apply(distutils.core.setup, (), setup_args)

