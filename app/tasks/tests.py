from datetime import datetime, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from .models import Category, Project, Task

User = get_user_model()


class TaskFilteringAPITestCase(TestCase):
    """Test cases for advanced task filtering."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="test@example.com", username="testuser", password="testpass123"
        )
        self.client.force_authenticate(user=self.user)

        # Create test categories
        self.web_category = Category.objects.create(slug="web", name="Web Development")
        self.design_category = Category.objects.create(slug="design", name="Design")

        # Create test project
        self.project = Project.objects.create(
            name="Test Project", user_id=self.user, status="in_progress"
        )

        # Create test tasks
        self.task1 = Task.objects.create(
            title="Web Development Task",
            description="Build a website",
            status="todo",
            priority="high",
            user_id=self.user,
            project=self.project,
            due_date=datetime.now().date() + timedelta(days=5),
        )
        self.task1.category.add(self.web_category)

        self.task2 = Task.objects.create(
            title="Design Task",
            description="Create mockups",
            status="in_progress",
            priority="medium",
            user_id=self.user,
            due_date=datetime.now().date() + timedelta(days=10),
        )
        self.task2.category.add(self.design_category)

        self.task3 = Task.objects.create(
            title="Bug Fix",
            description="Fix critical bug",
            status="completed",
            priority="high",
            user_id=self.user,
            project=self.project,
        )

    def test_filter_by_category(self):
        """Test filtering tasks by category."""
        response = self.client.get("/app/tasks/tasks/?category=web")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["id"], self.task1.id)
        self.assertIn("filters_applied", response.data)
        self.assertEqual(response.data["filters_applied"]["categories"], ["web"])

    def test_filter_by_multiple_categories(self):
        """Test filtering tasks by multiple categories."""
        response = self.client.get("/app/tasks/tasks/?category=web&category=design")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should return tasks that have ALL specified categories
        self.assertIn("filters_applied", response.data)
        self.assertEqual(
            set(response.data["filters_applied"]["categories"]), {"web", "design"}
        )

    def test_filter_by_project(self):
        """Test filtering tasks by project."""
        response = self.client.get("/app/tasks/tasks/?project=Test Project")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)  # task1 and task3
        self.assertIn("filters_applied", response.data)
        self.assertEqual(response.data["filters_applied"]["projects"], ["Test Project"])

    def test_filter_by_status(self):
        """Test filtering tasks by status."""
        response = self.client.get("/app/tasks/tasks/?status=todo&status=in_progress")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)  # task1 and task2
        self.assertIn("filters_applied", response.data)
        self.assertEqual(
            set(response.data["filters_applied"]["status"]), {"todo", "in_progress"}
        )

    def test_filter_by_priority(self):
        """Test filtering tasks by priority."""
        response = self.client.get("/app/tasks/tasks/?priority=high")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)  # task1 and task3
        self.assertIn("filters_applied", response.data)
        self.assertEqual(response.data["filters_applied"]["priority"], ["high"])

    def test_filter_by_date_range(self):
        """Test filtering tasks by due date range."""
        start_date = (datetime.now() + timedelta(days=1)).date().isoformat()
        end_date = (datetime.now() + timedelta(days=7)).date().isoformat()

        response = self.client.get(
            f"/app/tasks/tasks/?due_date_start={start_date}&due_date_end={end_date}"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)  # Only task1
        self.assertEqual(response.data["results"][0]["id"], self.task1.id)
        self.assertIn("filters_applied", response.data)
        self.assertIn("date_range", response.data["filters_applied"])

    def test_search_functionality(self):
        """Test full-text search across title and description."""
        response = self.client.get("/app/tasks/tasks/?search=bug")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)  # Only task3
        self.assertEqual(response.data["results"][0]["id"], self.task3.id)
        self.assertIn("filters_applied", response.data)
        self.assertEqual(response.data["filters_applied"]["search"], "bug")

    def test_combined_filters(self):
        """Test combining multiple filters."""
        response = self.client.get(
            "/app/tasks/tasks/?priority=high&status=todo&search=web"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)  # Only task1
        self.assertIn("filters_applied", response.data)
        filters = response.data["filters_applied"]
        self.assertEqual(filters["priority"], ["high"])
        self.assertEqual(filters["status"], ["todo"])
        self.assertEqual(filters["search"], "web")

    def test_pagination_with_filters(self):
        """Test that pagination works with filters."""
        # Create more tasks
        for i in range(15):
            task = Task.objects.create(
                title=f"Extra Task {i}",
                description="Extra task description",
                status="todo",
                priority="low",
                user_id=self.user,
            )
            task.category.add(self.web_category)

        response = self.client.get("/app/tasks/tasks/?category=web&page_size=10")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("next", response.data)  # Should have next page
        self.assertEqual(len(response.data["results"]), 10)

    def test_invalid_date_format_ignored(self):
        """Test that invalid date formats are ignored gracefully."""
        response = self.client.get("/app/tasks/tasks/?due_date_start=invalid-date")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should return all tasks since invalid filter is ignored
        self.assertEqual(len(response.data["results"]), 3)


class TaskBulkOperationsTestCase(TestCase):
    """Test cases for bulk task operations."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="test@example.com", username="testuser", password="testpass123"
        )
        self.client.force_authenticate(user=self.user)

        # Create test tasks
        self.tasks = []
        for i in range(5):
            task = Task.objects.create(
                title=f"Task {i}",
                description=f"Description {i}",
                status="todo",
                priority="low",
                user_id=self.user,
            )
            self.tasks.append(task)

        # Create a project for testing
        self.project = Project.objects.create(
            name="Bulk Test Project", user_id=self.user, status="in_progress"
        )

    def test_bulk_update_status(self):
        """Test bulk updating task status."""
        task_ids = [task.id for task in self.tasks[:3]]
        data = {"task_ids": task_ids, "updates": {"status": "completed"}}

        response = self.client.post(
            "/app/tasks/tasks/bulk-update/", data, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["updated_count"], 3)
        self.assertEqual(len(response.data["failed_updates"]), 0)

        # Verify tasks were updated
        for task_id in task_ids:
            task = Task.objects.get(id=task_id)
            self.assertEqual(task.status, "completed")

    def test_bulk_update_priority(self):
        """Test bulk updating task priority."""
        task_ids = [task.id for task in self.tasks[:2]]
        data = {"task_ids": task_ids, "updates": {"priority": "high"}}

        response = self.client.post(
            "/app/tasks/tasks/bulk-update/", data, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["updated_count"], 2)

        # Verify tasks were updated
        for task_id in task_ids:
            task = Task.objects.get(id=task_id)
            self.assertEqual(task.priority, "high")

    def test_bulk_update_project(self):
        """Test bulk updating task project."""
        task_ids = [task.id for task in self.tasks[:2]]
        data = {"task_ids": task_ids, "updates": {"project": "Bulk Test Project"}}

        response = self.client.post(
            "/app/tasks/tasks/bulk-update/", data, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["updated_count"], 2)

        # Verify tasks were updated
        for task_id in task_ids:
            task = Task.objects.get(id=task_id)
            self.assertEqual(task.project, self.project)

    def test_bulk_update_nonexistent_project(self):
        """Test bulk updating with nonexistent project."""
        task_ids = [self.tasks[0].id]
        data = {"task_ids": task_ids, "updates": {"project": "Nonexistent Project"}}

        response = self.client.post(
            "/app/tasks/tasks/bulk-update/", data, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["updated_count"], 0)
        self.assertEqual(len(response.data["failed_updates"]), 1)
        self.assertIn("not found", response.data["failed_updates"][0]["error"])

    def test_bulk_update_invalid_task_ids(self):
        """Test bulk updating with invalid task IDs."""
        data = {
            "task_ids": [9999, 8888],  # Non-existent IDs
            "updates": {"status": "completed"},
        }

        response = self.client.post(
            "/app/tasks/tasks/bulk-update/", data, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["updated_count"], 0)
        self.assertEqual(len(response.data["failed_updates"]), 2)

    def test_bulk_delete(self):
        """Test bulk deleting tasks."""
        task_ids = [task.id for task in self.tasks[:3]]
        data = {"task_ids": task_ids}

        response = self.client.delete(
            "/app/tasks/tasks/bulk-delete/", data, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["deleted_count"], 3)
        self.assertEqual(len(response.data["failed_deletes"]), 0)

        # Verify tasks were deleted
        for task_id in task_ids:
            self.assertFalse(Task.objects.filter(id=task_id).exists())

    def test_bulk_delete_invalid_ids(self):
        """Test bulk deleting with invalid task IDs."""
        data = {"task_ids": [9999, 8888]}  # Non-existent IDs

        response = self.client.delete(
            "/app/tasks/tasks/bulk-delete/", data, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["deleted_count"], 0)
        self.assertEqual(response.data["failed_deletes"], [9999, 8888])

    def test_bulk_operations_user_isolation(self):
        """Test that users can only perform bulk operations on their own tasks."""
        # Create another user and their tasks
        other_user = User.objects.create_user(
            email="other@example.com", username="otheruser", password="otherpass123"
        )
        other_task = Task.objects.create(
            title="Other User Task",
            description="Not accessible",
            status="todo",
            priority="low",
            user_id=other_user,
        )

        # Try to update other user's task
        data = {"task_ids": [other_task.id], "updates": {"status": "completed"}}

        response = self.client.post(
            "/app/tasks/tasks/bulk-update/", data, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["updated_count"], 0)
        self.assertEqual(len(response.data["failed_updates"]), 1)
        self.assertIn(
            "not found or not owned", response.data["failed_updates"][0]["error"]
        )

    def test_bulk_operations_validation(self):
        """Test validation for bulk operations."""
        # Test missing task_ids
        response = self.client.post(
            "/app/tasks/tasks/bulk-update/",
            {"updates": {"status": "completed"}},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Test missing updates
        response = self.client.post(
            "/app/tasks/tasks/bulk-update/",
            {"task_ids": [self.tasks[0].id]},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Test empty task_ids for bulk delete
        response = self.client.delete(
            "/app/tasks/tasks/bulk-delete/", {"task_ids": []}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
