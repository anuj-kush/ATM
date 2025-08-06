from django.http import HttpResponse
from django.shortcuts import render, redirect
from .models import ATM_Card
from .forms import TransactionForm
from .models import Transaction
from django.core.mail import send_mail
from .forms import LoginForm, OTPForm
from django.contrib.auth.hashers import make_password
from django.contrib import messages
import random
import datetime


def login_view(request):
    error_message = ''
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            cardnum = form.cleaned_data['cardnum']
            pin = form.cleaned_data['pin']
            try:
                card = ATM_Card.objects.get(atmcard_num=cardnum, atmcard_pin=pin)
                otp = str(random.randint(100000, 999999))
                request.session['cardnum'] = cardnum
                request.session['otp'] = otp
                request.session['otp_time'] = datetime.datetime.now().isoformat()
                

                # Send OTP email
                send_mail(
                    subject='Your ATM OTP Code',
                    message=f'Your OTP code is: {otp}',
                    from_email='youremail@example.com',
                    recipient_list=[card.email],
                    fail_silently=False,
                )
                return redirect('verify_otp')
            except ATM_Card.DoesNotExist:
                error_message = "Invalid card number or PIN"
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form, 'error_message': error_message})

def verify_otp(request):
    error_message = ''
    cardnum = request.session.get('cardnum')
    if not cardnum:
        return redirect('login')

    if request.method == 'POST':
        form = OTPForm(request.POST)
        if form.is_valid():
            user_otp = form.cleaned_data['otp']
            session_otp = request.session.get('otp')
            otp_time_str = request.session.get('otp_time')

            if not otp_time_str:
                error_message = 'Session expired. Please login again.'
            else:
                otp_time = datetime.datetime.fromisoformat(otp_time_str)
                now = datetime.datetime.now()
                if (now - otp_time).total_seconds() > 120:
                    error_message = 'OTP has expired. Please login again.'
                    # Optional: clear session
                    request.session.flush()
                elif user_otp == session_otp:
                    # OTP correct and not expired
                    return redirect('dashboard')
                else:
                    error_message = 'Incorrect OTP.'
    else:
        form = OTPForm()

    return render(request, 'verify_otp.html', {'form': form, 'error_message': error_message})


def dashboard(request):
    cardnum = request.session.get('cardnum')
    if not cardnum:
        return redirect('login')
    try:
        card = ATM_Card.objects.get(atmcard_num=cardnum)
    except ATM_Card.DoesNotExist:
        return redirect('login')
    return render(request, 'dashboard.html', {'card': card})

def logout_view(request):
    request.session.flush()
    return redirect('login')


def transaction_view(request):
    cardnum = request.session.get('cardnum')
    if not cardnum:
        return redirect('login')

    card = ATM_Card.objects.get(atmcard_num=cardnum)
    message = ''
    
    if request.method == 'POST':
        form = TransactionForm(request.POST)
        if form.is_valid():
            txn_type = form.cleaned_data['txn_type']
            amount = form.cleaned_data['amount']

            if txn_type == 'Withdraw' and card.balance < amount:
                message = 'Insufficient balance.'
            else:
                if txn_type == 'Withdraw':
                    card.balance -= amount
                else:
                    card.balance += amount
                card.save()

                Transaction.objects.create(card=card, txn_type=txn_type, amount=amount)
                return redirect('dashboard')
    else:
        form = TransactionForm()
    
    return render(request, 'transaction.html', {'form': form, 'card': card, 'message': message})


def register(request):
    if request.method == 'POST':
        card_num = request.POST['card_num']
        pin = request.POST.get('atmcard_pin')
        holder_name = request.POST.get('cardholder_name')
        balance = request.POST['balance']

        # Check if card already exists
        if ATM_Card.objects.filter(atmcard_num=card_num).exists():
            messages.error(request, 'Card number already registered.')
        else:
            ATM_Card.objects.create(
                atmcard_num=card_num,
                atmcard_pin=make_password(pin),  # hash the PIN
                cardholder_name=holder_name,
                balance=balance
            )
            messages.success(request, 'Registration successful! You can now log in.')
            return redirect('login')  # Redirect to login page

    return render(request, 'register.html')

