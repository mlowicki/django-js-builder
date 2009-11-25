"""
"""
from django.test import TestCase

from js_builder.utils import is_regexp

class UtilsTest(TestCase):
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

