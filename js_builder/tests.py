"""
"""
import os
import shutil

from django.test import TestCase

from js_builder.utils import is_regexp, find_in_dir, here

class UtilsTest(TestCase):
    
    def setUp(self):
        self.rootTestsDir = here(["tests_data"])
        os.mkdir(self.rootTestsDir);
    
    def tearDown(self):
        shutil.rmtree(self.rootTestsDir)
    
    def test_is_regexp(self):
        """
        Test is_regexp functions from utils
        """
        self.failUnless(is_regexp("file\.js"))
        self.failUnless(is_regexp(".*\.js"))
        self.failUnless(is_regexp(".*"))
        self.failUnless(is_regexp("core_(ajax|ui|dom).js"))
        self.failUnless(is_regexp("ui_.*\.js"))
        self.failIf(is_regexp("directory"))
        self.failIf(is_regexp("underscore_directory"))
        self.failIf(is_regexp("camelCaseDirectory"))
        self.failIf(is_regexp("file.js"))
        self.failIf(is_regexp("underscore_style.js"))
        self.failIf(is_regexp("camelCaseStyle.js"))

    def test_find_in_dir_single_dir(self):
        os.mkdir(os.path.join(self.rootTestsDir, "t"))
        files, dirs = find_in_dir("t", self.rootTestsDir)
        self.failUnlessEqual(len(files), 0)
        self.failUnlessEqual(len(dirs), 1)
        self.failUnlessEqual(dirs[0], "t")

    def test_find_in_dir_single_js_file(self):
        f = open(os.path.join(self.rootTestsDir, "t.js"), "w")
        f.close()
        os.mkdir(os.path.join(self.rootTestsDir, "t"))
        files, dirs = find_in_dir("t.js", self.rootTestsDir)
        self.failUnlessEqual(len(files), 1)
        self.failUnlessEqual(files[0], "t.js")
        self.failUnlessEqual(len(dirs), 0)

