from unittest import mock
from unittest.mock import MagicMock, patch

import requests
from django.test import TestCase

from todos.helpers import fetch_todos_from_api, get_external_todo_data
from todos.models import Todo


class FetchTodosFromApiTests(TestCase):
    """Test suite for the fetch_todos_from_api helper function."""

    def setUp(self) -> None:
        self.url = "https://example.com/api/todos"
        self.mock_json_data = [
            {"userId": 1, "id": 1, "title": "Test Todo 1", "completed": False},
            {"userId": 2, "id": 2, "title": "Test Todo 2", "completed": True},
        ]

    @patch("todos.helpers.todo_list_view_helper.requests.Session")
    def test_fetch_todos_successful(self, mock_session: MagicMock) -> None:
        """
        Test that fetch_todos_from_api returns JSON data on a successful response (HTTP 200).
        """
        # Configure the mock session to return a response with a 200 status code.
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.mock_json_data
        mock_session_instance = mock_session.return_value
        mock_session_instance.get.return_value = mock_response

        todos = fetch_todos_from_api(url=self.url)

        self.assertIsInstance(todos, list)
        self.assertEqual(todos, self.mock_json_data)
        # Ensure requests.Session.get was called once with the correct URL
        mock_session_instance.get.assert_called_once_with(self.url, timeout=10)

    @patch("todos.helpers.todo_list_view_helper.requests.Session")
    def test_fetch_todos_raises_exception_on_http_error(
        self, mock_session: MagicMock
    ) -> None:
        """
        Test that fetch_todos_from_api raises a RequestException if response.raise_for_status() fails
        (e.g., 4xx or 5xx after all retries).
        """
        # Mock a 500 response that triggers raise_for_status
        mock_response = mock.Mock()
        mock_response.status_code = 500
        # The next line ensures that calling response.raise_for_status() raises an HTTPError
        mock_response.raise_for_status.side_effect = requests.HTTPError("Server Error")

        mock_session_instance = mock_session.return_value
        mock_session_instance.get.return_value = mock_response

        with self.assertRaises(requests.RequestException):
            fetch_todos_from_api(url=self.url)

    @patch("todos.helpers.todo_list_view_helper.requests.Session")
    def test_fetch_todos_custom_status_forcelist(self, mock_session: MagicMock) -> None:
        """
        Test that the function respects a custom status_forcelist.
        If the error status is not in the list, it should not retry.
        """
        # We only retry on 500, but the server returns 400
        mock_response = mock.Mock()
        mock_response.status_code = 400
        mock_response.raise_for_status.side_effect = requests.HTTPError("Bad Request")

        mock_session_instance = mock_session.return_value
        mock_session_instance.get.return_value = mock_response

        custom_status = [500]  # 400 is not in the status_forcelist
        with self.assertRaises(requests.RequestException):
            # It should fail immediately without retrying
            fetch_todos_from_api(url=self.url, status_forcelist=custom_status)

        self.assertEqual(mock_session_instance.get.call_count, 1)

    @patch("todos.helpers.todo_list_view_helper.requests.Session")
    def test_fetch_todos_timeout(self, mock_session: MagicMock) -> None:
        """
        Test that a timeout error is raised if the request times out.
        """
        mock_session_instance = mock_session.return_value
        mock_session_instance.get.side_effect = requests.Timeout("Request timed out")

        with self.assertRaises(requests.RequestException):
            fetch_todos_from_api(url=self.url)

        # Should have attempted at least once
        mock_session_instance.get.assert_called_once_with(self.url, timeout=10)


class GetExternalTodoDataTests(TestCase):
    """Test suite for the get_external_todo_data helper function."""

    def setUp(self) -> None:
        self.test_todos_payload = [
            {"userId": 1, "id": 10, "title": "Title 1", "completed": False},
            {"userId": 1, "id": 11, "title": "Title 2", "completed": True},
            {"userId": 2, "id": 12, "title": "Title 3", "completed": False},
        ]

    @patch("todos.helpers.todo_list_view_helper.config")
    @patch("todos.helpers.todo_list_view_helper.fetch_todos_from_api")
    def test_successful_data_fetch(
        self, mock_fetch: MagicMock, mock_config: MagicMock
    ) -> None:
        """
        Test that get_external_todo_data creates Todo objects in the DB
        when the external API call returns valid data.
        """
        # Mock config to return a test URL
        mock_config.return_value = "http://fakeurl.com"
        # Mock fetch_todos_from_api to return our sample payload
        mock_fetch.return_value = self.test_todos_payload

        result = get_external_todo_data()
        # The function should have created 3 Todo objects
        self.assertIsNotNone(result)
        self.assertEqual(Todo.objects.count(), 3)

        # Check that each item from payload was created
        todo_ids_in_db = set(Todo.objects.values_list("api_id", flat=True))
        expected_ids = {10, 11, 12}
        self.assertEqual(todo_ids_in_db, expected_ids)

        # Check the call to fetch was made with the correct URL from mock_config
        mock_config.assert_called_with("TODO_API_URL", cast=str)
        mock_fetch.assert_called_once_with("http://fakeurl.com")

    @patch("todos.helpers.todo_list_view_helper.config")
    @patch("todos.helpers.todo_list_view_helper.fetch_todos_from_api", return_value=[])
    def test_empty_data_returns_none(
        self, mock_fetch: MagicMock, mock_config: MagicMock
    ) -> None:
        """
        If the external API returns an empty list, the function should not
        create any objects and should return None.
        """
        mock_config.return_value = "http://fakeurl.com"
        result = get_external_todo_data()

        self.assertIsNone(result)
        self.assertEqual(Todo.objects.count(), 0)
        mock_fetch.assert_called_once()

    @patch("todos.helpers.todo_list_view_helper.config")
    @patch(
        "todos.helpers.todo_list_view_helper.fetch_todos_from_api",
        side_effect=Exception("API error"),
    )
    @patch("todos.helpers.todo_list_view_helper.logger")
    def test_fetch_error_logs_and_returns_none(
        self, mock_logger: MagicMock, mock_fetch: MagicMock, mock_config: MagicMock
    ) -> None:
        """
        If fetching data fails (e.g., raises an exception), we log the error and return None.
        """
        mock_config.return_value = "http://fakeurl.com"
        result = get_external_todo_data()

        self.assertIsNone(result)
        self.assertEqual(Todo.objects.count(), 0)
        mock_fetch.assert_called_once()
        # Ensure logger.error was called
        mock_logger.error.assert_called_once()
        self.assertIn(
            "Error fetching todos from external API", mock_logger.error.call_args[0][0]
        )

    @patch("todos.helpers.todo_list_view_helper.config")
    @patch("todos.helpers.todo_list_view_helper.fetch_todos_from_api")
    @patch("todos.helpers.todo_list_view_helper.random.randint", return_value=5)
    def test_random_user_image_is_assigned(
        self, mock_randint: MagicMock, mock_fetch: MagicMock, mock_config: MagicMock
    ) -> None:
        """
        Test that each new user gets a random image assigned, and that the same user
        in the same payload gets the same image.
        """
        mock_config.return_value = "http://fakeurl.com"
        mock_fetch.return_value = self.test_todos_payload

        # Force random.randint to return 5 for the first user call, then something else for the second
        def randint_side_effect(low, high):
            # userId=1 is first encountered -> returns 5
            # userId=2 is second encountered -> returns 3
            if not hasattr(self, "_times_called"):
                self._times_called = 0
            if self._times_called == 0:
                result = 5
            else:
                result = 3
            self._times_called += 1
            return result

        mock_randint.side_effect = randint_side_effect

        get_external_todo_data()

        todos_user_1 = Todo.objects.filter(user_id=1)
        todos_user_2 = Todo.objects.filter(user_id=2)

        # Both user 1 items should have image=5
        for t in todos_user_1:
            self.assertEqual(t.image, "5")

        # user 2 item should have image=3
        for t in todos_user_2:
            self.assertEqual(t.image, "3")

        # We expected random.randint to be called exactly 2 times (for 2 distinct userIds)
        self.assertEqual(mock_randint.call_count, 2)

    @patch("todos.helpers.todo_list_view_helper.config")
    @patch("todos.helpers.todo_list_view_helper.fetch_todos_from_api")
    def test_same_user_image_consistency(
        self, mock_fetch: MagicMock, mock_config: MagicMock
    ) -> None:
        """
        Another approach to confirm the same user ID retains the same image
        within one API fetch, even if random has multiple calls.
        """
        mock_config.return_value = "http://fakeurl.com"
        payload = [
            {"userId": 1, "id": 1, "title": "Todo1", "completed": False},
            {"userId": 1, "id": 2, "title": "Todo2", "completed": True},
            {"userId": 1, "id": 3, "title": "Todo3", "completed": True},
        ]
        mock_fetch.return_value = payload

        get_external_todo_data()
        user1_todos = Todo.objects.filter(user_id=1)

        # All belong to the same user => must have the same 'image'.
        images = set(todo.image for todo in user1_todos)
        self.assertEqual(
            len(images), 1, "All todos for the same user should share the same image"
        )

    @patch("todos.helpers.todo_list_view_helper.config")
    def test_missing_todo_api_url(self, mock_config: MagicMock) -> None:
        """
        If the environment variable TODO_API_URL is missing or invalid, decouple.config
        might raise an exception or return an empty string. We can test behavior or
        how the code handles it. (Your code currently doesn't handle it explicitly,
        but let's show an example.)
        """
        # If config is missing, decouple.config might raise a KeyError or return None if you set a default
        mock_config.side_effect = KeyError("TODO_API_URL not found")

        with self.assertRaises(KeyError):
            get_external_todo_data()

        # No objects created
        self.assertEqual(Todo.objects.count(), 0)
