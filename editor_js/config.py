from django.conf import settings
from django.core.files.storage import default_storage
from django.utils.module_loading import import_string

DEFAULT_EDITOR_JS_TOOLS = {
    'header': {
        'class': 'Header',
        'script': 'https://cdn.jsdelivr.net/npm/@editorjs/header@latest',
    },
    'list': {
        'class': 'EditorjsList',
        'script': 'https://cdn.jsdelivr.net/npm/@editorjs/list@latest',
    },
    'quote': {
        'class': 'Quote',
        'script': 'https://cdn.jsdelivr.net/npm/@editorjs/quote@latest',
    },
    'table': {
        'class': 'Table',
        'script': 'https://cdn.jsdelivr.net/npm/@editorjs/table@latest',
        'config': {
            'inlineToolbar': True,
        }
    },
    'raw': {
        'class': 'RawTool',
        'script': 'https://cdn.jsdelivr.net/npm/@editorjs/raw@latest',
    },
    'embed': {
        'class': 'Embed',
        'script': 'https://cdn.jsdelivr.net/npm/@editorjs/embed@latest',
        'config': {
            'inlineToolbar': True,
        }
    },
    'image': {
        'class': 'ImageTool',
        'script': 'https://cdn.jsdelivr.net/npm/@editorjs/image@latest',
    },
    'button': {
        'class': 'ButtonTool',
        'script': 'editor_js/js/plugins/button-tool.js',
        'static': True,
    },
    'divider': {
        'class': 'DividerTool',
        'script': 'editor_js/js/plugins/divider-tool.js',
        'static': True,
    }
}

def get_editor_js_config():
    """
    Returns the final configuration for Editor.js, merging the library defaults
    with the user's custom settings.
    """
    config = {
        'STORAGE_BACKEND': None,
        'CSS_FILES': ['editor_js/css/editor_js_admin.css',],
        'RENDERER_CLASS': 'editor_js.renderers.EditorJsRenderer',
        'TOOLS': DEFAULT_EDITOR_JS_TOOLS
    }

    user_settings = getattr(settings, 'EDITOR_JS', {})

    if 'TOOLS' in user_settings:
        merged_tools = config['TOOLS'].copy()
        merged_tools.update(user_settings['TOOLS'])
        user_settings['TOOLS'] = merged_tools

    config.update(user_settings)
    
    return config

def get_editor_js_storage():
    """
    Helper function to get the storage class.
    Uses the class specified in settings.EDITOR_JS,
    otherwise falls back to default_storage.
    """
    config = get_editor_js_config()
    storage_path = config.get('STORAGE_BACKEND')

    if storage_path:
        try:
            return import_string(storage_path)()
        except ImportError:
            pass
    return default_storage