from datetime import datetime, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

User = get_user_model()


class AdminUserManagementTestCase(TestCase):
    """Test cases for admin user management API."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()

        # Create admin user
        self.admin_user = User.objects.create_user(
            email="admin@example.com",
            username="admin",
            password="adminpass123",
            is_staff=True,
            is_superuser=True,
        )

        # Create regular user
        self.regular_user = User.objects.create_user(
            email="user@example.com", username="user", password="userpass123"
        )

        # Create inactive user
        self.inactive_user = User.objects.create_user(
            email="inactive@example.com",
            username="inactive",
            password="inactivepass123",
            is_active=False,
        )

    def test_admin_can_list_users(self):
        """Test that admin users can list all users."""
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.get("/api/admin/users/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertEqual(len(response.data["results"]), 3)  # admin, regular, inactive

    def test_regular_user_cannot_access_admin_endpoints(self):
        """Test that regular users cannot access admin endpoints."""
        self.client.force_authenticate(user=self.regular_user)

        response = self.client.get("/api/admin/users/")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_cannot_access_admin_endpoints(self):
        """Test that unauthenticated users cannot access admin endpoints."""
        response = self.client.get("/api/admin/users/")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_filter_users_by_active_status(self):
        """Test filtering users by active status."""
        self.client.force_authenticate(user=self.admin_user)

        # Filter for active users
        response = self.client.get("/api/admin/users/?is_active=true")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        active_users = [user for user in response.data["results"] if user["is_active"]]
        self.assertEqual(len(active_users), len(response.data["results"]))

        # Filter for inactive users
        response = self.client.get("/api/admin/users/?is_active=false")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        inactive_users = [
            user for user in response.data["results"] if not user["is_active"]
        ]
        self.assertEqual(len(inactive_users), len(response.data["results"]))

    def test_filter_users_by_staff_status(self):
        """Test filtering users by staff status."""
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.get("/api/admin/users/?is_staff=true")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        staff_users = [user for user in response.data["results"] if user["is_staff"]]
        self.assertEqual(len(staff_users), len(response.data["results"]))

    def test_search_users(self):
        """Test searching users by email, username, etc."""
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.get("/api/admin/users/?search=admin")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data["results"]) >= 1)
        # Should find the admin user
        admin_found = any(
            user["email"] == "admin@example.com" for user in response.data["results"]
        )
        self.assertTrue(admin_found)

    def test_update_user_permissions(self):
        """Test updating user permissions."""
        self.client.force_authenticate(user=self.admin_user)

        data = {"is_staff": True, "is_active": True}

        response = self.client.patch(f"/api/admin/users/{self.regular_user.id}/", data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify user was updated
        self.regular_user.refresh_from_db()
        self.assertTrue(self.regular_user.is_staff)
        self.assertTrue(self.regular_user.is_active)

    def test_toggle_user_active_status(self):
        """Test toggling user active status."""
        self.client.force_authenticate(user=self.admin_user)

        # Deactivate user
        response = self.client.patch(
            f"/api/admin/users/{self.regular_user.id}/toggle-active/",
            {"is_active": False},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("deactivated", response.data["message"])

        # Verify user was deactivated
        self.regular_user.refresh_from_db()
        self.assertFalse(self.regular_user.is_active)

        # Reactivate user
        response = self.client.patch(
            f"/api/admin/users/{self.regular_user.id}/toggle-active/",
            {"is_active": True},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("activated", response.data["message"])

        # Verify user was reactivated
        self.regular_user.refresh_from_db()
        self.assertTrue(self.regular_user.is_active)

    def test_reset_user_password(self):
        """Test admin-initiated password reset."""
        self.client.force_authenticate(user=self.admin_user)

        data = {"new_password": "newpassword123!"}

        response = self.client.post(
            f"/api/admin/users/{self.regular_user.id}/reset-password/", data
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("Password reset successfully", response.data["message"])

        # Verify password was changed (user should be able to login with new password)
        self.regular_user.refresh_from_db()
        self.assertTrue(self.regular_user.check_password("newpassword123!"))

    def test_reset_password_validation(self):
        """Test password reset validation."""
        self.client.force_authenticate(user=self.admin_user)

        # Test weak password
        data = {"new_password": "123"}  # Too short

        response = self.client.post(
            f"/api/admin/users/{self.regular_user.id}/reset-password/", data
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_delete_user_not_allowed(self):
        """Test that user deletion is not allowed through API."""
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.delete(f"/api/admin/users/{self.regular_user.id}/")

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertIn("not allowed", response.data["error"])

    def test_pagination_admin_users(self):
        """Test pagination for admin user list."""
        self.client.force_authenticate(user=self.admin_user)

        # Create more users to test pagination
        for i in range(25):
            User.objects.create_user(
                email=f"user{i}@example.com",
                username=f"user{i}",
                password="password123",
            )

        response = self.client.get("/api/admin/users/?page_size=10")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("next", response.data)  # Should have next page
        self.assertEqual(len(response.data["results"]), 10)

    def test_date_range_filtering(self):
        """Test filtering users by registration date."""
        self.client.force_authenticate(user=self.admin_user)

        # Create user with specific date
        recent_user = User.objects.create_user(
            email="recent@example.com", username="recent", password="password123"
        )

        # Filter for recent registrations
        yesterday = (datetime.now() - timedelta(days=1)).isoformat()
        response = self.client.get(
            f"/api/admin/users/?registration_date_start={yesterday}"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should include the recently created user
        user_emails = [user["email"] for user in response.data["results"]]
        self.assertIn("recent@example.com", user_emails)

    def test_ordering_users(self):
        """Test ordering users by different fields."""
        self.client.force_authenticate(user=self.admin_user)

        # Test ordering by date_joined (most recent first)
        response = self.client.get("/api/admin/users/?ordering=-date_joined")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data["results"]
        self.assertTrue(len(results) >= 2)

        # Verify ordering (most recent first)
        for i in range(len(results) - 1):
            first_date = datetime.fromisoformat(
                results[i]["date_joined"].replace("Z", "+00:00")
            )
            second_date = datetime.fromisoformat(
                results[i + 1]["date_joined"].replace("Z", "+00:00")
            )
            self.assertGreaterEqual(first_date, second_date)


class ErrorResponseTestCase(TestCase):
    """Test cases for standardized error responses."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="test@example.com", username="testuser", password="testpass123"
        )

    def test_authentication_error_format(self):
        """Test that authentication errors follow standard format."""
        response = self.client.get("/api/admin/users/")  # Requires authentication

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("error", response.data)
        self.assertIn("code", response.data["error"])
        self.assertIn("message", response.data["error"])
        self.assertIn("timestamp", response.data)
        self.assertIn("request_id", response.data)

    def test_permission_error_format(self):
        """Test that permission errors follow standard format."""
        self.client.force_authenticate(user=self.user)  # Regular user, not admin

        response = self.client.get("/api/admin/users/")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("error", response.data)
        self.assertEqual(response.data["error"]["code"], "PERMISSION_DENIED")
        self.assertIn("timestamp", response.data)
        self.assertIn("request_id", response.data)

    def test_not_found_error_format(self):
        """Test that 404 errors follow standard format."""
        self.client.force_authenticate(user=self.user)

        response = self.client.get("/app/tasks/tasks/99999/")  # Non-existent task

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("error", response.data)
        self.assertEqual(response.data["error"]["code"], "RESOURCE_NOT_FOUND")
        self.assertIn("timestamp", response.data)
        self.assertIn("request_id", response.data)

    def test_validation_error_format(self):
        """Test that validation errors follow standard format."""
        self.client.force_authenticate(user=self.user)

        # Send invalid data to create a task
        response = self.client.post(
            "/app/tasks/tasks/",
            {
                "title": "",  # Required field empty
                "status": "invalid_status",  # Invalid choice
            },
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
        self.assertEqual(response.data["error"]["code"], "VALIDATION_ERROR")
        self.assertIn("field_errors", response.data["error"])
        self.assertIn("timestamp", response.data)
        self.assertIn("request_id", response.data)
