# Django Editor.js

[![PyPI version](https://badge.fury.io/py/dj-editor-js.svg)](https://badge.fury.io/py/dj-editor-js)
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

The library comes with the following default tools: **Header**, **List**, **Quote**, **Table**, **Raw HTML**, **Embed**, **Image**, **Button**, and **Divider**.

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
-   **Styling**: To match the editor's appearance with your frontend, provide a path to a custom CSS file in the `CSS_FILE` setting. This file will be loaded inside the editor's iframe.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
