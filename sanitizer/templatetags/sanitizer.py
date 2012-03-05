import re

from django import template
from django.template.defaultfilters import stringfilter
from django.utils.html import fix_ampersands
from django.utils.safestring import mark_safe
from django.conf import settings

from BeautifulSoup import BeautifulSoup, Tag, Comment, NavigableString

register = template.Library()


def _make_tag(name):
    return BeautifulSoup('<{0}>'.format(name)).findAll()[0]


@register.filter(name='notags')
@stringfilter
def notags(values):
    return allowtags(value, allowed='')


TAG_DEF = re.compile(r'([-a-z]*):?([a-z,]*)\[?([a-z,]*)\]?')
@register.filter(name="allowtags")
@stringfilter
def allowtags(value, allowed=None, callback=None):
    """Allows only whitelisted tags and attributes through.

    The setting ALLOWED_TAGS can override the behavior. The syntax of
    this setting is a space-separated list of tags, which are optionally
    followed by a colon and a comma-separated list of attribute permitted in
    the tag.
    
    For example, to allow <a> tags which are links or named anchors, but not
    to allow definition of an onclick attribute:

        ALLOWED_TAGS = "a:href,name"

    Additionally, tags can be removed along with their contents, rather than
    simply being stripped, by including them with a - prefix.

        ALLOWED_TAGS = "-script"

    Disallowed tags or attributes are simply removed.
    """
    
    if allowed is None:
        allowed = getattr(settings, "ALLOWED_TAGS",
            "a:href b i ul ol li p br")

    # Parse the configuration string, defining the allowed tags, their allowed
    # attributes and children, and tags which should be stripped along with
    # their contents
    valid_tag_defs = allowed.split()
    valid_tags = {
        '[document]': ([], None),
    }
    remove_tags = set()
    for match in TAG_DEF.finditer(allowed):
        tag_name, allowed_attrs, allowed_children = match.groups()
        if tag_name.startswith('-'):
            remove_tags.add(tag_name[1:])
            continue
        allowed_attrs = allowed_attrs.split(',')
        allowed_children = allowed_children.split(',')
        # SPECIAL CASE: tag:attrs[] means "no children allowed"
        # ommission of the [] at all means "any chidlren allowed"
        # allowed_children = [] if no children are allowed
        # allowed_children is None is no children are restricted
        if tag_name.endswith('[]'):
            allowed_children = []
        elif not allowed_children:
            allowed_children = None
        valid_tags[tag_name] = (allowed_attrs, allowed_children)

    for valid_tag, (valid_attributes, valid_children) in valid_tags.items():
        for valid_child in valid_children or ():
            valid_tags.setdefault(valid_child, ('', None))

    soup = BeautifulSoup(value, convertEntities=BeautifulSoup.HTML_ENTITIES)

    for comment in soup.findAll(
        text=lambda text: isinstance(text, Comment)):
        comment.extract()

    # Walk over the elements, depth-first
    for tag in soup.findAll(True):

        valid_attributes, valid_children = valid_tags.get(tag.name, ([], []))

        # Firstly, remove elements we don't want at all
        if tag.name in remove_tags:
            tag.extract()

        # Hide tags which are not allowed. They will not be rendered,
        # but their contents will be.
        if tag.name not in valid_tags:
            tag.hidden = True
        # Remove attributes on the tag which are not allowed
        else:
            tag.attrs = [(attr, val) for attr, val in tag.attrs
                         if attr in valid_attributes]

        # Is this tag allowed inside of the parent?
        parent = tag.parent
        if tag.name in valid_tags and parent.name in valid_tags:
            parent_children = valid_tags[parent.name][1]
            if parent_children is not None and tag.name not in parent_children:
                # This tag cannot be here
                parent_index = parent.parent.index(parent)
                def tag_siblings():
                    i = parent.index(tag) + 1
                    next_sibling = parent.contents[i]
                    while next_sibling is not None:
                        yield (i - 1, next_sibling)
                        try:
                            i += 1 
                            next_sibling = parent.contents[i]
                        except IndexError:
                            break
                siblings = list(tag_siblings())
                tag.extract()
                parent.parent.insert(parent_index + 1, tag)
                
                # Now we need to move all of our previous siblings into
                # a new container after the repositioned unested tag
                parent.parent.insert(parent_index + 2, _make_tag(parent.name))
                new_container = parent.parent.contents[parent_index + 2]

                for i, sibling in siblings:
                    if isinstance(sibling, NavigableString):
                        parent.contents[i] = u''
                    else:
                        sibling.extract()
                    new_container.contents.insert(i, sibling)

        # Clean up text nodes that might contain markup characters
        _escape_text_nodes(tag)

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
