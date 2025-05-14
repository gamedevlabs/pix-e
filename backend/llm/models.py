from django.db import models


# Create your models here.

class Pillar(models.Model):
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='pillars')
    pillar_id = models.PositiveIntegerField()

    title = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'pillar_id']

    def save(self, *args, **kwargs):
        if self.pillar_id is None:
            last = Pillar.objects.filter(user=self.user).order_by('-pillar_id').first()
            self.pillar_id = (last.pillar_id + 1) if last else 0
        super().save(*args, **kwargs)

class GameDesignDescription(models.Model):
    game_id = models.IntegerField(primary_key=True, default=0) #just 0 for now
    description = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)