import os
import shutil
from django.test import TestCase, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.files.storage import default_storage
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
