import os
import tempfile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from .models import BlogMedia, BlogPost, Tag

User = get_user_model()


class BlogMediaAPITestCase(TestCase):
    """Test cases for Blog Media API endpoints."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="test@example.com", username="testuser", password="testpass123"
        )
        self.client.force_authenticate(user=self.user)

        # Create a temporary directory for test uploads
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test data."""
        # Clean up any uploaded files
        for media in BlogMedia.objects.all():
            if media.file and os.path.isfile(media.file.path):
                os.remove(media.file.path)

    def create_test_file(self, filename="test.jpg", content=b"test image content"):
        """Create a test file for upload."""
        return SimpleUploadedFile(filename, content, content_type="image/jpeg")

    def test_upload_media_file(self):
        """Test uploading a media file."""
        test_file = self.create_test_file()

        response = self.client.post(
            "/app/blog/media/upload/", {"file": test_file}, format="multipart"
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("id", response.data)
        self.assertIn("url", response.data)
        self.assertEqual(response.data["original_filename"], "test.jpg")
        self.assertEqual(response.data["uploaded_by"], self.user.id)

    def test_upload_invalid_file_type(self):
        """Test uploading an invalid file type."""
        invalid_file = SimpleUploadedFile(
            "test.txt", b"invalid content", content_type="text/plain"
        )

        response = self.client.post(
            "/app/blog/media/upload/", {"file": invalid_file}, format="multipart"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_upload_oversized_file(self):
        """Test uploading a file that exceeds size limit."""
        # Create a file larger than 10MB
        large_content = b"x" * (11 * 1024 * 1024)  # 11MB
        large_file = SimpleUploadedFile(
            "large.jpg", large_content, content_type="image/jpeg"
        )

        response = self.client.post(
            "/app/blog/media/upload/", {"file": large_file}, format="multipart"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_media_files(self):
        """Test listing media files."""
        # Create some test media files
        for i in range(3):
            BlogMedia.objects.create(
                filename=f"test{i}.jpg",
                original_filename=f"test{i}.jpg",
                file_type="image/jpeg",
                file_size=1024,
                uploaded_by=self.user,
            )

        response = self.client.get("/app/blog/media/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertEqual(len(response.data["results"]), 3)

    def test_filter_media_by_type(self):
        """Test filtering media files by type."""
        # Create different types of media
        BlogMedia.objects.create(
            filename="image.jpg",
            original_filename="image.jpg",
            file_type="image/jpeg",
            file_size=1024,
            uploaded_by=self.user,
        )
        BlogMedia.objects.create(
            filename="document.pdf",
            original_filename="document.pdf",
            file_type="application/pdf",
            file_size=2048,
            uploaded_by=self.user,
        )

        response = self.client.get("/app/blog/media/?file_type=image/jpeg")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["file_type"], "image/jpeg")

    def test_search_media_files(self):
        """Test searching media files by filename."""
        BlogMedia.objects.create(
            filename="vacation_photo.jpg",
            original_filename="vacation_photo.jpg",
            file_type="image/jpeg",
            file_size=1024,
            uploaded_by=self.user,
        )
        BlogMedia.objects.create(
            filename="business_report.pdf",
            original_filename="business_report.pdf",
            file_type="application/pdf",
            file_size=2048,
            uploaded_by=self.user,
        )

        response = self.client.get("/app/blog/media/?search=vacation")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertIn("vacation", response.data["results"][0]["filename"])

    def test_get_media_detail(self):
        """Test retrieving a specific media file."""
        media = BlogMedia.objects.create(
            filename="test.jpg",
            original_filename="test.jpg",
            file_type="image/jpeg",
            file_size=1024,
            uploaded_by=self.user,
        )

        response = self.client.get(f"/app/blog/media/{media.id}/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], media.id)
        self.assertEqual(response.data["filename"], "test.jpg")

    def test_delete_media_file(self):
        """Test deleting a media file."""
        media = BlogMedia.objects.create(
            filename="test.jpg",
            original_filename="test.jpg",
            file_type="image/jpeg",
            file_size=1024,
            uploaded_by=self.user,
        )

        response = self.client.delete(f"/app/blog/media/{media.id}/")

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(BlogMedia.objects.filter(id=media.id).exists())

    def test_unauthenticated_access(self):
        """Test that unauthenticated users cannot access media endpoints."""
        self.client.force_authenticate(user=None)

        response = self.client.get("/app/blog/media/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        response = self.client.post("/app/blog/media/upload/", {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_date_range_filtering(self):
        """Test filtering media files by date range."""
        from datetime import datetime, timedelta

        # Create media files with different dates
        old_media = BlogMedia.objects.create(
            filename="old.jpg",
            original_filename="old.jpg",
            file_type="image/jpeg",
            file_size=1024,
            uploaded_by=self.user,
        )
        # Manually set an older date
        old_date = datetime.now() - timedelta(days=7)
        old_media.upload_date = old_date
        old_media.save()

        recent_media = BlogMedia.objects.create(
            filename="recent.jpg",
            original_filename="recent.jpg",
            file_type="image/jpeg",
            file_size=1024,
            uploaded_by=self.user,
        )

        # Filter for recent files
        yesterday = (datetime.now() - timedelta(days=1)).isoformat()
        response = self.client.get(f"/app/blog/media/?date_start={yesterday}")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["id"], recent_media.id)


class BlogPostAPITestCase(TestCase):
    """Test cases for Blog Post API endpoints."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="test@example.com", username="testuser", password="testpass123"
        )
        self.client.force_authenticate(user=self.user)

        self.tag = Tag.objects.create(name="Test Tag")

    def test_create_blog_post(self):
        """Test creating a blog post."""
        data = {
            "title": "Test Blog Post",
            "excerpt": "This is a test excerpt",
            "body_markdown": "# Test Content\n\nThis is test content.",
            "status": "published",
            "tags": [self.tag.id],
        }

        response = self.client.post("/app/blog/posts/", data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["title"], "Test Blog Post")
        self.assertEqual(response.data["author"]["id"], self.user.id)

    def test_list_blog_posts(self):
        """Test listing blog posts."""
        BlogPost.objects.create(
            title="Test Post 1",
            author=self.user,
            body_markdown="Content 1",
            status="published",
        )
        BlogPost.objects.create(
            title="Test Post 2",
            author=self.user,
            body_markdown="Content 2",
            status="draft",
        )

        response = self.client.get("/app/blog/posts/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertEqual(len(response.data["results"]), 2)

    def test_get_post_by_slug(self):
        """Test retrieving a post by slug."""
        post = BlogPost.objects.create(
            title="Test Post",
            author=self.user,
            body_markdown="Test content",
            status="published",
        )

        response = self.client.get(f"/app/blog/slug/{post.slug}/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], post.id)
        self.assertEqual(response.data["slug"], post.slug)

    def test_duplicate_title_creates_unique_slug(self):
        """Test that duplicate titles create unique slugs."""
        data = {
            "title": "Duplicate Title",
            "body_markdown": "Content 1",
            "status": "published",
        }

        # Create first post
        response1 = self.client.post("/app/blog/posts/", data)
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)

        # Create second post with same title
        data["body_markdown"] = "Content 2"
        response2 = self.client.post("/app/blog/posts/", data)
        self.assertEqual(response2.status_code, status.HTTP_201_CREATED)

        # Slugs should be different
        self.assertNotEqual(response1.data["slug"], response2.data["slug"])
        self.assertTrue(response2.data["slug"].endswith("-1"))
