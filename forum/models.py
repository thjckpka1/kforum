from django.db import models
from django.conf import settings
from django.utils.text import slugify
from ckeditor.fields import RichTextField
import bleach


class Category(models.Model):
	name = models.CharField(max_length=100)
	slug = models.SlugField(unique=True)

	def __str__(self):
		return self.name

	class Meta:
		verbose_name_plural = 'Categories'


class Tag(models.Model):
	name = models.CharField(max_length=50, unique=True)
	slug = models.SlugField(unique=True, blank=True)

	def save(self, *args, **kwargs):
		if not self.slug:
			self.slug = slugify(self.name)
		super().save(*args, **kwargs)

	def __str__(self):
		return self.name


class Post(models.Model):
	author = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name='posts'
	)
	category = models.ForeignKey(
		Category,
		on_delete=models.SET_NULL,
		null=True, blank=True,
		related_name='posts'
	)
	tags = models.ManyToManyField(Tag, blank=True)
	title = models.CharField(max_length=200)
	content = RichTextField()
	image = models.ImageField(upload_to='posts/', blank=True, null=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def __str__(self):
		return self.title

	class Meta:
		ordering = ['-created_at']

	def save(self, *args, **kwargs):
		allowed_tags = ['p', 'br', 'strong', 'b', 'em', 'i', 'u', 'strike', 'a', 'img', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'blockquote', 'pre', 'code', 'ul', 'ol', 'li']
		allowed_attrs = {
			'a': ['href', 'title', 'target', 'rel'],
			'img': ['src', 'alt', 'width', 'height', 'style'],
			'*':   ['class'],
		}
		self.content = bleach.clean(self.content, tags=allowed_tags, attributes=allowed_attrs, strip=True)
		super().save(*args, **kwargs)

	def nice_count(self):
		return self.reactions.filter(reaction=Reaction.NICE).count()

	def nah_count(self):
		return self.reactions.filter(reaction=Reaction.NAH).count()


class Comment(models.Model):
	post = models.ForeignKey(
		Post,
		on_delete=models.CASCADE,
		related_name='comments'
	)
	author = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name='comments'
	)
	content = models.TextField()
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return f'Comment by {self.author} on {self.post}'

	class Meta:
		ordering = ['created_at']


class Reaction(models.Model):
	NICE = 'nice'
	NAH = 'nah'
	REACTION_CHOICES = [
		(NICE, 'nice'),
		(NAH, 'nah'),
	]

	user = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name='reactions'
	)
	reaction = models.CharField(max_length=4, choices=REACTION_CHOICES)

	# Một trong hai phải có giá trị (post hoặc comment), không bao giờ cả hai
	post = models.ForeignKey(
		Post,
		on_delete=models.CASCADE,
		related_name='reactions',
		null=True, blank=True
	)
	comment = models.ForeignKey(
		Comment,
		on_delete=models.CASCADE,
		related_name='reactions',
		null=True, blank=True
	)

	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		# Mỗi user chỉ react 1 lần trên mỗi post/comment
		constraints = [
			models.UniqueConstraint(
				fields=['user', 'post'],
				condition=models.Q(post__isnull=False),
				name='unique_reaction_per_user_post'
			),
			models.UniqueConstraint(
				fields=['user', 'comment'],
				condition=models.Q(comment__isnull=False),
				name='unique_reaction_per_user_comment'
			),
		]

	def __str__(self):
		target = f'post:{self.post_id}' if self.post_id else f'comment:{self.comment_id}'
		return f'{self.user} — {self.reaction} — {target}'
