from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import RegisterForm, LoginForm
from forum.models import Reaction

User = get_user_model()


def register_view(request):
	if request.method == 'POST':
		form = RegisterForm(request.POST)
		if form.is_valid():
			user = form.save()
			login(request, user)
			messages.success(request, 'Đăng ký thành công!')
			return redirect('post_list')
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
			next_url = request.POST.get('next') or request.GET.get('next') or 'post_list'
			return redirect(next_url)
	else:
		form = LoginForm()
	return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
	logout(request)
	next_url = request.POST.get('next') or request.GET.get('next') or 'post_list'
	return redirect(next_url)


def home_view(request):
	return redirect('post_list')


# Bỏ @login_required ở đây
def profile_view(request, username=None):
	# username = request.resolver_match.kwargs.get('username')
	if username:
		if not request.user.is_authenticated:   # ← thêm dòng này
			return redirect('login')            # ← thêm dòng này
		profile_user = get_object_or_404(User, username=username)
	else:
		if not request.user.is_authenticated:
			return redirect('login')
		profile_user = request.user

	is_own_profile = request.user.is_authenticated and (request.user == profile_user)

	# Chỉ cho phép sửa profile của chính mình
	is_own_profile = (request.user == profile_user)

	if request.method == 'POST' and is_own_profile:
		user = request.user
		# Cập nhật thông tin cơ bản
		user.first_name = request.POST.get('first_name', '').strip()
		user.last_name = request.POST.get('last_name', '').strip()
		user.email = request.POST.get('email', '').strip()

		# Cập nhật phone nếu model có trường này
		if hasattr(user, 'phone'):
			user.phone = request.POST.get('phone', '').strip()

		# Cập nhật avatar nếu có upload
		if hasattr(user, 'avatar') and 'avatar' in request.FILES:
			user.avatar = request.FILES['avatar']

		user.save()
		messages.success(request, 'Cập nhật thông tin thành công!')
		return redirect('profile')

	# Lấy bài viết của user này
	user_posts = profile_user.posts.order_by('-created_at')

	post_nice_count    = Reaction.objects.filter(post__author=profile_user, reaction=Reaction.NICE).count()
	post_nah_count     = Reaction.objects.filter(post__author=profile_user, reaction=Reaction.NAH).count()
	comment_nice_count = Reaction.objects.filter(comment__author=profile_user, reaction=Reaction.NICE).count()
	comment_nah_count  = Reaction.objects.filter(comment__author=profile_user, reaction=Reaction.NAH).count()

	total_nice = post_nice_count + comment_nice_count
	total_nah  = post_nah_count  + comment_nah_count

	context = {
		'profile_user': profile_user,
		'is_own_profile': is_own_profile,
		'user_posts': user_posts,
		'total_posts': user_posts.count(),
		'total_comments': profile_user.comments.count(),
		'total_nice': total_nice,
		'total_nah': total_nah,
		'post_nice_count': post_nice_count,
		'post_nah_count': post_nah_count,
		'comment_nice_count': comment_nice_count,
		'comment_nah_count': comment_nah_count,
	}
	tab = request.GET.get('tab', 'profile')
	context['tab'] = tab

	return render(request, 'accounts/profile.html', context)
