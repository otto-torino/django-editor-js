import os
import shutil
from django.test import TestCase, override_settings
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

TEST_MEDIA_ROOT = os.path.join(os.path.dirname(__file__), 'test_media')

@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class ViewsTest(TestCase):

    def setUp(self):
        """Creates a temporary media directory before each test."""
        os.makedirs(TEST_MEDIA_ROOT, exist_ok=True)

    def tearDown(self):
        """Removes the temporary media directory after each test."""
        if os.path.exists(TEST_MEDIA_ROOT):
            shutil.rmtree(TEST_MEDIA_ROOT)

    def test_iframe_view(self):
        url = reverse('editor_js_iframe')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'editor_js/editor_js_iframe.html')

    def test_image_upload_view_get_request(self):
        """Tests that a GET request to the upload view fails correctly."""
        url = reverse('editor_js_image_upload')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {'success': 0, 'message': 'Invalid request method or no image provided.'})

    def test_image_upload_view_post_no_file(self):
        """
        Tests that a POST request without a file fails.
        """
        url = reverse('editor_js_image_upload')
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {'success': 0, 'message': 'Invalid request method or no image provided.'})

    def test_image_upload_view_post_invalid_file_type(self):
        """
        Tests that uploading a disallowed file type fails.
        """
        url = reverse('editor_js_image_upload')
        invalid_file = SimpleUploadedFile("test.txt", b"file_content", content_type="text/plain")
        
        response = self.client.post(url, {'image': invalid_file})
        
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {
            'success': 0,
            'message': 'Invalid file type: text/plain.'
        })

    def test_image_upload_view_post_success(self):
        """
        Tests successful image upload ("happy path").
        """
        url = reverse('editor_js_image_upload')
        image = SimpleUploadedFile("test_image.jpg", b"image_content", content_type="image/jpeg")
        
        response = self.client.post(url, {'image': image})
        
        self.assertEqual(response.status_code, 200)
        
        response_json = response.json()
        self.assertEqual(response_json['success'], 1)
        self.assertIn('file', response_json)
        self.assertIn('url', response_json['file'])
        
        file_url = response_json['file']['url']
        self.assertTrue(file_url.startswith('/media/editor_js/'))
        self.assertTrue(file_url.endswith('.jpg'))