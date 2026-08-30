from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet, TransactionViewSet, BudgetViewSet, CsrfTokenView, LoginView, GeminiTestView, GeminiChatView

router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'transactions', TransactionViewSet, basename='transaction')
router.register(r'budgets', BudgetViewSet, basename='budget')

urlpatterns = [
    path('', include(router.urls)),
    path('csrf/', CsrfTokenView.as_view(), name='csrf-token'),
    path('login/', LoginView.as_view(), name='login'),
    path('ai/test/', GeminiTestView.as_view(), name='gemini-test'),
    path('ai/chat/', GeminiChatView.as_view(), name='gemini-chat'),
]