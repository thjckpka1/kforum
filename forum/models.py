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
	# content = models.TextField()
	content = RichTextField()
	image = models.ImageField(upload_to='posts/', blank=True, null=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def __str__(self):
		return self.title

	class Meta:
		ordering = ['-created_at']

	def save(self, *args, **kwargs):
		# Lọc HTML, chỉ cho phép một số thẻ an toàn
		allowed_tags = ['p', 'br', 'strong', 'b', 'em', 'i', 'u', 'strike', 'a', 'img', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'blockquote', 'pre', 'code', 'ul', 'ol', 'li']
		allowed_attrs = {
			'a': ['href', 'title', 'target', 'rel'],
			'img': ['src', 'alt', 'width', 'height', 'style'],
			'*':   ['class'],  # nếu muốn giữ style, cần kiểm soát kỹ
		}
		self.content = bleach.clean(self.content, tags=allowed_tags, attributes=allowed_attrs, strip=True)
		super().save(*args, **kwargs)


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
