
import os
import re

from django.conf import settings
from django import template

here = lambda x: os.path.join(os.path.abspath(os.path.dirname(__file__)), *x)

def match(pattern, name, root):
    """
    Check if name matches the given pattern

    Parameters:
        pattern - regular expression or normal string
        name - file/dir name
        root - absolute path to directory
    Return:
        boolean
    """
    if is_regexp(pattern):
        if is_special_regexp(pattern):
            if os.path.isdir(os.path.join(root, name)):
                return True
            else:
                return False
        else:
            return re.match(pattern, name) != None
    else:
        return pattern == name

def find_in_dir(pattern, dir, onlyDirs = False, onlyFiles = False):
    """
    Finds directories and files matched to the pattern.
    Return tuple:
        ([files], [directories])

    Parameters:
        pattern - file name or regexp in string
        dir - absolute path to the directory
        onlyDirs - search only directories
        onlyFiles - search only files
    Return:
        names of the found files
    """
    files = map(lambda x: (x, os.path.join(dir, x)), os.listdir(dir))
    results = ([], [])

    for name, path in files:
        if os.path.isdir(path) and not onlyFiles:
            if match(pattern, name, dir):
                results[1].append(name)
        else:
            if onlyDirs:
                continue
            if match(pattern, name, dir):
                results[0].append(name)

    return results

def find(pattern, root):
    """
    Find files in the current directory and subdirectories which match
    the pattern.

    Parameters:
        pattern - pattern for matching files/directories e.g. **/d/[a-z]\.js
        root - current directory
    Return:
        absolute paths
    """
    sections = pattern.split("/")
    results = []

    if len(sections) > 1:
        onlyDirs = True
    else:
        onlyDirs = False

    if sections[0] == "***":
        results += find("/".join(sections[1:]), root)
        sections[0] = "**"

    files, dirs = find_in_dir(sections[0], root, onlyDirs = onlyDirs)
    results += map(lambda file: os.path.join(root, file), files)

    if len(sections) > 1:
        for dir in dirs:
            if is_special_regexp(sections[0]):
                results += find("/".join(sections), os.path.join(root, dir))
            results += find("/".join(sections[1:]), os.path.join(root, dir))

    return results

def find_package_files(list, root):
    """
    Find all files required by package definitions.

    Params:
        list of regular expressions or names
    Return:
        absolute paths to the files

    Function doesn't return files required by files dependencies.
    """
    files = []
    for item in list:
        files += find(item, root)
    return files

def is_special_regexp(s):
    """
    Check is string is special regular expression
    """
    if s == "**" or s == "***":
        return True
    return False

def is_regexp(path):
    """
    Check if path is regexp and return boolean
    """
    return re.search(r"[\\*?+\[\]|]", path) != None or \
        re.search("(\.[?+*])", path) != None # .? | .+ | .*

def check_config():
    """
    Check if JS_BUILDER_* are correct
    """
    # check if destination directory exists
    if not os.path.exists(settings.JS_BUILDER_DEST):
        raise Exception("Destination directory doesn't exists: %s" %
                                                    settings.JS_BUILDER_DEST)
    if not os.path.exists(settings.JS_BUILDER_SOURCE):
        raise Exception("Source directory doesn't exists: %s" %
                                                    settings.JS_BUILDER_SOURCE)

def get_file_dependencies(path, removeRequires=True):
    """
    Return file dependencies

    Parameters:
        path - absolute path to the file
    """
    results = []
    if removeRequires == False:
        f = open(path, "r")
        while True:
            r = re.match(r"//\ *require\ (?P<file>.*)", f.readline())
            if r == None:
                break
            else:
                results.append(os.path.join(
                                settings.JS_BUILDER_SOURCE, r.groupdict()["file"]))
        f.close()
    else:
        f = open(path, "r")
        lines = f.readlines()
        f.close()
        f = open(path, "w")
        check = True
        for line in lines:
            if check == False:
                f.write(line + "\n")
            else:
                r = re.match(r"//\ *require\ (?P<file>.*)", line)
                if r == None:
                    check = False
                    f.write(line + "\n")
                else:
                    results.append(os.path.join(
                            settings.JS_BUILDER_SOURCE, r.groupdict()["file"]))
        f.close()
    return results

class DependencyGraph(object):

    def __init__(self, out_edges):
        self.out_edges = out_edges
        # create in_edges dict
        self.in_edges = {}
        for out_edge in out_edges:
            for in_edge in out_edges[out_edge]:

                if not self.in_edges.has_key(in_edge):
                    self.in_edges[in_edge] = []
                if not out_edge in self.in_edges[in_edge]:
                    self.in_edges[in_edge].append(out_edge)
        # create a list of all edges in graph
        self.edges = []

        for e in self.in_edges:
            if not e in self.edges:
                self.edges.append(e)

        for e in self.out_edges:
            if not e in self.edges:
                self.edges.append(e)

    def has_edges(self):
        return len(self.get_edges()) != 0

    def get_edges(self):
        return self.edges

    def get_outgoing_edges(self, node):
        try:
            return self.out_edges[node]
        except KeyError, e:
            return []

    def get_incoming_edges(self, node):
        try:
            return self.in_edges[node]
        except KeyError, e:
            return []

    def has_incoming_edges(self, node):
        return len(self.get_incoming_edges(node)) > 0

    def has_outgoing_edges(self, node):
        return len(self.get_outgoing_edges(node)) > 0

    def remove_edge(self, outNode, inNode):
        self.get_outgoing_edges(outNode).remove(inNode)
        self.get_incoming_edges(inNode).remove(outNode)
        return self.remove_isolated_nodes()

    def remove_isolated_nodes(self):
        removed_nodes = []
        for e in reversed(self.edges):
            if not self.has_incoming_edges(e) and not self.has_outgoing_edges(e):
                self.edges.remove(e)
                removed_nodes.append(e)
                if e in self.in_edges:
                    del self.in_edges[e]
                if e in self.out_edges:
                    del self.out_edges[e]
        return removed_nodes

    def has_nodes_with_no_incoming_edges(self):
        return len(self.nodes_with_no_incoming_edges()) > 0

    def nodes_with_no_incoming_edges(self):
        results = []
        for e in self.edges:
            if not self.has_incoming_edges(e):
                results.append(e)
        return results

def topological_sorting(graph):
    """
    Parameters:
        graph - DependencyGraph
    """
    sorted_nodes = graph.remove_isolated_nodes()

    while graph.has_nodes_with_no_incoming_edges():
        a = graph.nodes_with_no_incoming_edges()[0]
        sorted_nodes.append(a)

        for node in reversed(graph.get_outgoing_edges(a)):
            removed_nodes = graph.remove_edge(a, node)

            if a in removed_nodes:
                removed_nodes.remove(a)
            sorted_nodes.extend(removed_nodes)

    if graph.has_edges():
        raise Exception("Dependency graph has at least one cycle")
    else:
        sorted_nodes.reverse()
        return sorted_nodes

def get_package_dependencies(files):
    dependencies = {}
    
    while len(files) > 0:
        fs = get_file_dependencies(files[0])
        dependencies[files[0]] = fs
        files.remove(files[0])
        for f in fs:
            if not f in files and not dependencies.has_key(f):
                files.append(f)
    return dependencies

def build_package(package_name):
    """
    Build package with 'package_name' name

    This might be useful http://www.djangosnippets.org/snippets/1011/
    during the tests.
    """
    check_config()
    if not package_name in settings.JS_BUILDER_PACKAGES:
        raise Exception("Unknown package: %s" % package_name)
    else:
        package_file = open(
            os.path.join(settings.JS_BUILDER_DEST, package_name + ".js"), "w")
        package_cfg = settings.JS_BUILDER_PACKAGES[package_name]
        files = find_package_files(package_cfg, settings.JS_BUILDER_SOURCE)
        dependencies = get_package_dependencies(
            map(lambda f: os.path.join(settings.JS_BUILDER_SOURCE, f), files))
        graph = DependencyGraph(dependencies)
        sorted_files = topological_sorting(graph)

        for file in sorted_files:
            f = open(file, "r")
            package_file.write(f.read())
            f.close()
        package_file.close()

def build_all_packages():
    """
    Build all packages from JS_BUILDER_PACKAGES
    """
    check_config()
    for package_name in settings.JS_BUILDER_PACKAGES:
        build_package(package_name)
