from django.core.validators import FileExtensionValidator, URLValidator
from django.db import models
from django.template.defaultfilters import slugify
from django.utils import timezone
import re, markdown2
from django.contrib.auth import get_user_model

User = get_user_model()


class SiteSettings(models.Model):
    """
    Singleton-ish model: the one place admin sets which author's posts are public on the landing page.
    Keep exactly one row; enforce in admin or via business rules.
    """
    featured_author = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL, related_name="featured_on_site"
    )

    def __str__(self):
        return "Site Settings"

    class Meta:
        verbose_name_plural = "Site settings"


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=60, unique=True, editable=False)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)[:60]
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class BlogPost(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"

    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="blog_posts")
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=230, editable=False, db_index=True)
    excerpt = models.CharField(max_length=300, blank=True)
    tags = models.ManyToManyField(Tag, blank=True, related_name="posts")
    # 👇 Markdown instead of raw HTML
    body_markdown = models.TextField()  

    status = models.CharField(max_length=10, choices=Status.choices, default=Status.DRAFT)

    meta_title = models.CharField(max_length=70, blank=True)
    meta_description = models.CharField(max_length=160, blank=True)

    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-published_at", "-created_at"]
        unique_together = [("author", "slug")]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)[:200]
        if self.status == BlogPost.Status.PUBLISHED and not self.published_at:
            self.published_at = timezone.now()
        return super().save(*args, **kwargs)

    @property
    def body_html(self) -> str:
        """Render Markdown to safe HTML (can be consumed by frontend if wanted)."""
        return markdown2.markdown(self.body_markdown)

    def __str__(self):
        return f"{self.title} — {self.author}"

"""
class BlogPost(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"

    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="blog_posts")
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=230, editable=False, db_index=True)
    excerpt = models.CharField(max_length=300, blank=True)
    body = models.TextField()  # Let the frontend handle rich text (e.g., TipTap/MDX)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.DRAFT)
    tags = models.ManyToManyField(Tag, blank=True, related_name="posts")

    # SEO / meta
    meta_title = models.CharField(max_length=70, blank=True)
    meta_description = models.CharField(max_length=160, blank=True)

    # Timestamps
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-published_at", "-created_at"]
        unique_together = [("author", "slug")]
        indexes = [
            models.Index(fields=["status", "published_at"]),
            models.Index(fields=["author", "status"]),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title)[:200] or "post"
            # Ensure uniqueness per author by appending a counter if needed
            slug_candidate = base
            counter = 1
            while BlogPost.objects.filter(author=self.author, slug=slug_candidate).exclude(pk=self.pk).exists():
                counter += 1
                slug_candidate = f"{base}-{counter}"
            self.slug = slug_candidate

        # Maintain published_at
        if self.status == BlogPost.Status.PUBLISHED and not self.published_at:
            self.published_at = timezone.now()
        if self.status == BlogPost.Status.DRAFT:
            # optional: clear published_at on re-draft
            self.published_at = None

        return super().save(*args, **kwargs)

    @property
    def is_public_landing_page_visible(self) -> bool:
        #Public only if this author is the featured author and post is published.
        settings_row = SiteSettings.objects.first()
        return (
            settings_row is not None
            and settings_row.featured_author_id == self.author_id
            and self.status == BlogPost.Status.PUBLISHED
        )

    def __str__(self):
        return f"{self.title} — {self.author}"
"""

def upload_post_image(instance, filename):
    return f"blog/{instance.post.author_id}/{instance.post_id}/images/{filename}"


def upload_post_audio(instance, filename):
    return f"blog/{instance.post.author_id}/{instance.post_id}/audio/{filename}"


class PostImage(models.Model):
    post = models.ForeignKey(BlogPost, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to=upload_post_image)
    alt_text = models.CharField(max_length=150, blank=True)
    caption = models.CharField(max_length=200, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]


class PostAudio(models.Model):
    post = models.ForeignKey(BlogPost, on_delete=models.CASCADE, related_name="audio_files")
    audio = models.FileField(
        upload_to=upload_post_audio,
        validators=[FileExtensionValidator(["mp3", "wav", "m4a", "aac", "ogg"])],
    )
    title = models.CharField(max_length=150, blank=True)
    duration_seconds = models.PositiveIntegerField(null=True, blank=True)  # optional: fill via processing
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]


YOUTUBE_REGEX = re.compile(
    r"(?:https?://)?(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)(?P<vid>[A-Za-z0-9_\-]{11})"
)


class PostYouTube(models.Model):
    """
    Store URLs (canonical watch or youtu.be) and keep a parsed video_id.
    Frontend can embed with <iframe src={`https://www.youtube.com/embed/${video_id}`}>…
    """
    post = models.ForeignKey(BlogPost, on_delete=models.CASCADE, related_name="youtube_videos")
    url = models.URLField(validators=[URLValidator()])
    video_id = models.CharField(max_length=11, editable=False, db_index=True)
    title = models.CharField(max_length=150, blank=True)  # optional, can be filled by a fetch task
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]
        unique_together = [("post", "video_id")]

    def save(self, *args, **kwargs):
        if self.url and not self.video_id:
            m = YOUTUBE_REGEX.search(self.url)
            if not m:
                raise ValueError("URL must be a valid YouTube watch or youtu.be link")
            self.video_id = m.group("vid")
        return super().save(*args, **kwargs)
