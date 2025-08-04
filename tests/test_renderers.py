from django.test import TestCase
from editor_js.renderers import EditorJsRenderer

class RendererTest(TestCase):
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
