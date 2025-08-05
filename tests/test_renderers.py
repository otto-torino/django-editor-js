import html

from django.test import TestCase
from editor_js.renderers import EditorJsRenderer

class RendererTest(TestCase):
    def test_init_with_dict(self):
        """Tests initialization with a Python dictionary."""
        data = {"blocks": []}
        try:
            EditorJsRenderer(data)
        except ValueError:
            self.fail("EditorJsRenderer unexpectedly raised ValueError with a dict.")

    def test_init_with_valid_json_string(self):
        """Tests initialization with a valid JSON string."""
        data_str = '{"blocks": []}'
        try:
            EditorJsRenderer(data_str)
        except ValueError:
            self.fail("EditorJsRenderer unexpectedly raised ValueError with a valid JSON string.")

    def test_init_with_invalid_json_string(self):
        """Tests that an invalid JSON string raises a ValueError."""
        invalid_data_str = '{"blocks": [}'
        with self.assertRaisesRegex(ValueError, "invalid JSON string"):
            EditorJsRenderer(invalid_data_str)

    def test_init_with_invalid_type(self):
        """Tests that an invalid data type (e.g., int) raises a ValueError."""
        with self.assertRaisesRegex(ValueError, "must be a dict or JSON string"):
            EditorJsRenderer(123)

    def test_render_with_no_blocks_key(self):
        """Tests that rendering data without 'blocks' key returns an empty string."""
        data = {"time": 1678886400, "version": "2.26.5"}
        renderer = EditorJsRenderer(data)
        self.assertEqual(renderer.render(), "")
    
    def test_render_paragraph(self):
        data = {
            "blocks": [
                {"type": "paragraph", "data": {"text": "Hello world"}}
            ]
        }
        renderer = EditorJsRenderer(data)
        html = renderer.render()
        self.assertEqual(html, "<p>Hello world</p>")

    def test_render_header(self):
        data = {
            "blocks": [
                {"type": "header", "data": {"text": "Title", "level": 2}}
            ]
        }
        renderer = EditorJsRenderer(data)
        html = renderer.render()
        self.assertEqual(html, "<h2>Title</h2>")

    def test_render_button(self):
        data = {
            "blocks": [
                {
                    "type": "button",
                    "data": {
                        "text": "Click me",
                        "url": "https://example.com",
                        "btnColor": "btn-primary",
                        "alignment": "center"
                    }
                }
            ]
        }
        renderer = EditorJsRenderer(data)
        html = renderer.render()
        expected_html = (
            '<div style="text-align: center;">'
            '<a href="https://example.com" class="btn btn-primary">Click me</a>'
            '</div>'
        )
        self.assertEqual(html, expected_html)

    def test_render_unknown_block(self):
        data = {
            "blocks": [
                {"type": "unknownBlock", "data": {}}
            ]
        }
        renderer = EditorJsRenderer(data)
        html = renderer.render()
        self.assertEqual(html, "<!-- Unsupported block type -->")

    def test_render_header(self):
        data = {"blocks": [{"type": "header", "data": {"text": "Title", "level": 1}}]}
        renderer = EditorJsRenderer(data)
        self.assertEqual(renderer.render(), "<h1>Title</h1>")

    def test_render_simple_list(self):
        """Tests a simple list (ordered and unordered)."""
        # Unordered list
        data_ul = {"blocks": [{"type": "list", "data": {"style": "unordered", "items": ["One", "Two"]}}]}
        renderer_ul = EditorJsRenderer(data_ul)
        self.assertEqual(renderer_ul.render(), "<ul><li>One</li><li>Two</li></ul>")
        
        # Ordered list
        data_ol = {"blocks": [{"type": "list", "data": {"style": "ordered", "items": ["One", "Two"]}}]}
        renderer_ol = EditorJsRenderer(data_ol)
        self.assertEqual(renderer_ol.render(), "<ol><li>One</li><li>Two</li></ol>")

    def test_render_nested_list(self):
        """Tests a list with nested items."""
        data = {
            "blocks": [{
                "type": "list",
                "data": {
                    "style": "unordered",
                    "items": [
                        "Item 1",
                        {
                            "content": "Item 2 with sublist",
                            "items": [ "Sub-item 1", "Sub-item 2" ]
                        }
                    ]
                }
            }]
        }
        renderer = EditorJsRenderer(data)
        expected_html = "<ul><li>Item 1</li><li>Item 2 with sublist<ul><li>Sub-item 1</li><li>Sub-item 2</li></ul></li></ul>"
        self.assertEqual(renderer.render(), expected_html)

    def test_render_quote(self):
        data = {"blocks": [{"type": "quote", "data": {"text": "The quote", "caption": "The author", "alignment": "center"}}]}
        renderer = EditorJsRenderer(data)
        self.assertIn('<blockquote style="text-align: center;">', renderer.render())
        self.assertIn("<p>The quote</p>", renderer.render())
        self.assertIn("<footer>The author</footer>", renderer.render())

    def test_render_code(self):
        code_content = 'let x = "<script>";'
        data = {"blocks": [{"type": "code", "data": {"code": code_content}}]}
        renderer = EditorJsRenderer(data)
        # Verify that the content is escaped
        self.assertEqual(renderer.render(), f"<pre><code>{html.escape(code_content)}</code></pre>")

    def test_render_image(self):
        data = {"blocks": [{"type": "image", "data": {"file": {"url": "/media/image.jpg"}, "caption": "My caption"}}]}
        renderer = EditorJsRenderer(data)
        self.assertEqual(renderer.render(), '<figure><img src="/media/image.jpg" alt="My caption"><figcaption>My caption</figcaption></figure>')

    def test_render_table(self):
        """Tests table rendering, with and without header."""
        # Table without header
        data_no_header = {"blocks": [{"type": "table", "data": {"withHeadings": False, "content": [["A", "B"], ["C", "D"]]}}]}
        renderer_no_header = EditorJsRenderer(data_no_header)
        expected_no_header = "<table><tbody><tr><td>A</td><td>B</td></tr><tr><td>C</td><td>D</td></tr></tbody></table>"
        self.assertEqual(renderer_no_header.render(), expected_no_header)
        
        # Table with header
        data_with_header = {"blocks": [{"type": "table", "data": {"withHeadings": True, "content": [["H1", "H2"], ["A", "B"]]}}]}
        renderer_with_header = EditorJsRenderer(data_with_header)
        self.assertIn("<thead><tr><th>H1</th><th>H2</th></tr></thead>", renderer_with_header.render())
        self.assertIn("<tbody><tr><td>A</td><td>B</td></tr></tbody>", renderer_with_header.render())

    def test_render_raw_html(self):
        """Tests the raw block, which should not be escaped."""
        raw_content = '<div class="custom"><b>Bold</b></div>'
        data = {"blocks": [{"type": "raw", "data": {"html": raw_content}}]}
        renderer = EditorJsRenderer(data)
        self.assertEqual(renderer.render(), raw_content)

    def test_render_embed(self):
        """Tests the embed block."""
        data = {"blocks": [{"type": "embed", "data": {"service": "youtube", "embed": "https://youtube.com/embed/123", "caption": "Video"}}]}
        renderer = EditorJsRenderer(data)
        self.assertIn('<iframe src="https://youtube.com/embed/123"', renderer.render())
        self.assertIn("<figcaption>Video</figcaption>", renderer.render())
        
        # Test with empty embed
        data_empty = {"blocks": [{"type": "embed", "data": {}}]}
        renderer_empty = EditorJsRenderer(data_empty)
        self.assertEqual(renderer_empty.render(), "")

    def test_render_divider(self):
        data = {"blocks": [{"type": "divider", "data": {}}]}
        renderer = EditorJsRenderer(data)
        self.assertEqual(renderer.render(), "<hr>")

    def test_render_with_safe_false(self):
        """Tests that with safe=False, HTML is not escaped."""
        data = {"blocks": [{"type": "header", "data": {"text": "<b>Bold Title</b>", "level": 2}}]}
        # Note `safe=False`
        renderer = EditorJsRenderer(data, safe=False)
        self.assertEqual(renderer.render(), "<h2><b>Bold Title</b></h2>")

    def test_render_empty_table(self):
        """Tests the rendering of an empty table."""
        data = {
            "blocks": [
                {
                    "type": "table",
                    "data": {
                        "withHeadings": False,
                        "content": []
                    }
                }
            ]
        }
        renderer = EditorJsRenderer(data)
        self.assertEqual(renderer.render(), "<table></table>")

