import json
from pathlib import Path

import editor_js
from django.test import TestCase
from django.urls import reverse

from editor_js.widgets import EditorJsIframeWidget

class WidgetTest(TestCase):

    def test_get_context_default(self):
        """
        Test get_context without a custom configuration.
        Checks that 'config_json' is an empty JSON object.
        """
        widget = EditorJsIframeWidget()
        context = widget.get_context(name='content', value='', attrs=None)

        self.assertIn('config_json', context['widget'])
        self.assertEqual(context['widget']['config_json'], '{}')

        self.assertIn('iframe_src', context['widget'])
        self.assertEqual(context['widget']['iframe_src'], reverse('editor_js_iframe'))

    def test_get_context_with_custom_config(self):
        """
        Test get_context with a custom configuration passed via attributes.
        Checks that the configuration is extracted, converted to JSON, and removed from attributes.
        """
        custom_config = {
            'tools': {
                'header': {'class': 'MyCustomHeader'},
                'list': {'class': 'MyCustomList'}
            }
        }
        
        attrs = {'config': custom_config}
        widget = EditorJsIframeWidget()
        context = widget.get_context(name='content', value='', attrs=attrs)

        self.assertIn('config_json', context['widget'])
        self.assertEqual(context['widget']['config_json'], json.dumps(custom_config))

        self.assertNotIn('config', context['widget']['attrs'])

        self.assertEqual(context['widget']['iframe_src'], reverse('editor_js_iframe'))

    def test_get_context_normalizes_empty_values(self):
        """
        An empty JSONField is prepared as None or the literal string "null".
        get_context should normalize these to an empty string so a visually
        empty editor maps to an empty value rather than a "null" wrapper.
        """
        widget = EditorJsIframeWidget()

        for empty_value in (None, 'null', 'None'):
            context = widget.get_context(name='content', value=empty_value, attrs=None)
            self.assertEqual(
                context['widget']['value'], '',
                msg=f'value {empty_value!r} should be normalized to an empty string',
            )

    def test_get_context_preserves_non_empty_value(self):
        """
        A real document value must be passed through unchanged.
        """
        widget = EditorJsIframeWidget()
        value = '{"blocks": []}'
        context = widget.get_context(name='content', value=value, attrs=None)
        self.assertEqual(context['widget']['value'], value)

    def test_media_assets(self):
        """
        Checks that the Media class correctly defines the widget assets.
        """
        widget = EditorJsIframeWidget()
        media = widget.media

        self.assertIn(
            'editor_js/js/vendor/iframe-resizer/iframeResizer.min.js',
            media._js
        )
        self.assertIn('editor_js/js/editor_js_widget.js', media._js)
        self.assertIn('editor_js/js/baton_adapter.js', media._js)
        self.assertIn('editor_js/css/editor_js_widget.css', media._css['all'])

    def test_render_has_no_inline_style_or_script(self):
        """
        Style and initialization come from the Media: inline ones would need the
        nonce of a Content Security Policy, which widgets cannot know.
        """
        widget = EditorJsIframeWidget()
        html = widget.render(name='content', value='', attrs={})

        self.assertNotIn('<style', html)
        self.assertNotIn('<script', html)

    def test_fullscreen_button_uses_themeable_styles(self):
        """
        The fullscreen button should follow admin theme colors instead of using
        fixed inline colors, so dark mode can style the icon correctly.
        """
        widget = EditorJsIframeWidget()
        html = widget.render(name='content', value='', attrs={})
        css_path = Path(editor_js.__file__).parent / 'static/editor_js/css/editor_js_widget.css'
        css = css_path.read_text()

        self.assertIn('class="editor-js-fullscreen-button"', html)
        self.assertIn('color: var(--body-fg, #333);', css)
        self.assertIn('background-color: var(--darkened-bg, #f0f0f0);', css)
        self.assertNotIn('background-color: #f0f0f0', css)


class VendorScriptsTest(TestCase):

    def test_vendor_scripts_need_no_eval(self):
        """
        No vendored script builds code from strings: a Content Security Policy
        without 'unsafe-eval' would report it. The image tool is patched.
        """
        vendor = Path(editor_js.__file__).parent / 'static/editor_js/js/vendor/editorjs'
        for script in vendor.glob('*.js'):
            with self.subTest(script=script.name):
                self.assertNotIn('new Function("return this")', script.read_text())

