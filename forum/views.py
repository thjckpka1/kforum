from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import get_user_model
from .models import Post, Comment, Category, Tag
from .forms import PostForm, CommentForm

User = get_user_model()


def post_list(request):
	posts = Post.objects.select_related('author', 'category').prefetch_related('tags', 'comments')
	categories = Category.objects.prefetch_related('posts').all()
	tags = Tag.objects.all()
	context = {
		'posts': posts,
		'categories': categories,
		'tags': tags,
		'total_posts': Post.objects.count(),
		'total_users': User.objects.count(),
		'total_comments': Comment.objects.count(),
	}
	return render(request, 'forum/post_list.html', context)


def post_detail(request, pk):
	post = get_object_or_404(Post, pk=pk)
	comments = post.comments.select_related('author')
	comment_form = CommentForm()

	if request.method == 'POST':
		if not request.user.is_authenticated:
			return redirect('login')
		comment_form = CommentForm(request.POST)
		if comment_form.is_valid():
			comment = comment_form.save(commit=False)
			comment.post = post
			comment.author = request.user
			comment.save()
			messages.success(request, 'Đã thêm bình luận!')
			return redirect('post_detail', pk=pk)

	return render(request, 'forum/post_detail.html', {
		'post': post,
		'comments': comments,
		'comment_form': comment_form,
	})


@login_required
def post_create(request):
	if request.method == 'POST':
		form = PostForm(request.POST, request.FILES)
		if form.is_valid():
			post = form.save(commit=False)
			post.author = request.user
			post.save()
			form.save_m2m()
			messages.success(request, 'Đăng bài thành công!')
			return redirect('post_detail', pk=post.pk)
	else:
		form = PostForm()
	return render(request, 'forum/post_form.html', {'form': form, 'action': 'Đăng bài mới'})


@login_required
def post_edit(request, pk):
	post = get_object_or_404(Post, pk=pk, author=request.user)
	if request.method == 'POST':
		form = PostForm(request.POST, request.FILES, instance=post)
		if form.is_valid():
			form.save()
			messages.success(request, 'Cập nhật bài thành công!')
			return redirect('post_detail', pk=pk)
	else:
		form = PostForm(instance=post)
	return render(request, 'forum/post_form.html', {'form': form, 'action': 'Chỉnh sửa bài'})


@login_required
def post_delete(request, pk):
	post = get_object_or_404(Post, pk=pk, author=request.user)
	if request.method == 'POST':
		post.delete()
		messages.success(request, 'Đã xóa bài viết!')
		return redirect('post_list')
	return render(request, 'forum/post_confirm_delete.html', {'post': post})
