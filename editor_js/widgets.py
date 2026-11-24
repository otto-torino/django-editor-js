import json
from urllib.parse import urlencode

from django import forms
from django.urls import reverse
from django.utils.translation import get_language

class EditorJsIframeWidget(forms.Widget):
    template_name = 'editor_js/admin/widgets/editor_js_widget.html'

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)

        # An empty JSONField is prepared as the literal string "null"
        # (json.dumps(None)). Render an empty textarea instead, so a visually
        # empty editor maps to an empty value rather than a non-empty "null"
        # wrapper. The widget JS already treats an empty value as an empty doc.
        if context['widget']['value'] in (None, 'null', 'None'):
            context['widget']['value'] = ''

        config = context['widget']['attrs'].pop('config', {})

        context['widget']['config_json'] = json.dumps(config)
        # the iframe is another request: tell it the language of this page
        context['widget']['iframe_src'] = (
            f"{reverse('editor_js_iframe')}?{urlencode({'lang': get_language() or ''})}"
        )
        return context

    class Media:
        css = {
            'all': ('editor_js/css/editor_js_widget.css',),
        }
        js = (
            # iframe resizer
            'editor_js/js/vendor/iframe-resizer/iframeResizer.min.js',
            # the widget, which initializes itself
            'editor_js/js/editor_js_widget.js',
            # Django Baton AI bridge: registers an editor adapter on Baton.AI so
            # translation/summarization/correction work on Editor.js fields.
            # No-op (and silent) when django-baton is not installed.
            'editor_js/js/baton_adapter.js',
        )