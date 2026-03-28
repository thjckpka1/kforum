import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from .models import Post, Comment, Category, Tag, Reaction
from .forms import PostForm, CommentForm

User = get_user_model()


def get_sidebar_context():
	"""Helper dùng chung cho sidebar ở mọi trang."""
	return {
		'categories': Category.objects.prefetch_related('posts').all(),
		'tags': Tag.objects.all(),
		'total_posts': Post.objects.count(),
		'total_users': User.objects.count(),
		'total_comments': Comment.objects.count(),
	}


def post_list(request):
	query = request.GET.get('q', '').strip()
	posts = Post.objects.select_related('author', 'category').prefetch_related('tags', 'comments').order_by('-created_at')
	if query:
		posts = posts.filter(title__icontains=query) | posts.filter(content__icontains=query)
		page_title = f'Kết quả tìm kiếm: "{query}"'
	else:
		page_title = 'Tất cả bài viết'
	context = {
		'posts': posts,
		'page_title': page_title,
		'search_query': query,
		**get_sidebar_context(),
	}
	return render(request, 'forum/post_list.html', context)


def post_by_category(request, slug):
	category = get_object_or_404(Category, slug=slug)
	posts = Post.objects.filter(category=category).select_related('author', 'category').prefetch_related('tags', 'comments').order_by('-created_at')
	context = {
		'posts': posts,
		'active_category': category,
		'page_title': f'Danh mục: {category.name}',
		**get_sidebar_context(),
	}
	return render(request, 'forum/post_list.html', context)


def post_by_tag(request, slug):
	tag = get_object_or_404(Tag, slug=slug)
	posts = Post.objects.filter(tags=tag).select_related('author', 'category').prefetch_related('tags', 'comments').order_by('-created_at')
	context = {
		'posts': posts,
		'active_tag': tag,
		'page_title': f'Tag: #{tag.name}',
		**get_sidebar_context(),
	}
	return render(request, 'forum/post_list.html', context)


def post_detail(request, pk):
	post = get_object_or_404(Post, pk=pk)
	comments = post.comments.select_related('author').prefetch_related('reactions')
	comment_form = CommentForm()

	# Reaction data cho post
	post_nice = post.reactions.filter(reaction=Reaction.NICE).count()
	post_nah = post.reactions.filter(reaction=Reaction.NAH).count()
	user_post_reaction = None

	# Reaction data cho từng comment (dạng dict để dùng trong template)
	comment_reactions = {}
	for c in comments:
		comment_reactions[c.pk] = {
			'nice': c.reactions.filter(reaction=Reaction.NICE).count(),
			'nah': c.reactions.filter(reaction=Reaction.NAH).count(),
			'user_reaction': None,
		}

	if request.user.is_authenticated:
		# Reaction hiện tại của user trên post
		try:
			user_post_reaction = post.reactions.get(user=request.user).reaction
		except Reaction.DoesNotExist:
			user_post_reaction = None

		# Reaction hiện tại của user trên từng comment
		user_comment_reactions = Reaction.objects.filter(
			user=request.user,
			comment__in=comments
		).values_list('comment_id', 'reaction')
		for comment_id, reaction in user_comment_reactions:
			if comment_id in comment_reactions:
				comment_reactions[comment_id]['user_reaction'] = reaction

	if request.method == 'POST':
		if not request.user.is_authenticated:
			return redirect('login')
		comment_form = CommentForm(request.POST)
		if comment_form.is_valid():
			comment = comment_form.save(commit=False)
			comment.post = post
			comment.author = request.user
			comment.save()
			# Nếu là AJAX request, trả về JSON có comment ID
			if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
				return JsonResponse({'ok': True, 'comment_id': comment.pk})
			return redirect('post_detail', pk=pk)

	return render(request, 'forum/post_detail.html', {
		'post': post,
		'comments': comments,
		'comment_form': comment_form,
		'post_nice': post_nice,
		'post_nah': post_nah,
		'user_post_reaction': user_post_reaction,
		'comment_reactions': comment_reactions,
		'comment_reactions_json': json.dumps(comment_reactions),
		**get_sidebar_context(),
	})


@login_required
def react_post(request, pk):
	"""AJAX endpoint: toggle like/dislike trên bài viết."""
	if request.method != 'POST':
		return JsonResponse({'error': 'Method not allowed'}, status=405)

	post = get_object_or_404(Post, pk=pk)
	reaction_type = request.POST.get('reaction')  # 'nice' hoặc 'nah'

	if reaction_type not in (Reaction.NICE, Reaction.NAH):
		return JsonResponse({'error': 'Invalid reaction'}, status=400)

	existing = Reaction.objects.filter(user=request.user, post=post).first()

	if existing:
		if existing.reaction == reaction_type:
			# Click lại cùng loại → bỏ reaction
			existing.delete()
			user_reaction = None
		else:
			# Đổi sang loại khác
			existing.reaction = reaction_type
			existing.save()
			user_reaction = reaction_type
	else:
		Reaction.objects.create(user=request.user, post=post, reaction=reaction_type)
		user_reaction = reaction_type

	return JsonResponse({
		'nice': post.reactions.filter(reaction=Reaction.NICE).count(),
		'nah': post.reactions.filter(reaction=Reaction.NAH).count(),
		'user_reaction': user_reaction,
	})


@login_required
def react_comment(request, pk):
	"""AJAX endpoint: toggle like/dislike trên comment."""
	if request.method != 'POST':
		return JsonResponse({'error': 'Method not allowed'}, status=405)

	comment = get_object_or_404(Comment, pk=pk)
	reaction_type = request.POST.get('reaction')

	if reaction_type not in (Reaction.NICE, Reaction.NAH):
		return JsonResponse({'error': 'Invalid reaction'}, status=400)

	existing = Reaction.objects.filter(user=request.user, comment=comment).first()

	if existing:
		if existing.reaction == reaction_type:
			existing.delete()
			user_reaction = None
		else:
			existing.reaction = reaction_type
			existing.save()
			user_reaction = reaction_type
	else:
		Reaction.objects.create(user=request.user, comment=comment, reaction=reaction_type)
		user_reaction = reaction_type

	return JsonResponse({
		'nice': comment.reactions.filter(reaction=Reaction.NICE).count(),
		'nah': comment.reactions.filter(reaction=Reaction.NAH).count(),
		'user_reaction': user_reaction,
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
