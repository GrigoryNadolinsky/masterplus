from django.contrib import admin
from .models import Request, User, AdminLog

@admin.register(Request)
class RequestAdmin(admin.ModelAdmin):
    list_display = ('last_name', 'first_name', 'category', 'status', 'created_at', 'importance')
    search_fields = ('last_name', 'first_name', 'category', 'status')
    list_filter = ('status', 'category', 'created_at')

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_superuser')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    list_filter = ('is_staff', 'is_superuser', 'is_active')

@admin.register(AdminLog)
class AdminLogAdmin(admin.ModelAdmin):
    list_display = ('action_time', 'user', 'content_type', 'object_id', 'action_flag', 'change_message')
    search_fields = ('user__username', 'object_repr')
    list_filter = ('action_time', 'user')