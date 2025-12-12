from django import forms

from .models import MovieScript


class MovieScriptForm(forms.ModelForm):
    class Meta:
        model = MovieScript
        fields = ["title", "file"]
