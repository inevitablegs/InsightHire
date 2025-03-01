from django.db import models
from django.contrib.auth.models import User

class InterviewerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    zoom_account_id = models.CharField(max_length=255, blank=True, null=True)
    zoom_client_id = models.CharField(max_length=255, blank=True, null=True)
    zoom_client_secret = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.user.username