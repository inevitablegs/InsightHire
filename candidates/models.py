# candidates/models.py
from django.db import models
from django.contrib.auth.models import User

class CandidateProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    resume = models.FileField(upload_to='resumes/', blank=True, null=True)
    meeting_link = models.URLField(blank=True, null=True)  # New field for meeting link

    def __str__(self):
        return self.user.username