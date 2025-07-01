import unittest

from email_tools_py import _rename_body_to_blockquote, quote_html


class TestEmailStuff(unittest.TestCase):
    def test_quote_html_with_body(self):
        received = """
<html><head>
<style>
body > div { color: red; }
p { font-size: 12px; }
</style>
</head><body ID="b" Class="main">the <p>Original content</p></body></html>
"""
        added = "New content"
        expected = """
<html>
 <head>
  <style>
   div#quoted_email > div { color: red; }
p { font-size: 12px; }
  </style>
 </head>
 <body>
  New content
  <div class="main" id="quoted_email">
   the
   <p>
    Original content
   </p>
  </div>
 </body>
</html>
"""
        result = quote_html(received, added)
        self.assertEqual(result.strip(), expected.strip())

    def test_quote_html_without_body(self):
        received = "<p>Original content</p>"
        added = "New content"
        expected = """
<html>
 <head>
  <style>
  </style>
 </head>
 <body>
  New content
  <div id="quoted_email">
   <p>
    Original content
   </p>
  </div>
 </body>
</html>
"""
        result = quote_html(received, added)
        self.assertEqual(result.strip(), expected.strip())

    def test_quote_html_body_no_head(self):
        received = "<html><body><p>Original content</p></body></html>"
        added = "New content"
        expected = """
<html>
 <body>
  New content
  <div id="quoted_email">
   <p>
    Original content
   </p>
  </div>
 </body>
</html>
"""
        result = quote_html(received, added)
        self.assertEqual(result.strip(), expected.strip())

    def test_quote_html_bare_body(self):
        received = "<BODY><p>Original content</p></BODY>"
        added = "New content"
        expected = """
<body>
 New content
 <div id="quoted_email">
  <p>
   Original content
  </p>
 </div>
</body>
"""
        result = quote_html(received, added)
        self.assertEqual(result.strip(), expected.strip())


class TestRenameBodyToBlockquote(unittest.TestCase):
    def test_simple_body_selector(self):
        css = "body { color: red; }"
        expected = "div#quoted_email { color: red; }"
        result = _rename_body_to_blockquote(css)
        self.assertEqual(result.strip(), expected)

    def test_compound_selector(self):
        css = "body.main { color: blue; } p { font-size: 12px; }"
        expected = (
            "div#quoted_email.main { color: blue; } p { font-size: 12px; }"
        )
        result = _rename_body_to_blockquote(css)
        self.assertEqual(result.strip(), expected)

    def test_multiple_body_selectors(self):
        css = (
            "body { margin: 0; } div { padding: 10px; } body { color: green; }"
        )
        expected = "div#quoted_email { margin: 0; } div { padding: 10px; } div#quoted_email { color: green; }"
        result = _rename_body_to_blockquote(css)
        self.assertEqual(result.strip(), expected)

    def test_body_with_existing_id(self):
        css = "body#content { background: white; }"
        expected = "div#quoted_email { background: white; }"
        result = _rename_body_to_blockquote(css)
        self.assertEqual(result.strip(), expected)

    def test_empty_css(self):
        css = ""
        expected = ""
        result = _rename_body_to_blockquote(css)
        self.assertEqual(result.strip(), expected)

    def test_no_body_selector(self):
        css = "div { color: red; } p { font-size: 12px; }"
        expected = "div { color: red; } p { font-size: 12px; }"
        result = _rename_body_to_blockquote(css)
        self.assertEqual(result.strip(), expected)

    def test_media_query(self):
        css = "@media screen { body { color: blue; } p { font-size: 12px; } }"
        expected = "@media screen { div#quoted_email { color: blue; } p { font-size: 12px; } }"
        result = _rename_body_to_blockquote(css)
        self.assertEqual(result.strip(), expected)

    def test_supports_rule(self):
        css = "@supports (display: grid) { body { display: grid; } }"
        expected = "@supports (display: grid) { div#quoted_email { display: grid; } }"
        result = _rename_body_to_blockquote(css)
        self.assertEqual(result.strip(), expected)

    def test_multiple_at_rules(self):
        css = """
        @media screen { body { color: blue; } }
        @supports (display: flex) { body { display: flex; } }
        """
        expected = """
        @media screen { div#quoted_email { color: blue; } }
        @supports (display: flex) { div#quoted_email { display: flex; } }
        """
        result = _rename_body_to_blockquote(css)
        self.assertEqual(result.strip(), expected.strip())

    def test_nested_at_rules(self):
        css = "@media screen { @supports (display: grid) { body { display: grid; } } }"
        # Function doesn't handle nested at-rules, should return original CSS
        expected = "@media screen { @supports (display: grid) { body { display: grid; } } }"
        result = _rename_body_to_blockquote(css)
        self.assertEqual(result.strip(), expected)

    def test_supports_rule_empty(self):
        css = "@supports (display: grid);"
        expected = "@supports (display: grid);"
        result = _rename_body_to_blockquote(css)
        self.assertEqual(result.strip(), expected)
