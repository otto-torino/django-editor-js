import os
import re
import shutil
from unittest import skipUnless

import django
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

    def test_iframe_has_no_inline_script(self):
        """
        Without a Content Security Policy no nonce is rendered, and every script
        is a file: the iframe initializes itself from editor_js_iframe.js.
        """
        html = self.client.get(reverse('editor_js_iframe')).content.decode()

        self.assertNotIn('nonce=', html)
        self.assertEqual(
            re.findall(r'<script(?![^>]*\bsrc=)[^>]*>', html), [],
        )
        # csp_nonce.js comes first, before the editor injects its styles
        self.assertLess(html.index('csp_nonce.js'), html.index('editorjs.min.js'))

    @skipUnless(django.VERSION >= (6, 0), "Django's CSP support needs Django >= 6.0")
    def test_iframe_carries_the_csp_nonce(self):
        templates = [{
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'APP_DIRS': True,
            'OPTIONS': {
                'context_processors': ['django.template.context_processors.csp'],
            },
        }]
        middleware = ['django.middleware.csp.ContentSecurityPolicyMiddleware']
        from django.utils.csp import CSP

        policy = {'script-src': [CSP.SELF, CSP.NONCE]}
        with self.settings(TEMPLATES=templates, MIDDLEWARE=middleware, SECURE_CSP=policy):
            response = self.client.get(reverse('editor_js_iframe'))
        html = response.content.decode()

        nonce = re.search(r"'nonce-([^']+)'", response.headers['Content-Security-Policy']).group(1)
        tags = re.findall(r'<(?:script|style|link)\b[^>]*>', html)
        self.assertTrue(tags)
        for tag in tags:
            self.assertIn(f'nonce="{nonce}"', tag)
        # the tools reading the nonce from the page, like the table one
        self.assertIn(f'<meta property="csp-nonce" content="{nonce}">', html)

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