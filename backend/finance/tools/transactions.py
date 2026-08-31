from datetime import date
from decimal import Decimal
from typing import Optional

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db.models import Sum
from django.utils import timezone

from ..models import Budget, Category, Transaction

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


def validate_month(value: Optional[str]) -> Optional[date]:
    if value is None or value == '':
        today = timezone.now().date()
        return date(today.year, today.month, 1)
    try:
        parts = value.split('-')
        if len(parts) != 2:
            raise ValueError
        year = int(parts[0])
        month = int(parts[1])
        if month < 1 or month > 12:
            raise ValueError
        return date(year, month, 1)
    except (ValueError, IndexError):
        raise TransactionToolError('Invalid month: must be YYYY-MM format')


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


def get_budget_status(
    user,
    *,
    month: Optional[str] = None,
) -> dict:
    if not user or not user.is_authenticated:
        raise TransactionToolError('Authenticated user required')

    month_start = validate_month(month)
    month_end = date(month_start.year, month_start.month + 1, 1) if month_start.month < 12 else date(month_start.year + 1, 1, 1)

    budgets = Budget.objects.filter(user=user, month=month_start).select_related('category')

    results = []
    for budget in budgets:
        spent = Transaction.objects.filter(
            user=user,
            category=budget.category,
            transaction_type=Transaction.TransactionType.EXPENSE,
            transaction_date__gte=month_start,
            transaction_date__lt=month_end,
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

        budget_amount = budget.amount
        remaining = budget_amount - spent

        if budget_amount > 0:
            percentage = (spent / budget_amount) * Decimal('100')
        else:
            percentage = Decimal('0')

        if percentage >= Decimal('100'):
            status = 'over_budget'
        elif percentage >= Decimal('80'):
            status = 'near_limit'
        else:
            status = 'under_budget'

        results.append({
            'category': budget.category.name,
            'budget_amount': str(budget_amount.quantize(Decimal('0.01'))),
            'spent_amount': str(spent.quantize(Decimal('0.01'))),
            'remaining_amount': str(remaining.quantize(Decimal('0.01'))),
            'percentage_used': str(percentage.quantize(Decimal('0.01'))),
            'status': status,
        })

    return {
        'month': month_start.strftime('%Y-%m'),
        'budgets': results,
    }


def _get_month_summary(user, month_start: date) -> dict:
    month_end = date(month_start.year, month_start.month + 1, 1) if month_start.month < 12 else date(month_start.year + 1, 1, 1)

    queryset = Transaction.objects.filter(
        user=user,
        transaction_date__gte=month_start,
        transaction_date__lt=month_end,
    )

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

    categories = queryset.filter(transaction_type=Transaction.TransactionType.EXPENSE).values('category__name').annotate(
        total=Sum('amount')
    )

    category_breakdown = {}
    for cat in categories:
        category_breakdown[cat['category__name']] = cat['total'] or Decimal('0')

    quantize_2dp = Decimal('0.01')
    return {
        'total_income': income_sum.quantize(quantize_2dp),
        'total_expenses': expense_sum.quantize(quantize_2dp),
        'net_balance': net_balance.quantize(quantize_2dp),
        'savings_rate': savings_rate.quantize(quantize_2dp),
        'categories': category_breakdown,
    }


def _calculate_change(current: Decimal, comparison: Decimal) -> dict:
    change = current - comparison
    if comparison != 0:
        change_percentage = (change / comparison) * Decimal('100')
    else:
        change_percentage = Decimal('0') if current == 0 else Decimal('100')

    quantize_2dp = Decimal('0.01')
    return {
        'current': str(current.quantize(quantize_2dp)),
        'comparison': str(comparison.quantize(quantize_2dp)),
        'change': str(change.quantize(quantize_2dp)),
        'change_percentage': str(change_percentage.quantize(quantize_2dp)),
    }


def compare_months(
    user,
    *,
    current_month: str,
    comparison_month: str,
) -> dict:
    if not user or not user.is_authenticated:
        raise TransactionToolError('Authenticated user required')

    current_start = validate_month(current_month)
    comparison_start = validate_month(comparison_month)

    current = _get_month_summary(user, current_start)
    comparison = _get_month_summary(user, comparison_start)

    all_categories = set(current['categories'].keys()) | set(comparison['categories'].keys())
    category_changes = []
    for cat_name in sorted(all_categories):
        current_val = current['categories'].get(cat_name, Decimal('0'))
        comparison_val = comparison['categories'].get(cat_name, Decimal('0'))
        change_data = _calculate_change(current_val, comparison_val)
        change_data['category'] = cat_name
        category_changes.append(change_data)

    return {
        'current_month': current_start.strftime('%Y-%m'),
        'comparison_month': comparison_start.strftime('%Y-%m'),
        'income': _calculate_change(current['total_income'], comparison['total_income']),
        'expenses': _calculate_change(current['total_expenses'], comparison['total_expenses']),
        'net_balance': _calculate_change(current['net_balance'], comparison['net_balance']),
        'savings_rate': {
            'current': str(current['savings_rate']),
            'comparison': str(comparison['savings_rate']),
            'change': str((current['savings_rate'] - comparison['savings_rate']).quantize(Decimal('0.01'))),
        },
        'categories': category_changes,
    }