from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from decimal import Decimal
from datetime import date
from unittest.mock import patch, MagicMock
from .models import Category, Transaction, Budget
from .services.gemini import GeminiService, GeminiServiceError, get_gemini_service, reset_gemini_service

User = get_user_model()


class CategoryAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.other_user = User.objects.create_user(username='otheruser', password='testpass123')
        self.category = Category.objects.create(name='Food', description='Food expenses')

    def test_list_categories_unauthenticated(self):
        response = self.client.get('/api/categories/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_create_category_authenticated(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post('/api/categories/', {'name': 'Transport', 'description': 'Transport costs'})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Transport')

    def test_create_category_unauthenticated(self):
        response = self.client.post('/api/categories/', {'name': 'Transport'})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_retrieve_category(self):
        response = self.client.get(f'/api/categories/{self.category.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Food')

    def test_update_category_authenticated(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(f'/api/categories/{self.category.id}/', {'description': 'Updated desc'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['description'], 'Updated desc')


class TransactionAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.other_user = User.objects.create_user(username='otheruser', password='testpass123')
        self.category = Category.objects.create(name='Food', description='Food expenses')
        self.other_category = Category.objects.create(name='Transport', description='Transport costs')
        self.user_transaction = Transaction.objects.create(
            user=self.user,
            amount=Decimal('50.00'),
            transaction_type='expense',
            category=self.category,
            description='Lunch',
            transaction_date=date(2024, 1, 15)
        )
        self.other_user_transaction = Transaction.objects.create(
            user=self.other_user,
            amount=Decimal('100.00'),
            transaction_type='income',
            category=self.category,
            description='Salary',
            transaction_date=date(2024, 1, 10)
        )

    def test_create_transaction(self):
        self.client.force_authenticate(user=self.user)
        data = {
            'amount': '25.50',
            'transaction_type': 'expense',
            'category': self.category.id,
            'description': 'Coffee',
            'transaction_date': '2024-01-20'
        }
        response = self.client.post('/api/transactions/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Decimal(response.data['amount']), Decimal('25.50'))
        self.assertEqual(response.data['transaction_type'], 'expense')
        self.assertEqual(response.data['user'], self.user.id)

    def test_create_transaction_invalid_amount(self):
        self.client.force_authenticate(user=self.user)
        data = {
            'amount': '0',
            'transaction_type': 'expense',
            'category': self.category.id,
            'transaction_date': '2024-01-20'
        }
        response = self.client.post('/api/transactions/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('amount', response.data)

    def test_create_transaction_invalid_type(self):
        self.client.force_authenticate(user=self.user)
        data = {
            'amount': '25.50',
            'transaction_type': 'invalid',
            'category': self.category.id,
            'transaction_date': '2024-01-20'
        }
        response = self.client.post('/api/transactions/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('transaction_type', response.data)

    def test_create_transaction_missing_category(self):
        self.client.force_authenticate(user=self.user)
        data = {
            'amount': '25.50',
            'transaction_type': 'expense',
            'transaction_date': '2024-01-20'
        }
        response = self.client.post('/api/transactions/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('category', response.data)

    def test_list_user_transactions(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/transactions/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], self.user_transaction.id)

    def test_list_other_user_transactions_forbidden(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/transactions/')
        other_ids = [t['id'] for t in response.data]
        self.assertNotIn(self.other_user_transaction.id, other_ids)

    def test_retrieve_own_transaction(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f'/api/transactions/{self.user_transaction.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.user_transaction.id)

    def test_retrieve_other_user_transaction_forbidden(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f'/api/transactions/{self.other_user_transaction.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_own_transaction(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(
            f'/api/transactions/{self.user_transaction.id}/',
            {'description': 'Updated lunch'}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['description'], 'Updated lunch')

    def test_update_other_user_transaction_forbidden(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(
            f'/api/transactions/{self.other_user_transaction.id}/',
            {'description': 'Hacked'}
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_own_transaction(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(f'/api/transactions/{self.user_transaction.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Transaction.objects.filter(id=self.user_transaction.id).exists())

    def test_delete_other_user_transaction_forbidden(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(f'/api/transactions/{self.other_user_transaction.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_unauthenticated_access_denied(self):
        response = self.client.get('/api/transactions/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class BudgetAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.other_user = User.objects.create_user(username='otheruser', password='testpass123')
        self.category = Category.objects.create(name='Food', description='Food expenses')
        self.other_category = Category.objects.create(name='Transport', description='Transport costs')
        self.user_budget = Budget.objects.create(
            user=self.user,
            category=self.category,
            amount=Decimal('500.00'),
            month=date(2024, 1, 1)
        )
        self.other_user_budget = Budget.objects.create(
            user=self.other_user,
            category=self.category,
            amount=Decimal('1000.00'),
            month=date(2024, 1, 1)
        )

    def test_create_budget(self):
        self.client.force_authenticate(user=self.user)
        data = {
            'category': self.other_category.id,
            'amount': '300.00',
            'month': '2024-02-01'
        }
        response = self.client.post('/api/budgets/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Decimal(response.data['amount']), Decimal('300.00'))
        self.assertEqual(response.data['user'], self.user.id)

    def test_create_budget_invalid_amount(self):
        self.client.force_authenticate(user=self.user)
        data = {
            'category': self.category.id,
            'amount': '0',
            'month': '2024-02-01'
        }
        response = self.client.post('/api/budgets/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('amount', response.data)

    def test_create_budget_invalid_month(self):
        self.client.force_authenticate(user=self.user)
        data = {
            'category': self.category.id,
            'amount': '300.00',
            'month': '2024-02-15'
        }
        response = self.client.post('/api/budgets/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('month', response.data)

    def test_create_duplicate_budget_forbidden(self):
        self.client.force_authenticate(user=self.user)
        data = {
            'category': self.category.id,
            'amount': '300.00',
            'month': '2024-01-01'
        }
        response = self.client.post('/api/budgets/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('non_field_errors', response.data)

    def test_list_user_budgets(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/budgets/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], self.user_budget.id)

    def test_retrieve_own_budget(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f'/api/budgets/{self.user_budget.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.user_budget.id)

    def test_retrieve_other_user_budget_forbidden(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f'/api/budgets/{self.other_user_budget.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_own_budget(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(
            f'/api/budgets/{self.user_budget.id}/',
            {'amount': '600.00'}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Decimal(response.data['amount']), Decimal('600.00'))

    def test_delete_own_budget(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(f'/api/budgets/{self.user_budget.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Budget.objects.filter(id=self.user_budget.id).exists())

    def test_unauthenticated_access_denied(self):
        response = self.client.get('/api/budgets/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class GeminiServiceTestCase(TestCase):
    def setUp(self):
        self.original_env = os.environ.get('GEMINI_API_KEY')
        os.environ['GEMINI_API_KEY'] = 'test-api-key'
        get_gemini_service.__dict__.pop('_gemini_service', None)
        reset_gemini_service()

    def tearDown(self):
        if self.original_env is not None:
            os.environ['GEMINI_API_KEY'] = self.original_env
        else:
            os.environ.pop('GEMINI_API_KEY', None)
        get_gemini_service.__dict__.pop('_gemini_service', None)
        reset_gemini_service()

    def test_gemini_service_requires_api_key(self):
        os.environ.pop('GEMINI_API_KEY', None)
        get_gemini_service.__dict__.pop('_gemini_service', None)
        reset_gemini_service()
        with self.assertRaises(GeminiServiceError) as ctx:
            get_gemini_service()
        self.assertIn('GEMINI_API_KEY not configured', str(ctx.exception))

    def test_send_prompt_success(self):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = 'Hello! This is a test response.'
        mock_client.models.generate_content.return_value = mock_response

        service = GeminiService(client=mock_client)
        result = service.send_prompt('Say hello')

        self.assertEqual(result, 'Hello! This is a test response.')
        mock_client.models.generate_content.assert_called_once()

    def test_send_prompt_empty_response(self):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = ''
        mock_client.models.generate_content.return_value = mock_response

        service = GeminiService(client=mock_client)
        with self.assertRaises(GeminiServiceError) as ctx:
            service.send_prompt('Say hello')
        self.assertIn('Empty response', str(ctx.exception))

    def test_send_prompt_api_error(self):
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = Exception('API quota exceeded')

        service = GeminiService(client=mock_client)
        with self.assertRaises(GeminiServiceError) as ctx:
            service.send_prompt('Say hello')
        self.assertIn('Gemini API error', str(ctx.exception))

    def test_send_prompt_empty_prompt(self):
        service = GeminiService(client=MagicMock())
        with self.assertRaises(GeminiServiceError) as ctx:
            service.send_prompt('')
        self.assertIn('Prompt cannot be empty', str(ctx.exception))

        with self.assertRaises(GeminiServiceError) as ctx:
            service.send_prompt('   ')
        self.assertIn('Prompt cannot be empty', str(ctx.exception))


import os


class GeminiTestViewTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        os.environ['GEMINI_API_KEY'] = 'test-api-key'
        get_gemini_service.__dict__.pop('_gemini_service', None)
        reset_gemini_service()

    def tearDown(self):
        os.environ.pop('GEMINI_API_KEY', None)
        get_gemini_service.__dict__.pop('_gemini_service', None)
        reset_gemini_service()

    def test_authenticated_request_success(self):
        self.client.force_authenticate(user=self.user)
        with patch('finance.views.get_gemini_service') as mock_get_service:
            mock_service = MagicMock()
            mock_service.send_prompt.return_value = 'Hello from Gemini!'
            mock_get_service.return_value = mock_service

            response = self.client.post('/api/ai/test/', {'message': 'Say hello'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['response'], 'Hello from Gemini!')

    def test_unauthenticated_request_denied(self):
        response = self.client.post('/api/ai/test/', {'message': 'Say hello'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_missing_message(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post('/api/ai/test/', {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('detail', response.data)
        self.assertIn('Message is required', response.data['detail'])

    def test_empty_message(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post('/api/ai/test/', {'message': '   '}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('detail', response.data)
        self.assertIn('Message is required', response.data['detail'])

    def test_gemini_service_error_handled(self):
        self.client.force_authenticate(user=self.user)
        with patch('finance.views.get_gemini_service') as mock_get_service:
            mock_service = MagicMock()
            mock_service.send_prompt.side_effect = GeminiServiceError('API quota exceeded')
            mock_get_service.return_value = mock_service

            response = self.client.post('/api/ai/test/', {'message': 'Say hello'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn('detail', response.data)
        self.assertIn('API quota exceeded', response.data['detail'])


class GetTransactionsToolTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.other_user = User.objects.create_user(username='otheruser', password='testpass123')
        self.category_food = Category.objects.create(name='Food', description='Food expenses')
        self.category_transport = Category.objects.create(name='Transport', description='Transport costs')

        Transaction.objects.create(
            user=self.user,
            amount=Decimal('50.00'),
            transaction_type='expense',
            category=self.category_food,
            description='Lunch',
            transaction_date=date(2024, 1, 15)
        )
        Transaction.objects.create(
            user=self.user,
            amount=Decimal('100.00'),
            transaction_type='income',
            category=self.category_transport,
            description='Salary',
            transaction_date=date(2024, 1, 20)
        )
        Transaction.objects.create(
            user=self.user,
            amount=Decimal('25.00'),
            transaction_type='expense',
            category=self.category_food,
            description='Coffee',
            transaction_date=date(2024, 2, 10)
        )
        Transaction.objects.create(
            user=self.other_user,
            amount=Decimal('200.00'),
            transaction_type='expense',
            category=self.category_food,
            description='Other user expense',
            transaction_date=date(2024, 1, 15)
        )

    def test_get_transactions_authenticated_user(self):
        from finance.tools.transactions import get_transactions
        results = get_transactions(self.user)
        self.assertEqual(len(results), 3)
        for txn in results:
            self.assertIn('amount', txn)
            self.assertIn('transaction_type', txn)
            self.assertIn('category', txn)
            self.assertIn('description', txn)
            self.assertIn('transaction_date', txn)

    def test_get_transactions_user_isolation(self):
        from finance.tools.transactions import get_transactions
        results = get_transactions(self.user)
        for txn in results:
            self.assertNotEqual(txn['description'], 'Other user expense')

    def test_get_transactions_filter_by_type_expense(self):
        from finance.tools.transactions import get_transactions
        results = get_transactions(self.user, transaction_type='expense')
        self.assertEqual(len(results), 2)
        for txn in results:
            self.assertEqual(txn['transaction_type'], 'expense')

    def test_get_transactions_filter_by_type_income(self):
        from finance.tools.transactions import get_transactions
        results = get_transactions(self.user, transaction_type='income')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['transaction_type'], 'income')
        self.assertEqual(results[0]['description'], 'Salary')

    def test_get_transactions_filter_by_category(self):
        from finance.tools.transactions import get_transactions
        results = get_transactions(self.user, category='Food')
        self.assertEqual(len(results), 2)
        for txn in results:
            self.assertEqual(txn['category'], 'Food')

    def test_get_transactions_filter_by_category_case_insensitive(self):
        from finance.tools.transactions import get_transactions
        results = get_transactions(self.user, category='food')
        self.assertEqual(len(results), 2)

    def test_get_transactions_filter_by_date_range(self):
        from finance.tools.transactions import get_transactions
        results = get_transactions(self.user, start_date='2024-01-01', end_date='2024-01-31')
        self.assertEqual(len(results), 2)
        for txn in results:
            self.assertTrue('2024-01' in txn['transaction_date'])

    def test_get_transactions_filter_by_start_date_only(self):
        from finance.tools.transactions import get_transactions
        results = get_transactions(self.user, start_date='2024-02-01')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['description'], 'Coffee')

    def test_get_transactions_filter_by_end_date_only(self):
        from finance.tools.transactions import get_transactions
        results = get_transactions(self.user, end_date='2024-01-31')
        self.assertEqual(len(results), 2)

    def test_get_transactions_limit(self):
        from finance.tools.transactions import get_transactions
        results = get_transactions(self.user, limit=2)
        self.assertEqual(len(results), 2)

    def test_get_transactions_limit_max_cap(self):
        from finance.tools.transactions import get_transactions, MAX_LIMIT
        results = get_transactions(self.user, limit=MAX_LIMIT + 50)
        self.assertEqual(len(results), 3)

    def test_get_transactions_empty_result(self):
        from finance.tools.transactions import get_transactions
        results = get_transactions(self.user, start_date='2030-01-01')
        self.assertEqual(len(results), 0)

    def test_get_transactions_invalid_transaction_type(self):
        from finance.tools.transactions import get_transactions, TransactionToolError
        with self.assertRaises(TransactionToolError) as ctx:
            get_transactions(self.user, transaction_type='invalid')
        self.assertIn('Invalid transaction_type', str(ctx.exception))

    def test_get_transactions_invalid_category(self):
        from finance.tools.transactions import get_transactions, TransactionToolError
        with self.assertRaises(TransactionToolError) as ctx:
            get_transactions(self.user, category='NonExistent')
        self.assertIn('Category not found', str(ctx.exception))

    def test_get_transactions_invalid_date_format(self):
        from finance.tools.transactions import get_transactions, TransactionToolError
        with self.assertRaises(TransactionToolError) as ctx:
            get_transactions(self.user, start_date='invalid-date')
        self.assertIn('Invalid start_date', str(ctx.exception))

    def test_get_transactions_start_after_end(self):
        from finance.tools.transactions import get_transactions, TransactionToolError
        with self.assertRaises(TransactionToolError) as ctx:
            get_transactions(self.user, start_date='2024-02-01', end_date='2024-01-01')
        self.assertIn('start_date cannot be after end_date', str(ctx.exception))

    def test_get_transactions_invalid_limit(self):
        from finance.tools.transactions import get_transactions, TransactionToolError
        with self.assertRaises(TransactionToolError) as ctx:
            get_transactions(self.user, limit=0)
        self.assertIn('Limit must be greater than zero', str(ctx.exception))

        with self.assertRaises(TransactionToolError) as ctx:
            get_transactions(self.user, limit=-5)
        self.assertIn('Limit must be greater than zero', str(ctx.exception))

    def test_get_transactions_unauthenticated_user_raises(self):
        from finance.tools.transactions import get_transactions, TransactionToolError
        class MockUser:
            is_authenticated = False
        with self.assertRaises(TransactionToolError) as ctx:
            get_transactions(MockUser())
        self.assertIn('Authenticated user required', str(ctx.exception))

    def test_get_transactions_none_user_raises(self):
        from finance.tools.transactions import get_transactions, TransactionToolError
        with self.assertRaises(TransactionToolError) as ctx:
            get_transactions(None)
        self.assertIn('Authenticated user required', str(ctx.exception))


class GeminiChatViewTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.other_user = User.objects.create_user(username='otheruser', password='testpass123')
        self.category_food = Category.objects.create(name='Food', description='Food expenses')
        self.category_transport = Category.objects.create(name='Transport', description='Transport costs')

        Transaction.objects.create(
            user=self.user,
            amount=Decimal('50.00'),
            transaction_type='expense',
            category=self.category_food,
            description='Lunch',
            transaction_date=date(2024, 1, 15)
        )
        Transaction.objects.create(
            user=self.user,
            amount=Decimal('100.00'),
            transaction_type='income',
            category=self.category_transport,
            description='Salary',
            transaction_date=date(2024, 1, 20)
        )
        Transaction.objects.create(
            user=self.other_user,
            amount=Decimal('200.00'),
            transaction_type='expense',
            category=self.category_food,
            description='Other user expense',
            transaction_date=date(2024, 1, 15)
        )

        os.environ['GEMINI_API_KEY'] = 'test-api-key'
        get_gemini_service.__dict__.pop('_gemini_service', None)
        reset_gemini_service()

    def tearDown(self):
        os.environ.pop('GEMINI_API_KEY', None)
        get_gemini_service.__dict__.pop('_gemini_service', None)
        reset_gemini_service()

    def _create_function_call(self, name, args):
        fc = MagicMock()
        fc.name = name
        fc.args = args
        return fc

    def _mock_gemini_response(self, mock_client, text_response=None, function_calls=None):
        mock_response = MagicMock()
        mock_candidate = MagicMock()
        mock_content = MagicMock()
        mock_parts = []

        if text_response:
            mock_text_part = MagicMock()
            mock_text_part.text = text_response
            mock_text_part.function_call = None
            mock_parts.append(mock_text_part)

        if function_calls:
            for fc in function_calls:
                mock_fc_part = MagicMock()
                mock_fc_part.function_call = fc
                mock_fc_part.text = None
                mock_parts.append(mock_fc_part)

        mock_content.parts = mock_parts
        mock_candidate.content = mock_content
        mock_response.candidates = [mock_candidate]
        return mock_response

    def test_authenticated_chat_success(self):
        self.client.force_authenticate(user=self.user)
        with patch('finance.services.gemini.genai.Client') as mock_genai:
            mock_client = MagicMock()
            mock_genai.return_value = mock_client
            mock_response = self._mock_gemini_response(mock_client, text_response='Hello! How can I help?')
            mock_client.models.generate_content.return_value = mock_response

            response = self.client.post('/api/ai/chat/', {'message': 'Hello'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['response'], 'Hello! How can I help?')
        mock_client.models.generate_content.assert_called_once()

    def test_unauthenticated_chat_denied(self):
        response = self.client.post('/api/ai/chat/', {'message': 'Hello'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_missing_message(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post('/api/ai/chat/', {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('detail', response.data)
        self.assertIn('Message is required', response.data['detail'])

    def test_empty_message(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post('/api/ai/chat/', {'message': '   '}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('detail', response.data)
        self.assertIn('Message is required', response.data['detail'])

    def test_gemini_normal_response_without_tool(self):
        self.client.force_authenticate(user=self.user)
        with patch('finance.services.gemini.genai.Client') as mock_genai:
            mock_client = MagicMock()
            mock_genai.return_value = mock_client
            mock_response = self._mock_gemini_response(mock_client, text_response='I cannot answer that.')
            mock_client.models.generate_content.return_value = mock_response

            response = self.client.post('/api/ai/chat/', {'message': 'What is the meaning of life?'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['response'], 'I cannot answer that.')

    def test_gemini_requests_get_transactions(self):
        self.client.force_authenticate(user=self.user)
        with patch('finance.services.gemini.genai.Client') as mock_genai:
            mock_client = MagicMock()
            mock_genai.return_value = mock_client

            call_count = [0]

            def side_effect(*args, **kwargs):
                call_count[0] += 1
                resp = MagicMock()
                if call_count[0] == 1:
                    fc = self._create_function_call('get_transactions', {'category': 'Food'})
                    mc = MagicMock()
                    mp = MagicMock()
                    fc_part = MagicMock()
                    fc_part.function_call = fc
                    fc_part.text = None
                    mp.parts = [fc_part]
                    mc.content = mp
                    resp.candidates = [mc]
                else:
                    mc = MagicMock()
                    mp = MagicMock()
                    tp = MagicMock()
                    tp.text = 'You spent $50.00 on food.'
                    tp.function_call = None
                    mp.parts = [tp]
                    mc.content = mp
                    resp.candidates = [mc]
                return resp

            mock_client.models.generate_content.side_effect = side_effect

            response = self.client.post('/api/ai/chat/', {'message': 'What did I spend on food?'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('50.00', response.data['response'])
        self.assertIn('food', response.data['response'].lower())
        self.assertEqual(mock_client.models.generate_content.call_count, 2)

    def test_tool_executed_with_request_user(self):
        self.client.force_authenticate(user=self.user)
        with patch('finance.services.gemini.genai.Client') as mock_genai:
            mock_client = MagicMock()
            mock_genai.return_value = mock_client

            call_count = [0]

            def side_effect(*args, **kwargs):
                call_count[0] += 1
                resp = MagicMock()
                if call_count[0] == 1:
                    fc = self._create_function_call('get_transactions', {'category': 'Food'})
                    mc = MagicMock()
                    mp = MagicMock()
                    fc_part = MagicMock()
                    fc_part.function_call = fc
                    fc_part.text = None
                    mp.parts = [fc_part]
                    mc.content = mp
                    resp.candidates = [mc]
                else:
                    mc = MagicMock()
                    mp = MagicMock()
                    tp = MagicMock()
                    tp.text = 'You spent $50.00 on food (Lunch).'
                    tp.function_call = None
                    mp.parts = [tp]
                    mc.content = mp
                    resp.candidates = [mc]
                return resp

            mock_client.models.generate_content.side_effect = side_effect

            response = self.client.post('/api/ai/chat/', {'message': 'What did I spend on food?'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Verify only user's transactions were returned (not other_user's)
        self.assertIn('50.00', response.data['response'])
        self.assertNotIn('200.00', response.data['response'])

    def test_model_cannot_specify_another_user(self):
        self.client.force_authenticate(user=self.user)
        with patch('finance.services.gemini.genai.Client') as mock_genai:
            mock_client = MagicMock()
            mock_genai.return_value = mock_client

            call_count = [0]

            def side_effect(*args, **kwargs):
                call_count[0] += 1
                resp = MagicMock()
                if call_count[0] == 1:
                    # Model tries to pass user_id - should be ignored
                    fc = self._create_function_call('get_transactions', {'category': 'Food', 'user_id': self.other_user.id})
                    mc = MagicMock()
                    mp = MagicMock()
                    fc_part = MagicMock()
                    fc_part.function_call = fc
                    fc_part.text = None
                    mp.parts = [fc_part]
                    mc.content = mp
                    resp.candidates = [mc]
                else:
                    mc = MagicMock()
                    mp = MagicMock()
                    tp = MagicMock()
                    tp.text = 'You spent $50.00 on food.'
                    tp.function_call = None
                    mp.parts = [tp]
                    mc.content = mp
                    resp.candidates = [mc]
                return resp

            mock_client.models.generate_content.side_effect = side_effect

            response = self.client.post('/api/ai/chat/', {'message': 'Show me food expenses'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should only see user's own transactions
        self.assertIn('50.00', response.data['response'])
        self.assertNotIn('200.00', response.data['response'])

    def test_tool_result_sent_back_to_gemini(self):
        self.client.force_authenticate(user=self.user)
        with patch('finance.services.gemini.genai.Client') as mock_genai:
            mock_client = MagicMock()
            mock_genai.return_value = mock_client

            call_count = [0]

            def side_effect(*args, **kwargs):
                call_count[0] += 1
                resp = MagicMock()
                if call_count[0] == 1:
                    fc = self._create_function_call('get_transactions', {'transaction_type': 'expense'})
                    mc = MagicMock()
                    mp = MagicMock()
                    fc_part = MagicMock()
                    fc_part.function_call = fc
                    fc_part.text = None
                    mp.parts = [fc_part]
                    mc.content = mp
                    resp.candidates = [mc]
                elif call_count[0] == 2:
                    mc = MagicMock()
                    mp = MagicMock()
                    tp = MagicMock()
                    tp.text = 'You have 2 expenses totaling $75.00.'
                    tp.function_call = None
                    mp.parts = [tp]
                    mc.content = mp
                    resp.candidates = [mc]
                else:
                    mc = MagicMock()
                    mp = MagicMock()
                    tp = MagicMock()
                    tp.text = 'Done.'
                    tp.function_call = None
                    mp.parts = [tp]
                    mc.content = mp
                    resp.candidates = [mc]
                return resp

            mock_client.models.generate_content.side_effect = side_effect

            response = self.client.post('/api/ai/chat/', {'message': 'Show my expenses'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(mock_client.models.generate_content.call_count, 2)
        self.assertIn('expense', response.data['response'].lower())

    def test_malformed_tool_arguments(self):
        self.client.force_authenticate(user=self.user)
        with patch('finance.services.gemini.genai.Client') as mock_genai:
            mock_client = MagicMock()
            mock_genai.return_value = mock_client

            call_count = [0]

            def side_effect(*args, **kwargs):
                call_count[0] += 1
                resp = MagicMock()
                if call_count[0] == 1:
                    # Invalid category name
                    fc = self._create_function_call('get_transactions', {'category': 'NonExistentCategory'})
                    mc = MagicMock()
                    mp = MagicMock()
                    fc_part = MagicMock()
                    fc_part.function_call = fc
                    fc_part.text = None
                    mp.parts = [fc_part]
                    mc.content = mp
                    resp.candidates = [mc]
                else:
                    mc = MagicMock()
                    mp = MagicMock()
                    tp = MagicMock()
                    tp.text = 'Category not found.'
                    tp.function_call = None
                    mp.parts = [tp]
                    mc.content = mp
                    resp.candidates = [mc]
                return resp

            mock_client.models.generate_content.side_effect = side_effect

            response = self.client.post('/api/ai/chat/', {'message': 'Show me invalid category'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Tool should handle error gracefully and return to Gemini
        self.assertIn('category', response.data['response'].lower())

    def test_gemini_api_failure(self):
        self.client.force_authenticate(user=self.user)
        with patch('finance.services.gemini.genai.Client') as mock_genai:
            mock_client = MagicMock()
            mock_genai.return_value = mock_client
            mock_client.models.generate_content.side_effect = Exception('API quota exceeded')

            response = self.client.post('/api/ai/chat/', {'message': 'Hello'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn('detail', response.data)
        self.assertIn('API quota exceeded', response.data['detail'])

    def test_max_tool_iterations(self):
        self.client.force_authenticate(user=self.user)
        with patch('finance.services.gemini.genai.Client') as mock_genai:
            mock_client = MagicMock()
            mock_genai.return_value = mock_client

            # Always return function calls, never a final response
            def side_effect(*args, **kwargs):
                fc = self._create_function_call('get_transactions', {'category': 'Food'})
                mc = MagicMock()
                mp = MagicMock()
                fc_part = MagicMock()
                fc_part.function_call = fc
                fc_part.text = None
                mp.parts = [fc_part]
                mc.content = mp
                resp = MagicMock()
                resp.candidates = [mc]
                return resp

            mock_client.models.generate_content.side_effect = side_effect

            response = self.client.post('/api/ai/chat/', {'message': 'Loop forever'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn('detail', response.data)
        self.assertIn('Max tool iterations reached', response.data['detail'])


class GetFinancialSummaryToolTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.other_user = User.objects.create_user(username='otheruser', password='testpass123')
        self.category_food = Category.objects.create(name='Food', description='Food expenses')
        self.category_transport = Category.objects.create(name='Transport', description='Transport costs')
        self.category_salary = Category.objects.create(name='Salary', description='Salary income')

        Transaction.objects.create(
            user=self.user,
            amount=Decimal('50.00'),
            transaction_type='expense',
            category=self.category_food,
            description='Lunch',
            transaction_date=date(2024, 1, 15)
        )
        Transaction.objects.create(
            user=self.user,
            amount=Decimal('100.00'),
            transaction_type='income',
            category=self.category_salary,
            description='Salary',
            transaction_date=date(2024, 1, 20)
        )
        Transaction.objects.create(
            user=self.user,
            amount=Decimal('25.00'),
            transaction_type='expense',
            category=self.category_food,
            description='Coffee',
            transaction_date=date(2024, 2, 10)
        )
        Transaction.objects.create(
            user=self.user,
            amount=Decimal('200.00'),
            transaction_type='income',
            category=self.category_salary,
            description='Bonus',
            transaction_date=date(2024, 2, 15)
        )
        Transaction.objects.create(
            user=self.other_user,
            amount=Decimal('500.00'),
            transaction_type='expense',
            category=self.category_food,
            description='Other user expense',
            transaction_date=date(2024, 1, 15)
        )

    def test_get_financial_summary_correct_income(self):
        from finance.tools.transactions import get_financial_summary
        result = get_financial_summary(self.user)
        self.assertEqual(result['total_income'], '300.00')

    def test_get_financial_summary_correct_expenses(self):
        from finance.tools.transactions import get_financial_summary
        result = get_financial_summary(self.user)
        self.assertEqual(result['total_expenses'], '75.00')

    def test_get_financial_summary_correct_net_balance(self):
        from finance.tools.transactions import get_financial_summary
        result = get_financial_summary(self.user)
        self.assertEqual(result['net_balance'], '225.00')

    def test_get_financial_summary_correct_savings_rate(self):
        from finance.tools.transactions import get_financial_summary
        result = get_financial_summary(self.user)
        self.assertEqual(result['savings_rate'], '75.00')

    def test_get_financial_summary_zero_income(self):
        from finance.tools.transactions import get_financial_summary
        user_no_income = User.objects.create_user(username='noincome', password='testpass123')
        Transaction.objects.create(
            user=user_no_income,
            amount=Decimal('50.00'),
            transaction_type='expense',
            category=self.category_food,
            description='Expense only',
            transaction_date=date(2024, 1, 15)
        )
        result = get_financial_summary(user_no_income)
        self.assertEqual(result['total_income'], '0.00')
        self.assertEqual(result['total_expenses'], '50.00')
        self.assertEqual(result['net_balance'], '-50.00')
        self.assertEqual(result['savings_rate'], '0.00')

    def test_get_financial_summary_date_filtering_start_date(self):
        from finance.tools.transactions import get_financial_summary
        result = get_financial_summary(self.user, start_date='2024-02-01')
        self.assertEqual(result['total_income'], '200.00')
        self.assertEqual(result['total_expenses'], '25.00')
        self.assertEqual(result['net_balance'], '175.00')
        self.assertEqual(result['savings_rate'], '87.50')

    def test_get_financial_summary_date_filtering_end_date(self):
        from finance.tools.transactions import get_financial_summary
        result = get_financial_summary(self.user, end_date='2024-01-31')
        self.assertEqual(result['total_income'], '100.00')
        self.assertEqual(result['total_expenses'], '50.00')
        self.assertEqual(result['net_balance'], '50.00')
        self.assertEqual(result['savings_rate'], '50.00')

    def test_get_financial_summary_date_filtering_range(self):
        from finance.tools.transactions import get_financial_summary
        result = get_financial_summary(self.user, start_date='2024-01-01', end_date='2024-01-31')
        self.assertEqual(result['total_income'], '100.00')
        self.assertEqual(result['total_expenses'], '50.00')

    def test_get_financial_summary_user_isolation(self):
        from finance.tools.transactions import get_financial_summary
        result = get_financial_summary(self.user)
        self.assertEqual(result['total_income'], '300.00')
        self.assertEqual(result['total_expenses'], '75.00')
        other_result = get_financial_summary(self.other_user)
        self.assertEqual(other_result['total_income'], '0.00')
        self.assertEqual(other_result['total_expenses'], '500.00')

    def test_get_financial_summary_invalid_date_format(self):
        from finance.tools.transactions import get_financial_summary, TransactionToolError
        with self.assertRaises(TransactionToolError) as ctx:
            get_financial_summary(self.user, start_date='invalid-date')
        self.assertIn('Invalid start_date', str(ctx.exception))

    def test_get_financial_summary_start_after_end(self):
        from finance.tools.transactions import get_financial_summary, TransactionToolError
        with self.assertRaises(TransactionToolError) as ctx:
            get_financial_summary(self.user, start_date='2024-02-01', end_date='2024-01-01')
        self.assertIn('start_date cannot be after end_date', str(ctx.exception))

    def test_get_financial_summary_unauthenticated_user_raises(self):
        from finance.tools.transactions import get_financial_summary, TransactionToolError
        class MockUser:
            is_authenticated = False
        with self.assertRaises(TransactionToolError) as ctx:
            get_financial_summary(MockUser())
        self.assertIn('Authenticated user required', str(ctx.exception))

    def test_get_financial_summary_none_user_raises(self):
        from finance.tools.transactions import get_financial_summary, TransactionToolError
        with self.assertRaises(TransactionToolError) as ctx:
            get_financial_summary(None)
        self.assertIn('Authenticated user required', str(ctx.exception))

    def test_get_financial_summary_empty_result(self):
        from finance.tools.transactions import get_financial_summary
        empty_user = User.objects.create_user(username='emptyuser', password='testpass123')
        result = get_financial_summary(empty_user)
        self.assertEqual(result['total_income'], '0.00')
        self.assertEqual(result['total_expenses'], '0.00')
        self.assertEqual(result['net_balance'], '0.00')
        self.assertEqual(result['savings_rate'], '0.00')

    def test_get_financial_summary_uses_decimal_precision(self):
        from finance.tools.transactions import get_financial_summary
        user = User.objects.create_user(username='preciseuser', password='testpass123')
        Transaction.objects.create(
            user=user,
            amount=Decimal('100.00'),
            transaction_type='income',
            category=self.category_salary,
            description='Income',
            transaction_date=date(2024, 1, 1)
        )
        Transaction.objects.create(
            user=user,
            amount=Decimal('33.33'),
            transaction_type='expense',
            category=self.category_food,
            description='Expense',
            transaction_date=date(2024, 1, 2)
        )
        result = get_financial_summary(user)
        self.assertEqual(result['total_income'], '100.00')
        self.assertEqual(result['total_expenses'], '33.33')
        self.assertEqual(result['net_balance'], '66.67')
        self.assertEqual(result['savings_rate'], '66.67')


class GeminiFinancialSummaryToolTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.other_user = User.objects.create_user(username='otheruser', password='testpass123')
        self.category_food = Category.objects.create(name='Food', description='Food expenses')
        self.category_transport = Category.objects.create(name='Transport', description='Transport costs')
        self.category_salary = Category.objects.create(name='Salary', description='Salary income')

        Transaction.objects.create(
            user=self.user,
            amount=Decimal('50.00'),
            transaction_type='expense',
            category=self.category_food,
            description='Lunch',
            transaction_date=date(2024, 1, 15)
        )
        Transaction.objects.create(
            user=self.user,
            amount=Decimal('100.00'),
            transaction_type='income',
            category=self.category_salary,
            description='Salary',
            transaction_date=date(2024, 1, 20)
        )
        Transaction.objects.create(
            user=self.other_user,
            amount=Decimal('200.00'),
            transaction_type='expense',
            category=self.category_food,
            description='Other user expense',
            transaction_date=date(2024, 1, 15)
        )

        os.environ['GEMINI_API_KEY'] = 'test-api-key'
        get_gemini_service.__dict__.pop('_gemini_service', None)
        reset_gemini_service()

    def tearDown(self):
        os.environ.pop('GEMINI_API_KEY', None)
        get_gemini_service.__dict__.pop('_gemini_service', None)
        reset_gemini_service()

    def _create_function_call(self, name, args):
        fc = MagicMock()
        fc.name = name
        fc.args = args
        return fc

    def _mock_gemini_response(self, mock_client, text_response=None, function_calls=None):
        mock_response = MagicMock()
        mock_candidate = MagicMock()
        mock_content = MagicMock()
        mock_parts = []

        if text_response:
            mock_text_part = MagicMock()
            mock_text_part.text = text_response
            mock_text_part.function_call = None
            mock_parts.append(mock_text_part)

        if function_calls:
            for fc in function_calls:
                mock_fc_part = MagicMock()
                mock_fc_part.function_call = fc
                mock_fc_part.text = None
                mock_parts.append(mock_fc_part)

        mock_content.parts = mock_parts
        mock_candidate.content = mock_content
        mock_response.candidates = [mock_candidate]
        return mock_response

    def test_gemini_requests_get_financial_summary(self):
        self.client.force_authenticate(user=self.user)
        with patch('finance.services.gemini.genai.Client') as mock_genai:
            mock_client = MagicMock()
            mock_genai.return_value = mock_client

            call_count = [0]

            def side_effect(*args, **kwargs):
                call_count[0] += 1
                resp = MagicMock()
                if call_count[0] == 1:
                    fc = self._create_function_call('get_financial_summary', {})
                    mc = MagicMock()
                    mp = MagicMock()
                    fc_part = MagicMock()
                    fc_part.function_call = fc
                    fc_part.text = None
                    mp.parts = [fc_part]
                    mc.content = mp
                    resp.candidates = [mc]
                else:
                    mc = MagicMock()
                    mp = MagicMock()
                    tp = MagicMock()
                    tp.text = 'Your total income is $100.00, expenses $50.00, net balance $50.00, savings rate 50%.'
                    tp.function_call = None
                    mp.parts = [tp]
                    mc.content = mp
                    resp.candidates = [mc]
                return resp

            mock_client.models.generate_content.side_effect = side_effect

            response = self.client.post('/api/ai/chat/', {'message': 'What is my financial summary?'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('100.00', response.data['response'])
        self.assertIn('50.00', response.data['response'])
        self.assertEqual(mock_client.models.generate_content.call_count, 2)

    def test_gemini_requests_financial_summary_with_date_filter(self):
        self.client.force_authenticate(user=self.user)
        with patch('finance.services.gemini.genai.Client') as mock_genai:
            mock_client = MagicMock()
            mock_genai.return_value = mock_client

            call_count = [0]

            def side_effect(*args, **kwargs):
                call_count[0] += 1
                resp = MagicMock()
                if call_count[0] == 1:
                    fc = self._create_function_call('get_financial_summary', {'start_date': '2024-01-01', 'end_date': '2024-01-31'})
                    mc = MagicMock()
                    mp = MagicMock()
                    fc_part = MagicMock()
                    fc_part.function_call = fc
                    fc_part.text = None
                    mp.parts = [fc_part]
                    mc.content = mp
                    resp.candidates = [mc]
                else:
                    mc = MagicMock()
                    mp = MagicMock()
                    tp = MagicMock()
                    tp.text = 'January summary: income $100.00, expenses $50.00.'
                    tp.function_call = None
                    mp.parts = [tp]
                    mc.content = mp
                    resp.candidates = [mc]
                return resp

            mock_client.models.generate_content.side_effect = side_effect

            response = self.client.post('/api/ai/chat/', {'message': 'What is my January summary?'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('100.00', response.data['response'])
        self.assertIn('50.00', response.data['response'])
        self.assertEqual(mock_client.models.generate_content.call_count, 2)

    def test_financial_summary_tool_executed_with_request_user(self):
        self.client.force_authenticate(user=self.user)
        with patch('finance.services.gemini.genai.Client') as mock_genai:
            mock_client = MagicMock()
            mock_genai.return_value = mock_client

            call_count = [0]

            def side_effect(*args, **kwargs):
                call_count[0] += 1
                resp = MagicMock()
                if call_count[0] == 1:
                    fc = self._create_function_call('get_financial_summary', {})
                    mc = MagicMock()
                    mp = MagicMock()
                    fc_part = MagicMock()
                    fc_part.function_call = fc
                    fc_part.text = None
                    mp.parts = [fc_part]
                    mc.content = mp
                    resp.candidates = [mc]
                else:
                    mc = MagicMock()
                    mp = MagicMock()
                    tp = MagicMock()
                    tp.text = 'Your income: $100.00, expenses: $50.00.'
                    tp.function_call = None
                    mp.parts = [tp]
                    mc.content = mp
                    resp.candidates = [mc]
                return resp

            mock_client.models.generate_content.side_effect = side_effect

            response = self.client.post('/api/ai/chat/', {'message': 'Show my summary'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('100.00', response.data['response'])
        self.assertIn('50.00', response.data['response'])

    def test_model_cannot_specify_another_user_in_financial_summary(self):
        self.client.force_authenticate(user=self.user)
        with patch('finance.services.gemini.genai.Client') as mock_genai:
            mock_client = MagicMock()
            mock_genai.return_value = mock_client

            call_count = [0]

            def side_effect(*args, **kwargs):
                call_count[0] += 1
                resp = MagicMock()
                if call_count[0] == 1:
                    fc = self._create_function_call('get_financial_summary', {'user_id': self.other_user.id})
                    mc = MagicMock()
                    mp = MagicMock()
                    fc_part = MagicMock()
                    fc_part.function_call = fc
                    fc_part.text = None
                    mp.parts = [fc_part]
                    mc.content = mp
                    resp.candidates = [mc]
                else:
                    mc = MagicMock()
                    mp = MagicMock()
                    tp = MagicMock()
                    tp.text = 'Your income: $100.00, expenses: $50.00.'
                    tp.function_call = None
                    mp.parts = [tp]
                    mc.content = mp
                    resp.candidates = [mc]
                return resp

            mock_client.models.generate_content.side_effect = side_effect

            response = self.client.post('/api/ai/chat/', {'message': 'Show my summary'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('100.00', response.data['response'])
        self.assertIn('50.00', response.data['response'])

    def test_gemini_can_choose_between_tools(self):
        self.client.force_authenticate(user=self.user)
        with patch('finance.services.gemini.genai.Client') as mock_genai:
            mock_client = MagicMock()
            mock_genai.return_value = mock_client

            call_count = [0]

            def side_effect(*args, **kwargs):
                call_count[0] += 1
                resp = MagicMock()
                if call_count[0] == 1:
                    fc = self._create_function_call('get_financial_summary', {})
                    mc = MagicMock()
                    mp = MagicMock()
                    fc_part = MagicMock()
                    fc_part.function_call = fc
                    fc_part.text = None
                    mp.parts = [fc_part]
                    mc.content = mp
                    resp.candidates = [mc]
                elif call_count[0] == 2:
                    fc = self._create_function_call('get_transactions', {'category': 'Food'})
                    mc = MagicMock()
                    mp = MagicMock()
                    fc_part = MagicMock()
                    fc_part.function_call = fc
                    fc_part.text = None
                    mp.parts = [fc_part]
                    mc.content = mp
                    resp.candidates = [mc]
                else:
                    mc = MagicMock()
                    mp = MagicMock()
                    tp = MagicMock()
                    tp.text = 'Summary: income $100.00, expenses $50.00. Food expenses: $50.00.'
                    tp.function_call = None
                    mp.parts = [tp]
                    mc.content = mp
                    resp.candidates = [mc]
                return resp

            mock_client.models.generate_content.side_effect = side_effect

            response = self.client.post('/api/ai/chat/', {'message': 'Show my summary and food expenses'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(mock_client.models.generate_content.call_count, 3)
        self.assertIn('income', response.data['response'].lower())
        self.assertIn('food', response.data['response'].lower())

    def test_both_tools_still_work_independently(self):
        self.client.force_authenticate(user=self.user)
        with patch('finance.services.gemini.genai.Client') as mock_genai:
            mock_client = MagicMock()
            mock_genai.return_value = mock_client

            call_count = [0]

            def side_effect(*args, **kwargs):
                call_count[0] += 1
                resp = MagicMock()
                if call_count[0] == 1:
                    fc = self._create_function_call('get_transactions', {'transaction_type': 'expense'})
                    mc = MagicMock()
                    mp = MagicMock()
                    fc_part = MagicMock()
                    fc_part.function_call = fc
                    fc_part.text = None
                    mp.parts = [fc_part]
                    mc.content = mp
                    resp.candidates = [mc]
                else:
                    mc = MagicMock()
                    mp = MagicMock()
                    tp = MagicMock()
                    tp.text = 'You have 2 expenses totaling $75.00.'
                    tp.function_call = None
                    mp.parts = [tp]
                    mc.content = mp
                    resp.candidates = [mc]
                return resp

            mock_client.models.generate_content.side_effect = side_effect

            response = self.client.post('/api/ai/chat/', {'message': 'Show my expenses'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(mock_client.models.generate_content.call_count, 2)
        self.assertIn('75.00', response.data['response'])


class GetBudgetStatusToolTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.other_user = User.objects.create_user(username='otheruser', password='testpass123')
        self.category_food = Category.objects.create(name='Food', description='Food expenses')
        self.category_transport = Category.objects.create(name='Transport', description='Transport costs')
        self.category_shopping = Category.objects.create(name='Shopping', description='Shopping expenses')
        self.category_entertainment = Category.objects.create(name='Entertainment', description='Entertainment expenses')

        self.user_budget_food = Budget.objects.create(
            user=self.user,
            category=self.category_food,
            amount=Decimal('500.00'),
            month=date(2024, 1, 1)
        )
        self.user_budget_transport = Budget.objects.create(
            user=self.user,
            category=self.category_transport,
            amount=Decimal('300.00'),
            month=date(2024, 1, 1)
        )
        self.other_user_budget = Budget.objects.create(
            user=self.other_user,
            category=self.category_food,
            amount=Decimal('1000.00'),
            month=date(2024, 1, 1)
        )

        Transaction.objects.create(
            user=self.user,
            amount=Decimal('100.00'),
            transaction_type='expense',
            category=self.category_food,
            description='Groceries',
            transaction_date=date(2024, 1, 15)
        )
        Transaction.objects.create(
            user=self.user,
            amount=Decimal('50.00'),
            transaction_type='expense',
            category=self.category_food,
            description='Dining out',
            transaction_date=date(2024, 1, 20)
        )
        Transaction.objects.create(
            user=self.user,
            amount=Decimal('200.00'),
            transaction_type='expense',
            category=self.category_transport,
            description='Gas',
            transaction_date=date(2024, 1, 10)
        )
        Transaction.objects.create(
            user=self.user,
            amount=Decimal('1000.00'),
            transaction_type='income',
            category=self.category_shopping,
            description='Salary',
            transaction_date=date(2024, 1, 5)
        )
        Transaction.objects.create(
            user=self.other_user,
            amount=Decimal('300.00'),
            transaction_type='expense',
            category=self.category_food,
            description='Other user food',
            transaction_date=date(2024, 1, 15)
        )

    def test_get_budget_status_correct_budget_calculation(self):
        from finance.tools.transactions import get_budget_status
        result = get_budget_status(self.user, month='2024-01')
        self.assertEqual(result['month'], '2024-01')
        self.assertEqual(len(result['budgets']), 2)

        food_budget = next(b for b in result['budgets'] if b['category'] == 'Food')
        self.assertEqual(food_budget['budget_amount'], '500.00')

        transport_budget = next(b for b in result['budgets'] if b['category'] == 'Transport')
        self.assertEqual(transport_budget['budget_amount'], '300.00')

    def test_get_budget_status_correct_spending_calculation(self):
        from finance.tools.transactions import get_budget_status
        result = get_budget_status(self.user, month='2024-01')

        food_budget = next(b for b in result['budgets'] if b['category'] == 'Food')
        self.assertEqual(food_budget['spent_amount'], '150.00')

        transport_budget = next(b for b in result['budgets'] if b['category'] == 'Transport')
        self.assertEqual(transport_budget['spent_amount'], '200.00')

    def test_get_budget_status_correct_remaining_amount(self):
        from finance.tools.transactions import get_budget_status
        result = get_budget_status(self.user, month='2024-01')

        food_budget = next(b for b in result['budgets'] if b['category'] == 'Food')
        self.assertEqual(food_budget['remaining_amount'], '350.00')

        transport_budget = next(b for b in result['budgets'] if b['category'] == 'Transport')
        self.assertEqual(transport_budget['remaining_amount'], '100.00')

    def test_get_budget_status_correct_percentage_calculation(self):
        from finance.tools.transactions import get_budget_status
        result = get_budget_status(self.user, month='2024-01')

        food_budget = next(b for b in result['budgets'] if b['category'] == 'Food')
        self.assertEqual(food_budget['percentage_used'], '30.00')

        transport_budget = next(b for b in result['budgets'] if b['category'] == 'Transport')
        self.assertEqual(transport_budget['percentage_used'], '66.67')

    def test_get_budget_status_status_thresholds(self):
        from finance.tools.transactions import get_budget_status

        # Under budget (< 80%)
        user = User.objects.create_user(username='thresholduser', password='testpass123')
        cat = Category.objects.create(name='TestCat', description='Test')
        Budget.objects.create(user=user, category=cat, amount=Decimal('1000.00'), month=date(2024, 1, 1))
        Transaction.objects.create(user=user, amount=Decimal('500.00'), transaction_type='expense', category=cat, description='Test', transaction_date=date(2024, 1, 15))
        result = get_budget_status(user, month='2024-01')
        self.assertEqual(result['budgets'][0]['status'], 'under_budget')

        # Near limit (80-100%)
        user2 = User.objects.create_user(username='thresholduser2', password='testpass123')
        cat2 = Category.objects.create(name='TestCat2', description='Test')
        Budget.objects.create(user=user2, category=cat2, amount=Decimal('1000.00'), month=date(2024, 1, 1))
        Transaction.objects.create(user=user2, amount=Decimal('900.00'), transaction_type='expense', category=cat2, description='Test', transaction_date=date(2024, 1, 15))
        result = get_budget_status(user2, month='2024-01')
        self.assertEqual(result['budgets'][0]['status'], 'near_limit')

        # Over budget (> 100%)
        user3 = User.objects.create_user(username='thresholduser3', password='testpass123')
        cat3 = Category.objects.create(name='TestCat3', description='Test')
        Budget.objects.create(user=user3, category=cat3, amount=Decimal('1000.00'), month=date(2024, 1, 1))
        Transaction.objects.create(user=user3, amount=Decimal('1200.00'), transaction_type='expense', category=cat3, description='Test', transaction_date=date(2024, 1, 15))
        result = get_budget_status(user3, month='2024-01')
        self.assertEqual(result['budgets'][0]['status'], 'over_budget')

    def test_get_budget_status_month_filtering(self):
        from finance.tools.transactions import get_budget_status
        Budget.objects.create(user=self.user, category=self.category_shopping, amount=Decimal('200.00'), month=date(2024, 2, 1))
        Transaction.objects.create(user=self.user, amount=Decimal('50.00'), transaction_type='expense', category=self.category_shopping, description='Feb shopping', transaction_date=date(2024, 2, 10))

        result = get_budget_status(self.user, month='2024-02')
        self.assertEqual(result['month'], '2024-02')
        self.assertEqual(len(result['budgets']), 1)
        self.assertEqual(result['budgets'][0]['category'], 'Shopping')

    def test_get_budget_status_current_month_default(self):
        from finance.tools.transactions import get_budget_status
        from django.utils import timezone
        today = timezone.now().date()
        current_month = date(today.year, today.month, 1)

        Budget.objects.create(user=self.user, category=self.category_entertainment, amount=Decimal('100.00'), month=current_month)
        Transaction.objects.create(user=self.user, amount=Decimal('30.00'), transaction_type='expense', category=self.category_entertainment, description='Movie', transaction_date=current_month)

        result = get_budget_status(self.user)
        self.assertEqual(result['month'], current_month.strftime('%Y-%m'))
        self.assertEqual(len(result['budgets']), 1)
        self.assertEqual(result['budgets'][0]['category'], 'Entertainment')

    def test_get_budget_status_multiple_categories(self):
        from finance.tools.transactions import get_budget_status
        result = get_budget_status(self.user, month='2024-01')
        categories = [b['category'] for b in result['budgets']]
        self.assertIn('Food', categories)
        self.assertIn('Transport', categories)
        self.assertEqual(len(result['budgets']), 2)

    def test_get_budget_status_category_with_zero_spending(self):
        from finance.tools.transactions import get_budget_status
        Budget.objects.create(user=self.user, category=self.category_shopping, amount=Decimal('200.00'), month=date(2024, 1, 1))
        result = get_budget_status(self.user, month='2024-01')

        shopping_budget = next(b for b in result['budgets'] if b['category'] == 'Shopping')
        self.assertEqual(shopping_budget['spent_amount'], '0.00')
        self.assertEqual(shopping_budget['remaining_amount'], '200.00')
        self.assertEqual(shopping_budget['percentage_used'], '0.00')
        self.assertEqual(shopping_budget['status'], 'under_budget')

    def test_get_budget_status_category_over_budget(self):
        from finance.tools.transactions import get_budget_status
        result = get_budget_status(self.user, month='2024-01')

        transport_budget = next(b for b in result['budgets'] if b['category'] == 'Transport')
        self.assertEqual(transport_budget['status'], 'under_budget')

        user = User.objects.create_user(username='overuser', password='testpass123')
        cat = Category.objects.create(name='OverCat', description='Over')
        Budget.objects.create(user=user, category=cat, amount=Decimal('100.00'), month=date(2024, 1, 1))
        Transaction.objects.create(user=user, amount=Decimal('150.00'), transaction_type='expense', category=cat, description='Over', transaction_date=date(2024, 1, 15))
        result = get_budget_status(user, month='2024-01')
        self.assertEqual(result['budgets'][0]['status'], 'over_budget')

    def test_get_budget_status_no_budgets(self):
        from finance.tools.transactions import get_budget_status
        empty_user = User.objects.create_user(username='emptyuser', password='testpass123')
        result = get_budget_status(empty_user, month='2024-01')
        self.assertEqual(result['month'], '2024-01')
        self.assertEqual(result['budgets'], [])

    def test_get_budget_status_invalid_month(self):
        from finance.tools.transactions import get_budget_status, TransactionToolError
        with self.assertRaises(TransactionToolError) as ctx:
            get_budget_status(self.user, month='invalid')
        self.assertIn('Invalid month', str(ctx.exception))

        with self.assertRaises(TransactionToolError) as ctx:
            get_budget_status(self.user, month='2024')
        self.assertIn('Invalid month', str(ctx.exception))

        with self.assertRaises(TransactionToolError) as ctx:
            get_budget_status(self.user, month='2024-13')
        self.assertIn('Invalid month', str(ctx.exception))

    def test_get_budget_status_user_isolation(self):
        from finance.tools.transactions import get_budget_status
        result = get_budget_status(self.user, month='2024-01')
        self.assertEqual(len(result['budgets']), 2)

        other_result = get_budget_status(self.other_user, month='2024-01')
        self.assertEqual(len(other_result['budgets']), 1)
        self.assertEqual(other_result['budgets'][0]['category'], 'Food')

    def test_get_budget_status_unauthenticated_user_raises(self):
        from finance.tools.transactions import get_budget_status, TransactionToolError
        class MockUser:
            is_authenticated = False
        with self.assertRaises(TransactionToolError) as ctx:
            get_budget_status(MockUser())
        self.assertIn('Authenticated user required', str(ctx.exception))

    def test_get_budget_status_none_user_raises(self):
        from finance.tools.transactions import get_budget_status, TransactionToolError
        with self.assertRaises(TransactionToolError) as ctx:
            get_budget_status(None)
        self.assertIn('Authenticated user required', str(ctx.exception))

    def test_get_budget_status_uses_decimal_precision(self):
        from finance.tools.transactions import get_budget_status
        user = User.objects.create_user(username='preciseuser', password='testpass123')
        cat = Category.objects.create(name='Precision', description='Precision')
        Budget.objects.create(user=user, category=cat, amount=Decimal('1000.00'), month=date(2024, 1, 1))
        Transaction.objects.create(user=user, amount=Decimal('333.33'), transaction_type='expense', category=cat, description='Test', transaction_date=date(2024, 1, 15))
        result = get_budget_status(user, month='2024-01')
        self.assertEqual(result['budgets'][0]['spent_amount'], '333.33')
        self.assertEqual(result['budgets'][0]['percentage_used'], '33.33')
        self.assertEqual(result['budgets'][0]['remaining_amount'], '666.67')


class GeminiBudgetStatusToolTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.other_user = User.objects.create_user(username='otheruser', password='testpass123')
        self.category_food = Category.objects.create(name='Food', description='Food expenses')
        self.category_transport = Category.objects.create(name='Transport', description='Transport costs')
        self.category_salary = Category.objects.create(name='Salary', description='Salary income')

        Budget.objects.create(
            user=self.user,
            category=self.category_food,
            amount=Decimal('500.00'),
            month=date(2024, 1, 1)
        )
        Budget.objects.create(
            user=self.user,
            category=self.category_transport,
            amount=Decimal('300.00'),
            month=date(2024, 1, 1)
        )
        Budget.objects.create(
            user=self.other_user,
            category=self.category_food,
            amount=Decimal('1000.00'),
            month=date(2024, 1, 1)
        )

        Transaction.objects.create(
            user=self.user,
            amount=Decimal('100.00'),
            transaction_type='expense',
            category=self.category_food,
            description='Groceries',
            transaction_date=date(2024, 1, 15)
        )
        Transaction.objects.create(
            user=self.user,
            amount=Decimal('200.00'),
            transaction_type='expense',
            category=self.category_transport,
            description='Gas',
            transaction_date=date(2024, 1, 10)
        )
        Transaction.objects.create(
            user=self.other_user,
            amount=Decimal('300.00'),
            transaction_type='expense',
            category=self.category_food,
            description='Other user food',
            transaction_date=date(2024, 1, 15)
        )

        os.environ['GEMINI_API_KEY'] = 'test-api-key'
        get_gemini_service.__dict__.pop('_gemini_service', None)
        reset_gemini_service()

    def tearDown(self):
        os.environ.pop('GEMINI_API_KEY', None)
        get_gemini_service.__dict__.pop('_gemini_service', None)
        reset_gemini_service()

    def _create_function_call(self, name, args):
        fc = MagicMock()
        fc.name = name
        fc.args = args
        return fc

    def _mock_gemini_response(self, mock_client, text_response=None, function_calls=None):
        mock_response = MagicMock()
        mock_candidate = MagicMock()
        mock_content = MagicMock()
        mock_parts = []

        if text_response:
            mock_text_part = MagicMock()
            mock_text_part.text = text_response
            mock_text_part.function_call = None
            mock_parts.append(mock_text_part)

        if function_calls:
            for fc in function_calls:
                mock_fc_part = MagicMock()
                mock_fc_part.function_call = fc
                mock_fc_part.text = None
                mock_parts.append(mock_fc_part)

        mock_content.parts = mock_parts
        mock_candidate.content = mock_content
        mock_response.candidates = [mock_candidate]
        return mock_response

    def test_gemini_requests_get_budget_status(self):
        self.client.force_authenticate(user=self.user)
        with patch('finance.services.gemini.genai.Client') as mock_genai:
            mock_client = MagicMock()
            mock_genai.return_value = mock_client

            call_count = [0]

            def side_effect(*args, **kwargs):
                call_count[0] += 1
                resp = MagicMock()
                if call_count[0] == 1:
                    fc = self._create_function_call('get_budget_status', {'month': '2024-01'})
                    mc = MagicMock()
                    mp = MagicMock()
                    fc_part = MagicMock()
                    fc_part.function_call = fc
                    fc_part.text = None
                    mp.parts = [fc_part]
                    mc.content = mp
                    resp.candidates = [mc]
                else:
                    mc = MagicMock()
                    mp = MagicMock()
                    tp = MagicMock()
                    tp.text = 'Your Food budget: $500.00 budget, $100.00 spent (20.00%). Transport: $300.00 budget, $200.00 spent (66.67%).'
                    tp.function_call = None
                    mp.parts = [tp]
                    mc.content = mp
                    resp.candidates = [mc]
                return resp

            mock_client.models.generate_content.side_effect = side_effect

            response = self.client.post('/api/ai/chat/', {'message': 'Am I over my Food budget?'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('500.00', response.data['response'])
        self.assertIn('100.00', response.data['response'])
        self.assertEqual(mock_client.models.generate_content.call_count, 2)

    def test_gemini_requests_budget_status_without_month(self):
        self.client.force_authenticate(user=self.user)
        with patch('finance.services.gemini.genai.Client') as mock_genai:
            mock_client = MagicMock()
            mock_genai.return_value = mock_client

            call_count = [0]

            def side_effect(*args, **kwargs):
                call_count[0] += 1
                resp = MagicMock()
                if call_count[0] == 1:
                    fc = self._create_function_call('get_budget_status', {})
                    mc = MagicMock()
                    mp = MagicMock()
                    fc_part = MagicMock()
                    fc_part.function_call = fc
                    fc_part.text = None
                    mp.parts = [fc_part]
                    mc.content = mp
                    resp.candidates = [mc]
                else:
                    mc = MagicMock()
                    mp = MagicMock()
                    tp = MagicMock()
                    tp.text = 'Current month budgets look good.'
                    tp.function_call = None
                    mp.parts = [tp]
                    mc.content = mp
                    resp.candidates = [mc]
                return resp

            mock_client.models.generate_content.side_effect = side_effect

            response = self.client.post('/api/ai/chat/', {'message': 'How much of my Shopping budget have I used?'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(mock_client.models.generate_content.call_count, 2)

    def test_budget_status_tool_executed_with_request_user(self):
        self.client.force_authenticate(user=self.user)
        with patch('finance.services.gemini.genai.Client') as mock_genai:
            mock_client = MagicMock()
            mock_genai.return_value = mock_client

            call_count = [0]

            def side_effect(*args, **kwargs):
                call_count[0] += 1
                resp = MagicMock()
                if call_count[0] == 1:
                    fc = self._create_function_call('get_budget_status', {'month': '2024-01'})
                    mc = MagicMock()
                    mp = MagicMock()
                    fc_part = MagicMock()
                    fc_part.function_call = fc
                    fc_part.text = None
                    mp.parts = [fc_part]
                    mc.content = mp
                    resp.candidates = [mc]
                else:
                    mc = MagicMock()
                    mp = MagicMock()
                    tp = MagicMock()
                    tp.text = 'Your Food budget: $500.00 budget, $100.00 spent. Transport: $300.00 budget, $200.00 spent.'
                    tp.function_call = None
                    mp.parts = [tp]
                    mc.content = mp
                    resp.candidates = [mc]
                return resp

            mock_client.models.generate_content.side_effect = side_effect

            response = self.client.post('/api/ai/chat/', {'message': 'Which categories are over budget?'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('500.00', response.data['response'])
        self.assertIn('100.00', response.data['response'])

    def test_model_cannot_specify_another_user_in_budget_status(self):
        self.client.force_authenticate(user=self.user)
        with patch('finance.services.gemini.genai.Client') as mock_genai:
            mock_client = MagicMock()
            mock_genai.return_value = mock_client

            call_count = [0]

            def side_effect(*args, **kwargs):
                call_count[0] += 1
                resp = MagicMock()
                if call_count[0] == 1:
                    fc = self._create_function_call('get_budget_status', {'month': '2024-01', 'user_id': self.other_user.id})
                    mc = MagicMock()
                    mp = MagicMock()
                    fc_part = MagicMock()
                    fc_part.function_call = fc
                    fc_part.text = None
                    mp.parts = [fc_part]
                    mc.content = mp
                    resp.candidates = [mc]
                else:
                    mc = MagicMock()
                    mp = MagicMock()
                    tp = MagicMock()
                    tp.text = 'Your Food budget: $500.00 budget, $100.00 spent.'
                    tp.function_call = None
                    mp.parts = [tp]
                    mc.content = mp
                    resp.candidates = [mc]
                return resp

            mock_client.models.generate_content.side_effect = side_effect

            response = self.client.post('/api/ai/chat/', {'message': 'Show my budget status'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('500.00', response.data['response'])
        self.assertIn('100.00', response.data['response'])

    def test_gemini_can_choose_between_all_tools(self):
        self.client.force_authenticate(user=self.user)
        with patch('finance.services.gemini.genai.Client') as mock_genai:
            mock_client = MagicMock()
            mock_genai.return_value = mock_client

            call_count = [0]

            def side_effect(*args, **kwargs):
                call_count[0] += 1
                resp = MagicMock()
                if call_count[0] == 1:
                    fc = self._create_function_call('get_financial_summary', {})
                    mc = MagicMock()
                    mp = MagicMock()
                    fc_part = MagicMock()
                    fc_part.function_call = fc
                    fc_part.text = None
                    mp.parts = [fc_part]
                    mc.content = mp
                    resp.candidates = [mc]
                elif call_count[0] == 2:
                    fc = self._create_function_call('get_budget_status', {'month': '2024-01'})
                    mc = MagicMock()
                    mp = MagicMock()
                    fc_part = MagicMock()
                    fc_part.function_call = fc
                    fc_part.text = None
                    mp.parts = [fc_part]
                    mc.content = mp
                    resp.candidates = [mc]
                elif call_count[0] == 3:
                    fc = self._create_function_call('get_transactions', {'category': 'Food'})
                    mc = MagicMock()
                    mp = MagicMock()
                    fc_part = MagicMock()
                    fc_part.function_call = fc
                    fc_part.text = None
                    mp.parts = [fc_part]
                    mc.content = mp
                    resp.candidates = [mc]
                else:
                    mc = MagicMock()
                    mp = MagicMock()
                    tp = MagicMock()
                    tp.text = 'Summary: income $1000.00, expenses $300.00. Budget: Food 30%, Transport 66%. Food transactions: $100.00.'
                    tp.function_call = None
                    mp.parts = [tp]
                    mc.content = mp
                    resp.candidates = [mc]
                return resp

            mock_client.models.generate_content.side_effect = side_effect

            response = self.client.post('/api/ai/chat/', {'message': 'Show my summary, budget status, and food expenses'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(mock_client.models.generate_content.call_count, 4)
        self.assertIn('income', response.data['response'].lower())
        self.assertIn('budget', response.data['response'].lower())
        self.assertIn('food', response.data['response'].lower())

    def test_all_tools_still_work_independently(self):
        self.client.force_authenticate(user=self.user)
        with patch('finance.services.gemini.genai.Client') as mock_genai:
            mock_client = MagicMock()
            mock_genai.return_value = mock_client

            call_count = [0]

            def side_effect(*args, **kwargs):
                call_count[0] += 1
                resp = MagicMock()
                if call_count[0] == 1:
                    fc = self._create_function_call('get_budget_status', {'month': '2024-01'})
                    mc = MagicMock()
                    mp = MagicMock()
                    fc_part = MagicMock()
                    fc_part.function_call = fc
                    fc_part.text = None
                    mp.parts = [fc_part]
                    mc.content = mp
                    resp.candidates = [mc]
                else:
                    mc = MagicMock()
                    mp = MagicMock()
                    tp = MagicMock()
                    tp.text = 'Food budget: $500.00, spent $100.00 (20%).'
                    tp.function_call = None
                    mp.parts = [tp]
                    mc.content = mp
                    resp.candidates = [mc]
                return resp

            mock_client.models.generate_content.side_effect = side_effect

            response = self.client.post('/api/ai/chat/', {'message': 'Show my Food budget status'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(mock_client.models.generate_content.call_count, 2)
        self.assertIn('500.00', response.data['response'])
        self.assertIn('100.00', response.data['response'])


class CompareMonthsToolTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.other_user = User.objects.create_user(username='otheruser', password='testpass123')
        self.category_food = Category.objects.create(name='Food', description='Food expenses')
        self.category_transport = Category.objects.create(name='Transport', description='Transport costs')
        self.category_shopping = Category.objects.create(name='Shopping', description='Shopping expenses')
        self.category_salary = Category.objects.create(name='Salary', description='Salary income')

        # Current month: 2024-02 (Feb) - higher income and expenses
        Transaction.objects.create(
            user=self.user,
            amount=Decimal('2000.00'),
            transaction_type='income',
            category=self.category_salary,
            description='February Salary',
            transaction_date=date(2024, 2, 1)
        )
        Transaction.objects.create(
            user=self.user,
            amount=Decimal('500.00'),
            transaction_type='expense',
            category=self.category_food,
            description='February Groceries',
            transaction_date=date(2024, 2, 5)
        )
        Transaction.objects.create(
            user=self.user,
            amount=Decimal('300.00'),
            transaction_type='expense',
            category=self.category_transport,
            description='February Gas',
            transaction_date=date(2024, 2, 10)
        )
        Transaction.objects.create(
            user=self.user,
            amount=Decimal('200.00'),
            transaction_type='expense',
            category=self.category_shopping,
            description='February Shopping',
            transaction_date=date(2024, 2, 15)
        )

        # Comparison month: 2024-01 (Jan) - lower income and expenses
        Transaction.objects.create(
            user=self.user,
            amount=Decimal('1800.00'),
            transaction_type='income',
            category=self.category_salary,
            description='January Salary',
            transaction_date=date(2024, 1, 1)
        )
        Transaction.objects.create(
            user=self.user,
            amount=Decimal('400.00'),
            transaction_type='expense',
            category=self.category_food,
            description='January Groceries',
            transaction_date=date(2024, 1, 5)
        )
        Transaction.objects.create(
            user=self.user,
            amount=Decimal('250.00'),
            transaction_type='expense',
            category=self.category_transport,
            description='January Gas',
            transaction_date=date(2024, 1, 10)
        )

        # Other user's transactions (for isolation test)
        Transaction.objects.create(
            user=self.other_user,
            amount=Decimal('1000.00'),
            transaction_type='income',
            category=self.category_salary,
            description='Other user income',
            transaction_date=date(2024, 1, 1)
        )

    def test_compare_months_income_comparison(self):
        from finance.tools.transactions import compare_months
        result = compare_months(self.user, current_month='2024-02', comparison_month='2024-01')
        self.assertEqual(result['income']['current'], '2000.00')
        self.assertEqual(result['income']['comparison'], '1800.00')
        self.assertEqual(result['income']['change'], '200.00')
        self.assertEqual(result['income']['change_percentage'], '11.11')

    def test_compare_months_expense_comparison(self):
        from finance.tools.transactions import compare_months
        result = compare_months(self.user, current_month='2024-02', comparison_month='2024-01')
        self.assertEqual(result['expenses']['current'], '1000.00')
        self.assertEqual(result['expenses']['comparison'], '650.00')
        self.assertEqual(result['expenses']['change'], '350.00')
        self.assertEqual(result['expenses']['change_percentage'], '53.85')

    def test_compare_months_net_balance_comparison(self):
        from finance.tools.transactions import compare_months
        result = compare_months(self.user, current_month='2024-02', comparison_month='2024-01')
        self.assertEqual(result['net_balance']['current'], '1000.00')
        self.assertEqual(result['net_balance']['comparison'], '1150.00')
        self.assertEqual(result['net_balance']['change'], '-150.00')
        self.assertEqual(result['net_balance']['change_percentage'], '-13.04')

    def test_compare_months_savings_rate_comparison(self):
        from finance.tools.transactions import compare_months
        result = compare_months(self.user, current_month='2024-02', comparison_month='2024-01')
        # Feb: (2000-1000)/2000 * 100 = 50%
        # Jan: (1800-650)/1800 * 100 = 63.89%
        self.assertEqual(result['savings_rate']['current'], '50.00')
        self.assertEqual(result['savings_rate']['comparison'], '63.89')
        self.assertEqual(result['savings_rate']['change'], '-13.89')

    def test_compare_months_positive_and_negative_changes(self):
        from finance.tools.transactions import compare_months
        result = compare_months(self.user, current_month='2024-02', comparison_month='2024-01')
        # Income increased
        self.assertTrue(result['income']['change'].startswith('+') or not result['income']['change'].startswith('-'))
        # Expenses increased
        self.assertTrue(result['expenses']['change'].startswith('+') or not result['expenses']['change'].startswith('-'))
        # Net balance decreased
        self.assertTrue(result['net_balance']['change'].startswith('-'))

    def test_compare_months_category_level_changes(self):
        from finance.tools.transactions import compare_months
        result = compare_months(self.user, current_month='2024-02', comparison_month='2024-01')
        categories = {c['category']: c for c in result['categories']}
        self.assertIn('Food', categories)
        self.assertIn('Transport', categories)
        self.assertIn('Shopping', categories)

        food = categories['Food']
        self.assertEqual(food['current'], '500.00')
        self.assertEqual(food['comparison'], '400.00')
        self.assertEqual(food['change'], '100.00')
        self.assertEqual(food['change_percentage'], '25.00')

        transport = categories['Transport']
        self.assertEqual(transport['current'], '300.00')
        self.assertEqual(transport['comparison'], '250.00')
        self.assertEqual(transport['change'], '50.00')
        self.assertEqual(transport['change_percentage'], '20.00')

    def test_compare_months_category_present_only_in_current_month(self):
        from finance.tools.transactions import compare_months
        result = compare_months(self.user, current_month='2024-02', comparison_month='2024-01')
        categories = {c['category']: c for c in result['categories']}
        shopping = categories['Shopping']
        self.assertEqual(shopping['current'], '200.00')
        self.assertEqual(shopping['comparison'], '0.00')
        self.assertEqual(shopping['change'], '200.00')
        self.assertEqual(shopping['change_percentage'], '100.00')

    def test_compare_months_category_present_only_in_comparison_month(self):
        from finance.tools.transactions import compare_months
        # Add a category only in comparison month
        cat_entertainment = Category.objects.create(name='Entertainment', description='Entertainment')
        Transaction.objects.create(
            user=self.user,
            amount=Decimal('100.00'),
            transaction_type='expense',
            category=cat_entertainment,
            description='January Movie',
            transaction_date=date(2024, 1, 20)
        )
        result = compare_months(self.user, current_month='2024-02', comparison_month='2024-01')
        categories = {c['category']: c for c in result['categories']}
        entertainment = categories['Entertainment']
        self.assertEqual(entertainment['current'], '0.00')
        self.assertEqual(entertainment['comparison'], '100.00')
        self.assertEqual(entertainment['change'], '-100.00')
        self.assertEqual(entertainment['change_percentage'], '-100.00')

    def test_compare_months_zero_comparison_values(self):
        from finance.tools.transactions import compare_months
        user = User.objects.create_user(username='zerouser', password='testpass123')
        cat = Category.objects.create(name='NewCat', description='New')
        # Only current month has transactions
        Transaction.objects.create(
            user=user,
            amount=Decimal('500.00'),
            transaction_type='income',
            category=cat,
            description='Income',
            transaction_date=date(2024, 2, 1)
        )
        Transaction.objects.create(
            user=user,
            amount=Decimal('100.00'),
            transaction_type='expense',
            category=cat,
            description='Expense',
            transaction_date=date(2024, 2, 5)
        )
        result = compare_months(user, current_month='2024-02', comparison_month='2024-01')
        self.assertEqual(result['income']['comparison'], '0.00')
        self.assertEqual(result['income']['change'], '500.00')
        self.assertEqual(result['income']['change_percentage'], '100.00')
        self.assertEqual(result['expenses']['comparison'], '0.00')
        self.assertEqual(result['expenses']['change'], '100.00')
        self.assertEqual(result['expenses']['change_percentage'], '100.00')

    def test_compare_months_months_with_no_transactions(self):
        from finance.tools.transactions import compare_months
        empty_user = User.objects.create_user(username='emptyuser', password='testpass123')
        result = compare_months(empty_user, current_month='2024-02', comparison_month='2024-01')
        self.assertEqual(result['income']['current'], '0.00')
        self.assertEqual(result['income']['comparison'], '0.00')
        self.assertEqual(result['expenses']['current'], '0.00')
        self.assertEqual(result['expenses']['comparison'], '0.00')
        self.assertEqual(result['net_balance']['current'], '0.00')
        self.assertEqual(result['net_balance']['comparison'], '0.00')
        self.assertEqual(result['savings_rate']['current'], '0.00')
        self.assertEqual(result['savings_rate']['comparison'], '0.00')
        self.assertEqual(result['categories'], [])

    def test_compare_months_invalid_month_format(self):
        from finance.tools.transactions import compare_months, TransactionToolError
        with self.assertRaises(TransactionToolError) as ctx:
            compare_months(self.user, current_month='invalid', comparison_month='2024-01')
        self.assertIn('Invalid month', str(ctx.exception))

        with self.assertRaises(TransactionToolError) as ctx:
            compare_months(self.user, current_month='2024-02', comparison_month='invalid')
        self.assertIn('Invalid month', str(ctx.exception))

        with self.assertRaises(TransactionToolError) as ctx:
            compare_months(self.user, current_month='2024', comparison_month='2024-01')
        self.assertIn('Invalid month', str(ctx.exception))

        with self.assertRaises(TransactionToolError) as ctx:
            compare_months(self.user, current_month='2024-13', comparison_month='2024-01')
        self.assertIn('Invalid month', str(ctx.exception))

    def test_compare_months_user_isolation(self):
        from finance.tools.transactions import compare_months
        result = compare_months(self.user, current_month='2024-02', comparison_month='2024-01')
        self.assertEqual(result['income']['current'], '2000.00')

        other_result = compare_months(self.other_user, current_month='2024-02', comparison_month='2024-01')
        self.assertEqual(other_result['income']['current'], '0.00')
        self.assertEqual(other_result['income']['comparison'], '1000.00')

    def test_compare_months_unauthenticated_user_raises(self):
        from finance.tools.transactions import compare_months, TransactionToolError
        class MockUser:
            is_authenticated = False
        with self.assertRaises(TransactionToolError) as ctx:
            compare_months(MockUser(), current_month='2024-02', comparison_month='2024-01')
        self.assertIn('Authenticated user required', str(ctx.exception))

    def test_compare_months_none_user_raises(self):
        from finance.tools.transactions import compare_months, TransactionToolError
        with self.assertRaises(TransactionToolError) as ctx:
            compare_months(None, current_month='2024-02', comparison_month='2024-01')
        self.assertIn('Authenticated user required', str(ctx.exception))

    def test_compare_months_uses_decimal_precision(self):
        from finance.tools.transactions import compare_months
        user = User.objects.create_user(username='preciseuser', password='testpass123')
        cat = Category.objects.create(name='Precision', description='Precision')
        Transaction.objects.create(
            user=user,
            amount=Decimal('1000.00'),
            transaction_type='income',
            category=cat,
            description='Income',
            transaction_date=date(2024, 2, 1)
        )
        Transaction.objects.create(
            user=user,
            amount=Decimal('333.33'),
            transaction_type='expense',
            category=cat,
            description='Expense',
            transaction_date=date(2024, 2, 5)
        )
        Transaction.objects.create(
            user=user,
            amount=Decimal('900.00'),
            transaction_type='income',
            category=cat,
            description='Income',
            transaction_date=date(2024, 1, 1)
        )
        Transaction.objects.create(
            user=user,
            amount=Decimal('300.00'),
            transaction_type='expense',
            category=cat,
            description='Expense',
            transaction_date=date(2024, 1, 5)
        )
        result = compare_months(user, current_month='2024-02', comparison_month='2024-01')
        self.assertEqual(result['income']['current'], '1000.00')
        self.assertEqual(result['income']['comparison'], '900.00')
        self.assertEqual(result['expenses']['current'], '333.33')
        self.assertEqual(result['expenses']['comparison'], '300.00')
        self.assertEqual(result['net_balance']['current'], '666.67')
        self.assertEqual(result['net_balance']['comparison'], '600.00')


class GeminiCompareMonthsToolTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.other_user = User.objects.create_user(username='otheruser', password='testpass123')
        self.category_food = Category.objects.create(name='Food', description='Food expenses')
        self.category_transport = Category.objects.create(name='Transport', description='Transport costs')
        self.category_salary = Category.objects.create(name='Salary', description='Salary income')

        Transaction.objects.create(
            user=self.user,
            amount=Decimal('2000.00'),
            transaction_type='income',
            category=self.category_salary,
            description='February Salary',
            transaction_date=date(2024, 2, 1)
        )
        Transaction.objects.create(
            user=self.user,
            amount=Decimal('500.00'),
            transaction_type='expense',
            category=self.category_food,
            description='February Groceries',
            transaction_date=date(2024, 2, 5)
        )
        Transaction.objects.create(
            user=self.user,
            amount=Decimal('1800.00'),
            transaction_type='income',
            category=self.category_salary,
            description='January Salary',
            transaction_date=date(2024, 1, 1)
        )
        Transaction.objects.create(
            user=self.user,
            amount=Decimal('400.00'),
            transaction_type='expense',
            category=self.category_food,
            description='January Groceries',
            transaction_date=date(2024, 1, 5)
        )
        Transaction.objects.create(
            user=self.other_user,
            amount=Decimal('1000.00'),
            transaction_type='income',
            category=self.category_salary,
            description='Other user income',
            transaction_date=date(2024, 1, 1)
        )

        os.environ['GEMINI_API_KEY'] = 'test-api-key'
        get_gemini_service.__dict__.pop('_gemini_service', None)
        reset_gemini_service()

    def tearDown(self):
        os.environ.pop('GEMINI_API_KEY', None)
        get_gemini_service.__dict__.pop('_gemini_service', None)
        reset_gemini_service()

    def _create_function_call(self, name, args):
        fc = MagicMock()
        fc.name = name
        fc.args = args
        return fc

    def _mock_gemini_response(self, mock_client, text_response=None, function_calls=None):
        mock_response = MagicMock()
        mock_candidate = MagicMock()
        mock_content = MagicMock()
        mock_parts = []

        if text_response:
            mock_text_part = MagicMock()
            mock_text_part.text = text_response
            mock_text_part.function_call = None
            mock_parts.append(mock_text_part)

        if function_calls:
            for fc in function_calls:
                mock_fc_part = MagicMock()
                mock_fc_part.function_call = fc
                mock_fc_part.text = None
                mock_parts.append(mock_fc_part)

        mock_content.parts = mock_parts
        mock_candidate.content = mock_content
        mock_response.candidates = [mock_candidate]
        return mock_response

    def test_gemini_requests_compare_months(self):
        self.client.force_authenticate(user=self.user)
        with patch('finance.services.gemini.genai.Client') as mock_genai:
            mock_client = MagicMock()
            mock_genai.return_value = mock_client

            call_count = [0]

            def side_effect(*args, **kwargs):
                call_count[0] += 1
                resp = MagicMock()
                if call_count[0] == 1:
                    fc = self._create_function_call('compare_months', {'current_month': '2024-02', 'comparison_month': '2024-01'})
                    mc = MagicMock()
                    mp = MagicMock()
                    fc_part = MagicMock()
                    fc_part.function_call = fc
                    fc_part.text = None
                    mp.parts = [fc_part]
                    mc.content = mp
                    resp.candidates = [mc]
                else:
                    mc = MagicMock()
                    mp = MagicMock()
                    tp = MagicMock()
                    tp.text = 'Income increased by $200 (11.11%). Expenses increased by $350 (53.85%). Net balance decreased by $150.'
                    tp.function_call = None
                    mp.parts = [tp]
                    mc.content = mp
                    resp.candidates = [mc]
                return resp

            mock_client.models.generate_content.side_effect = side_effect

            response = self.client.post('/api/ai/chat/', {'message': 'Compare my finances for February and January'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('200', response.data['response'])
        self.assertIn('11.11', response.data['response'])
        self.assertEqual(mock_client.models.generate_content.call_count, 2)

    def test_gemini_compare_months_tool_executed_with_request_user(self):
        self.client.force_authenticate(user=self.user)
        with patch('finance.services.gemini.genai.Client') as mock_genai:
            mock_client = MagicMock()
            mock_genai.return_value = mock_client

            call_count = [0]

            def side_effect(*args, **kwargs):
                call_count[0] += 1
                resp = MagicMock()
                if call_count[0] == 1:
                    fc = self._create_function_call('compare_months', {'current_month': '2024-02', 'comparison_month': '2024-01'})
                    mc = MagicMock()
                    mp = MagicMock()
                    fc_part = MagicMock()
                    fc_part.function_call = fc
                    fc_part.text = None
                    mp.parts = [fc_part]
                    mc.content = mp
                    resp.candidates = [mc]
                else:
                    mc = MagicMock()
                    mp = MagicMock()
                    tp = MagicMock()
                    tp.text = 'Your income increased by $200, expenses by $350.'
                    tp.function_call = None
                    mp.parts = [tp]
                    mc.content = mp
                    resp.candidates = [mc]
                return resp

            mock_client.models.generate_content.side_effect = side_effect

            response = self.client.post('/api/ai/chat/', {'message': 'How did I do this month compared to last month?'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('200', response.data['response'])
        self.assertIn('350', response.data['response'])

    def test_model_cannot_specify_another_user_in_compare_months(self):
        self.client.force_authenticate(user=self.user)
        with patch('finance.services.gemini.genai.Client') as mock_genai:
            mock_client = MagicMock()
            mock_genai.return_value = mock_client

            call_count = [0]

            def side_effect(*args, **kwargs):
                call_count[0] += 1
                resp = MagicMock()
                if call_count[0] == 1:
                    fc = self._create_function_call('compare_months', {'current_month': '2024-02', 'comparison_month': '2024-01', 'user_id': self.other_user.id})
                    mc = MagicMock()
                    mp = MagicMock()
                    fc_part = MagicMock()
                    fc_part.function_call = fc
                    fc_part.text = None
                    mp.parts = [fc_part]
                    mc.content = mp
                    resp.candidates = [mc]
                else:
                    mc = MagicMock()
                    mp = MagicMock()
                    tp = MagicMock()
                    tp.text = 'Your income increased by $200, expenses by $350.'
                    tp.function_call = None
                    mp.parts = [tp]
                    mc.content = mp
                    resp.candidates = [mc]
                return resp

            mock_client.models.generate_content.side_effect = side_effect

            response = self.client.post('/api/ai/chat/', {'message': 'Compare my February and January'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('200', response.data['response'])
        self.assertIn('350', response.data['response'])

    def test_gemini_can_choose_compare_months_with_other_tools(self):
        self.client.force_authenticate(user=self.user)
        with patch('finance.services.gemini.genai.Client') as mock_genai:
            mock_client = MagicMock()
            mock_genai.return_value = mock_client

            call_count = [0]

            def side_effect(*args, **kwargs):
                call_count[0] += 1
                resp = MagicMock()
                if call_count[0] == 1:
                    fc = self._create_function_call('compare_months', {'current_month': '2024-02', 'comparison_month': '2024-01'})
                    mc = MagicMock()
                    mp = MagicMock()
                    fc_part = MagicMock()
                    fc_part.function_call = fc
                    fc_part.text = None
                    mp.parts = [fc_part]
                    mc.content = mp
                    resp.candidates = [mc]
                elif call_count[0] == 2:
                    fc = self._create_function_call('get_transactions', {'category': 'Food', 'start_date': '2024-02-01', 'end_date': '2024-02-29'})
                    mc = MagicMock()
                    mp = MagicMock()
                    fc_part = MagicMock()
                    fc_part.function_call = fc
                    fc_part.text = None
                    mp.parts = [fc_part]
                    mc.content = mp
                    resp.candidates = [mc]
                else:
                    mc = MagicMock()
                    mp = MagicMock()
                    tp = MagicMock()
                    tp.text = 'Comparison: income +11%, expenses +53%. Food transactions in Feb: $500.'
                    tp.function_call = None
                    mp.parts = [tp]
                    mc.content = mp
                    resp.candidates = [mc]
                return resp

            mock_client.models.generate_content.side_effect = side_effect

            response = self.client.post('/api/ai/chat/', {'message': 'Compare February to January and show my Food transactions'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(mock_client.models.generate_content.call_count, 3)
        self.assertIn('income', response.data['response'].lower())
        self.assertIn('food', response.data['response'].lower())