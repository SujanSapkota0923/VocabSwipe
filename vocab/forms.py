from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import WordList

INPUT_CLASS = (
    'w-full px-4 py-3 rounded-lg border border-line bg-white text-ink '
    'placeholder:text-mute focus:border-brand-500 focus:ring-2 focus:ring-brand-100 '
    'outline-none transition-colors'
)


class UploadFileForm(forms.Form):
    name = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'List name (optional)'}),
    )
    description = forms.CharField(
        max_length=280,
        required=False,
        widget=forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Short description (optional)'}),
    )
    file = forms.FileField(widget=forms.FileInput(attrs={'accept': '.txt,.csv,.xlsx'}))
    is_public = forms.BooleanField(
        required=False,
        label='Make this list public',
        help_text='Public lists can be played by anyone, no account needed.',
    )


class ListSettingsForm(forms.ModelForm):
    class Meta:
        model = WordList
        fields = ('name', 'description', 'is_public')
        labels = {'is_public': 'Public list'}
        help_texts = {'is_public': 'Anyone can find and play it without an account.'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].widget.attrs['class'] = INPUT_CLASS
        self.fields['description'].widget.attrs['class'] = INPUT_CLASS


class SignupForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = INPUT_CLASS


class JoinCodeForm(forms.Form):
    code = forms.CharField(
        max_length=8,
        widget=forms.TextInput(attrs={
            'class': INPUT_CLASS + ' uppercase tracking-[0.35em] font-semibold text-center',
            'placeholder': 'ABC123',
            'autocapitalize': 'characters',
            'autocomplete': 'off',
        }),
    )

    def clean_code(self):
        return self.cleaned_data['code'].strip().upper()
