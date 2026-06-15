from django.contrib import admin
from .models import RadiologyOrder, RadiologyStudy, RadiologyReport

admin.site.register(RadiologyOrder)
admin.site.register(RadiologyStudy)
admin.site.register(RadiologyReport)
