from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import WordList

INPUT_CLASS = 'input'

ALLOWED_UPLOAD_EXTENSIONS = ('.txt', '.csv', '.tsv', '.xlsx', '.xlsm')
MAX_UPLOAD_BYTES = 5 * 1024 * 1024


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
    file = forms.FileField(widget=forms.FileInput(attrs={'accept': '.txt,.csv,.tsv,.xlsx'}))
    is_public = forms.BooleanField(
        required=False,
        label='Make this list public',
        help_text='Public lists can be played by anyone, no account needed.',
    )

    def clean_file(self):
        uploaded = self.cleaned_data['file']
        name = (uploaded.name or '').lower()

        if not name.endswith(ALLOWED_UPLOAD_EXTENSIONS):
            allowed = ', '.join(ALLOWED_UPLOAD_EXTENSIONS)
            raise forms.ValidationError(f'Use one of these file types: {allowed}.')

        if uploaded.size > MAX_UPLOAD_BYTES:
            limit_mb = MAX_UPLOAD_BYTES // (1024 * 1024)
            raise forms.ValidationError(f'That file is larger than {limit_mb} MB.')

        return uploaded


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
            'class': INPUT_CLASS + ' input-code',
            'placeholder': 'ABC123',
            'autocapitalize': 'characters',
            'autocomplete': 'off',
        }),
    )

    def clean_code(self):
        return self.cleaned_data['code'].strip().upper()
