import uuid

from django.db import models


class MovieProject(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(
        "auth.User", on_delete=models.CASCADE, related_name="assets_metadata"
    )

    name = models.CharField(max_length=255)
    description = models.CharField(max_length=511)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "movie project"
        verbose_name_plural = "movie projects"

        def __str__(self):
            return self.verbose_name


def upload_to_scripts(instance, filename):
    return f"moviescriptevaluator/files/{filename}"


class MovieScript(models.Model):
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to=upload_to_scripts)
    project = models.ForeignKey(
        MovieProject, on_delete=models.CASCADE, related_name="scripts"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class AssetMetaData(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        MovieProject, on_delete=models.CASCADE, related_name="assets_metadata"
    )
    name = models.CharField(max_length=255)
    class_name = models.CharField(max_length=255)
    path = models.CharField(max_length=255)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "asset metadata"
        verbose_name_plural = "asset metadata"

    def __str__(self):
        return "Name: {name}, Class Name: {class_name}, Path: {path}".format(
            name=self.name, class_name=self.class_name, path=self.path
        )


class RequiredAssets(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    asset = models.ForeignKey(
        AssetMetaData,
        on_delete=models.CASCADE,
        related_name="required_assets",
        null=True,
        blank=True,
    )
    project = models.ForeignKey(
        MovieProject, on_delete=models.CASCADE, related_name="required_assets"
    )
    name = models.CharField(max_length=255)
    purpose = models.CharField(max_length=255)
    description = models.CharField(max_length=255)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class ScriptSceneAnalysisResult(models.Model):
    project = models.ForeignKey(
        MovieProject, on_delete=models.CASCADE, related_name="results"
    )

    scene = models.CharField(max_length=255)
    asset_name = models.CharField(max_length=255)
    asset_type = models.CharField(max_length=255)
    fab_search_keyword = models.CharField(max_length=255)
    notes = models.CharField(max_length=1024)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "Scene: {scene}, Asset Name: {asset_name}, Type: {asset_type}, Key Words: {fab_search_keyword}, Notes: {notes}".format(
                scene=self.scene, asset_name=self.asset_name, asset_type=self.asset_type, fab_search_keyword=self.fab_search_keyword, notes=self.notes
        )
