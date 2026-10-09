from django.urls import path

from . import views

urlpatterns = [
    path("", views.alarm_list, name="alarm_list"),
    path("new/", views.alarm_create, name="alarm_create"),
    path("<int:pk>/edit/", views.alarm_edit, name="alarm_edit"),
    path("<int:pk>/delete/", views.alarm_delete, name="alarm_delete"),
    path("<int:pk>/toggle/", views.alarm_toggle, name="alarm_toggle"),
    path("due/", views.alarms_due, name="alarms_due"),
    path("<int:pk>/ack/", views.alarm_ack, name="alarm_ack"),
]
