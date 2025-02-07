import uuid

from django.db import models


class Todo(models.Model):
    uuid = models.UUIDField(
        default=uuid.uuid4, editable=False, unique=True, primary_key=True
    )
    api_id = models.IntegerField(unique=True)
    user_id = models.IntegerField()
    title = models.CharField(max_length=200)
    image = models.TextField()
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} (ID: {self.api_id}) - (USER: {self.user_id})"
