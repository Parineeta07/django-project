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
    status = models.CharField(max_length=50, null=True, blank=True)  # Add the field
    
    # 👇 The fix: add related_name="tasks"
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="tasks")

    is_completed = models.BooleanField(default=False)

    def __str__(self):
        return self.name

class MoodEntry(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    mood = models.CharField(max_length=50)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.mood} ({self.timestamp.strftime('%Y-%m-%d %H:%M')})"
