from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.db.models import Sum, Q
from django.http import JsonResponse
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Transaction, Category, Budget
from .forms import TransactionForm, CategoryForm, BudgetForm
import json

def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}!')
            
            # Create default categories
            default_categories = [
                ('Salary', 'income'),
                ('Freelance', 'income'),
                ('Food', 'expense'),
                ('Transportation', 'expense'),
                ('Entertainment', 'expense'),
                ('Utilities', 'expense'),
            ]
            
            for name, cat_type in default_categories:
                Category.objects.create(name=name, type=cat_type, user=user)
            
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

@login_required
def dashboard(request):
    # Get current month data
    current_month = timezone.now().replace(day=1)
    
    # Calculate totals
    total_income = Transaction.objects.filter(
        user=request.user, 
        type='income',
        date__gte=current_month
    ).aggregate(Sum('amount'))['amount__sum'] or 0
    
    total_expenses = Transaction.objects.filter(
        user=request.user, 
        type='expense',
        date__gte=current_month
    ).aggregate(Sum('amount'))['amount__sum'] or 0
    
    balance = total_income - total_expenses
    
    # Recent transactions
    recent_transactions = Transaction.objects.filter(user=request.user)[:5]
    
    # Monthly data for chart
    monthly_data = []
    for i in range(6):
        month = (timezone.now() - timedelta(days=30*i)).replace(day=1)
        month_income = Transaction.objects.filter(
            user=request.user,
            type='income',
            date__year=month.year,
            date__month=month.month
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        
        month_expenses = Transaction.objects.filter(
            user=request.user,
            type='expense',
            date__year=month.year,
            date__month=month.month
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        
        monthly_data.append({
            'month': month.strftime('%b %Y'),
            'income': float(month_income),
            'expenses': float(month_expenses)
        })
    
    monthly_data.reverse()
    
    context = {
        'total_income': total_income,
        'total_expenses': total_expenses,
        'balance': balance,
        'recent_transactions': recent_transactions,
        'monthly_data': json.dumps(monthly_data),
    }
    
    return render(request, 'finance/dashboard.html', context)

@login_required
def transactions_view(request):
    transactions = Transaction.objects.filter(user=request.user)
    
    # Filter by type if specified
    transaction_type = request.GET.get('type')
    if transaction_type in ['income', 'expense']:
        transactions = transactions.filter(type=transaction_type)
    
    # Filter by category if specified
    category_id = request.GET.get('category')
    if category_id:
        transactions = transactions.filter(category_id=category_id)
    
    categories = Category.objects.filter(user=request.user)
    
    context = {
        'transactions': transactions,
        'categories': categories,
        'selected_type': transaction_type,
        'selected_category': category_id,
    }
    
    return render(request, 'finance/transactions.html', context)

@login_required
def add_transaction(request):
    if request.method == 'POST':
        form = TransactionForm(request.POST, user=request.user)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.user = request.user
            transaction.save()
            messages.success(request, 'Transaction added successfully!')
            return redirect('transactions')
    else:
        form = TransactionForm(user=request.user)
    
    return render(request, 'finance/add_transaction.html', {'form': form})

@login_required
def edit_transaction(request, pk):
    transaction = get_object_or_404(Transaction, pk=pk, user=request.user)
    
    if request.method == 'POST':
        form = TransactionForm(request.POST, instance=transaction, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Transaction updated successfully!')
            return redirect('transactions')
    else:
        form = TransactionForm(instance=transaction, user=request.user)
    
    return render(request, 'finance/edit_transaction.html', {'form': form, 'transaction': transaction})

@login_required
def delete_transaction(request, pk):
    transaction = get_object_or_404(Transaction, pk=pk, user=request.user)
    
    if request.method == 'POST':
        transaction.delete()
        messages.success(request, 'Transaction deleted successfully!')
        return redirect('transactions')
    
    return render(request, 'finance/delete_transaction.html', {'transaction': transaction})

@login_required
def categories_view(request):
    categories = Category.objects.filter(user=request.user)
    return render(request, 'finance/categories.html', {'categories': categories})

@login_required
def add_category(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save(commit=False)
            category.user = request.user
            category.save()
            messages.success(request, 'Category added successfully!')
            return redirect('categories')
    else:
        form = CategoryForm()
    
    return render(request, 'finance/add_category.html', {'form': form})

@login_required
def reports_view(request):
    # Category-wise expense data
    expense_by_category = Transaction.objects.filter(
        user=request.user,
        type='expense'
    ).values('category__name').annotate(
        total=Sum('amount')
    ).order_by('-total')
    
    # Income vs Expense trend (last 12 months)
    trend_data = []
    for i in range(12):
        month = (timezone.now() - timedelta(days=30*i)).replace(day=1)
        month_income = Transaction.objects.filter(
            user=request.user,
            type='income',
            date__year=month.year,
            date__month=month.month
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        
        month_expenses = Transaction.objects.filter(
            user=request.user,
            type='expense',
            date__year=month.year,
            date__month=month.month
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        
        trend_data.append({
            'month': month.strftime('%b %Y'),
            'income': float(month_income),
            'expenses': float(month_expenses)
        })
    
    trend_data.reverse()
    
    context = {
        'expense_by_category': expense_by_category,
        'trend_data': json.dumps(trend_data),
    }
    
    return render(request, 'finance/reports.html', context)