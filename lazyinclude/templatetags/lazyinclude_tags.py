from django import template
from django.utils.safestring import mark_safe
from django.conf import settings

register = template.Library()

#@register.tag
def lazyinclude(parser, token):
    """
    Only valid form: {% lazyinclude "_custom_stuff.html" %}
    """
    if not any(map(lambda x: "LazyIncludeMiddleware" in x, settings.MIDDLEWARE_CLASSES)):
        return template.loader_tags.do_include(parser, token)
    bits = token.contents.split()
    if not len(bits) == 2:
        raise template.TemplateSyntaxError('Tag must look sth. like this:{% lazyinclude "([a-z/_]+\.html)" %}')
    return LazyIncludeNode(template.BLOCK_TAG_START + token.contents + template.BLOCK_TAG_END)
lazyinclude = register.tag(lazyinclude)

class LazyIncludeNode(template.Node):
    def __init__(self, output):
        self.output = output

    def render(self, context):
        return mark_safe(self.output)
