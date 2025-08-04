from django import template
from django.conf import settings
from django.utils.module_loading import import_string
from django.utils.safestring import mark_safe

from ..renderers import EditorJsRenderer

register = template.Library()

def get_renderer_class():
    """
    Reads the path to the renderer class from settings,
    otherwise returns our default class.
    """
    editor_js_settings = getattr(settings, 'EDITOR_JS', {})    
    path = editor_js_settings.get('RENDERER_CLASS', None)

    if path:
        try:
            return import_string(path)
        except ImportError:
            pass
    return EditorJsRenderer

@register.filter(name='render_editor_js')
def editor_js(value):
    """
    Filter that renders the Editor.js JSON using the class specified
    in the settings or the default class.
    """
    if not value:
        return ""
    
    Renderer = get_renderer_class()
    renderer_instance = Renderer(value)
    
    return mark_safe(renderer_instance.render())
