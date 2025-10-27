from django.db import models

class AssetMetaData(models.Model):
    #owner = models.ForeignKey("auth.User", on_delete=models.CASCADE, related_name="assets_metadata")
    #project_name = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    class_name = models.CharField(max_length=255)
    path = models.CharField(max_length=255)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "asset metadata"
        verbose_name_plural = "asset metadata"

    def __str__(self):
        return self.name