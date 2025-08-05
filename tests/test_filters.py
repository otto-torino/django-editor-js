from django.test import TestCase, override_settings
from django.utils.safestring import SafeString

from editor_js.templatetags.editor_js_filters import get_renderer_class, editor_js as render_editor_js_filter
from editor_js.renderers import EditorJsRenderer

class DummyRenderer:
    def __init__(self, data):
        self.data = data
    def render(self):
        return "CUSTOM RENDERER OUTPUT"

class TemplateTagsTest(TestCase):

    def test_get_renderer_class_default(self):
        """
        Checks that the default renderer class is returned if there are no settings.
        """
        Renderer = get_renderer_class()
        self.assertIs(Renderer, EditorJsRenderer)

    def test_get_renderer_class_with_valid_custom_path(self):
        """
        Checks that the custom renderer class is returned if the path in settings is valid.
        """
        dummy_renderer_path = f'{self.__class__.__module__}.{DummyRenderer.__name__}'
        
        with override_settings(EDITOR_JS={'RENDERER_CLASS': dummy_renderer_path}):
            Renderer = get_renderer_class()
            self.assertIs(Renderer, DummyRenderer)

    @override_settings(EDITOR_JS={'RENDERER_CLASS': 'path.to.non.existent.Class'})
    def test_get_renderer_class_with_invalid_custom_path(self):
        """
        Checks that the default renderer class is returned if the custom path is invalid.
        """
        Renderer = get_renderer_class()
        self.assertIs(Renderer, EditorJsRenderer)

    def test_filter_with_empty_value(self):
        """
        Checks that the filter returns an empty string if the value is null.
        """
        self.assertEqual(render_editor_js_filter(None), "")
        self.assertEqual(render_editor_js_filter(""), "")

    def test_filter_with_valid_value_and_default_renderer(self):
        """
        Checks the default behavior of the filter with valid data.
        """
        data = {
            "blocks": [{"type": "paragraph", "data": {"text": "Hello"}}]
        }
        result = render_editor_js_filter(data)
        self.assertEqual(result, "<p>Hello</p>")
        self.assertIsInstance(result, SafeString)

    def test_filter_uses_custom_renderer_from_settings(self):
        """
        Checks that the filter correctly uses the custom renderer class defined in settings.
        """
        data = {
            "blocks": [{"type": "paragraph", "data": {"text": "Hello"}}]
        }
        
        dummy_renderer_path = f'{self.__class__.__module__}.{DummyRenderer.__name__}'

        with override_settings(EDITOR_JS={'RENDERER_CLASS': dummy_renderer_path}):
            result = render_editor_js_filter(data)
            self.assertEqual(result, "CUSTOM RENDERER OUTPUT")
