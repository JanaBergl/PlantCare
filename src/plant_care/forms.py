from django import forms
from django.core.exceptions import ValidationError

def duplicity_check(model, **kwargs):
    """
    """
    if model.objects.filter(**kwargs).first():
        return True
    return False
