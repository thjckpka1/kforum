from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from .forms import RegisterForm, LoginForm

def register_view(request):
	if request.method == 'POST':
		form = RegisterForm(request.POST)
		if form.is_valid():
			user = form.save()
			login(request, user)
			messages.success(request, 'Đăng ký thành công!')
			return redirect('home')
	else:
		form = RegisterForm()
	return render(request, 'accounts/register.html', {'form': form})

def login_view(request):
	if request.method == 'POST':
		form = LoginForm(request, data=request.POST)
		if form.is_valid():
			user = form.get_user()
			login(request, user)
			messages.success(request, 'Đăng nhập thành công!')
			return redirect('home')
	else:
		form = LoginForm()
	return render(request, 'accounts/login.html', {'form': form})

def logout_view(request):
	logout(request)
	return redirect('login')

def home_view(request):
	return render(request, 'accounts/home.html')