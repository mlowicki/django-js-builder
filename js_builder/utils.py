
import os
import re

from django.conf import settings

here = lambda x: os.path.join(os.path.abspath(os.path.dirname(__file__)), *x)

def match(pattern, name, root):
    """
    TODO
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

def find_in_dir(pattern, dir, onlyDirs = False):
    """
    Finds directories and files matched to the pattern.
    Return tuple:
        ([files], [directories])

    Parameters:
        pattern - file name or regexp in string
        dir - absolute path to the directory
        onlyDirs - indicate if search only directories
    """
    files = map(lambda x: (x, os.path.join(dir, x)), os.listdir(dir))
    results = ([], [])

    for name, path in files:
        if os.path.isdir(path):
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
    TODO
        doc
        handle "**" pattern
    """
    sections = pattern.split("/")
    results = []

    if len(sections) > 1:
        onlyDirs = True
    else:
        onlyDirs = False

    files, dirs = find_in_dir(sections[0], root, onlyDirs = onlyDirs)
    results += map(lambda file: os.path.join(root, file), files)

    if len(sections) > 1:
        for dir in dirs:
            results += find("/".join(sections[1:]), os.path.join(root, dir))

    return results

def is_special_regexp(path):
    """
    TODO
    """
    if path == "**":
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
    TODO
    """
    check_config()
    if not package_name in settings.JS_BUILDER_PACKAGES:
        raise Exception("Unknown package: %s" % package_name)
    else:
        print "building %s package ..." % package_name
        package_file = open(
            os.path.join(settings.JS_BUILDER_DEST, package_name + ".js"), "w")
        package_cfg = settings.JS_BUILDER_PACKAGES[package_name]
        for item in package_cfg:
            f = open(os.path.join(settings.JS_BUILDER_SOURCE, item), "r")
            package_file.write(f.read())
            f.close()
        package_file.close()


def build_all_packages():
    """
    TODO
    """
    check_config()
    for package_name in settings.JS_BUILDER_PACKAGES:
        build_package(package_name)
