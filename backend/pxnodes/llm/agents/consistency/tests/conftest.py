import pytest
from django.contrib.auth import get_user_model

from game_concept.models import Project

User = get_user_model()


@pytest.fixture
def user(db):
    return User.objects.create_user(username="structural_test_user", password="pass")


@pytest.fixture
def project_a(user):
    return Project.objects.create(user=user, name="Project A")


@pytest.fixture
def project_b(user):
    return Project.objects.create(user=user, name="Project B")
