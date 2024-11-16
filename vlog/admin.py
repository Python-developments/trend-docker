from django.contrib import admin
from .models import Video

class VideoAdmin(admin.ModelAdmin):
    list_display = ('author', 'title', 'description', 'video', 'duration', 'created_at', 'updated_at')

admin.site.register(Video, VideoAdmin)
