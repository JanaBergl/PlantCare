from django import forms
from django.core.exceptions import ValidationError
from plant_care.models import Plant, PlantGroup


def duplicity_check(model, **kwargs):
    """
    """
    if model.objects.filter(**kwargs).first():
        return True
    return False


class PlantModelForm(forms.ModelForm):
    """"""

    class Meta:
        model = Plant
        fields = [
            'name',
            'group',
            'date',
            'notes',
        ]

        labels = {
            'name': 'Name',
            'group': 'Group',
            'date': 'Date of purchase',
            'notes': 'Notes',
        }

        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control'}),
            'group': forms.Select(attrs={'class': 'form-control'}),
        }


class PlantGroupModelForm(forms.ModelForm):
    """"""

    class Meta:
        model = PlantGroup
        fields = '__all__'

        labels = {
            'group_name': 'Group name',
        }



        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': ''}),
        }
