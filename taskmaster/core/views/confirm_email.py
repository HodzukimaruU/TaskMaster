from django.shortcuts import redirect
from django.http import HttpRequest, HttpResponseBadRequest, HttpResponse
from django.views.decorators.http import require_http_methods
from core.models import ConfirmationCode


def confirm_email_view(request: HttpRequest) -> HttpResponse:
    code = request.GET.get('code')
    try:
        confirmation = ConfirmationCode.objects.get(code=code)
        if confirmation.is_expired():
            return HttpResponseBadRequest('Verification code has expired.')
        user = confirmation.user
        user.is_active = True
        user.save()
        confirmation.delete()
        return redirect('login')
    except ConfirmationCode.DoesNotExist:
        return HttpResponseBadRequest('Verification code is invalid.')

@require_http_methods(["GET"])
def confirm_email_stub_controller(request: HttpRequest) -> HttpResponse:
    return HttpResponse("Confirmation email sent. Please confirm it by the link.")
