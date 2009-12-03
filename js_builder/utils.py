
import os
import re

from django.conf import settings

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
        for item in package_cfg:
            files = find_package_files(item, settings.JS_BUILDER_SOURCE)
            for file in files:
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
