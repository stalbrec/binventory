from django.views import generic
from .models import Box, Item
from django.shortcuts import render, redirect
import qrcode
import base64
from io import BytesIO
# Create your views here.
import logging

class IndexView(generic.ListView):
    template_name = "inventory/index.html"
    context_object_name = "full_inventory"

    def get_queryset(self):
        return Item.objects.order_by("name")


class BoxAwareDetailView(generic.DetailView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["available_boxes"] = Box.objects.all()
        return context


class ItemView(BoxAwareDetailView):
    model = Item
    template_name = "inventory/item.html"

    def post(self, request, *args, **kwargs):
        pk = kwargs.get("pk")
        if request.method == "POST":
            obj = self.model.objects.get(id=pk)
            new_box_id = request.POST.get("new_box")[0]
            new_box = Box.objects.get(id=new_box_id)
            if new_box:
                obj.box = new_box
            obj.save()
        return redirect("inventory:item", pk)


class BoxView(BoxAwareDetailView):
    model = Box
    template_name = "inventory/box.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        full_url = self.request.build_absolute_uri(
            self.object.get_absolute_url()
        )
        context["full_url"]=full_url

        qr = qrcode.make(full_url)
        buffer = BytesIO()
        qr.save(buffer, format="PNG")
        img_str = base64.b64encode(buffer.getvalue())
        context["qr_image_data"] = f"data:image/png;base64,{img_str.decode()}"
        logging.error(img_str)
        return context


def new_item(request):
    if request.method == "POST":
        item_name = request.POST.get("name")
        box_id = request.POST.get("box")[0]
        Item.objects.create(name=item_name, box=Box.objects.get(id=box_id))
        return redirect("inventory:index")
    return render(
        request, "inventory/new.html", dict(available_boxes=Box.objects.all())
    )
