from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

INPUT_CLASS = (
    'w-full px-4 py-3 rounded-xl border border-slate-200 bg-white '
    'focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100 outline-none transition-all'
)


class UploadFileForm(forms.Form):
    name = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'List name (optional)'}),
    )
    file = forms.FileField(widget=forms.FileInput(attrs={'accept': '.txt,.csv,.xlsx'}))


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
            'class': INPUT_CLASS + ' uppercase tracking-[0.3em] font-bold text-center',
            'placeholder': 'ABC123',
            'autocapitalize': 'characters',
        }),
    )

    def clean_code(self):
        return self.cleaned_data['code'].strip().upper()
