from django.contrib import admin
from .models import Category, Tag, Post, Comment

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'category', 'created_at']
    list_filter = ['category', 'tags']
    search_fields = ['title', 'content']

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['author', 'post', 'created_at']

admin.site.register(Category)
admin.site.register(Tag)