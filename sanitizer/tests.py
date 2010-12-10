"""
This file demonstrates two different styles of tests (one doctest and one
unittest). These will both pass when you run "manage.py test".

Replace these with more appropriate tests for your application.
"""

from django.test import TestCase


from sanitizer.templatetags.sanitizer import allowtags

class SanitizerTest(TestCase):

    def test_remove_not_allowed(self):

        cleaned = allowtags("<a></a><b></b>", "a")
        self.assertEqual(cleaned, "<a></a>")

    def test_remove_nested_not_allowed(self):
    
        cleaned = allowtags("<a><b></b></a>", "a")
        self.assertEqual(cleaned, "<a></a>")

    def test_remove_outer_not_allowed(self):
    
        cleaned = allowtags("<a><b></b></a>", "b")
        self.assertEqual(cleaned, "<b></b>")

    def test_allow_multiple(self):
    
        cleaned = allowtags("<a></a><b></b><c></c>", "a c")
        self.assertEqual(cleaned, "<a></a><c></c>")

    def test_allow_specific_attribute(self):
    
        cleaned = allowtags('<a b="x" c="y"></a>', "a:b")
        self.assertEqual(cleaned, '<a b="x"></a>')

    def test_distinguish_attribute_allowances(self):
    
        cleaned = allowtags('<a b="x" c="y"></a><d b="x" c="y"></d>', "a:b d:c")
        self.assertEqual(cleaned, '<a b="x"></a><d c="y"></d>')

    def test_keep_contents_of_disallowed(self):
    
        cleaned = allowtags("<blink>test</blink>", "")
        self.assertEqual(cleaned, 'test')

    def test_unclosed_disallowed_removed(self):

        cleaned = allowtags("<b>test", "a")
        self.assertEqual(cleaned, 'test')

    def test_unclosed_trailing_disallowed_removed(self):
    
        cleaned = allowtags("<b>test<b>", "a")
        self.assertEqual(cleaned, "test")

    def test_dirty_tricks(self):
        
        self.assertEqual(
            allowtags('<<script></script>script>test<<script></script>script>'),
            '&lt;script&gt;test&lt;script&gt;')
