
from django import template

register = template.Library()

@register.tag
def js_package(parser, token):
    try:
        # split_contents() knows not to split quoted strings.
        tag_name, package_name = token.split_contents()
    except ValueError:
        msg = '%r tag requires a single argument' % token.split_contents()[0]
        raise template.TemplateSyntaxError(msg)
    return JSPackageNode(package_name[1:-1])


class JSPackageNode(template.Node):

    def __init__(self, package_name):
        self.package_name = str(package_name)

    def render(self, context):
        return self.package_name + ".js"