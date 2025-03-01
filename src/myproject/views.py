from django.http import HttpResponse
from django.views.generic import RedirectView
from django.urls import reverse_lazy





def home_page(request):
    """
    Home page of Django Kurz app
    """
    return HttpResponse("<h1>Domovska stranka projektu Django</h1>")


class HomePageRedirectView(RedirectView):
    pattern_name = "plant_care:home-page-app"

    def get_redirect_url(self):
        return reverse_lazy(self.pattern_name)