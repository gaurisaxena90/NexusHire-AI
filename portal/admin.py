from django.contrib import admin
from .models import UserProfile, Job, Application

# Humari tables ko admin panel mein register kar rahe hain
admin.site.register(UserProfile)
admin.site.register(Job)
admin.site.register(Application)