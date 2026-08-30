from django.db import models
from django.conf import settings


class Category(models.Model):
    class CategoryType(models.TextChoices):
        INCOME = 'income', 'Income'
        EXPENSE = 'expense', 'Expense'
        BOTH = 'both', 'Both'

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, default='')
    type = models.CharField(
        max_length=7,
        choices=CategoryType.choices,
        default=CategoryType.BOTH,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name


class Transaction(models.Model):
    class TransactionType(models.TextChoices):
        INCOME = 'income', 'Income'
        EXPENSE = 'expense', 'Expense'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='transactions'
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    transaction_type = models.CharField(
        max_length=7,
        choices=TransactionType.choices,
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='transactions'
    )
    description = models.TextField(blank=True, default='')
    transaction_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-transaction_date', '-created_at']
        indexes = [
            models.Index(fields=['user', 'transaction_date']),
            models.Index(fields=['user', 'transaction_type']),
        ]

    def __str__(self):
        return f'{self.user} - {self.transaction_type}: {self.amount}'


class Budget(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='budgets'
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='budgets'
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    month = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-month', 'category__name']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'category', 'month'],
                name='unique_user_category_month_budget'
            )
        ]
        indexes = [
            models.Index(fields=['user', 'month']),
        ]

    def __str__(self):
        return f'{self.user} - {self.category}: {self.amount} ({self.month.strftime("%Y-%m")})'