from django.contrib import admin

from .models import *

admin.site.register(Customer)
admin.site.register(Target)
admin.site.register(Baz)
admin.site.register(CustomerBaz)
