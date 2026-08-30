from datetime import date
from decimal import Decimal
from typing import Optional

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db.models import Sum

from ..models import Category, Transaction

User = get_user_model()

MAX_LIMIT = 100
DEFAULT_LIMIT = 50


class TransactionToolError(Exception):
    pass


def validate_date_range(start_date: Optional[str], end_date: Optional[str]) -> tuple[Optional[date], Optional[date]]:
    parsed_start = validate_date(start_date, 'start_date')
    parsed_end = validate_date(end_date, 'end_date')
    if parsed_start and parsed_end and parsed_start > parsed_end:
        raise TransactionToolError('start_date cannot be after end_date')
    return parsed_start, parsed_end


def validate_date(value: Optional[str], field_name: str) -> Optional[date]:
    if value is None or value == '':
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise TransactionToolError(f'Invalid {field_name}: must be YYYY-MM-DD format')


def validate_transaction_type(value: Optional[str]) -> Optional[str]:
    if value is None or value == '':
        return None
    valid_types = [t.value for t in Transaction.TransactionType]
    if value not in valid_types:
        raise TransactionToolError(
            f'Invalid transaction_type: must be one of {valid_types}'
        )
    return value


def validate_category(value: Optional[str], user) -> Optional[Category]:
    if value is None or value == '':
        return None
    try:
        category = Category.objects.get(name__iexact=value)
    except Category.DoesNotExist:
        raise TransactionToolError(f'Category not found: {value}')
    return category


def validate_limit(value: Optional[int]) -> int:
    if value is None:
        return DEFAULT_LIMIT
    try:
        limit = int(value)
    except (TypeError, ValueError):
        raise TransactionToolError('Invalid limit: must be an integer')
    if limit <= 0:
        raise TransactionToolError('Limit must be greater than zero')
    return min(limit, MAX_LIMIT)


def get_transactions(
    user,
    *,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    transaction_type: Optional[str] = None,
    category: Optional[str] = None,
    limit: Optional[int] = None,
) -> list[dict]:
    if not user or not user.is_authenticated:
        raise TransactionToolError('Authenticated user required')

    parsed_start = validate_date(start_date, 'start_date')
    parsed_end = validate_date(end_date, 'end_date')
    validated_type = validate_transaction_type(transaction_type)
    validated_category = validate_category(category, user)
    validated_limit = validate_limit(limit)

    if parsed_start and parsed_end and parsed_start > parsed_end:
        raise TransactionToolError('start_date cannot be after end_date')

    queryset = Transaction.objects.filter(user=user).select_related('category')

    if parsed_start:
        queryset = queryset.filter(transaction_date__gte=parsed_start)
    if parsed_end:
        queryset = queryset.filter(transaction_date__lte=parsed_end)
    if validated_type:
        queryset = queryset.filter(transaction_type=validated_type)
    if validated_category:
        queryset = queryset.filter(category=validated_category)

    queryset = queryset[:validated_limit]

    results = []
    for txn in queryset:
        results.append({
            'amount': str(txn.amount),
            'transaction_type': txn.transaction_type,
            'category': txn.category.name,
            'description': txn.description,
            'transaction_date': txn.transaction_date.isoformat(),
        })

    return results


def get_financial_summary(
    user,
    *,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> dict:
    if not user or not user.is_authenticated:
        raise TransactionToolError('Authenticated user required')

    parsed_start, parsed_end = validate_date_range(start_date, end_date)

    queryset = Transaction.objects.filter(user=user)

    if parsed_start:
        queryset = queryset.filter(transaction_date__gte=parsed_start)
    if parsed_end:
        queryset = queryset.filter(transaction_date__lte=parsed_end)

    income_sum = queryset.filter(transaction_type=Transaction.TransactionType.INCOME).aggregate(
        total=Sum('amount')
    )['total'] or Decimal('0')

    expense_sum = queryset.filter(transaction_type=Transaction.TransactionType.EXPENSE).aggregate(
        total=Sum('amount')
    )['total'] or Decimal('0')

    net_balance = income_sum - expense_sum

    if income_sum > 0:
        savings_rate = ((income_sum - expense_sum) / income_sum) * Decimal('100')
    else:
        savings_rate = Decimal('0')

    quantize_2dp = Decimal('0.01')
    return {
        'total_income': str(income_sum.quantize(quantize_2dp)),
        'total_expenses': str(expense_sum.quantize(quantize_2dp)),
        'net_balance': str(net_balance.quantize(quantize_2dp)),
        'savings_rate': str(savings_rate.quantize(quantize_2dp)),
    }