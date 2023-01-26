A openimis self registration back end module to allow connection from the mobile app:

https://github.com/openimis/mobile-self_registration_flutter

# Developer Settings
  > Developers can set their app setting through env files 



#sample .env settings
```
  DB_HOST=127.0.0.1
  DB_PORT=1433
  DB_NAME=YOUR_DB_NAME
  DB_USER=YOUR_DB_USERNAME
  DB_PASSWORD=YOUR_DB_PASSWORD
  DEBUG=True
  ROW_SECURITY=True
  USE_EMAIL_OTP=False
  EMAIL_OTP_SUBJECT=HIBVerification
  EMAIL_HOST=SMTP_EMAIL_HOST
  EMAIL_PORT=YOUR_EMAIL_SERVER_PORT
  EMAIL_HOST_USER='me@gmail.com'
  EMAIL_HOST_PASSWORD='password'
  DOIT_SMS_URL=https:sms_url 

```

#Import env settings variable to settings , example
```
    EMAIL_USE_TLS = True
    EMAIL_HOST = os.environ.get('EMAIL_HOST')
    EMAIL_PORT = os.environ.get('EMAIL_PORT')
    EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
    EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')



    DOIT_SMS_URL = os.environ.get("DOIT_SMS_URL")
    SMS_TOKEN=os.environ.get("SMS_TOKEN")

    EMAIL_SUBJECT=os.environ.get("EMAIL_OTP_SUBJECT")
    USE_EMAIL_OTP =os.environ.get("USE_EMAIL_OTP")

```
#important note:
 Developers need to change following code for non-nepali locale, because of date is different, in file Schema.py
 ```
      from .date_np_en import date_np_en
      """ 
          Need to convert nepali date to english date , since people uses nepali date
      """
      j = date_np_en.get(str(dob)) 
 ```


