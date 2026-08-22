from django.urls import path

from . import views

app_name = "interaction"

urlpatterns = [
    path("guestbook/", views.guestbook, name="guestbook"),
    path("comment/<uslug:slug>/", views.submit_comment, name="submit_comment"),
    path("like/<uslug:slug>/", views.toggle_like, name="toggle_like"),
]
