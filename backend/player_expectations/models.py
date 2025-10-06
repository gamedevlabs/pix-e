# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete`
#   + set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify,
#   * and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class PlayerExpectationsAbsa(models.Model):
    unnamed_0 = models.IntegerField(
        db_column="Unnamed: 0", blank=True, null=True
    )  # Field name made lowercase. Field renamed to remove unsuitable characters.
    appid = models.IntegerField(blank=True, null=True)
    name = models.TextField(blank=True, null=True)
    release_date = models.TextField(blank=True, null=True)
    required_age = models.IntegerField(blank=True, null=True)
    price = models.TextField(blank=True, null=True)  # This field type is a guess.
    dlc_count = models.IntegerField(blank=True, null=True)
    categories = models.TextField(blank=True, null=True)
    genres = models.TextField(blank=True, null=True)
    user_score = models.IntegerField(blank=True, null=True)
    positive = models.IntegerField(blank=True, null=True)
    negative = models.IntegerField(blank=True, null=True)
    tags = models.TextField(blank=True, null=True)
    review_text = models.TextField(blank=True, null=True)
    explicit_expectations = models.TextField(blank=True, null=True)
    has_explicit = models.TextField(blank=True, null=True)
    expectations = models.TextField(blank=True, null=True)
    absa_expectations = models.TextField(
        db_column="ABSA_expectations", blank=True, null=True
    )  # Field name made lowercase.
    dominant_aspect = models.TextField(blank=True, null=True)
    dominant_sentiment = models.TextField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = "player_expectations_absa"


class PlayerExpectationsConfusions(models.Model):
    index = models.IntegerField(blank=True, null=True)
    sentence = models.TextField(blank=True, null=True)
    model_aspect = models.TextField(blank=True, null=True)
    gpt_aspect = models.TextField(blank=True, null=True)
    agreement = models.TextField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = "player_expectations_confusions"
