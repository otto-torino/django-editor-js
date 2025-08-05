Configuration
=============

You can customize the library by adding an ``EDITOR_JS`` dictionary to your ``settings.py``. If you don't provide this, the library will use its sensible defaults.

.. code-block:: python

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
                'static': True,
                'config': {
                    'placeholder': 'Enter your custom text...'
                }
            },
            # Remove a default tool
            'quote': None,
        }
    }
