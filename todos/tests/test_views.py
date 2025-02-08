import json
import uuid
from unittest.mock import patch

from django.test import Client, TestCase
from django.urls import reverse

from todos.models import Todo


class TodoListViewTest(TestCase):
    def setUp(self):
        self.url = reverse("todo_list")

    @patch("todos.views.get_external_todo_data")
    def test_calls_external_api_when_no_todos_exist(self, mock_get_external) -> None:
        """
        When the database is empty, the view should call get_external_todo_data
        to populate it.
        """
        # Ensure the database is empty
        self.assertFalse(Todo.objects.exists())

        # Perform a GET request
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        # Check that the external data fetching function was called exactly once.
        mock_get_external.assert_called_once()

        # Even though the external function is called, your test does not depend
        # on its implementation. If that function creates objects, they should now
        # be present in the context. You might optionally check context variables.
        self.assertIn("total_todos", response.context)
        self.assertIn("completed_todos", response.context)
        self.assertIn("uncompleted_todos", response.context)

    @patch("todos.views.get_external_todo_data")
    def test_does_not_call_external_api_when_todos_exist(
        self, mock_get_external
    ) -> None:
        """
        If there are already todos in the database, the external API should not be called.
        """
        # Create a sample Todo in the database.
        Todo.objects.create(api_id=1, title="Sample Todo", completed=False, user_id=1)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        # Confirm that the external API was not called.
        mock_get_external.assert_not_called()

    @patch("todos.views.get_external_todo_data")
    def test_filtering_functionality(self, mock_get_external) -> None:
        """
        Test that the view correctly filters todos based on the 'filter' GET parameter.
        """
        # Create two todos: one completed and one not.
        Todo.objects.create(
            api_id=1, title="Incomplete Todo", completed=False, user_id=1
        )
        Todo.objects.create(api_id=2, title="Complete Todo", completed=True, user_id=2)

        # Test filter for incomplete todos.
        response = self.client.get(self.url, {"filter": "todo"})
        self.assertEqual(response.status_code, 200)
        todos = response.context["todos"]
        for todo in todos:
            self.assertFalse(todo.completed)

        # Test filter for completed todos.
        response = self.client.get(self.url, {"filter": "complete"})
        self.assertEqual(response.status_code, 200)
        todos = response.context["todos"]
        for todo in todos:
            self.assertTrue(todo.completed)

        # Test filter for all todos.
        response = self.client.get(self.url, {"filter": "all"})
        self.assertEqual(response.status_code, 200)
        todos = response.context["todos"]
        self.assertEqual(todos.count(), 2)

    @patch("todos.views.get_external_todo_data")
    def test_context_data_includes_extra_information(self, mock_get_external) -> None:
        """
        Verify that extra context variables (total_todos, completed_todos, uncompleted_todos, current_filter)
        are correctly added to the context.
        """
        # Create sample todos.
        Todo.objects.create(
            api_id=1, title="Incomplete Todo", completed=False, user_id=1
        )
        Todo.objects.create(api_id=2, title="Complete Todo", completed=True, user_id=2)

        # Make a GET request with a filter parameter.
        response = self.client.get(self.url, {"filter": "complete"})
        self.assertEqual(response.status_code, 200)

        context = response.context
        # Check that the context has the extra keys.
        self.assertIn("total_todos", context)
        self.assertIn("completed_todos", context)
        self.assertIn("uncompleted_todos", context)
        self.assertIn("current_filter", context)

        # Verify the counts.
        self.assertEqual(context["total_todos"], 2)
        self.assertEqual(context["completed_todos"], 1)
        self.assertEqual(context["uncompleted_todos"], 1)
        self.assertEqual(context["current_filter"], "complete")

    def test_pagination(self) -> None:
        """
        Test that the view paginates the Todo items correctly.

        - Creates 25 Todo objects.
        - Verifies that the first page contains 20 items.
        - Verifies that pagination is active.
        - Verifies that the second page contains the remaining 5 items.
        """
        for i in range(25):
            Todo.objects.create(api_id=i, title=f"Todo {i}", completed=False, user_id=1)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        # Check first page has 20 items
        todos_on_first_page = response.context["todos"]
        self.assertEqual(todos_on_first_page.count(), 20)
        # Check pagination is active
        self.assertTrue(response.context["is_paginated"])

        # Retrieve the second page
        response_page_2 = self.client.get(self.url, {"page": 2})
        todos_on_second_page = response_page_2.context["todos"]
        self.assertEqual(todos_on_second_page.count(), 5)

    def test_default_ordering(self) -> None:
        """
        Test that the view orders the Todo items by their 'api_id' in ascending order.
        """
        Todo.objects.create(api_id=10, title="Todo 10", completed=False, user_id=1)
        Todo.objects.create(api_id=2, title="Todo 2", completed=False, user_id=1)
        Todo.objects.create(api_id=5, title="Todo 5", completed=True, user_id=1)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        todos = response.context["todos"]
        api_ids = [todo.api_id for todo in todos]
        # Verify they are in ascending order
        self.assertEqual(api_ids, sorted(api_ids))

    def test_invalid_filter_param_defaults_to_all(self) -> None:
        """
        Test that providing an invalid filter parameter defaults to returning all todos.

        - Creates one completed and one uncompleted Todo.
        - Passes a non-existent filter parameter in the query string.
        - Expects the response to contain all todos.
        - Expects the 'current_filter' context to be set to 'all'.
        """
        Todo.objects.create(
            api_id=1, title="Incomplete Todo", completed=False, user_id=1
        )
        Todo.objects.create(api_id=2, title="Complete Todo", completed=True, user_id=2)

        response = self.client.get(self.url, {"filter": "non-existent-filter"})
        self.assertEqual(response.status_code, 200)

        todos = response.context["todos"]
        # Should return all todos if the filter is invalid
        self.assertEqual(todos.count(), 2)
        # Also confirm that the current_filter in context is "all"
        self.assertEqual(response.context["current_filter"], "all")

    @patch("todos.views.get_external_todo_data")
    def test_external_api_failure_graceful_handling(self, mock_get_external) -> None:
        """
        Test the view's behavior when the external API call fails.

        - Mocks get_external_todo_data to raise an exception.
        - Expects the view to handle this gracefully and return 200.
        - Expects the database to remain empty.
        """
        mock_get_external.side_effect = Exception("External API error")

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Todo.objects.exists())

    def test_no_filter_param(self) -> None:
        """
        Test that omitting the 'filter' parameter in the query string
        returns all Todo objects.
        """
        Todo.objects.create(api_id=1, title="Test 1", completed=False, user_id=1)
        Todo.objects.create(api_id=2, title="Test 2", completed=True, user_id=1)
        Todo.objects.create(api_id=3, title="Test 3", completed=True, user_id=2)

        # Make a request without a 'filter' parameter
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        todos = response.context["todos"]
        # Should get all 3
        self.assertEqual(todos.count(), 3)
        self.assertEqual(response.context["current_filter"], "all")


class ToggleTodoCompletionTests(TestCase):
    """Test suite for the toggle_todo_completion view."""

    def setUp(self) -> None:
        """
        Create a Django test client and a sample Todo object.
        We'll manipulate this Todo in different tests.
        """
        self.client = Client()
        self.url = reverse("toggle_todo")

        # Create a Todo item for testing.
        self.todo = Todo.objects.create(
            api_id=999, title="Test Todo", completed=False, user_id=1
        )

    def test_toggle_todo_successful(self) -> None:
        """
        Ensure that a valid POST request with a correct 'todo_id'
        toggles the 'completed' status of the Todo.
        """
        payload = {
            "todo_id": str(self.todo.uuid)
        }  # Must be a string for JSON serializing
        response = self.client.post(
            self.url, data=json.dumps(payload), content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)

        # Check JSON response.
        data = response.json()
        self.assertTrue(data["success"])
        self.assertIn("completed", data)
        self.assertTrue(
            data["completed"]
        )

        # Refresh from DB and confirm it actually toggled.
        self.todo.refresh_from_db()
        self.assertTrue(self.todo.completed)

    def test_missing_todo_id(self) -> None:
        """
        Sending a POST request without 'todo_id' should return a 400 status
        and an appropriate error message.
        """
        payload = {}  # Missing 'todo_id'
        response = self.client.post(
            self.url, data=json.dumps(payload), content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)

        data = response.json()
        self.assertFalse(data["success"])
        self.assertIn("error", data)
        self.assertEqual(data["error"], "Missing todo_id")

    def test_todo_not_found(self) -> None:
        """
        Providing a 'todo_id' that doesn't exist in the database
        should return a 404 status and an appropriate error message.
        """
        fake_uuid = str(uuid.uuid4())  # Random UUID not in the database
        payload = {"todo_id": fake_uuid}
        response = self.client.post(
            self.url, data=json.dumps(payload), content_type="application/json"
        )
        self.assertEqual(response.status_code, 404)

        data = response.json()
        self.assertFalse(data["success"])
        self.assertIn("error", data)
        self.assertEqual(data["error"], "Todo not found")

    def test_invalid_json(self) -> None:
        """
        Providing invalid JSON data in the body (e.g., a string that
        cannot be parsed as JSON) should return a 400 status with an error.
        """
        invalid_payload = "This is not valid JSON"
        response = self.client.post(
            self.url, data=invalid_payload, content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)

        data = response.json()
        self.assertFalse(data["success"])
        self.assertIn("error", data)
        self.assertEqual(data["error"], "Invalid JSON")

    def test_method_not_allowed(self) -> None:
        """
        The view is decorated with @require_http_methods(["POST"]).
        Sending a GET request should return a 405 (Method Not Allowed).
        """
        response = self.client.get(self.url)
        self.assertEqual(
            response.status_code, 405
        )

    @patch("todos.views.logger.exception")
    def test_unexpected_exception(self, mock_logger) -> None:
        """
        Simulate an unexpected exception inside the view (e.g., DB error).
        We'll patch the 'Todo.objects.get' to raise an Exception,
        then verify we handle it gracefully.
        """
        with patch(
            "todos.models.Todo.objects.get",
            side_effect=Exception("Something went wrong"),
        ):
            payload = {"todo_id": str(self.todo.uuid)}
            response = self.client.post(
                self.url, data=json.dumps(payload), content_type="application/json"
            )
            self.assertEqual(response.status_code, 400)

            data = response.json()
            self.assertFalse(data["success"])
            self.assertIn("error", data)
            self.assertEqual(data["error"], "Something went wrong")

            # Ensure our logger.exception was called.
            mock_logger.assert_called_once()
