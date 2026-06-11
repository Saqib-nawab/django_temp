from django import forms

from .models import Post


INPUT_CLASSES = (
    "mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 "
    "text-gray-900 shadow-sm focus:border-blue-500 focus:ring-blue-500 "
    "focus:outline-none focus:ring-1 sm:text-sm"
)


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ["title", "content"]
        widgets = {
            "title": forms.TextInput(attrs={"class": INPUT_CLASSES}),
            "content": forms.Textarea(attrs={"class": INPUT_CLASSES, "rows": 8}),
        }
