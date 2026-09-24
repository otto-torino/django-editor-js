# Django Editor.js

[![PyPI version](https://badge.fury.io/py/dj-editor-js.svg)](https://badge.fury.io/py/dj-editor-js)
[![Downloads](https://static.pepy.tech/badge/dj-editor-js)](https://pepy.tech/project/dj-editor-js)
[![Build Status](https://github.com/otto-torino/django-editor-js/actions/workflows/ci.yml/badge.svg)](https://github.com/otto-torino/django-editor-js/actions/workflows/ci.yml)
[![Coverage Status](https://codecov.io/gh/otto-torino/django-editor-js/graph/badge.svg)](https://codecov.io/gh/otto-torino/django-editor-js)

A modern, extensible, and self-contained Django app for integrating the block-style [Editor.js](https://editorjs.io/) into your projects.

This library provides a custom `EditorJSField` for your models and a sandboxed iframe widget for the Django admin, ensuring a clean, conflict-free editing experience. It comes with powerful features like automatic image management, dynamic tool configuration, and a customizable HTML renderer.

## Key Features

-   **Iframe Sandboxing**: The editor is rendered within an `iframe` to prevent CSS and JavaScript conflicts with the Django admin or your site's styles.
-   **Dynamic Tool Configuration**: Configure all Editor.js tools directly from your project's `settings.py`. Add, remove, or override the default toolset, including your own custom-built plugins.
-   **Automatic Image Management**: Integrated image upload endpoint with configurable storage. Automatically deletes unused images from storage when a model instance is updated or deleted.
-   **Extensible HTML Renderer**: A server-side Python class converts the saved JSON data into clean HTML, with methods for each block type that can be easily extended or overridden.
-   **Built-in Template Filter**: Render your content with a simple `{% load ... %}` and filter call, no need to write your own rendering logic.
-   **Sensible Defaults**: Works out-of-the-box with a rich set of common Editor.js tools.
-   **Admin-Friendly UI**: Features include automatic iframe resizing and a fullscreen editing mode for a better user experience.
-   **Baton AI ready**: Zero-config integration with [django-baton](https://github.com/otto-torino/django-baton)'s AI features — translation, summarization and correction work on Editor.js fields (see [Baton AI Integration](#baton-ai-integration)).

---

## Installation

1.  Install the package from PyPI:
    ```bash
    pip install dj-editor-js
    ```

2.  Add `'editor_js'` to your `INSTALLED_APPS` in `settings.py`:
    ```python
    # settings.py
    INSTALLED_APPS = [
        # ...
        'django.contrib.admin',
        'django.contrib.auth',
        # ...
        'editor_js',
    ]
    ```

---

## Configuration

1.  **Include the URLs**: Add the library's URLs to your project's `urls.py`. These are required for the iframe and the image upload endpoint.

    ```python
    # your_project/urls.py
    from django.urls import path, include
    
    urlpatterns = [
        path('admin/', admin.site.urls),
        path('editor-js/', include('editor_js.urls')),
        # ... your other urls
    ]
    ```

2.  **Configure Settings (Optional)**: You can customize the library by adding an `EDITOR_JS` dictionary to your `settings.py`. If you don't provide this, the library will use its sensible defaults.

    ```python
    # settings.py
    EDITOR_JS = {
        # Define a custom storage backend for uploaded images.
        "STORAGE_BACKEND": "app.storage.PrivateMediaStorage",
    
        # Specify the custom CSS files to be loaded inside the editor's iframe.
        "CSS_FILES": ["my_app/css/style.css", "other_app/css/style.css"],
    
        # Specify a custom Python class to render the JSON data to HTML.
        "RENDERER_CLASS": "my_app.renderers.MyCustomRenderer",
    
        # Configure the tools available to the editor.
        "TOOLS": {
            # Add a new custom tool
            'my_custom_tool': {
                'class': 'MyCustomTool',
                'script': 'my_app/js/my-custom-tool.js',
                'static': True, # True if the script is a local static file
                'config': {
                    'placeholder': 'Enter your custom text...'
                }
            },
            # Remove a default tool
            'quote': None,
        }
    }
    ```

---

## Usage

### In Your Models

Use the `EditorJSField` in your models as you would any other Django model field. It stores the editor's content as JSON.

- **To use a custom set of Editor.js tools for a field**, pass a `tools` dictionary to the field.
- **To use the global (default) tool configuration**, define the field without the `tools` argument.

Since EditorJSField inherits from Django's models.JSONField, you can also pass any of its standard attributes, such as `blank=True` or `null=True`.

Example:
```python
# my_app/models.py
from django.db import models
from editor_js.fields import EditorJSField

class Post(models.Model):
    title = models.CharField(max_length=200)

    # This field will only have Header and List tools
    summary = EditorJSField(tools={
        'header': {
            'class': 'Header',
            'script': 'https://cdn.jsdelivr.net/npm/@editorjs/header@latest',
        },
        'list': {
            'class': 'EditorjsList',
            'script': 'https://cdn.jsdelivr.net/npm/@editorjs/list@latest',
        }
    })

    # This field will use the default or global tool configuration
    body = EditorJSField()
    # ...
```

The field will automatically render the iframe widget in the Django admin.

### Editor interactions

- **Add vertical space:** open the block menu with the `+` button and choose **Spacer**. Its block settings let you choose a small, medium, or large gap.
- **Convert blocks:** select two or more consecutive paragraphs and choose **Bulleted list** or **Numbered list**. When a list block is selected, the same toolbar can switch its list style or convert every item back to a normal paragraph. Inline formatting is preserved.

### Rendering Content in Templates

The library includes a built-in template filter to easily render your `EditorJSField` data as HTML.

1.  **Load the filter** in your template:
    ```django
    {% load editor_js_filters %}
    ```

2.  **Apply the filter** to your field's data:
    ```django
    <!-- post_detail.html -->
    {% load editor_js_filters %}
    
    <article>
        <h1>{{ post.title }}</h1>
        <div class="content">
            {{ post.body|render_editor_js }}
        </div>
    </article>
    ```

The filter will automatically use your custom renderer class if you have specified one in your settings.

---

## Demo Application

A fully functional demo application is included to showcase the features of this library. To try it out:

**1. Clone the repository:**
```bash
git clone https://github.com/otto-torino/django-editor-js.git
cd django-editor-js
```

**2. Run the demo:**

- **On Windows:**
    ```cmd
    run_demo.bat
    ```

- **On macOS / Linux:**
    ```bash
    ./run_demo.sh
    ```

This will set up a minimal Django project, create a database, and start the development server so you can explore the editor in action.

---

## Customization

This library is designed to be highly extensible.

### Adding & Removing Tools

You can fully control the tools available in the editor via the `EDITOR_JS['TOOLS']` dictionary in `settings.py`.

-   **To remove a default tool**, set its key to `None`:
    ```python
    "TOOLS": { 'raw': None, 'table': None }
    ```

-   **To add a new tool**, add a new key with its configuration:
    ```python
    "TOOLS": {
        'my_checklist': {
            'class': 'Checklist', # The JS class name
            'script': '[https://cdn.jsdelivr.net/npm/@editorjs/checklist@latest](https://cdn.jsdelivr.net/npm/@editorjs/checklist@latest)', # URL or static path
            'static': False, # Is it a local static file?
        }
    }
    ```

The library comes with the following default tools: **Header**, **List**, **Quote**, **Table**, **Raw HTML**, **Embed**, **Image**, **Button**, **Divider**, and **Spacer**.

### Inline Toolbar

The Editor.js inline toolbar (bold, italic, link, ...) is **enabled by default for every tool**, including custom ones. To disable it for a specific tool — or to restrict which actions it offers — set `inlineToolbar` in the tool's configuration:

```python
"TOOLS": {
    # Disable the inline toolbar for headers
    'header': {
        'class': 'Header',
        'script': 'editor_js/js/vendor/editorjs/header.min.js',
        'static': True,
        'inlineToolbar': False,
    },
    # Only allow bold and link inside lists
    'list': {
        'class': 'EditorjsList',
        'script': 'editor_js/js/vendor/editorjs/list.min.js',
        'static': True,
        'inlineToolbar': ['bold', 'link'],
    },
}
```

### Bundled inline tools

Besides the native bold and italic, the library bundles three inline tools:

-   **`link`** — replaces the native Editor.js link tool, adding an **"Open in new tab"** checkbox: when checked, the anchor is saved with `target="_blank"` and `rel="noopener noreferrer"`. Same icons and behavior as the native tool otherwise.
-   **`marker`** — highlights the selection, wrapping it in `<mark class="cdx-marker">`.
-   **`fontSize`** — applies a preset size (Small, Normal, Large, Huge) to the selection via `<span class="cdx-font-size" style="font-size: ...">`.

They are used everywhere by default — including fields that define their own per-field `tools` — unless a configuration addresses the tool's key itself: set `'link'`, `'marker'` or `'fontSize'` to `None` (in `EDITOR_JS['TOOLS']` or in a per-field `tools` dict) to remove it, or override it with your own tool like any other.

### Custom HTML Rendering

If you add a custom tool, you'll need to tell Django how to render it.

1.  Subclass the provided `EditorJsRenderer` and add a `render_my_tool_name` method.
2.  Update `settings.py` to point to your new class.

```python
# my_app/renderers.py
from editor_js.renderers import EditorJsRenderer

class MyCustomRenderer(EditorJsRenderer):
    def render_my_custom_tool(self, data):
        # Logic to convert the tool's data to HTML
        items = data.get('items', [])
        html = "<ul>"
        for item in items:
            checked = 'checked' if item.get('checked') else ''
            text = self.escape(item.get('text', ''))
            html += f'<li><input type="checkbox" {checked} disabled> {text}</li>'
        html += "</ul>"
        return html

# settings.py
EDITOR_JS = {
    "RENDERER_CLASS": "my_app.renderers.MyCustomRenderer",
    # ...
}
```

### Custom Storage & Styling

-   **Storage**: To use a different storage system (like Amazon S3), set the `STORAGE_BACKEND` setting to the dotted path of your storage class (e.g., `'storages.backends.s3boto3.S3Boto3Storage'`).
-   **Styling**: To match the editor's appearance with your frontend, provide a list of paths to your custom CSS files in the `CSS_FILES` setting. These files will be loaded in the specified order inside the editor's iframe.

## Baton AI Integration

If you use [`django-baton`](https://github.com/otto-torino/django-baton) (>= 5.2) as your admin theme, this library integrates with **Baton AI out of the box — no configuration required**. Translation, summarization and correction work on your `EditorJSField`s, alongside CKEditor and native fields on the same form.

### How it works

The widget ships a small adapter (`editor_js/js/baton_adapter.js`) that is loaded automatically via the widget's `Media` and **self-registers** on `Baton.AI`. It bridges the two data models:

-   **Reading** — Editor.js block JSON is converted to HTML so the AI receives clean prose.
-   **Writing** — the AI's HTML result is converted back into Editor.js blocks and re-rendered inside the iframe editor.

When Baton is not installed the adapter is a silent no-op, so it is always safe to ship.

### Setup

Install both apps and configure your Baton AI credentials (see Baton's docs for obtaining them):

```python
# settings.py
INSTALLED_APPS = [
    "baton",
    "editor_js",
    # ...
    "baton.autodiscover",
]

BATON = {
    "BATON_CLIENT_ID": os.getenv("BATON_CLIENT_ID"),
    "BATON_CLIENT_SECRET": os.getenv("BATON_CLIENT_SECRET"),
    "AI": {
        "ENABLE_TRANSLATIONS": True,
        "ENABLE_CORRECTIONS": True,
    },
}
```

Then use an `EditorJSField` as usual. For **translation**, make it translatable with `django-modeltranslation`; for **summarization**, point Baton's `baton_summarize_fields` at it as a source and/or target. The AI buttons appear automatically.

> **Note on non-text blocks.** Translation and summarization send only text-bearing blocks (paragraph, header, list, quote, code) to the AI. Media-like blocks (image, table, embed, button, divider) carry no translatable prose and are not part of the round-trip — keep this in mind when running in-place **correction** on a field that mixes prose and media, as the rewritten content is rebuilt from the text blocks.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
