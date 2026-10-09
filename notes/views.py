from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import FolderForm, NoteForm
from .models import Folder, Note, Tag
from .utils import render_markdown


@login_required
def note_list(request):
    notes = Note.objects.filter(user=request.user).prefetch_related("tags", "folder")
    folder_id = request.GET.get("folder")
    tag_id = request.GET.get("tag")
    q = request.GET.get("q", "").strip()

    if folder_id == "none":
        notes = notes.filter(folder__isnull=True)
    elif folder_id:
        notes = notes.filter(folder_id=folder_id)

    if tag_id:
        notes = notes.filter(tags__id=tag_id)

    if q:
        notes = notes.filter(Q(title__icontains=q) | Q(content__icontains=q))

    context = {
        "notes": notes.distinct(),
        "folders": Folder.objects.filter(user=request.user),
        "tags": Tag.objects.filter(user=request.user),
        "folder_form": FolderForm(),
        "active_folder": folder_id,
        "active_tag": tag_id,
        "q": q,
    }
    return render(request, "notes/list.html", context)


@login_required
def note_detail(request, pk):
    note = get_object_or_404(
        Note.objects.prefetch_related("tags", "folder"),
        pk=pk,
        user=request.user,
    )
    return render(
        request,
        "notes/detail.html",
        {"note": note, "rendered": render_markdown(note.content)},
    )


@login_required
def note_create(request):
    if request.method == "POST":
        form = NoteForm(request.user, request.POST)
        if form.is_valid():
            note = form.save()
            messages.success(request, "Note created.")
            return redirect("note_detail", pk=note.pk)
    else:
        initial = {}
        folder_id = request.GET.get("folder")
        if folder_id:
            initial["folder"] = folder_id
        form = NoteForm(request.user, initial=initial)
    return render(request, "notes/form.html", {"form": form, "title": "New note"})


@login_required
def note_edit(request, pk):
    note = get_object_or_404(Note, pk=pk, user=request.user)
    if request.method == "POST":
        form = NoteForm(request.user, request.POST, instance=note)
        if form.is_valid():
            form.save()
            messages.success(request, "Note updated.")
            return redirect("note_detail", pk=note.pk)
    else:
        form = NoteForm(request.user, instance=note)
    return render(request, "notes/form.html", {"form": form, "title": "Edit note", "note": note})


@login_required
@require_POST
def note_delete(request, pk):
    note = get_object_or_404(Note, pk=pk, user=request.user)
    note.delete()
    messages.success(request, "Note deleted.")
    return redirect("note_list")


@login_required
@require_POST
def note_toggle_pin(request, pk):
    note = get_object_or_404(Note, pk=pk, user=request.user)
    note.is_pinned = not note.is_pinned
    note.save(update_fields=["is_pinned", "updated_at"])
    return redirect(request.POST.get("next") or "note_list")


@login_required
@require_POST
def folder_create(request):
    form = FolderForm(request.POST)
    if form.is_valid():
        folder = form.save(commit=False)
        folder.user = request.user
        folder.save()
        messages.success(request, "Folder created.")
    else:
        messages.error(request, "Could not create folder.")
    return redirect("note_list")


@login_required
@require_POST
def folder_delete(request, pk):
    folder = get_object_or_404(Folder, pk=pk, user=request.user)
    folder.delete()
    messages.success(request, "Folder deleted.")
    return redirect("note_list")
