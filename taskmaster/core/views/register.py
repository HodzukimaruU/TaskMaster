from django.shortcuts import render, redirect
from django.urls import reverse
from django.core.mail import send_mail
from django.conf import settings

from core.models import ConfirmationCode
from core.forms import RegistrationForm

import uuid
import time

def register_view(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            
            confirmation_code = str(uuid.uuid4())
            expiration_time = int(time.time()) + settings.CONFIRMATION_CODE_LIFETIME
            ConfirmationCode.objects.create(
                code=confirmation_code, user=user, expiration_time=expiration_time
            )
            
            confirmation_url = settings.SERVER_HOST + reverse("confirm_email") + f"?code={confirmation_code}"
            send_mail(
                'Подтвердите ваш email',
                f'Пожалуйста, подтвердите ваш email по следующей ссылке: {confirmation_url}',
                settings.EMAIL_FROM,
                [user.email],
            )
        return redirect(to="confirm_email_sent")
    else:
        form = RegistrationForm()
    return render(request, 'register.html', {'form': form})