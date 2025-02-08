from django.urls import path

from todos import views

urlpatterns = [
    path("", views.TodoListView.as_view(), name="todo_list"),
    path("toggle-todo/", views.toggle_todo_completion, name="toggle_todo"),
]

# Register custom error handlers
handler404 = "todos.errors.custom_404"
handler500 = "todos.errors.custom_500"
