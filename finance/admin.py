from django.contrib import admin
from .models import Category, Transaction, Budget

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'type', 'user', 'created_at']
    list_filter = ['type', 'created_at']
    search_fields = ['name', 'user__username']
    ordering = ['-created_at']

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['user', 'category', 'amount', 'type', 'date', 'created_at']
    list_filter = ['type', 'category', 'date', 'created_at']
    search_fields = ['description', 'user__username', 'category__name']
    ordering = ['-date', '-created_at']
    date_hierarchy = 'date'

@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ['user', 'category', 'amount', 'month', 'created_at']
    list_filter = ['month', 'created_at']
    search_fields = ['user__username', 'category__name']
    ordering = ['-month']