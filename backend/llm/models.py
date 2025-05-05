from django.db import models


# Create your models here.

# Entire keying system needs to rely on probably foreign keys from the user table

class Pillar(models.Model):
    pillar_id = models.IntegerField(primary_key=True, default=0)
    #user_id = models.CharField(max_length=255)
    description = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class GameDesignDescription(models.Model):
    user_id = models.CharField(max_length=255, primary_key=True)
    description = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)