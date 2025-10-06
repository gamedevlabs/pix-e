from django.db import models

class AssetMetaData(models.Model):
    name = models.CharField(max_length=255)
    class_name = models.CharField(max_length=255)
    path = models.CharField(max_length=255)

    class Meta:
        verbose_name = "asset metadata"
        verbose_name_plural = "asset metadata"

    def __str__(self):
        return self.name