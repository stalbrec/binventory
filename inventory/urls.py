from django.urls import path

from . import views

app_name = "inventory"

urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path("new", views.new_item, name="new"),
    path("item/<int:pk>", views.ItemView.as_view(), name="item"),
    path("box/<int:pk>", views.BoxView.as_view(), name="box")
]