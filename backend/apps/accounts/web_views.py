from django.contrib import messages
from django.contrib.auth import login as django_login, logout as django_logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator
from django.views import View

from .services import AuthService, ProfileService


class RegisterWebView(View):
    """Server-rendered web registration page."""
    template_name = 'accounts/register.html'

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('home')
        return render(request, self.template_name)

    def post(self, request):
        email = request.POST.get('email', '').strip()
        username = request.POST.get('username', '').strip()
        full_name = request.POST.get('full_name', '').strip()
        password = request.POST.get('password', '')
        password_confirm = request.POST.get('password_confirm', '')

        # Basic form validation
        if not email or not username or not full_name or not password:
            messages.error(request, 'All fields are required.')
            return render(request, self.template_name, {
                'email': email,
                'username': username,
                'full_name': full_name,
            })

        if password != password_confirm:
            messages.error(request, 'Passwords do not match.')
            return render(request, self.template_name, {
                'email': email,
                'username': username,
                'full_name': full_name,
            })

        try:
            user, tokens = AuthService.register_user(
                email=email,
                username=username,
                full_name=full_name,
                password=password
            )
            # Log user into Django browser session
            django_login(request, user, backend='apps.accounts.backends.EmailOrUsernameModelBackend')
            messages.success(request, f'Welcome to Circlo, @{user.username}!')
            return redirect('home')
        except Exception as e:
            messages.error(request, str(e))
            return render(request, self.template_name, {
                'email': email,
                'username': username,
                'full_name': full_name,
            })


class LoginWebView(View):
    """Server-rendered web login page."""
    template_name = 'accounts/login.html'

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('home')
        return render(request, self.template_name, {
            'next': request.GET.get('next', '')
        })

    def post(self, request):
        identifier = request.POST.get('identifier', '').strip()
        password = request.POST.get('password', '')
        next_url = request.POST.get('next', '')

        if not identifier or not password:
            messages.error(request, 'Please provide both email/username and password.')
            return render(request, self.template_name, {'identifier': identifier, 'next': next_url})

        user, tokens = AuthService.authenticate_user(
            identifier=identifier,
            password=password,
            request=request
        )

        if not user:
            messages.error(request, 'Invalid email/username or password.')
            return render(request, self.template_name, {'identifier': identifier, 'next': next_url})

        if not user.is_active:
            messages.error(request, 'This account is currently deactivated.')
            return render(request, self.template_name, {'identifier': identifier, 'next': next_url})

        django_login(request, user, backend='apps.accounts.backends.EmailOrUsernameModelBackend')
        messages.success(request, f'Welcome back, @{user.username}!')

        if next_url and next_url.startswith('/'):
            return redirect(next_url)
        return redirect('home')


class LogoutWebView(View):
    """Logs out user from browser session."""
    def get(self, request):
        return self.post(request)

    def post(self, request):
        django_logout(request)
        messages.info(request, 'You have been logged out.')
        return redirect('accounts-web:login')


class PasswordResetWebView(View):
    """Server-rendered password reset request page."""
    template_name = 'accounts/password_reset.html'

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        email = request.POST.get('email', '').strip()
        if email:
            result = AuthService.generate_password_reset_token(email)
            if result:
                user, uid, token = result
                reset_url = f"/auth/password-reset-confirm/{uid}/{token}/"
                messages.info(request, f'Dev Link: {reset_url}')
        messages.success(request, 'If an account exists with that email address, password reset instructions have been sent.')
        return render(request, self.template_name)


class PasswordResetConfirmWebView(View):
    """Server-rendered password reset confirm page."""
    template_name = 'accounts/password_reset_confirm.html'

    def get(self, request, uidb64, token):
        return render(request, self.template_name, {'uid': uidb64, 'token': token})

    def post(self, request, uidb64, token):
        new_password = request.POST.get('new_password', '')
        new_password_confirm = request.POST.get('new_password_confirm', '')

        if not new_password or new_password != new_password_confirm:
            messages.error(request, 'Passwords do not match or cannot be empty.')
            return render(request, self.template_name, {'uid': uidb64, 'token': token})

        try:
            AuthService.reset_password_with_token(uidb64, token, new_password)
            messages.success(request, 'Your password has been reset successfully! You can now log in.')
            return redirect('accounts-web:login')
        except ValidationError as e:
            messages.error(request, str(e.message_dict.get('token', ['Invalid token'])[0]))
            return render(request, self.template_name, {'uid': uidb64, 'token': token})


@method_decorator(login_required, name='dispatch')
class PasswordChangeWebView(View):
    """Allows authenticated user to change password via web UI."""
    template_name = 'accounts/password_change.html'

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        current_password = request.POST.get('current_password', '')
        new_password = request.POST.get('new_password', '')
        new_password_confirm = request.POST.get('new_password_confirm', '')

        if new_password != new_password_confirm:
            messages.error(request, 'New passwords do not match.')
            return render(request, self.template_name)

        try:
            AuthService.change_password(request.user, current_password, new_password)
            # Re-authenticate in session to prevent session invalidation
            django_login(request, request.user, backend='apps.accounts.backends.EmailOrUsernameModelBackend')
            messages.success(request, 'Your password has been changed successfully.')
            return redirect('profile-me')
        except ValidationError as e:
            msg = e.message_dict.get('current_password', ['Error changing password'])[0]
            messages.error(request, msg)
            return render(request, self.template_name)
