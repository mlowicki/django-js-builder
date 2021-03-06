"""
"""
import os
import shutil
import time
import urllib

from django.test import TestCase
from django import template
from django.conf import settings

from js_builder.utils import (is_regexp, is_special_regexp, find_in_dir, here,
                              find, find_package_files, build_package,
                              get_file_dependencies, DependencyGraph,
                              GraphEdge, GraphNode, topological_sorting,
                              check_config, LOG_FILE)
from js_builder.tests_utils import SettingsTestCase, check_last_log


class UtilsTest(SettingsTestCase):
    """
    TODO:
        tests for checking if right files are created according to
        GET, JS_BUILDER_COMPERSS and DEBUG values
    """
    def setUp(self):
        self.rootTestsDir = here(["tests_data"])
        if os.path.isdir(self.rootTestsDir):
            shutil.rmtree(self.rootTestsDir)
        os.mkdir(self.rootTestsDir)
        self.settings_manager.set(JS_BUILDER_LOGGING=[LOG_FILE])
        self.settings_manager.set(JS_BUILDER_EXCEPTION=False)

    def tearDown(self):
        super(UtilsTest, self).tearDown()
        shutil.rmtree(self.rootTestsDir)

    def test_is_special_regexp(self):
        """
        Test is_special_regexp functions from utils
        """
        self.failUnless(is_special_regexp("**"))
        self.failIf(is_special_regexp("file.js"))
        self.failIf(is_special_regexp("directory"))
        self.failIf(is_special_regexp("[abc]"))
        self.failIf(is_special_regexp(".*"))

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
        """
        Test find_in_dir function with directory name as parameters
        """
        os.mkdir(os.path.join(self.rootTestsDir, "t"))
        os.mkdir(os.path.join(self.rootTestsDir, "r"))
        os.mkdir(os.path.join(self.rootTestsDir, "tt"))
        files, dirs = find_in_dir("t", self.rootTestsDir)
        self.failUnlessEqual(len(files), 0)
        self.failUnlessEqual(len(dirs), 1)
        self.failUnlessEqual(dirs[0], "t")

    def test_find_in_dir_single_js_file(self):
        """
        Test find_in_dir function with file name as parameters
        """
        f = open(os.path.join(self.rootTestsDir, "t.js"), "w")
        f.close()
        f = open(os.path.join(self.rootTestsDir, "r.js"), "w")
        f.close()
        f = open(os.path.join(self.rootTestsDir, "tt.js"), "w")
        f.close()
        os.mkdir(os.path.join(self.rootTestsDir, "t"))
        os.mkdir(os.path.join(self.rootTestsDir, "r"))
        files, dirs = find_in_dir("t.js", self.rootTestsDir)
        self.failUnlessEqual(len(files), 1)
        self.failUnlessEqual(files[0], "t.js")
        self.failUnlessEqual(len(dirs), 0)

    def test_find_in_dir_regexp(self):
        """
        Test find_in_dir function with regexps as parameters
        """
        f = open(os.path.join(self.rootTestsDir, "a.js"), "w")
        f.close()
        f = open(os.path.join(self.rootTestsDir, "b.js"), "w")
        f.close()
        f = open(os.path.join(self.rootTestsDir, "c.js"), "w")
        f.close()
        f = open(os.path.join(self.rootTestsDir, "d.js"), "w")
        f.close()
        files, dirs = find_in_dir("[abc]\.js", self.rootTestsDir)
        self.failUnlessEqual(len(files), 3)
        self.failUnless("a.js" in files)
        self.failUnless("b.js" in files)
        self.failUnless("c.js" in files)
        self.failUnlessEqual(len(dirs), 0)

        files, dirs = find_in_dir(".*\.js", self.rootTestsDir)
        self.failUnlessEqual(len(files), 4)
        self.failUnless("a.js" in files)
        self.failUnless("b.js" in files)
        self.failUnless("c.js" in files)
        self.failUnless("d.js" in files)
        self.failUnlessEqual(len(dirs), 0)

        os.mkdir(os.path.join(self.rootTestsDir, "e"))
        os.mkdir(os.path.join(self.rootTestsDir, "f"))
        files, dirs = find_in_dir(".*", self.rootTestsDir)
        self.failUnlessEqual(len(files), 4)
        self.failUnless("a.js" in files)
        self.failUnless("b.js" in files)
        self.failUnless("c.js" in files)
        self.failUnless("d.js" in files)
        self.failUnlessEqual(len(dirs), 2)
        self.failUnless("e" in dirs)
        self.failUnless("f" in dirs)

    def test_find_in_dir_special_regexp(self):
        """
        Test find_in_dir function with special regexps as parameters
        """
        f = open(os.path.join(self.rootTestsDir, "a.js"), "w")
        f.close()
        f = open(os.path.join(self.rootTestsDir, "b.js"), "w")
        f.close()
        f = open(os.path.join(self.rootTestsDir, "c.js"), "w")
        f.close()
        os.mkdir(os.path.join(self.rootTestsDir, "d"))
        os.mkdir(os.path.join(self.rootTestsDir, "ee"))
        files, dirs = find_in_dir("**", self.rootTestsDir)
        self.failUnlessEqual(len(files), 0)
        self.failUnlessEqual(len(dirs), 2)
        self.failUnless("d" in dirs)
        self.failUnless("ee" in dirs)

    def test_find(self):
        f = open(os.path.join(self.rootTestsDir, "a.js"), "w")
        f.close()
        f = open(os.path.join(self.rootTestsDir, "b.js"), "w")
        f.close()
        os.mkdir(os.path.join(self.rootTestsDir, "d1"))
        f = open(os.path.join(self.rootTestsDir, "d1", "c.js"), "w")
        f.close()
        os.mkdir(os.path.join(self.rootTestsDir, "d2"))
        f = open(os.path.join(self.rootTestsDir, "d2", "d.js"), "w")
        f.close()
        files = find(".*\.js", self.rootTestsDir)
        self.failUnlessEqual(len(files), 2)
        self.failUnless(os.path.join(self.rootTestsDir, "a.js") in files)
        self.failUnless(os.path.join(self.rootTestsDir, "b.js") in files)

        files = find("d[1-2]/.*\.js", self.rootTestsDir)
        self.failUnlessEqual(len(files), 2)
        self.failUnless(os.path.join(self.rootTestsDir, "d1", "c.js") in files)
        self.failUnless(os.path.join(self.rootTestsDir, "d2", "d.js") in files)

        files = find("d1/.*\.js", self.rootTestsDir)
        self.failUnlessEqual(len(files), 1)
        self.failUnless(os.path.join(self.rootTestsDir, "d1", "c.js") in files)

        files = find(".*/.*\.js", self.rootTestsDir)
        self.failUnlessEqual(len(files), 2)
        self.failUnless(os.path.join(self.rootTestsDir, "d1", "c.js") in files)
        self.failUnless(os.path.join(self.rootTestsDir, "d2", "d.js") in files)

        files = find("d3/.*\.js", self.rootTestsDir)
        self.failUnlessEqual(len(files), 0)

        files = find("d1/.*/c.js", self.rootTestsDir)
        self.failUnlessEqual(len(files), 0)

        os.mkdir(os.path.join(self.rootTestsDir, "d1", "cc"))
        files = find("d1/cc.*", self.rootTestsDir)
        self.failUnlessEqual(len(files), 0)

    def test_find_with_special_regexp(self):
        """
        Tests special regexps handling
        """
        f = open(os.path.join(self.rootTestsDir, "a.js"), "w")
        f.close()
        f = open(os.path.join(self.rootTestsDir, "b.js"), "w")
        f.close()
        os.mkdir(os.path.join(self.rootTestsDir, "d1"))
        f = open(os.path.join(self.rootTestsDir, "d1", "c.js"), "w")
        f.close()
        os.mkdir(os.path.join(self.rootTestsDir, "d2"))
        f = open(os.path.join(self.rootTestsDir, "d2", "d.js"), "w")
        f.close()
        os.mkdir(os.path.join(self.rootTestsDir, "d2", "d3"))
        f = open(os.path.join(self.rootTestsDir, "d2", "d3", "e.js"), "w")
        f.close()
        files = find("**/.*\.js", self.rootTestsDir)
        self.failUnlessEqual(len(files), 3)
        self.failUnless(
                    os.path.join(self.rootTestsDir, "d1", "c.js") in files)
        self.failUnless(
                    os.path.join(self.rootTestsDir, "d2", "d.js") in files)
        self.failUnless(
            os.path.join(self.rootTestsDir, "d2", "d3", "e.js") in files)
        #
        # very depth directories structure
        #
        os.mkdir(os.path.join(self.rootTestsDir, "d2", "d3", "d4"))
        os.mkdir(os.path.join(self.rootTestsDir, "d2", "d3", "d4", "d5"))
        f = open(os.path.join(
                    self.rootTestsDir, "d2", "d3", "d4", "d5", "f.js"), "w")
        files = find("**/[^abcde]\.js", self.rootTestsDir)
        self.failUnlessEqual(len(files), 1)
        self.failUnless(os.path.join(
                self.rootTestsDir, "d2", "d3", "d4", "d5", "f.js") in files)

        files = find("**/d3/e.js", self.rootTestsDir)
        self.failUnlessEqual(len(files), 1)
        self.failUnless(os.path.join(
                            self.rootTestsDir, "d2", "d3", "e.js") in files)

        files = find("d2/**/.*\.js", self.rootTestsDir)
        self.failUnlessEqual(len(files), 2)
        self.failUnless(os.path.join(
                            self.rootTestsDir, "d2", "d3", "e.js") in files)
        self.failUnless(os.path.join(
                self.rootTestsDir, "d2", "d3", "d4", "d5", "f.js") in files)

        # none matching files
        files = find("**/[^a-f]\.js", self.rootTestsDir)
        self.failUnlessEqual(len(files), 0)

        # "***" pattern tests
        files = find("***/.*\.js", self.rootTestsDir)
        self.failUnlessEqual(len(files), 6)
        self.failUnless(
                    os.path.join(self.rootTestsDir, "a.js") in files)
        self.failUnless(
                    os.path.join(self.rootTestsDir, "b.js") in files)
        self.failUnless(
                    os.path.join(self.rootTestsDir, "d1", "c.js") in files)
        self.failUnless(
                    os.path.join(self.rootTestsDir, "d2", "d.js") in files)
        self.failUnless(
                os.path.join(self.rootTestsDir, "d2", "d3", "e.js") in files)
        self.failUnless(os.path.join(
                self.rootTestsDir, "d2", "d3", "d4", "d5", "f.js") in files)

        files = find("***/d1/c.js", self.rootTestsDir)
        self.failUnlessEqual(len(files), 1)
        self.failUnless(
                    os.path.join(self.rootTestsDir, "d1", "c.js") in files)

        files = find("d2/***/.*\.js", self.rootTestsDir)
        self.failUnlessEqual(len(files), 3)
        self.failUnless(os.path.join(
                            self.rootTestsDir, "d2", "d.js") in files)
        self.failUnless(os.path.join(
                            self.rootTestsDir, "d2", "d3", "e.js") in files)
        self.failUnless(os.path.join(
                self.rootTestsDir, "d2", "d3", "d4", "d5", "f.js") in files)

        files = find("***/d2/c.js", self.rootTestsDir)
        self.failUnlessEqual(len(files), 0)

    def test_find_package_files(self):
        f = open(os.path.join(self.rootTestsDir, "a.js"), "w")
        f.close()
        f = open(os.path.join(self.rootTestsDir, "b.js"), "w")
        f.close()
        os.mkdir(os.path.join(self.rootTestsDir, "d1"))
        f = open(os.path.join(self.rootTestsDir, "d1", "c.js"), "w")
        f.close()
        os.mkdir(os.path.join(self.rootTestsDir, "d2"))
        f = open(os.path.join(self.rootTestsDir, "d2", "d.js"), "w")
        f.close()
        os.mkdir(os.path.join(self.rootTestsDir, "d3"))
        f = open(os.path.join(self.rootTestsDir, "d3", "e.js"), "w")
        f.close()
        os.mkdir(os.path.join(self.rootTestsDir, "d3", "d4"))
        f = open(os.path.join(self.rootTestsDir, "d3", "d4", "f.js"), "w")
        files = find_package_files(["**/[df]", "[a-z]\.js"], self.rootTestsDir)
        self.failUnlessEqual(len(files), 4)
        self.failUnless(
                    os.path.join(self.rootTestsDir, "a.js") in files)
        self.failUnless(
                    os.path.join(self.rootTestsDir, "b.js") in files)
        self.failUnless(
                    os.path.join(self.rootTestsDir, "d2", "d.js") in files)
        self.failUnless(
                os.path.join(self.rootTestsDir, "d3", "d4", "f.js") in files)

        files = find_package_files(["**/[^a-h]", "[g-z]\.js"],
                                                            self.rootTestsDir)
        self.failUnlessEqual(len(files), 0)

    def test_build_package(self):
        #
        # TODO:
        #     more tests
        #
        os.mkdir(os.path.join(self.rootTestsDir, "data"))
        os.mkdir(os.path.join(self.rootTestsDir, "source"))
        os.mkdir(os.path.join(self.rootTestsDir, "dest"))

        self.settings_manager.set(
                JS_BUILDER_PACKAGES={"p1": [], "p2": ["a.js"]},
                JS_BUILDER_DEST=os.path.join(self.rootTestsDir, "dest"),
                JS_BUILDER_SOURCE=os.path.join(self.rootTestsDir, "source"))

        # wrong package name
        build_package("wrong package name")
        self.failUnless(check_last_log("wrong package name"))
        self.failUnlessEqual(
                    os.listdir(os.path.join(self.rootTestsDir, "dest")), [])

        # empty package
        build_package("p1")

        f = open(os.path.join(self.rootTestsDir, "source", "a.js"), "w")
        f.write("// require b.js\n")
        f.write("// require c.js\n")
        f.close()
        f = open(os.path.join(self.rootTestsDir, "source", "b.js"), "w")
        f.close()
        f = open(os.path.join(self.rootTestsDir, "source", "c.js"), "w")
        f.close()
        build_package("p2")

    def test_inline_js(self):
        self.settings_manager.set(
            JS_BUILDER_PACKAGES={},
            JS_BUILDER_DEST=os.path.join(self.rootTestsDir, "dest"),
            JS_BUILDER_SOURCE=os.path.join(self.rootTestsDir, "source"),
            DEBUG=True)
        os.mkdir(os.path.join(self.rootTestsDir, "source"))
        f = open(os.path.join(self.rootTestsDir, "source", "a.js"), "w")
        content= "function t() { return True; }"
        f.write(content)
        f.close()
        t = template.Template("{% load js_tags %}{% inline_js 'a.js' %}")
        c = template.Context({})
        html = "<script type='text/javascript' src='%s'>%s</script>" %\
        (urllib.pathname2url(os.path.join(settings.MEDIA_URL, 'a.js')), content)
        self.failUnlessEqual(t.render(c), html)

    def test_js_package_tag(self):
        """
        """
        self.settings_manager.set(
            JS_BUILDER_PACKAGES={"p1": [], "p2": ["[ab]\.js"],
                                 "p3": ["a.js", "b.js"], "p4": ["[a-z]\.js"],
                                 "p5": ["[a-z]\.js"]},
            JS_BUILDER_DEST=os.path.join(self.rootTestsDir, "dest"),
            JS_BUILDER_SOURCE=os.path.join(self.rootTestsDir, "source"),
            DEBUG=True)
        os.mkdir(os.path.join(self.rootTestsDir, "source"))
        os.mkdir(os.path.join(self.rootTestsDir, "dest"))

        html = "{% load js_tags %}"
        html += "{% js_package 'p1' %}"
        t = template.Template(html)
        c = template.Context({})
        self.failUnlessEqual(t.render(c),"<script type='text/javascript' " + \
                             "src='" + settings.MEDIA_URL + "p1.js'></script>")

        f = open(os.path.join(self.rootTestsDir, "source", "a.js"), "w")
        f.write("a")
        f.close()
        f = open(os.path.join(self.rootTestsDir, "source", "b.js"), "w")
        f.write("b")
        f.close()
        t = template.Template("{% load js_tags %}{% js_package 'p2' %}")
        c = template.Context({})
        self.failUnlessEqual(t.render(c), "<script type='text/javascript' " +\
                        "src='" + settings.MEDIA_URL + "p2.js'></script>")
        f = open(os.path.join(settings.JS_BUILDER_DEST, "p2.js"), "r")
        self.failUnlessEqual(f.read(), "a\nb")

        f = open(os.path.join(self.rootTestsDir, "source", "a.js"), "w")
        f.write("// require b.js\n")
        f.write("a")
        f.close()
        f = open(os.path.join(self.rootTestsDir, "source", "b.js"), "w")
        f.write("b")
        f.close()
        t = template.Template("{% load js_tags %}{% js_package 'p3' %}")
        c = template.Context({})
        self.failUnlessEqual(t.render(c), "<script type='text/javascript' " +\
                            "src='" + settings.MEDIA_URL + "p3.js'></script>")
        f = open(os.path.join(settings.JS_BUILDER_DEST, "p3.js"), "r")
        self.failUnlessEqual(f.read(), "b\n// require b.js\na")
        # check if content of the source file isn't changed
        f = open(os.path.join(self.rootTestsDir, "source", "a.js"), "r")
        self.failUnlessEqual(f.read(), "// require b.js\na")
        f.close()

        f = open(os.path.join(self.rootTestsDir, "source", "a.js"), "w")
        f.write("// require b.js\n")
        f.write("a")
        f.close()
        f = open(os.path.join(self.rootTestsDir, "source", "b.js"), "w")
        f.write("// require c.js\n")
        f.write("b")
        f.close()
        f = open(os.path.join(self.rootTestsDir, "source", "c.js"), "w")
        f.write("// require a.js\n")
        f.write("c")
        f.close()
        #
        # fix it
        #
        #self.failUnlessRaises(Exception, template.Template,
        #                      "{% load js_tags %}{% js_package 'p4' %}")

        f = open(os.path.join(self.rootTestsDir, "source", "a.js"), "w")
        f.write("// require b.js\n")
        f.write("// require c.js\n")
        f.write("// require d.js\n")
        f.write("a")
        f.close()
        f = open(os.path.join(self.rootTestsDir, "source", "b.js"), "w")
        f.write("// require d.js\n")
        f.write("// require c.js\n")
        f.write("b")
        f.close()
        f = open(os.path.join(self.rootTestsDir, "source", "c.js"), "w")
        f.write("// require d.js\n")
        f.write("c")
        f.close()
        f = open(os.path.join(self.rootTestsDir, "source", "d.js"), "w")
        f.write("d")
        f.close()
        t = template.Template("{% load js_tags%}{% js_package 'p5' %}")
        self.failUnlessEqual(t.render(c), "<script type='text/javascript' " +
                            "src='" + settings.MEDIA_URL + "p5.js'></script>")
        f = open(os.path.join(settings.JS_BUILDER_DEST, "p5.js"), "r")
        self.failUnlessEqual(f.read(), "d\n// require d.js\nc\n// require " +
                "d.js\n// require c.js\nb\n// require b.js\n// require " +
                "c.js\n// require d.js\na")

    def test_get_file_dependencies(self):
        self.settings_manager.set(JS_BUILDER_SOURCE=self.rootTestsDir)
        f = open(os.path.join(self.rootTestsDir, "a.js"), "w")
        f.write("// require b.js\n")
        f.write("//require c.js\n")
        f.write("// comment\n")
        f.close()
        f = open(os.path.join(self.rootTestsDir, "b.js"), "w")
        f.close()
        f = open(os.path.join(self.rootTestsDir, "c.js"), "w")
        f.close()
        dependencies = get_file_dependencies(
                                    os.path.join(self.rootTestsDir, "a.js"))
        self.failUnlessEqual(len(dependencies), 2)
        self.failUnless(
                    os.path.join(self.rootTestsDir, "b.js") in dependencies)
        self.failUnless(
                    os.path.join(self.rootTestsDir, "c.js") in dependencies)

    def test_topological_sorting(self):        
        """
        """
        graph = DependencyGraph([GraphEdge("a", "b")])
        results = topological_sorting(graph)

        self.failUnlessEqual(len(results), 2)
        self.failUnlessEqual(results[0], "b")
        self.failUnlessEqual(results[1], "a")

        graph = DependencyGraph([GraphEdge("a", "b"),
                                 GraphEdge("b", "c"),
                                 GraphEdge("a", "c")])
        results = topological_sorting(graph)
        self.failUnlessEqual(len(results), 3)
        self.failUnlessEqual(results[0], "c")
        self.failUnlessEqual(results[1], "b")
        self.failUnlessEqual(results[2], "a")

        graph = DependencyGraph([GraphEdge("a", "b"),
                                 GraphEdge("b", "c"),
                                 GraphEdge("d", "b"),
                                 GraphEdge("d", "a")])
        results = topological_sorting(graph)
        self.failUnlessEqual(len(results), 4)
        self.failUnlessEqual(results[0], "c")
        self.failUnlessEqual(results[1], "b")
        self.failUnlessEqual(results[2], "a")
        self.failUnlessEqual(results[3], "d")

        graph = DependencyGraph([GraphEdge("a", "b"),
                                 GraphEdge("b", "c"),
                                 GraphEdge("c", "a")])
        self.failUnlessRaises(Exception, topological_sorting, graph)

        graph = DependencyGraph([], [GraphNode("a"), GraphNode("b")])
        results = topological_sorting(graph)
        self.failUnlessEqual(len(results), 2)
        self.failUnless("a" in results)
        self.failUnless("b" in results)

    def test_dont_update_output_when_error(self):
        """
        Check if output file isn't updated when there was some errors during
        the building process
        """
        self.settings_manager.set(
            JS_BUILDER_PACKAGES={"p1": ["[a-z]\.js"]},
            JS_BUILDER_DEST=os.path.join(self.rootTestsDir, "dest"),
            JS_BUILDER_SOURCE=os.path.join(self.rootTestsDir, "source"),
            DEBUG=True)
        os.mkdir(os.path.join(self.rootTestsDir, "source"))
        os.mkdir(os.path.join(self.rootTestsDir, "dest"))

        f = open(os.path.join(self.rootTestsDir, "source", "a.js"), "w")
        f.write("// require b.js")
        f.close()
        f = open(os.path.join(self.rootTestsDir, "source", "b.js"), "w")
        f.write("// require a.js")
        f.close()
        t = template.Template("{% load js_tags %}{% js_package 'p1' %}")
        c = template.Context({})
        t.render(c)
        self.failIf(os.path.exists(os.path.join(
                                        self.rootTestsDir, "dest", "p1.js")))

    def test_package_needs_rebuilding(self):
        """
        """
        self.settings_manager.set(
            JS_BUILDER_PACKAGES={"p1": ["[a-z]\.js"]},
            JS_BUILDER_DEST=os.path.join(self.rootTestsDir, "dest"),
            JS_BUILDER_SOURCE=os.path.join(self.rootTestsDir, "source"),
            DEBUG=True)
        os.mkdir(os.path.join(self.rootTestsDir, "source"))
        os.mkdir(os.path.join(self.rootTestsDir, "dest"))

        html = "{% load js_tags %}"
        html += "{% js_package 'p1' %}"
        t = template.Template(html)
        c = template.Context({})
        self.failUnlessEqual(t.render(c),
                             "<script type='text/javascript' src='" +\
                             settings.MEDIA_URL + "p1.js'></script>")

        f = open(os.path.join(self.rootTestsDir, "source", "a.js"), "w")
        f.write("a")
        f.close()
        f = open(os.path.join(self.rootTestsDir, "source", "b.js"), "w")
        f.write("b")
        f.close()
        t = template.Template("{% load js_tags %}{% js_package 'p1' %}")
        c = template.Context({})
        self.failUnlessEqual(t.render(c), 
                             "<script type='text/javascript' src='" +\
                             settings.MEDIA_URL + "p1.js'></script>")
        package_file = os.path.join(self.rootTestsDir, "dest", "p1.js")
        old_m_time = os.path.getmtime(package_file)
        time.sleep(2)
        self.failUnlessEqual(t.render(c), 
                             "<script type='text/javascript' src='" +\
                             settings.MEDIA_URL + "p1.js'></script>")
        self.failUnlessEqual(os.path.getmtime(package_file), old_m_time)

        f = open(os.path.join(self.rootTestsDir, "source", "a.js"), "w")
        f.write("aa")
        f.close()
        t = template.Template("{% load js_tags %}{% js_package 'p1' %}")
        c = template.Context({})
        self.failUnlessEqual(t.render(c), 
                             "<script type='text/javascript' src='" +\
                             settings.MEDIA_URL + "p1.js'></script>")
        current_m_time = os.path.getmtime(package_file)
        current_time = time.time()
        self.failUnless(current_m_time <= current_time and
                                            current_time <= current_m_time +1)
