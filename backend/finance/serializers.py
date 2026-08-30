from rest_framework import serializers
from .models import Category, Transaction, Budget
from django.contrib.auth import get_user_model

User = get_user_model()


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'type', 'created_at']
        read_only_fields = ['id', 'created_at']


class TransactionSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Transaction
        fields = [
            'id', 'user', 'amount', 'transaction_type', 'category',
            'category_name', 'description', 'transaction_date',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError('Amount must be greater than zero.')
        return value

    def validate_category(self, value):
        if not value:
            raise serializers.ValidationError('Category is required.')
        return value


class BudgetSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    spent = serializers.SerializerMethodField()

    class Meta:
        model = Budget
        fields = [
            'id', 'user', 'category', 'category_name', 'amount',
            'month', 'spent', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

    def get_spent(self, obj):
        from django.db.models import Sum
        from .models import Transaction
        spent = Transaction.objects.filter(
            user=obj.user,
            category=obj.category,
            transaction_type='expense',
            transaction_date__year=obj.month.year,
            transaction_date__month=obj.month.month,
        ).aggregate(total=Sum('amount'))['total']
        return str(spent or 0)

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError('Budget amount must be greater than zero.')
        return value

    def validate_category(self, value):
        if not value:
            raise serializers.ValidationError('Category is required.')
        return value

    def validate_month(self, value):
        if value.day != 1:
            raise serializers.ValidationError('Month must be the first day of the month (e.g., 2024-01-01).')
        return value

    def validate(self, attrs):
        user = self.context['request'].user
        category = attrs.get('category')
        month = attrs.get('month')

        if self.instance is None:
            if Budget.objects.filter(user=user, category=category, month=month).exists():
                raise serializers.ValidationError(
                    'A budget for this category and month already exists.'
                )
        return attrs