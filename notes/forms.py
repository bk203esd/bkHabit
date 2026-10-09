from django import forms

from .models import Folder, Note, Tag


class NoteForm(forms.ModelForm):
    tag_names = forms.CharField(
        required=False,
        help_text="Comma-separated tags",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "work, ideas"}),
    )

    class Meta:
        model = Note
        fields = ["title", "content", "folder", "is_pinned"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "content": forms.Textarea(
                attrs={
                    "class": "form-control markdown-editor",
                    "rows": 14,
                    "placeholder": "# Heading\n\n- list item\n\n**bold** and *italic*",
                }
            ),
            "folder": forms.Select(attrs={"class": "form-control"}),
            "is_pinned": forms.CheckboxInput(attrs={"class": "form-check"}),
        }

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.fields["folder"].queryset = Folder.objects.filter(user=user)
        self.fields["folder"].required = False
        if self.instance and self.instance.pk:
            self.fields["tag_names"].initial = ", ".join(
                self.instance.tags.values_list("name", flat=True)
            )

    def save(self, commit=True):
        note = super().save(commit=False)
        note.user = self.user
        if commit:
            note.save()
            self._save_tags(note)
        return note

    def _save_tags(self, note):
        raw = self.cleaned_data.get("tag_names") or ""
        names = [part.strip() for part in raw.split(",") if part.strip()]
        tags = []
        for name in names:
            tag, _ = Tag.objects.get_or_create(user=self.user, name=name)
            tags.append(tag)
        note.tags.set(tags)


class FolderForm(forms.ModelForm):
    class Meta:
        model = Folder
        fields = ["name"]
        widgets = {"name": forms.TextInput(attrs={"class": "form-control"})}
