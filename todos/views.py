import logging
from typing import Any, Dict

from django.db.models import QuerySet
from django.views.generic import ListView

from todos.helpers import get_external_todo_data
from todos.models import Todo

logger = logging.getLogger(__name__)


class TodoListView(ListView):
    """
    A class-based ListView for displaying Todo items.

    This view performs the following tasks:
    1. Retrieves a list of Todo objects from the database.
    2. If no Todo objects exist in the database, it attempts to fetch
       data from an external API and store it.
    3. Allows filtering of Todo items based on the 'filter' GET parameter.
    4. Adds additional metadata to the context, such as the total number of todos,
       and counts of completed/uncompleted tasks.

    Additional Context Variables:
        - `total_todos`: Total number of Todo items.
        - `completed_todos`: Count of completed Todo items.
        - `uncompleted_todos`: Count of incomplete Todo items.
        - `current_filter`: The active filter applied to the todos list.

    URL Parameters:
        - `filter`: (optional) A query parameter used to filter todos.
          - `"all"`: Returns all todos (default behavior).
          - `"todo"`: Returns only uncompleted todos.
          - `"complete"`: Returns only completed todos.
          - Any other value defaults to `"all"`.
    """

    model = Todo
    template_name = "todos.html"
    context_object_name = "todos"
    paginate_by = 20
    ordering = ["api_id"]

    def get_queryset(self) -> QuerySet[Todo]:
        """
        Retrieve and filter Todo items from the database.

        If the database is empty:
        - Attempts to fetch and populate Todo items from an external API.
        - If an exception occurs during the external API call, it logs the error
          and proceeds without crashing.

        Filtering Logic:
        - If a valid `filter` query parameter is provided, filters the queryset accordingly.
        - If an invalid filter is provided, defaults to `"all"` (returns all todos).

        Returns:
            QuerySet[Todo]: A queryset containing Todo objects based on the applied filter.
        """
        qs = super().get_queryset()
        if not qs.exists():
            try:
                get_external_todo_data()
            except Exception as e:
                logger.exception(f"Error fetching external data: {e}")

        filter_param = self.request.GET.get("filter", "all")

        filters = {
            "todo": lambda q: q.filter(completed=False),
            "complete": lambda q: q.filter(completed=True),
            "all": lambda q: q,
        }

        if filter_param not in filters:
            filter_param = "all"

        qs = filters[filter_param](qs)

        return qs

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """
        Add additional metadata to the template context.

        This method provides extra context variables to the template, including:
        - `total_todos`: Total number of todos in the database.
        - `completed_todos`: Number of completed todos.
        - `uncompleted_todos`: Number of uncompleted todos.
        - `current_filter`: The filter parameter currently applied.

        If an invalid filter is detected, it defaults `current_filter` to `"all"`.

        Returns:
            Dict[str, Any]: The context dictionary containing the original and additional metadata.
        """
        context = super().get_context_data(**kwargs)

        all_todos = Todo.objects.all()
        context["total_todos"] = all_todos.count()
        context["completed_todos"] = all_todos.filter(completed=True).count()
        context["uncompleted_todos"] = all_todos.filter(completed=False).count()
        context["current_filter"] = self.request.GET.get("filter", "all")

        if context["current_filter"] not in {"todo", "complete", "all"}:
            context["current_filter"] = "all"
        return context
