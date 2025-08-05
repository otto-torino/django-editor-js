from django.test import TestCase, override_settings
from django.core.files.storage import FileSystemStorage, default_storage
from editor_js.config import get_editor_js_config, get_editor_js_storage

class ConfigTestCase(TestCase):
    @override_settings(EDITOR_JS={
        'TOOLS': {
            'header': {
                'class': 'MyCustomHeader',
                'script': 'path/to/my/custom/header.js'
            },
            'alert': {
                'class': 'AlertTool',
                'script': 'path/to/alert.js'
            }
        }
    })
    def test_get_editor_js_config_with_custom_tools(self):
        config = get_editor_js_config()
        tools = config.get('TOOLS')

        self.assertIn('alert', tools)
        self.assertEqual(tools['alert']['class'], 'AlertTool')

        self.assertIn('header', tools)
        self.assertEqual(tools['header']['class'], 'MyCustomHeader')

        self.assertIn('list', tools)
        self.assertEqual(tools['list']['class'], 'EditorjsList')


class StorageTestCase(TestCase):
    @override_settings(EDITOR_JS={
        'STORAGE_BACKEND': 'django.core.files.storage.FileSystemStorage'
    })
    def test_get_editor_js_storage_with_valid_custom_backend(self):
        storage_instance = get_editor_js_storage()
        self.assertIsInstance(storage_instance, FileSystemStorage)
        self.assertIsNot(storage_instance, default_storage)

    @override_settings(EDITOR_JS={
        'STORAGE_BACKEND': 'path.to.non.existent.StorageClass'
    })
    def test_get_editor_js_storage_with_invalid_custom_backend(self):
        storage_instance = get_editor_js_storage()
        self.assertIs(storage_instance, default_storage)
