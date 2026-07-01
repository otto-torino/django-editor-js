import json
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
        Checks that the Media class correctly defines JavaScript assets.
        """
        widget = EditorJsIframeWidget()
        media = widget.media

        self.assertIn(
            'editor_js/js/vendor/iframe-resizer/iframeResizer.min.js',
            media._js
        )
        self.assertIn('editor_js/js/baton_adapter.js', media._js)

    def test_fullscreen_button_uses_themeable_styles(self):
        """
        The fullscreen button should follow admin theme colors instead of using
        fixed inline colors, so dark mode can style the icon correctly.
        """
        widget = EditorJsIframeWidget()
        html = widget.render(name='content', value='', attrs={})

        self.assertIn('class="editor-js-fullscreen-button"', html)
        self.assertIn('color: var(--body-fg, #333);', html)
        self.assertIn('background-color: var(--darkened-bg, #f0f0f0);', html)
        self.assertNotIn('background-color: #f0f0f0', html)
