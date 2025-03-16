from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from django.views.generic import RedirectView, TemplateView, FormView
from django.urls import reverse_lazy
from plant_care.utils import is_member_of_group


class HomePageRedirectView(RedirectView):
    pattern_name = "plant_care:home-page-app"

    def get_redirect_url(self):
        return reverse_lazy(self.pattern_name)


class AccountLoginView(FormView):
    """
    View for user login. Redirects to login confirmation page.
    """
    template_name = "account_login_page_template.html"
    form_class = AuthenticationForm

    def form_valid(self, form):
        """
        Handles valid form submission by authenticating the user.
        """
        username = form.cleaned_data.get("username")
        password = form.cleaned_data.get("password")

        user = authenticate(self.request, username=username, password=password)
        if user is not None:
            login(self.request, user)
            return HttpResponseRedirect(reverse_lazy("login-confirmation"))

        return super().form_valid(form)


class AccountLoginConfirmationView(TemplateView):
    """
    View for user login confirmation. Redirects user to home page.
    """
    template_name = "account_login_confirmation_template.html"


class AccountLogoutYesNoView(TemplateView):
    """
    View for displaying a logout confirmation page.
    """
    template_name = "account_logout_yes_no_confirmation.html"


class AccountLogoutView(RedirectView):
    """
    View for handling user logout and redirecting to the logout confirmation page.
    """
    url = reverse_lazy("logout-confirmation")
    logged_out_user = None

    def get(self, request, *args, **kwargs):
        """
        Logs out the current user and stores the user object for use in the redirect URL.
        """
        self.logged_out_user = request.user
        logout(request)
        return super().get(request, *args, **kwargs)

    def get_redirect_url(self, *args, **kwargs):
        """
        Constructs the URL for redirection with the user ID as a query parameter.
        """
        user_pk = self.logged_out_user.pk if self.logged_out_user else None
        return self.url + f"?userid={user_pk}"


class AccountLogoutConfirmationView(TemplateView):
    """
    View for displaying a confirmation message after a successful logout.
    """
    template_name = "account_logout_confirmation_template.html"

    def get_context_data(self, **kwargs):
        """
        Adds the user object to the context if a valid 'userid' is provided in the query string.
        """
        context = super().get_context_data(**kwargs)
        user_pk = self.request.GET.get('userid')
        if user_pk:
            user = User.objects.filter(pk=int(user_pk)).first()
            if user:
                context["user"] = user
            else:
                context["error"] = "User not found"

        return context


class UserRightsMixin:
    """
    Mixin to check if a user has the required access rights.
    """
    access_rights = []

    def user_has_rights(self, user):
        """
        Checks if the user belongs to at least one of the required groups.
        """
        return is_member_of_group(user, self.access_rights)

    def get_context_rights(self):
        """
        Adds user access rights information to the context.
        """
        context = {
            "user_has_rights": self.user_has_rights(self.request.user)
        }
        return context