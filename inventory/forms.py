from io import BytesIO
from zipfile import BadZipFile

from django import forms
from openpyxl import load_workbook
from openpyxl.utils.exceptions import InvalidFileException

from .models import Item


class ExcelImportForm(forms.Form):
    mode = forms.ChoiceField(choices=[
        ("append", "append"),
        # ("replace", "replace")
        ])
    file = forms.FileField()

    def clean_file(self):
        file = self.cleaned_data["file"]
        try:
            workbook = load_workbook(BytesIO(file.read()))
        except (BadZipFile, InvalidFileException, KeyError) as exc:
            raise forms.ValidationError(
                "Could not read this file as an Excel (.xlsx) workbook."
            ) from exc
        self.cleaned_data["workbook"] = workbook
        return file


class NewItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ["name", "box"]
