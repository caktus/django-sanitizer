from django import template
from django.template.defaultfilters import stringfilter
from django.utils.html import fix_ampersands
from django.utils.safestring import mark_safe
from django.conf import settings

from BeautifulSoup import BeautifulSoup, Comment, NavigableString

register = template.Library()


@register.filter(name="allowtags")
@stringfilter
def allowtags(value, allowed=None):
    """Allows only whitelisted tags and attributes through.

    The setting ALLOWED_TAGS can override the behavior. The syntax of
    this setting is a space-separated list of tags, which are optionally
    followed by a colon and a comma-separated list of attribute permitted in
    the tag.
    
    For example, to allow <a> tags which are links or named anchors, but not
    to allow definition of an onclick attribute:

        ALLOWED_TAGS = "a:href,name"

    Disallowed tags or attributes are simply removed.
    """
    
    if allowed is None:
        allowed = getattr(settings, "ALLOWED_TAGS",
            "a:href b i ul ol li p br")

    valid_tag_defs = allowed.split()
    valid_tags = {}
    for tag_def in valid_tag_defs:
        try:
            tag_name, allowed_attrs = tag_def.split(':') 
            allowed_attrs = allowed_attrs.split(',')
        except ValueError:
            tag_name, allowed_attrs = tag_def.split(':')[0], ()
        valid_tags[tag_name] = allowed_attrs

    soup = BeautifulSoup(value, convertEntities=BeautifulSoup.HTML_ENTITIES)
    for comment in soup.findAll(
        text=lambda text: isinstance(text, Comment)):
        comment.extract()
    for tag in soup.findAll(True):
        _escape_text_nodes(tag)
        if tag.name not in valid_tags:
            tag.hidden = True
        else:
            tag.attrs = [(attr, val) for attr, val in tag.attrs
                         if attr in valid_tags[tag.name]]
    _escape_text_nodes(soup)
    return mark_safe(soup.renderContents().decode('utf8').replace('javascript:', ''))


@register.filter(name="maptags")
@stringfilter
def maptags(value, mapping):
    """Maps between given and expected tag names.

    For example, to down-shift headers.
    
        {{ text|maptags:"h4=h5 h3=h4 h2=h3 h1=h2" }}
    """

    mapping = dict(m.split('=') for m in mapping.split())

    soup = BeautifulSoup(value, convertEntities=BeautifulSoup.HTML_ENTITIES)
    for tag in soup.findAll(True):
        _escape_text_nodes(tag)
        tag.name = mapping.get(tag.name, tag.name)
    _escape_text_nodes(soup)

    return mark_safe(soup.renderContents().decode('utf8'))


def _escape_text_nodes(tag):
    for i, child in enumerate(tag.contents):
        if isinstance(child, NavigableString):
            t = fix_ampersands(child)
            t = t.replace('<', '&lt;').replace('>', '&gt;')
            child.parent.contents[i] = NavigableString(t)
