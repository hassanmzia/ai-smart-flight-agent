from django.contrib import admin
from .models import UserContact


@admin.register(UserContact)
class UserContactAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'city', 'country', 'relationship', 'invite_status')
    list_filter = ('relationship', 'invite_status')
    search_fields = ('name', 'city', 'owner__email')
    raw_id_fields = ('owner', 'linked_user')
