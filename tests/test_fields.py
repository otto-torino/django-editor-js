import os
import shutil
from unittest import mock

from django.test import TestCase, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.files.storage import default_storage
from editor_js.fields import EditorJSField
from editor_js.widgets import EditorJsIframeWidget
from .test_app.models import Post

TEST_MEDIA_ROOT = os.path.join(os.path.dirname(__file__), 'test_media')

@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class FieldsTest(TestCase):
    
    def setUp(self):
        """
        Creates a temporary media directory before each test.
        """
        os.makedirs(TEST_MEDIA_ROOT, exist_ok=True)
        default_storage.base_url = '/media/'

    def tearDown(self):
        """
        Removes the temporary media directory and its contents after each test.
        """
        if os.path.exists(TEST_MEDIA_ROOT):
            shutil.rmtree(TEST_MEDIA_ROOT)

    def _create_dummy_image(self, name='test_image.jpg'):
        """
        Creates a dummy image file and saves it to the test storage.
        """
        image = SimpleUploadedFile(name, b"file_content", content_type="image/jpeg")
        file_path = default_storage.save(f'editor_js/{name}', image)
        return default_storage.url(file_path)

    def test_image_url_extraction(self):
        """
        Tests that the _extract_image_urls method correctly extracts URLs.
        """
        image_url = self._create_dummy_image()
        data = {
            "blocks": [
                {"type": "paragraph", "data": {"text": "Hello"}},
                {"type": "image", "data": {"file": {"url": image_url}, "caption": "Test"}}
            ]
        }
        post = Post(content=data)
        field = post._meta.get_field('content')
        extracted_urls = field._extract_image_urls(post.content)
        
        self.assertEqual(len(extracted_urls), 1)
        self.assertIn(image_url, extracted_urls)

    def test_orphan_image_deletion_on_save(self):
        """
        Tests that unused images are deleted from storage upon saving.
        """
        image_url_to_delete = self._create_dummy_image('image_to_delete.jpg')
        relative_path_to_delete = image_url_to_delete.replace(default_storage.base_url, '')

        post = Post.objects.create(content={
            "blocks": [
                {"type": "image", "data": {"file": {"url": image_url_to_delete}}}
            ]
        })
        
        self.assertTrue(default_storage.exists(relative_path_to_delete))

        new_image_url = self._create_dummy_image('new_image.jpg')
        post.content = {
            "blocks": [
                {"type": "image", "data": {"file": {"url": new_image_url}}}
            ]
        }
        post.save()

        self.assertFalse(default_storage.exists(relative_path_to_delete))
        
        relative_path_new = new_image_url.replace(default_storage.base_url, '')
        self.assertTrue(default_storage.exists(relative_path_new))

    def test_image_deletion_on_instance_delete(self):
        """
        Tests that images are deleted when the model instance is deleted.
        """
        image_url = self._create_dummy_image('image_to_be_deleted_with_post.jpg')
        relative_path = image_url.replace(default_storage.base_url, '')
        
        post = Post.objects.create(content={
            "blocks": [
                {"type": "image", "data": {"file": {"url": image_url}}}
            ]
        })
        
        self.assertTrue(default_storage.exists(relative_path))

        post.delete()

        self.assertFalse(default_storage.exists(relative_path))


    def test_delete_instance_with_empty_data(self):
        """
        Tests that the delete signal correctly handles empty data.
        """
        # Create a post with content=None and then delete it
        post = Post.objects.create(content=None)
        # The assertion is that the code does not raise an error
        try:
            post.delete()
        except Exception as e:
            self.fail(f"Deletion with empty data raised an exception: {e}")

    @mock.patch('editor_js.fields.get_editor_js_storage')
    def test_delete_instance_with_storage_without_base_url(self, mock_get_storage):
        """
        Tests that the delete signal does nothing if the storage has no base_url.
        """
        # Configure the mock storage to not have 'base_url'
        mock_storage = mock.MagicMock()
        del mock_storage.base_url  # Remove the attribute
        mock_get_storage.return_value = mock_storage
        
        image_url = self._create_dummy_image()
        post = Post.objects.create(content={"blocks": [{"type": "image", "data": {"file": {"url": image_url}}}]})
        
        post.delete()
        
        # Verify that the storage's delete method was NOT called
        mock_storage.delete.assert_not_called()

    def test_delete_instance_with_external_image_url(self):
        """
        Tests that the delete signal ignores external URLs.
        This covers the branch `if url.startswith(base_url):` when it is False.
        """
        external_url = "https://cdn.example.com/image.jpg"
        post = Post.objects.create(content={"blocks": [{"type": "image", "data": {"file": {"url": external_url}}}]})
        
        # The assertion is that no errors are raised and no local file is touched
        try:
            post.delete()
        except Exception as e:
            self.fail(f"Deletion with external URL raised an exception: {e}")

    def test_delete_non_existent_image_on_instance_delete(self):
        """
        Tests that deletion handles the case where the file no longer exists.
        This covers the branch `if storage.exists(decoded_path):` when it is False.
        """
        image_url = self._create_dummy_image('image_that_will_vanish.jpg')
        relative_path = image_url.replace(default_storage.base_url, '')
        
        post = Post.objects.create(content={"blocks": [{"type": "image", "data": {"file": {"url": image_url}}}]})
        
        # The file exists
        self.assertTrue(default_storage.exists(relative_path))
        
        # Manually delete the file from disk before deleting the instance
        default_storage.delete(relative_path)
        self.assertFalse(default_storage.exists(relative_path))
        
        # Now delete the instance, which should not cause errors
        try:
            post.delete()
        except Exception as e:
            self.fail(f"Deleting a non-existent file raised an exception: {e}")

    @mock.patch('editor_js.fields.get_editor_js_storage')
    def test_exception_on_delete_is_handled(self, mock_get_storage):
        """
        Tests that an exception during file deletion is caught.
        This covers the `except Exception as e:` block.
        """
        # Mock storage that raises an exception when .delete() is called
        mock_storage = mock.MagicMock()
        mock_storage.base_url = default_storage.base_url
        mock_storage.exists.return_value = True
        mock_storage.delete.side_effect = IOError("Permission denied")
        mock_get_storage.return_value = mock_storage
        
        image_url = self._create_dummy_image('image_to_fail_delete.jpg')
        post = Post.objects.create(content={"blocks": [{"type": "image", "data": {"file": {"url": image_url}}}]})

        # Deletion should catch the exception and not crash the test
        try:
            post.delete()
        except IOError:
            self.fail("IOError exception was not caught by the signal handler.")

    def test_extract_image_urls_with_malformed_data(self):
        """
        Tests that URL extraction handles image blocks without URLs.
        """
        data = {
            "blocks": [
                {"type": "image", "data": {"file": {"url": None}}}, # URL is None
                {"type": "image", "data": {"file": {}}}, # 'url' not present
                {"type": "image", "data": {}} # 'file' not present
            ]
        }
        field = EditorJSField()
        extracted_urls = field._extract_image_urls(data)
        self.assertEqual(len(extracted_urls), 0)

    def test_pre_save_on_new_instance_with_pk_triggers_doesnotexist(self):
        """
        Tests that pre_save handles creating an instance with a pre-assigned pk
        that is not yet present in the DB. This covers the `except DoesNotExist` block.
        """
        image_url = self._create_dummy_image('new_post_with_pk.jpg')
        
        # Create an instance with a pk that definitely does not exist
        post = Post(pk=99999, content={"blocks": [{"type": "image", "data": {"file": {"url": image_url}}}]})
        
        # When calling .save(), model_instance.pk is 99999 (True).
        # The code will enter the `if` block and try .get(pk=99999),
        # raising DoesNotExist, which will be caught by the except block.
        try:
            post.save()
        except Exception as e:
            self.fail(f"Saving with pre-assigned pk failed: {e}")

    def test_formfield_default_behavior(self):
        """
        Tests the default behavior of formfield without custom tools.
        This covers the path where `if self.tools` is false.
        """
        # Get the field directly from the Post model
        field_instance = Post._meta.get_field('content')
        
        # Call the method to get the form field
        form_field = field_instance.formfield()
        
        # Check that the widget is the correct one
        self.assertIsInstance(form_field.widget, EditorJsIframeWidget)
        
        # Check that the config passed to the widget is empty
        widget_config = form_field.widget.attrs.get('config', {})
        self.assertEqual(widget_config, {})

    def test_formfield_with_custom_tools(self):
        """
        Tests the behavior of formfield with custom tools.
        This covers the path where `if self.tools` is true.
        """
        # Define a custom tools configuration
        custom_tools = {
            "header": {
                "class": "MyCustomHeaderTool",
                "inlineToolbar": True
            }
        }
        
        # Create a field instance on the fly, passing the tools
        field_instance = EditorJSField(tools=custom_tools)
        
        # Call the method to get the form field
        form_field = field_instance.formfield()

        # Check that the widget is the correct one
        self.assertIsInstance(form_field.widget, EditorJsIframeWidget)

        # Check that the custom config has been passed to the widget
        widget_config = form_field.widget.attrs.get('config', {})
        self.assertIn('tools', widget_config)
        self.assertEqual(widget_config['tools'], custom_tools)

    @mock.patch('editor_js.fields.get_editor_js_storage')
    def test_pre_save_orphan_deletion_with_storage_without_base_url(self, mock_get_storage):
        """
        Verifies that pre_save does not delete anything if the storage has no base_url.
        This covers `if base_url:` in pre_save when it is false.
        """
        mock_storage = mock.MagicMock()
        del mock_storage.base_url
        mock_get_storage.return_value = mock_storage

        post = Post.objects.create(content={"blocks": [{"type": "image", "data": {"file": {"url": "some_url"}}}]})
        post.content = {"blocks": []} # Removes the image
        post.save()
        
        mock_storage.delete.assert_not_called()

    def test_pre_save_orphan_deletion_with_external_url(self):
        """
        Verifies that pre_save ignores external URLs.
        This covers `if url.startswith(base_url):` in pre_save when it is false.
        """
        post = Post.objects.create(content={"blocks": [{"type": "image", "data": {"file": {"url": "https://example.com/image.jpg"}}}]})
        post.content = {"blocks": []} # Removes the external image
        
        try:
            post.save()
        except Exception as e:
            self.fail(f"Saving with external URL failed: {e}")

    def test_pre_save_orphan_deletion_of_non_existent_file(self):
        """
        Verifies that pre_save handles a file that no longer exists on disk.
        This covers `if storage.exists(decoded_path):` in pre_save when it is false.
        """
        image_url = self._create_dummy_image('image_for_presave_vanish.jpg')
        relative_path = image_url.replace(default_storage.base_url, '')
        
        post = Post.objects.create(content={"blocks": [{"type": "image", "data": {"file": {"url": image_url}}}]})
        
        # Manually delete the file
        default_storage.delete(relative_path)
        
        post.content = {"blocks": []} # Remove the image from the post
        
        try:
            post.save() # Should not fail
        except Exception as e:
            self.fail(f"Saving with non-existent file failed: {e}")

    @mock.patch('editor_js.fields.get_editor_js_storage')
    def test_pre_save_exception_on_orphan_delete_is_handled(self, mock_get_storage):
        """
        Tests that an exception during orphan file deletion in pre_save is properly caught.
        """
        mock_storage = mock.MagicMock()
        mock_storage.base_url = default_storage.base_url
        mock_storage.exists.return_value = True
        mock_storage.delete.side_effect = IOError("Permission denied during save")
        mock_get_storage.return_value = mock_storage

        image_url = self._create_dummy_image('image_to_fail_orphan_delete.jpg')
        
        post = Post.objects.create(content={"blocks": [{"type": "image", "data": {"file": {"url": image_url}}}]})
        
        post.content = {"blocks": []}
        
        try:
            post.save()
        except IOError:
            self.fail("IOError exception during pre_save was not caught.")

        mock_storage.delete.assert_called_once()
