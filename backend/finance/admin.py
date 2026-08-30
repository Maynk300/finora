from django.contrib import admin
from .models import Category, Transaction, Budget


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name']
    readonly_fields = ['created_at']


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['user', 'transaction_type', 'amount', 'category', 'transaction_date', 'created_at']
    list_filter = ['transaction_type', 'category', 'transaction_date']
    search_fields = ['user__username', 'description', 'category__name']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'transaction_date'


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ['user', 'category', 'amount', 'month', 'created_at']
    list_filter = ['category', 'month']
    search_fields = ['user__username', 'category__name']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'month'