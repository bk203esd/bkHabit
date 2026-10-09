from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from accounts.models import RegistrationStatus

from .models import Note
from .utils import render_markdown


class NoteTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="writer",
            password="complex-pass-123",
            is_active=True,
        )
        profile = self.user.profile
        profile.registration_status = RegistrationStatus.APPROVED
        profile.save()
        self.client.force_login(self.user)

    def test_markdown_rendering(self):
        html = render_markdown("# Hello\n\n- one\n- two")
        self.assertIn("<h1>", html)
        self.assertIn("<li>", html)

    def test_create_note_with_tags(self):
        response = self.client.post(
            reverse("note_create"),
            {
                "title": "Ideas",
                "content": "## List\n\n- alpha",
                "folder": "",
                "tag_names": "personal, later",
                "is_pinned": True,
            },
        )
        self.assertEqual(response.status_code, 302)
        note = Note.objects.get(title="Ideas")
        self.assertTrue(note.is_pinned)
        self.assertEqual(note.tags.count(), 2)
