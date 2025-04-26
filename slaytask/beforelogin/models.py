from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

class Task(models.Model):
    name = models.CharField(max_length=100, default="Unnamed Task")
    age = models.IntegerField(default=18)
    description = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    due_date = models.DateTimeField(default=timezone.now)
    
    # 👇 The fix: add related_name="tasks"
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="tasks")

    is_completed = models.BooleanField(default=False)

    def __str__(self):
        return self.name
