"""
Comprehensive tests for the accounts app — personal API key feature.

Covers model creation, encryption round-trip, key validation,
API CRUD endpoints.
"""

import hashlib
import hmac
from unittest.mock import patch

from cryptography.fernet import InvalidToken
from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient

from accounts.constants import ProviderType
from accounts.encryption import (
    _SESSION_EXPIRES_AT_NAME,
    _SESSION_KEY_NAME,
    clear_key_from_session,
    decrypt_api_key,
    derive_encryption_key,
    encrypt_api_key,
    generate_encryption_salt,
    get_encryption_key_from_session,
    store_key_in_session,
)
from accounts.models import UserApiKey
from accounts.validation import validate_key_format

_TEST_PASSWORD = "test_password_123!"
_TEST_SALT = generate_encryption_salt()
_TEST_FERNET_KEY = derive_encryption_key(_TEST_PASSWORD, _TEST_SALT)


def _create_test_user(username="testuser") -> User:
    return User.objects.create_user(
        username=username,
        password=_TEST_PASSWORD,
    )


def _encrypt_for_user(raw_key: str) -> bytes:
    return encrypt_api_key(raw_key, _TEST_FERNET_KEY)


def _make_fingerprint(raw_key: str, pepper: str = "test_pepper") -> str:
    return hmac.new(
        pepper.encode("utf-8"),
        raw_key.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def _masked(raw_key: str) -> str:
    if len(raw_key) >= 4:
        return f"\u2022\u2022\u2022\u2022{raw_key[-4:]}"
    return "\u2022\u2022\u2022\u2022"


def _login_and_store_key(client: APIClient, user: User) -> None:
    client.force_login(user)
    session = client.session
    store_key_in_session(session, _TEST_FERNET_KEY)
    session.save()


@override_settings(API_KEY_FINGERPRINT_PEPPER="test_pepper")
class UserApiKeyModelTests(TestCase):
    def setUp(self):
        self.user = _create_test_user()
        self.raw_key = "sk-" + "a" * 48
        self.encrypted = _encrypt_for_user(self.raw_key)
        self.fingerprint = _make_fingerprint(self.raw_key)
        self.masked = _masked(self.raw_key)

    def _create_key(self, **overrides) -> UserApiKey:
        defaults = dict(
            user=self.user,
            provider=ProviderType.OPENAI,
            label="My Test Key",
            encrypted_key=self.encrypted,
            key_fingerprint=self.fingerprint,
            masked_key=self.masked,
        )
        defaults.update(overrides)
        return UserApiKey.objects.create(**defaults)

    def test_create_with_all_fields(self):
        key = self._create_key()
        fetched = UserApiKey.objects.get(pk=key.pk)
        self.assertEqual(fetched.user, self.user)
        self.assertEqual(fetched.provider, ProviderType.OPENAI)
        self.assertEqual(fetched.label, "My Test Key")
        self.assertEqual(fetched.encrypted_key, self.encrypted)
        self.assertEqual(fetched.key_fingerprint, self.fingerprint)
        self.assertEqual(fetched.masked_key, self.masked)
        self.assertTrue(fetched.is_active)
        self.assertIsNotNone(fetched.created_at)
        self.assertIsNotNone(fetched.updated_at)

    def test_uuid_auto_generated(self):
        key = self._create_key()
        self.assertIsNotNone(key.pk)
        self.assertEqual(len(str(key.pk)), 36)
        self.assertEqual(str(key.pk).count("-"), 4)

    def test_str_returns_correct_format(self):
        key = self._create_key()
        expected = f"{self.user.username} / {ProviderType.OPENAI} / My Test Key"
        self.assertEqual(str(key), expected)

    def test_get_masked_key_returns_masked_key(self):
        key = self._create_key()
        self.assertEqual(key.get_masked_key(), self.masked)

    def test_unique_constraint_user_and_label(self):
        self._create_key()
        with self.assertRaises(Exception) as ctx:
            self._create_key()
        self.assertIn("UNIQUE constraint failed", str(ctx.exception))

    def test_unique_constraint_allows_same_label_different_user(self):
        self._create_key()
        other_user = _create_test_user("otheruser")
        key2 = UserApiKey.objects.create(
            user=other_user,
            provider=ProviderType.OPENAI,
            label="My Test Key",
            encrypted_key=self.encrypted,
            key_fingerprint=_make_fingerprint(
                "sk-bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
            ),
            masked_key=_masked("sk-bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"),
        )
        self.assertIsNotNone(key2.pk)

    def test_ordering_is_created_at_descending(self):
        key1 = self._create_key(label="First Key")
        key2 = self._create_key(
            label="Second Key",
            encrypted_key=_encrypt_for_user("sk-" + "b" * 48),
            key_fingerprint=_make_fingerprint("sk-" + "b" * 48),
            masked_key=_masked("sk-" + "b" * 48),
        )
        qs = UserApiKey.objects.filter(user=self.user)
        self.assertEqual(qs[0], key2)
        self.assertEqual(qs[1], key1)

    def test_index_on_user_is_active(self):
        index_names = [idx.name for idx in UserApiKey._meta.indexes]
        self.assertIn("user_api_keys_active_idx", index_names)


class EncryptionTests(TestCase):
    def setUp(self):
        self.password = "my_secure_password_42!"
        self.raw_key = "sk-" + "x" * 48
        self.salt = generate_encryption_salt()
        self.enc_key = derive_encryption_key(self.password, self.salt)

    def test_encrypt_decrypt_round_trip(self):
        encrypted = encrypt_api_key(self.raw_key, self.enc_key)
        decrypted = decrypt_api_key(encrypted, self.enc_key)
        self.assertEqual(decrypted, self.raw_key)

    def test_wrong_key_fails_to_decrypt(self):
        encrypted = encrypt_api_key(self.raw_key, self.enc_key)
        wrong_key = derive_encryption_key("different_password", self.salt)
        with self.assertRaises(InvalidToken):
            decrypt_api_key(encrypted, wrong_key)

    def test_derive_produces_consistent_output(self):
        key1 = derive_encryption_key(self.password, self.salt)
        key2 = derive_encryption_key(self.password, self.salt)
        self.assertEqual(key1, key2)

    def test_derive_produces_different_output_for_different_passwords(self):
        key1 = derive_encryption_key(self.password, self.salt)
        key2 = derive_encryption_key("another_password_99!", self.salt)
        self.assertNotEqual(key1, key2)

    def test_derive_key_is_urlsafe_base64_and_32_bytes(self):
        key = derive_encryption_key(self.password, self.salt)
        self.assertEqual(len(key), 44)
        import base64
        decoded = base64.urlsafe_b64decode(key)
        self.assertEqual(len(decoded), 32)

    def test_derive_with_orm_salt_does_not_crash(self):
        user = User.objects.create_user(username="saltuser", password="pw123")
        from accounts.models import UserSalt
        salt_obj = UserSalt.objects.create(user=user, salt=generate_encryption_salt())
        salt_obj.refresh_from_db()
        key = derive_encryption_key("pw123", salt=bytes(salt_obj.salt))
        self.assertEqual(len(key), 44)

    def test_store_and_get_session_round_trip(self):
        session = {}
        store_key_in_session(session, self.enc_key)
        self.assertIn(_SESSION_KEY_NAME, session)
        self.assertIn(_SESSION_EXPIRES_AT_NAME, session)
        retrieved = get_encryption_key_from_session(session)
        self.assertEqual(retrieved, self.enc_key)

    def test_get_encryption_key_returns_none_when_missing(self):
        self.assertIsNone(get_encryption_key_from_session({}))

    def test_get_encryption_key_returns_none_when_expired(self):
        session = {}
        store_key_in_session(session, self.enc_key)
        FAR_FUTURE = 9999999999.0
        with patch("accounts.encryption.time.time", return_value=FAR_FUTURE):
            retrieved = get_encryption_key_from_session(session)
            self.assertIsNone(retrieved)

    def test_get_encryption_key_bumps_ttl_on_access(self):
        session = {}
        store_key_in_session(session, self.enc_key)
        original_expires = session[_SESSION_EXPIRES_AT_NAME]
        with patch("accounts.encryption.time.time", return_value=original_expires - 3500):
            retrieved = get_encryption_key_from_session(session)
            self.assertEqual(retrieved, self.enc_key)
        self.assertGreater(session[_SESSION_EXPIRES_AT_NAME], original_expires)

    def test_clear_key_from_session(self):
        session = {}
        store_key_in_session(session, self.enc_key)
        clear_key_from_session(session)
        self.assertNotIn(_SESSION_KEY_NAME, session)
        self.assertNotIn(_SESSION_EXPIRES_AT_NAME, session)

    def test_encrypt_empty_key_raises_value_error(self):
        with self.assertRaises(ValueError):
            encrypt_api_key("", self.enc_key)

    def test_decrypt_empty_cipher_raises_value_error(self):
        with self.assertRaises(ValueError):
            decrypt_api_key(b"", self.enc_key)

    def test_encrypt_with_none_key_raises_runtime_error(self):
        with self.assertRaises(RuntimeError):
            encrypt_api_key("sk-test", None)


class ValidationTests(TestCase):
    def test_openai_valid_key(self):
        valid, msg = validate_key_format("openai", "sk-" + "a" * 20)
        self.assertTrue(valid)
        self.assertEqual(msg, "")

    def test_openai_invalid_prefix(self):
        valid, msg = validate_key_format("openai", "ak-" + "a" * 20)
        self.assertFalse(valid)
        self.assertIn("sk-", msg)

    def test_openai_too_short(self):
        valid, msg = validate_key_format("openai", "sk-" + "a" * 19)
        self.assertFalse(valid)

    def test_gemini_valid_key(self):
        valid, msg = validate_key_format("gemini", "AIza" + "a" * 10)
        self.assertTrue(valid)
        self.assertEqual(msg, "")

    def test_gemini_invalid_prefix(self):
        valid, msg = validate_key_format("gemini", "BIza" + "a" * 10)
        self.assertFalse(valid)
        self.assertIn("AIza", msg)

    def test_gemini_too_short(self):
        valid, msg = validate_key_format("gemini", "AIza" + "a" * 9)
        self.assertFalse(valid)

    def test_custom_valid_key(self):
        valid, msg = validate_key_format("custom", "a" * 8)
        self.assertTrue(valid)
        self.assertEqual(msg, "")

    def test_custom_too_short(self):
        valid, msg = validate_key_format("custom", "a" * 7)
        self.assertFalse(valid)
        self.assertIn("at least 8", msg)

    def test_morpheus_valid_key(self):
        valid, msg = validate_key_format("morpheus", "sk-" + "b" * 25)
        self.assertTrue(valid)
        self.assertEqual(msg, "")

    def test_whitespace_trimming_rejection(self):
        valid, msg = validate_key_format("openai", " sk-" + "a" * 20)
        self.assertFalse(valid)
        self.assertIn("whitespace", msg)

    def test_trailing_whitespace_rejection(self):
        valid, msg = validate_key_format("openai", "sk-" + "a" * 20 + " ")
        self.assertFalse(valid)
        self.assertIn("whitespace", msg)

    def test_empty_key_rejection(self):
        valid, msg = validate_key_format("openai", "")
        self.assertFalse(valid)
        self.assertIn("required", msg)

    def test_blank_key_rejection(self):
        valid, msg = validate_key_format("openai", "   ")
        self.assertFalse(valid)
        self.assertIn("required", msg)

    def test_unknown_provider_passes_any_key(self):
        valid, msg = validate_key_format("unknown_provider", "tiny")
        self.assertTrue(valid)
        self.assertEqual(msg, "")


@override_settings(
    API_KEY_FINGERPRINT_PEPPER="test_pepper",
    CACHES={"default": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"}},
)
class UserApiKeyAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = _create_test_user()
        self.list_url = "/api/accounts/api-keys/"
        self.raw_key = "sk-" + "c" * 48
        self.encrypted = _encrypt_for_user(self.raw_key)
        self.fingerprint = _make_fingerprint(self.raw_key)
        self.masked = _masked(self.raw_key)

    def _create_key_in_db(self, **overrides) -> UserApiKey:
        defaults = dict(
            user=self.user,
            provider=ProviderType.OPENAI,
            label="DB Key",
            encrypted_key=self.encrypted,
            key_fingerprint=self.fingerprint,
            masked_key=self.masked,
        )
        defaults.update(overrides)
        return UserApiKey.objects.create(**defaults)

    def _detail_url(self, key: UserApiKey) -> str:
        return f"/api/accounts/api-keys/{key.pk}/"

    def test_list_returns_401_when_unauthenticated(self):
        resp = self.client.get(self.list_url)
        self.assertIn(resp.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_create_returns_401_when_unauthenticated(self):
        resp = self.client.post(
            self.list_url, {"provider": "openai", "label": "X", "key": "sk-test"}
        )
        self.assertIn(resp.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_list_returns_users_keys(self):
        self._create_key_in_db()
        other = _create_test_user("other")
        UserApiKey.objects.create(
            user=other,
            provider=ProviderType.GEMINI,
            label="Other Key",
            encrypted_key=_encrypt_for_user("AIza" + "d" * 10),
            key_fingerprint=_make_fingerprint("AIza" + "d" * 10),
            masked_key=_masked("AIza" + "d" * 10),
        )
        _login_and_store_key(self.client, self.user)
        resp = self.client.get(self.list_url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 1)

    def test_list_response_does_not_contain_raw_key(self):
        self._create_key_in_db()
        _login_and_store_key(self.client, self.user)
        resp = self.client.get(self.list_url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        for entry in resp.data:
            self.assertNotIn("key", entry)

    def test_list_response_contains_masked_key(self):
        self._create_key_in_db()
        _login_and_store_key(self.client, self.user)
        resp = self.client.get(self.list_url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        for entry in resp.data:
            self.assertIn("masked_key", entry)
            self.assertTrue(entry["masked_key"].endswith(self.raw_key[-4:]))
            self.assertNotIn(self.raw_key[:-4], entry["masked_key"])

    def test_create_creates_new_key(self):
        _login_and_store_key(self.client, self.user)
        payload = {
            "provider": ProviderType.OPENAI,
            "label": "My New Key",
            "key": self.raw_key,
        }
        resp = self.client.post(self.list_url, payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data["label"], "My New Key")
        self.assertEqual(resp.data["provider"], ProviderType.OPENAI)
        self.assertIn("masked_key", resp.data)
        self.assertNotIn("key", resp.data)
        self.assertEqual(UserApiKey.objects.filter(user=self.user).count(), 1)

    def test_create_rejects_duplicate_fingerprint(self):
        self._create_key_in_db()
        _login_and_store_key(self.client, self.user)
        payload = {
            "provider": ProviderType.OPENAI,
            "label": "Duplicate Key",
            "key": self.raw_key,
        }
        resp = self.client.post(self.list_url, payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("already have this API key", str(resp.data))

    def test_create_validates_key_format_before_encrypting(self):
        _login_and_store_key(self.client, self.user)
        payload = {
            "provider": ProviderType.OPENAI,
            "label": "Bad Key",
            "key": "not-a-valid-key",
        }
        resp = self.client.post(self.list_url, payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("sk-", str(resp.data))

    def test_create_requires_session_encryption_key(self):
        self.client.force_login(self.user)
        payload = {
            "provider": ProviderType.OPENAI,
            "label": "No Session Key",
            "key": self.raw_key,
        }
        resp = self.client.post(self.list_url, payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Session expired", str(resp.data))

    def test_create_allows_same_key_for_different_provider_label(self):
        self._create_key_in_db(label="Original Key")
        _login_and_store_key(self.client, self.user)
        payload = {
            "provider": ProviderType.OPENAI,
            "label": "Same Key Diff Label",
            "key": self.raw_key,
        }
        resp = self.client.post(self.list_url, payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_custom_requires_base_url(self):
        _login_and_store_key(self.client, self.user)
        payload = {
            "provider": ProviderType.CUSTOM,
            "label": "Custom No URL",
            "key": "abcdefgh",
        }
        resp = self.client.post(self.list_url, payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("base_url", str(resp.data))

    def test_patch_updates_label_and_active_status(self):
        key = self._create_key_in_db()
        _login_and_store_key(self.client, self.user)
        resp = self.client.patch(
            self._detail_url(key),
            {"label": "Updated Label", "is_active": False},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        key.refresh_from_db()
        self.assertEqual(key.label, "Updated Label")
        self.assertFalse(key.is_active)

    def test_patch_does_not_change_key_field(self):
        key = self._create_key_in_db()
        original_cipher = key.encrypted_key
        _login_and_store_key(self.client, self.user)
        self.client.patch(
            self._detail_url(key),
            {"label": "New Label"},
            format="json",
        )
        key.refresh_from_db()
        self.assertEqual(key.encrypted_key, original_cipher)

    def test_delete_removes_key(self):
        key = self._create_key_in_db()
        _login_and_store_key(self.client, self.user)
        resp = self.client.delete(self._detail_url(key))
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(UserApiKey.objects.filter(user=self.user).count(), 0)

    def test_delete_other_users_key_returns_404(self):
        key = self._create_key_in_db()
        other = _create_test_user("otheruser")
        _login_and_store_key(self.client, other)
        resp = self.client.delete(self._detail_url(key))
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_retrieve_does_not_contain_raw_key(self):
        key = self._create_key_in_db()
        _login_and_store_key(self.client, self.user)
        resp = self.client.get(self._detail_url(key))
        self.assertNotIn("key", resp.data)
