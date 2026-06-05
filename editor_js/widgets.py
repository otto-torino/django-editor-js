import json
from django import forms
from django.urls import reverse

class EditorJsIframeWidget(forms.Widget):
    template_name = 'editor_js/admin/widgets/editor_js_widget.html'

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)

        config = context['widget']['attrs'].pop('config', {})

        context['widget']['config_json'] = json.dumps(config)
        context['widget']['iframe_src'] = reverse('editor_js_iframe')
        return context

    class Media:
        js = (
            # iframe resizer
            'https://cdnjs.cloudflare.com/ajax/libs/iframe-resizer/4.3.9/iframeResizer.min.js',
            # Django Baton AI bridge: registers an editor adapter on Baton.AI so
            # translation/summarization/correction work on Editor.js fields.
            # No-op (and silent) when django-baton is not installed.
            'editor_js/js/baton_adapter.js',
        )