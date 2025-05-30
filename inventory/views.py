from django.views import generic
from .models import Box, Item
from django.shortcuts import render, redirect
from django.http import HttpResponse
import qrcode
import qrcode.image.svg
import base64
from io import BytesIO
from zipfile import ZipFile, ZIP_DEFLATED
from openpyxl import Workbook, load_workbook
from django import forms

# Create your views here.
import logging


class ExcelImportForm(forms.Form):
    # title = forms.CharField(max_length=50)
    mode = forms.ChoiceField(choices=[
        ("append", "append"), 
        # ("replace", "replace")
        ])
    file = forms.FileField()


def import_excel(request):
    if request.method == "POST":
        form = ExcelImportForm(request.POST, request.FILES)
        if form.is_valid():
            buffer = BytesIO(request.FILES["file"].read())
            wb = load_workbook(buffer)
            ws = wb.active
            # import_mode = form.cleaned_data["mode"]
            for irow in range(2, ws.max_row + 1):
                row = ws[irow]
                item_id, item_name, box_name, box_location = row
                box_query = Box.objects.filter(name=box_name.value)
                if box_query.exists():
                    box = box_query[0]
                else:
                    box = Box.objects.create(
                        name=box_name.value, location=box_location.value
                    )
                Item.objects.create(name=item_name.value, box=box)
        return redirect("inventory:index")
    else:
        form = ExcelImportForm()
    return render(request, "inventory/import.html", {"form": form})


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
        full_url = self.request.build_absolute_uri(self.object.get_absolute_url())
        context["full_url"] = full_url

        buffer = get_qr_code_buffer(full_url)
        img_str = base64.b64encode(buffer.getvalue())
        context["qr_image_data"] = f"data:image/svg+xml;base64,{img_str.decode()}"
        logging.error(img_str)
        return context


def get_qr_code_buffer(full_url: str) -> BytesIO:
    qr_buffer = BytesIO()
    factory = qrcode.image.svg.SvgPathImage
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H)
    qr.add_data(full_url)
    qr_image = qr.make_image(
        image_factory=factory,
        module_drawer=qrcode.image.styles.moduledrawers.svg.SvgPathCircleDrawer(),
    )
    qr_image.save(qr_buffer)

    return qr_buffer


def download_all_box_qr_codes(request):
    zip_buffer = BytesIO()
    with ZipFile(zip_buffer, "a", ZIP_DEFLATED) as zip_file:
        for box in Box.objects.order_by("id"):
            box_full_url = request.build_absolute_uri(box.get_absolute_url())
            zip_file.writestr(
                f"{box.name}.svg", get_qr_code_buffer(box_full_url).getvalue()
            )
    zip_buffer.seek(0)

    response = HttpResponse(
        zip_buffer.read(),
        content_type="application/zip",
    )
    downlaod_fname = "box_qr_codes.zip"
    response["Content-Disposition"] = f'attachment; filename="{downlaod_fname}"'
    return response


def export_excel(request):
    wb = Workbook()
    ws = wb.active
    ws.title = "Inventory"
    columns = ["item-id", "item-name", "box-name", "box-location"]
    ws.append(columns)

    for item in Item.objects.order_by("id"):
        ws.append([item.id, item.name, item.box.name, item.box.location])
    xlsx_buffer = BytesIO()
    wb.save(xlsx_buffer)

    xlsx_buffer.seek(0)

    response = HttpResponse(
        xlsx_buffer.read(),
        content_type="application/vnd.openxmlformats-officedocument.speadsheetml.sheet",
    )
    downlaod_fname = "inventory.xlsx"
    response["Content-Disposition"] = f'attachment; filename="{downlaod_fname}"'
    return response


def new_item(request):
    if request.method == "POST":
        item_name = request.POST.get("name")
        box_id = request.POST.get("box")[0]
        Item.objects.create(name=item_name, box=Box.objects.get(id=box_id))
        return redirect("inventory:index")
    return render(
        request, "inventory/new.html", dict(available_boxes=Box.objects.all())
    )
