from django.contrib import admin

from .models import *

admin.site.register(UserProfile)
admin.site.register(Status)
admin.site.register(Sample)
admin.site.register(Image)
admin.site.register(TaskHistory)
admin.site.register(TestCase)

