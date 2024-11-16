from django.contrib import admin
from .models import CustomUser,Block


class CustomUserAdmin(admin.ModelAdmin):
    model = CustomUser
    list_display = ['id','username', 'email', 'avatar', 'is_staff', 'is_active', 'date_joined']
    search_fields = ['id','username', 'email']
admin.site.register(CustomUser, CustomUserAdmin)


class BlockAdmin(admin.ModelAdmin):
    list_display = ('blocker', 'blocked', 'timestamp')
    search_fields = ('blocker__username', 'blocked__username')
    readonly_fields = ('timestamp',)


admin.site.register(Block, BlockAdmin)