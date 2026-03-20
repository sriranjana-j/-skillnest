from django.db import models
from django.contrib.auth.models import User


class Progress(models.Model):
	user = models.ForeignKey(User, on_delete=models.CASCADE)
	domain = models.CharField(max_length=50)
	score = models.IntegerField()
	total = models.IntegerField()
	date = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ["-date"]


class InterviewScore(models.Model):
	user = models.ForeignKey(User, on_delete=models.CASCADE)
	score = models.IntegerField()
	date = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ["-date"]
