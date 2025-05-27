from django.contrib import admin

# Register your models here.
from .models import PassportRequest, PassportRejection, Resident, Passport
admin.site.register(PassportRequest)