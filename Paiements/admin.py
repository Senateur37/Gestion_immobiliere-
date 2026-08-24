from django.contrib import admin

from .models import Deposit, Payment, PaymentRecord

admin.site.register(Payment)
admin.site.register(PaymentRecord)
admin.site.register(Deposit)
