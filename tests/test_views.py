import base64
import importlib.util
import os
import re
import shutil
from unittest import skipUnless

import django
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
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

    def login(self, **kwargs):
        user = get_user_model().objects.create_user(
            'editor', password='password', **{'is_staff': True, **kwargs}
        )
        self.client.force_login(user)
        return user

    def png(self, name='test_image.png'):
        return SimpleUploadedFile(name, PNG, content_type='image/png')

    def upload(self, image, client=None, **extra):
        return (client or self.client).post(
            reverse('editor_js_image_upload'), {'image': image}, **extra
        )

    def test_image_upload_view_get_request(self):
        """Only POST is allowed."""
        self.login()
        response = self.client.get(reverse('editor_js_image_upload'))
        self.assertEqual(response.status_code, 405)

    def test_image_upload_view_refuses_anonymous_users(self):
        response = self.upload(self.png())
        self.assertEqual(response.status_code, 403)
        self.assertJSONEqual(response.content, {
            'success': 0, 'message': 'You are not allowed to upload images.'
        })
        self.assertFalse(os.path.exists(os.path.join(TEST_MEDIA_ROOT, 'editor_js')))

    def test_image_upload_view_refuses_users_out_of_the_staff(self):
        self.login(is_staff=False)
        self.assertEqual(self.upload(self.png()).status_code, 403)

    def test_image_upload_view_refuses_inactive_staff_users(self):
        user = self.login()
        user.is_active = False
        user.save()
        self.assertEqual(self.upload(self.png()).status_code, 403)

    @override_settings(EDITOR_JS={'IMAGE_UPLOAD_PERMISSION': 'tests.test_views.anyone'})
    def test_image_upload_permission_can_be_configured(self):
        self.assertEqual(self.upload(self.png()).status_code, 200)

    def test_image_upload_view_requires_the_csrf_token(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.login())
        client.get(reverse('editor_js_iframe'))
        token = client.cookies['csrftoken'].value

        self.assertEqual(self.upload(self.png(), client=client).status_code, 403)
        response = self.upload(self.png(), client=client, HTTP_X_CSRFTOKEN=token)
        self.assertEqual(response.status_code, 200)

    def test_image_upload_view_post_no_file(self):
        """A POST without a file fails."""
        self.login()
        response = self.client.post(reverse('editor_js_image_upload'), {})
        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(response.content, {'success': 0, 'message': 'No image provided.'})

    def test_image_upload_view_post_invalid_file_type(self):
        """A disallowed content type fails."""
        self.login()
        invalid_file = SimpleUploadedFile("test.txt", b"file_content", content_type="text/plain")
        response = self.upload(invalid_file)
        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(response.content, {
            'success': 0,
            'message': 'Invalid file type: text/plain.'
        })

    def test_image_upload_view_refuses_a_file_that_is_not_an_image(self):
        """The content type comes from the client: the bytes are checked."""
        self.login()
        fake = SimpleUploadedFile(
            "page.jpg", b"<html><script>alert(1)</script></html>", content_type="image/jpeg"
        )
        response = self.upload(fake)
        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(response.content, {'success': 0, 'message': 'Invalid image file.'})

    @skipUnless(importlib.util.find_spec('PIL'), "Pillow is not installed")
    def test_image_upload_view_refuses_a_broken_image_when_pillow_is_installed(self):
        self.login()
        broken = SimpleUploadedFile("broken.png", PNG[:16] + b"broken", content_type="image/png")
        self.assertEqual(self.upload(broken).status_code, 400)

    def test_image_upload_view_post_success(self):
        """A staff user uploads an image ("happy path")."""
        self.login()
        response = self.upload(self.png())

        self.assertEqual(response.status_code, 200)
        file_url = response.json()['file']['url']
        self.assertEqual(response.json()['success'], 1)
        self.assertTrue(file_url.startswith('/media/editor_js/'))
        self.assertTrue(file_url.endswith('.png'))

    def test_image_upload_view_saves_the_extension_of_the_format(self):
        """An image named as a page is not served as a page."""
        self.login()
        response = self.upload(self.png('page.html'))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['file']['url'].endswith('/editor_js/page.png'))


def anyone(request):
    return True


# a valid 1x1 PNG
PNG = base64.b64decode(
    'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=='
)
