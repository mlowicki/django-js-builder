
import os
import re
import commands

from django.conf import settings
from django import template

here = lambda x: os.path.join(os.path.abspath(os.path.dirname(__file__)), *x)

def match(pattern, name, root):
    """
    Check if name matches the given pattern

    Parameters:
        pattern <string> - regular expression or normal string
        name <string> - file/dir name
        root <string> - absolute path to directory
    Return:
        bool
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

def find_in_dir(pattern, dir, only_dirs = False, only_files = False):
    """
    Finds directories and files matched to the pattern.

    Parameters:
        pattern <string> - file name or regexp in string
        dir <string> - absolute path to the directory
        only_dirs <bool> - search only directories
        only_files <bool> - search only files
    Return:
        tuple - ([files], [directories])
    """
    files = map(lambda x: (x, os.path.join(dir, x)), os.listdir(dir))
    results = ([], [])

    for name, path in files:
        if os.path.isdir(path) and not only_files:
            if match(pattern, name, dir):
                results[1].append(name)
        else:
            if only_dirs:
                continue
            if match(pattern, name, dir):
                results[0].append(name)

    return results

def find(pattern, root):
    """
    Find files in the current directory and subdirectories which match
    the pattern.

    Parameters:
        pattern <string> - pattern for matching files/directories
                           e.g. **/d/[a-z]\.js
        root <string> - current directory
    Return:
        list - absolute paths
    """
    sections = pattern.split("/")
    results = []

    if len(sections) > 1:
        only_dirs = True
    else:
        only_dirs = False

    if sections[0] == "***":
        results += find("/".join(sections[1:]), root)
        sections[0] = "**"

    files, dirs = find_in_dir(sections[0], root, only_dirs = only_dirs)
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

    Function doesn't return files required by files dependencies

    Params:
        list <list> - list of regular expressions or names
    Return:
        list - absolute paths to the files
    """
    files = []
    for item in list:
        files += find(item, root)
    return files

def is_special_regexp(s):
    """
    Check is string is special regular expression

    Parameters:
        s <string>
    Return:
        <bool>
    """
    if s == "**" or s == "***":
        return True
    return False

def is_regexp(path):
    """
    Check if path is regexp and return boolean

    Parameters:
        path <string>
    Return:
        <bool>
    """
    return re.search(r"[\\*?+\[\]|]", path) != None or \
        re.search("(\.[?+*])", path) != None # .? | .+ | .*

def check_config():
    """
    Check if JS_BUILDER_* are set and correct
    """
    if not hasattr(settings, "JS_BUILDER_DEST"):
        raise Exception("JS_BUILDER_DEST is not set")

    if not hasattr(settings, "JS_BUILDER_SOURCE"):
        raise Exception("JS_BUILDER_SOURCE is not set")

    if not hasattr(settings, "JS_BUILDER_PACKAGES"):
        raise Exception("JS_BUILDER_PACKAGES is not set")

    if not os.path.exists(settings.JS_BUILDER_DEST):
        raise Exception("Destination directory doesn't exists: %s" %
                                                    settings.JS_BUILDER_DEST)
    if not os.path.exists(settings.JS_BUILDER_SOURCE):
        raise Exception("Source directory doesn't exists: %s" %
                                                    settings.JS_BUILDER_SOURCE)

def get_file_dependencies(path, remove_requires=True):
    """
    Return file dependencies

    Parameters:
        path <string> -  absolute path to the file
        remove_requires <bool>
    """
    results = []
    if remove_requires == False:
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

        for i in range(len(lines)):
            r = re.match(r"//\ *require\ (?P<file>.*)", lines[i])
            if r == None:
                f.write("".join(lines[i:]))
                break
            else:
                results.append(os.path.join(
                            settings.JS_BUILDER_SOURCE, r.groupdict()["file"]))
        f.close()
    return results


class GraphEdge(object):
    """
    Class represents edge in graph
    """
    def __init__(self, start, end):
        self.start = start
        self.end = end


class GraphNode(object):
    """
    Class represents node in graph
    """
    def __init__(self, name, out_edges=[], in_edges=[]):
        self.name = name
        self.in_edges = in_edges
        self.out_edges = out_edges

    def add_in_edge(self, name):
        if not name in self.in_edges:
            self.in_edges.append(name)

    def add_out_edge(self, name):
        if not name in self.out_edges:
            self.out_edges.append(name)

    def get_name(self):
        return self.name

    def get_outgoing_edges(self):
        return self.out_edges

    def get_incoming_edges(self):
        return self.in_edges

    def remove_out_edge(self, node):
        self.out_edges.remove(node)

    def remove_in_edge(self, node):
        self.in_edges.remove(node)

    def has_edge(self):
        return self.has_incoming_edges() or self.has_outgoing_edges()

    def has_incoming_edge(self):
        return len(self.in_edges) > 0

    def has_outgoing_edge(self):
        return len(self.out_edges) > 0


class DependencyGraph(object):
    """
    Class for represeting dependency graph
    """
    def __init__(self, edges, isolated_nodes=[]):
        self.nodes = isolated_nodes

        for edge in edges:
            if not edge.start in map(lambda n: n.get_name(), self.nodes):
                self.nodes.append(GraphNode(edge.start, [edge.end], []))
            else:
                for node in self.nodes:
                    if node.get_name() == edge.start:
                        node.add_out_edge(edge.end)

            if not edge.end in map(lambda n: n.get_name(), self.nodes):
                self.nodes.append(GraphNode(edge.end, [], [edge.start]))
            else:
                for node in self.nodes:
                    if node.get_name() == edge.end:
                        node.add_in_edge(edge.start)

    def has_edge(self):
        for node in self.nodes:
            if node.has_edge():
                return True
        return False

    def get_node(self, name):
        for node in self.nodes:
            if node.get_name() == name:
                return node
        return None

    def remove_edge(self, start_node, end_node):
        if type(start_node) == type(""):
            start_node = self.get_node(start_node)
        if type(end_node) == type(""):
            end_node = self.get_node(end_node)
        end_node.remove_in_edge(start_node.get_name())
        start_node.remove_out_edge(end_node.get_name())
        return self.remove_isolated_nodes()

    def remove_isolated_nodes(self):
        removed_nodes = []
        for node in reversed(self.nodes):
            if not node.has_incoming_edge() and not node.has_outgoing_edge():
                self.nodes.remove(node)
                removed_nodes.append(node)
        return removed_nodes

    def has_nodes_with_no_incoming_edge(self):
        """
        Check if there are some nods without incoming nodes
        Return:
            bool
        """
        return len(self.nodes_with_no_incoming_edge()) > 0

    def nodes_with_no_incoming_edge(self):
        """
        Return list of nodes without any incoming edges

        Return:
            list
        """
        results = []
        for node in self.nodes:
            if not node.has_incoming_edge():
                results.append(node)
        return results

def topological_sorting(graph):
    """
    Parameters:
        graph <DependencyGraph>

    Return:
        list
    """
    sorted_nodes = map(lambda n: n.get_name(), graph.remove_isolated_nodes())

    while graph.has_nodes_with_no_incoming_edge():
        a = graph.nodes_with_no_incoming_edge()[0]
        sorted_nodes.append(a.get_name())

        for node in reversed(a.get_outgoing_edges()):
            removed_nodes = map(lambda n: n.get_name(),
                                graph.remove_edge(a, node))

            if a.get_name() in removed_nodes:
                removed_nodes.remove(a.get_name())
            sorted_nodes.extend(removed_nodes)

    if graph.has_edge():
        raise Exception("Dependency graph has at least one cycle")
    else:
        sorted_nodes.reverse()
        return sorted_nodes

def get_package_dependencies(files):
    """
    Return all files needed to build the package

    Parameters:
        files <list>
    Return
        list
    """
    dependencies = {}
    
    while len(files) > 0:
        fs = get_file_dependencies(files[0])
        dependencies[files[0]] = fs
        files.remove(files[0])
        for f in fs:
            if not f in files and not dependencies.has_key(f):
                files.append(f)
    return dependencies

def get_unique_files(dependencies):
    files = []

    for k, v in dependencies.iteritems():
        if not k in files:
            files.append(k)
        for item in v:
            if not item in files:
                files.append(item)
    return files

def package_needs_rebuilding(files, package_name):
    package_file = os.path.join(
                            settings.JS_BUILDER_DEST, package_name + ".js")
    if not os.path.exists(package_file):
        return True
    package_m_time = os.path.getmtime(package_file)
    for f in files:
        if os.path.getmtime(f) > package_m_time:
            return True
    return False

def compress_package(package_name):
    """
        TODO
    """
    in_file = os.path.join(settings.JS_BUILDER_DEST, package_name + ".js")
    out_file = os.path.join(settings.JS_BUILDER_DEST, package_name + "-min.js")
    command = "java -jar " + here(
                ("yuicompressor-2.4.2", "yuicompressor-2.4.2.jar",))
    command += " " + in_file + " -o " + out_file
    status, output = commands.getstatusoutput(command)
    if status != 0:
        print "There was some problems with JavaScript compression"
        print output

def build_package(package_name, check_configuration=True, **options):
    """
    Build package with 'package_name' name

    Parameters:
        package_name <str>
        check_config <bool>
    """
    if check_configuration:
        check_config()
    if not package_name in settings.JS_BUILDER_PACKAGES:
        raise Exception("Unknown package: %s" % package_name)
    else:
        package_cfg = settings.JS_BUILDER_PACKAGES[package_name]
        files = find_package_files(package_cfg, settings.JS_BUILDER_SOURCE)
        dependencies = get_package_dependencies(
            map(lambda f: os.path.join(settings.JS_BUILDER_SOURCE, f), files))

        if package_needs_rebuilding(get_unique_files(dependencies),
                                    package_name):
            edges = []
            package_file = open(os.path.join(
                        settings.JS_BUILDER_DEST, package_name + ".js"), "w")
            isolated_nodes = []
            for k in dependencies:
                if len(dependencies[k]) == 0:
                    isolated_nodes.append(GraphNode(k, [], []))
                else:
                    for node in dependencies[k]:
                        edges.append(GraphEdge(k, node))
            graph = DependencyGraph(edges, isolated_nodes)
            sorted_files = topological_sorting(graph)

            for i in range(len(sorted_files)):
                f = open(sorted_files[i], "r")
                package_file.write(f.read())
                if i != len(sorted_files) -1:
                    package_file.write("\n")
                f.close()
            package_file.close()

            if options.get("compress", False):
                compress_package(package_name)
        else:
            if not os.path.exists(os.path.join(settings.JS_BUILDER_DEST,
                package_name + "-min.js")) and options.get("compress", False):
                compress_package(package_name)

def build_all_packages(**options):
    """
    Build all packages from JS_BUILDER_PACKAGES
    """
    check_config()
    for package_name in settings.JS_BUILDER_PACKAGES:
        build_package(package_name, False, **options)
