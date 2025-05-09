from django.db import models


# Create your models here.

# Entire keying system needs to rely on probably foreign keys from the user table

class Pillar(models.Model):
    pillar_id = models.BigAutoField(primary_key=True)
    #user_id = models.CharField(max_length=255)
    title = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class GameDesignDescription(models.Model):
    game_id = models.IntegerField(primary_key=True, default=0) #just 0 for now
    description = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)