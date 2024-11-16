from django.contrib import admin
from .models import Profile, Follow

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['id','user', 'bio', 'avatar', 'background_pic', 'created_at', 'updated_at']
    search_fields = ['user__username', 'user__email', 'user__first_name', 'user__last_name', 'bio', ]
    list_filter = ['created_at', 'updated_at']
    list_display_links = ['user']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        (None, {
            'fields': ('user', 'bio', 'avatar', 'background_pic')
        }),
        ('Date Information', {
            'fields': ('created_at', 'updated_at')
        })
    )
@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ['follower', 'following', 'created_at']
    search_fields = ['follower__username', 'following__username']
    list_filter = ['created_at']
    list_display_links = ['follower']
    readonly_fields = ['created_at']
    fieldsets = (
        (None, {
            'fields': ('follower', 'following')
        }),
        ('Date Information', {
            'fields': ('created_at',)
        })
    )   


