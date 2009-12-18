
import os
from contextlib import closing
import urllib

from django import template
from django.conf import settings

from js_builder.utils import build_package

register = template.Library()


@register.tag
def js_package(parser, token):
    try:
        tag_name, package_name = token.split_contents()
    except ValueError:
        msg = '%r tag requires a single argument' % token.split_contents()[0]
        raise template.TemplateSyntaxError(msg)
    return JSPackageNode(package_name[1:-1])

@register.tag
def inline_js(parser, token):
    try:
        tag_name, file_name = token.split_contents()
    except ValueError:
        msg = '%r tag requires a single argument' % token.split_contents()[0]
        raise template.TemplateSyntaxError(msg)
    return InlineJSNode(file_name[1:-1])


class InlineJSNode(template.Node):

    def __init__(self, path):
        self.path = path

    def render(self, context):
        with closing(open(os.path.join(settings.JS_BUILDER_SOURCE,
                                                        self.path))) as script:
            return "<script type='text/javascript' src='%s'>%s</script>" %\
                (urllib.pathname2url(os.path.join(
                                settings.MEDIA_URL, self.path)), script.read())


class JSPackageNode(template.Node):

    def __init__(self, package_name):
        self.package_name = str(package_name)

    def render(self, context):
        compressed_package = "<script type='text/javascript' src='" +\
                settings.MEDIA_URL + self.package_name + "-min.js'></script>"

        if settings.DEBUG == False:
            build_package(self.package_name, compress=True)
            return compressed_package

        uncompressed_package = "<script type='text/javascript' src='" +\
                settings.MEDIA_URL + self.package_name + ".js'></script>"

        if "request" in context:
            compress = context["request"].GET.get("compress", "False")
            if compress == "True":
                build_package(self.package_name, compress=True)
                return compressed_package
            elif compress == "False":
                build_package(self.package_name)
                return uncompressed_package

        if hasattr(settings, "JS_BUILDER_COMPRESS"):
            if getattr(settings, "JS_BUILDER_COMPRESS"):
                build_package(self.package_name, compress=True)
                return compressed_package

        build_package(self.package_name)
        return uncompressed_package
