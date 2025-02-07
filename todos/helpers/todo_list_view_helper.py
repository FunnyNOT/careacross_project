import logging
import random
from typing import Any, Dict, List, Optional

import requests
from decouple import config
from django.db.models import QuerySet
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

from todos.models import Todo

logger = logging.getLogger(__name__)


def fetch_todos_from_api(
    url: str,
    retries: int = 3,
    backoff_factor: float = 0.3,
    status_forcelist: Optional[List[int]] = None,
) -> List[Dict[str, Any]]:
    """
    Fetch todos from an external API using a session with a retry strategy.

    Args:
        url (str): The URL of the external API.
        retries (int, optional): Maximum number of retry attempts. Defaults to 3.
        backoff_factor (float, optional): A factor to calculate the delay between retries. Defaults to 0.3.
        status_forcelist (Optional[List[int]], optional): HTTP status codes that should trigger a retry.
            Defaults to [500, 502, 503, 504] if not provided.

    Returns:
        List[Dict[str, Any]]: A list of dictionaries representing todo items.

    Raises:
        requests.RequestException: If the request fails after all retry attempts.
    """
    if status_forcelist is None:
        status_forcelist = [500, 502, 503, 504]

    session = requests.Session()
    retry_strategy = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
        raise_on_status=True,
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    response = session.get(url, timeout=10)
    response.raise_for_status()
    return response.json()


logger = logging.getLogger(__name__)


def get_external_todo_data() -> Optional[QuerySet[Todo]]:
    """
    Fetches todo data from an external API, assigns a consistent random image
    per user, and stores the data in the database.

    Returns:
        Optional[QuerySet[Todo]]: A queryset containing the newly created Todo objects,
        or None if an error occurs.
    """
    url: str = config("TODO_API_URL", cast=str)

    try:
        data: List[dict] = fetch_todos_from_api(url)
        todos_to_create: List[Todo] = []
        user_image_mapping: dict[int, int] = {}

        for item in data:
            user_id: int = item.get("userId")
            if user_id not in user_image_mapping:
                user_image_mapping[user_id] = random.randint(1, 7)

            todos_to_create.append(
                Todo(
                    title=item.get("title"),
                    api_id=item.get("id"),
                    user_id=user_id,
                    image=user_image_mapping[user_id],
                    completed=item.get("completed", False),
                )
            )

        if todos_to_create:
            Todo.objects.bulk_create(todos_to_create)
            return Todo.objects.all()

    except Exception as e:
        logger.error(f"Error fetching todos from external API: {e}")

    return None
