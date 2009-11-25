
import os
import re

from django.conf import settings

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
    """
    check_config()
    for package_name in settings.JS_BUILDER_PACKAGES:
        build_package(package_name)
