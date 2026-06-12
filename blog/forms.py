from django import forms

from .models import Comment, Post


INPUT_CLASSES = (
    "mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 "
    "text-gray-900 shadow-sm focus:border-blue-500 focus:ring-blue-500 "
    "focus:outline-none focus:ring-1 sm:text-sm"
)


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ["title", "content", "image", "category", "tags", "status"]
        widgets = {
            "title": forms.TextInput(attrs={"class": INPUT_CLASSES}),
            "content": forms.Textarea(attrs={"class": INPUT_CLASSES, "rows": 8}),
            "image": forms.ClearableFileInput(
                attrs={"class": "mt-1 block w-full text-sm text-gray-600"}
            ),
            "category": forms.Select(attrs={"class": INPUT_CLASSES}),
            "tags": forms.SelectMultiple(attrs={"class": INPUT_CLASSES, "size": 4}),
            "status": forms.Select(attrs={"class": INPUT_CLASSES}),
        }
        help_texts = {
            "tags": "Hold Cmd/Ctrl to select multiple tags.",
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["body"]
        widgets = {
            "body": forms.Textarea(
                attrs={
                    "class": INPUT_CLASSES,
                    "rows": 3,
                    "placeholder": "Write a comment…",
                }
            ),
        }
        labels = {"body": ""}
