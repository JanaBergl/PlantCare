from django.http import request
from django.shortcuts import render
from django.views.generic import ListView, TemplateView
from django.urls import reverse_lazy
from plant_care.models import Plant

"""
Listování rostlin: Zobrazit všechny rostliny v databázi - různé řazení - datum, jméno, skupiny.
Detail rostliny: Detailní zobrazení jedné rostliny a její péče (zálivka, hnojení, atd.).
Přidání nové rostliny: Formulář pro přidání nové rostliny.
Úprava rostliny: Formulář pro úpravu existující rostliny.
Zobrazení varování
Seznam mrtvých rostlin
Zalévání, ...

"""


class HomePageTemplateView(TemplateView):
    """"""
    template_name = "home_page.html"

    def get_context_data(self, **kwargs):
        """Overrides parent method get_context_data, adds 'user_name' to context."""
        context = super().get_context_data(**kwargs)
        context["user_name"] = self.request.user.username
        return context


class PlantListingView(ListView):
    """"""
    model = Plant
    context_object_name = "plants"

    def get_queryset(self):
        """"""
