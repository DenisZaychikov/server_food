from django.contrib import admin

from .models import Subscription, User

admin.site.register(Subscription)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_filter = ('username', 'email')
