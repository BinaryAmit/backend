from django.db import models

class Room(models.Model):
    code = models.CharField(max_length=32, unique=True)
    title = models.CharField(max_length=128, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.code
