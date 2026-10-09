from django.urls import path

from . import views

urlpatterns = [
    path("", views.note_list, name="note_list"),
    path("new/", views.note_create, name="note_create"),
    path("folders/new/", views.folder_create, name="folder_create"),
    path("folders/<int:pk>/delete/", views.folder_delete, name="folder_delete"),
    path("<int:pk>/", views.note_detail, name="note_detail"),
    path("<int:pk>/edit/", views.note_edit, name="note_edit"),
    path("<int:pk>/delete/", views.note_delete, name="note_delete"),
    path("<int:pk>/pin/", views.note_toggle_pin, name="note_toggle_pin"),
]
