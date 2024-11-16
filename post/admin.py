from django.contrib import admin
from django.db.models import Count
from .models import Post, Comment, LikePost, HiddenPost
from reactions.models import Reaction


class ReactionInline(admin.TabularInline):
    model = Reaction
    extra = 0
    readonly_fields = ('user', 'reaction_type', 'created_at')
    can_delete = True
    show_change_link = True
    verbose_name = 'Reaction'
    verbose_name_plural = 'Reactions'


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'content', 'top_reactions_display', 'comment_count', 'like_count')
    search_fields = ('user__username', 'content')
    list_filter = ('created_at',)
    inlines = [ReactionInline]
    list_per_page = 50

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.prefetch_related('post_reactions', 'comments', 'likes')
        return qs

    def top_reactions_display(self, obj):
        """
        Displays the top 3 reactions with their counts.
        """
        return obj.top_reactions_display()

    top_reactions_display.short_description = 'Top Reactions'

    def comment_count(self, obj):
        return obj.comment_count()
    comment_count.short_description = 'Comments'

    def like_count(self, obj):
        return obj.like_count()
    like_count.short_description = 'Likes'


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('post', 'user', 'content', 'created_at')
    search_fields = ('user__username', 'post__user__username', 'content')
    list_filter = ('created_at',)


@admin.register(LikePost)
class LikePostAdmin(admin.ModelAdmin):
    list_display = ('post', 'user', 'like_counter', 'comment_counter')
    search_fields = ('user__username', 'post__user__username')
    list_filter = ('created_at',)

    def like_counter(self, obj):
        return obj.post.likes.count()
    like_counter.short_description = 'Like Count'

    def comment_counter(self, obj):
        return obj.post.comments.count()
    comment_counter.short_description = 'Comment Count'


@admin.register(HiddenPost)
class HiddenPostAdmin(admin.ModelAdmin):
    list_display = ('user', 'post')
    search_fields = ('user__username', 'post__id')
    list_filter = ('user', 'post')


@admin.register(Reaction)
class ReactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'post', 'reaction_type', 'created_at')
    search_fields = ('user__username', 'post__content', 'reaction_type')
    list_filter = ('created_at', 'reaction_type')
