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

    def test_media_assets(self):
        """
        Checks that the Media class correctly defines JavaScript assets.
        """
        widget = EditorJsIframeWidget()
        media = widget.media

        self.assertIn(
            'https://cdnjs.cloudflare.com/ajax/libs/iframe-resizer/4.3.9/iframeResizer.min.js',
            media._js
        )