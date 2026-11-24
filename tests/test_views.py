import base64
import importlib.util
import json
import os
import re
import shutil
from html import unescape
from unittest import skipUnless

import django
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

from editor_js.config import get_editor_js_config

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

    def _iframe_i18n(self, query=''):
        html = self.client.get(reverse('editor_js_iframe') + query).content.decode()
        raw = re.search(r"data-i18n-json='([^']*)'", html).group(1)
        return html, json.loads(unescape(raw))

    def test_iframe_is_translated_in_the_language_asked_by_the_widget(self):
        html, i18n = self._iframe_i18n('?lang=it')

        self.assertIn('<html lang="it">', html)
        self.assertIn('data-placeholder="Scrivi qualcosa..."', html)
        messages = i18n['messages']
        self.assertEqual(messages['ui']['popover']['Filter'], 'Filtra')
        self.assertEqual(messages['blockTunes']['moveUp']['Move up'], 'Sposta su')
        self.assertEqual(messages['toolNames']['Button'], 'Bottone')
        tools = i18n['toolMessages']
        self.assertEqual(tools['ButtonTool']['+ Add button'], '+ Aggiungi bottone')
        self.assertEqual(tools['Header']['Heading 2'], 'Titolo 2')
        self.assertEqual(i18n['iframe']['Paragraphs'], 'Paragrafi')

    def test_iframe_translates_the_same_english_text_by_its_context(self):
        _, i18n = self._iframe_i18n('?lang=it')
        tools = i18n['toolMessages']

        self.assertEqual(i18n['messages']['toolNames']['Heading'], 'Titolo')
        self.assertEqual(tools['Table']['Heading'], 'Intestazione')
        self.assertEqual(tools['ButtonTool']['Small'], 'Piccola')
        self.assertEqual(tools['SpacerTool']['Small'], 'Piccolo')

    def test_iframe_texts_are_not_taken_from_other_apps(self):
        """
        Django uses the translation of the first installed app that has a
        text: the admin, before the editor, translates "Delete" as "Cancella".
        """
        with self.modify_settings(INSTALLED_APPS={'prepend': 'django.contrib.admin'}):
            _, i18n = self._iframe_i18n('?lang=it')

        self.assertEqual(i18n['messages']['blockTunes']['delete']['Delete'], 'Elimina')
        self.assertEqual(i18n['messages']['ui']['toolbar']['toolbox']['Add'], 'Aggiungi')

    def test_iframe_has_a_text_for_every_tool_of_the_default_config(self):
        """Every default tool with texts of its own has their translations."""
        _, i18n = self._iframe_i18n('?lang=it')
        for name, info in get_editor_js_config()['TOOLS'].items():
            if info['class'] in ('DividerTool', 'MarkerTool'):
                continue  # no texts but their title, in toolNames
            with self.subTest(tool=name):
                self.assertIn(info['class'], i18n['toolMessages'])

    def test_iframe_falls_back_to_the_language_of_the_request(self):
        """A language the project does not have is not used."""
        html, i18n = self._iframe_i18n('?lang=xx')

        self.assertIn('<html lang="en-us">', html)
        self.assertEqual(i18n['messages']['ui']['popover']['Filter'], 'Filter')

    def test_iframe_loads_the_dragging_of_the_blocks(self):
        """Editor.js does not move the blocks by dragging: editorjs-drag-drop does."""
        html = self.client.get(reverse('editor_js_iframe')).content.decode()

        self.assertIn('editor_js/js/vendor/editorjs/drag-drop.min.js', html)
        self.assertLess(html.index('editorjs.min.js'), html.index('drag-drop.min.js'))

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
