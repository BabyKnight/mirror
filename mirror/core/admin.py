from django.contrib import admin

from .models import *

admin.site.register(UserProfile)
admin.site.register(Sample)
admin.site.register(Image)
admin.site.register(Task)
admin.site.register(TestCase)

