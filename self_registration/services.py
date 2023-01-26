
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
def send_email_otp(insuree, otp):
    try:  
        subject, from_email, to = f"{settings.get('EMAIL_OTP_SUBJECT')}", f'{settings.get('EMAIL_HOST_USER')}', f'{insuree.email}'
        text_content = f'Your Request for OTP code is {otp}.'
        html_content = '<p>Please do not share your OTP with anyone</p>'
        msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
        msg.attach_alternative(html_content, "text/html")
        msg.send()#fail_silently also can be set
    except:
        pass