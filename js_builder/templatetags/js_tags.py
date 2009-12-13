
import os

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
    package_name = package_name[1:-1]

    if settings.DEBUG == True:
        #
        # Remove compress=True. Compressed files should be created only
        # if request requires that
        #
        build_package(package_name, compress=True)
    return JSPackageNode(package_name)


class JSPackageNode(template.Node):

    def __init__(self, package_name):
        self.package_name = str(package_name)

    def render(self, context):
        compressed_package = "<script type='text/javascript' src='" +\
                settings.MEDIA_URL + self.package_name + "-min.js'></script>"

        if settings.DEBUG == False:
            return compressed_package

        uncompressed_package = "<script type='text/javascript' src='" +\
                settings.MEDIA_URL + self.package_name + ".js'></script>"

        if "request" in context:
            compress = context["request"].GET.get("compress", "False")
            if compress == "True":
                return compressed_package
            elif compress == "False":
                return uncompressed_package

        if hasattr(settings, "JS_BUILDER_COMPRESS"):
            if getattr(settings, "JS_BUILDER_COMPRESS"):
                return compressed_package
            else:
                return uncompressed_package
        return uncompressed_package
