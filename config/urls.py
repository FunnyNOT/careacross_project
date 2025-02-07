from django.urls import path

from todos import views

urlpatterns = [
    path("", views.TodoListView.as_view(), name="todo_list"),
]

# Register custom error handlers
handler404 = "todos.errors.custom_404"
handler500 = "todos.errors.custom_500"
