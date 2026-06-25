# portal_publik/forms.py

from django import forms
from .models import PesanKontak

class KontakForm(forms.ModelForm):
    class Meta:
        model = PesanKontak
        fields = ['nama', 'email', 'hp', 'kategori', 'pesan']
        widgets = {
            'nama': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nama Lengkap'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Alamat Email'}),
            'hp': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nomor HP'}),
            'kategori': forms.Select(attrs={'class': 'form-control'}),
            'pesan': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Tuliskan pesan Anda...'}),
        }