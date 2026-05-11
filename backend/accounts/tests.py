"""
Comprehensive tests for the accounts app — personal API key feature.

Covers model creation, encryption round-trip, key validation,
API CRUD endpoints, test endpoint, LLM integration, and throttling.
"""

import hashlib
import hmac
import time
from unittest.mock import MagicMock, patch

from cryptography.fernet import InvalidToken
from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.exceptions import NotAuthenticated
from rest_framework.test import APIClient, APIRequestFactory

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

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_TEST_PASSWORD = "test_password_123!"
_TEST_SALT = generate_encryption_salt()
_TEST_FERNET_KEY = derive_encryption_key(_TEST_PASSWORD, _TEST_SALT)


def _create_test_user(username="testuser") -> User:
    """Create and return a test user."""
    return User.objects.create_user(
        username=username,
        password=_TEST_PASSWORD,
    )


def _encrypt_for_user(raw_key: str) -> bytes:
    """Encrypt a key with the standard test Fernet key."""
    return encrypt_api_key(raw_key, _TEST_FERNET_KEY)


def _make_fingerprint(raw_key: str, pepper: str = "test_pepper") -> str:
    """Compute the HMAC fingerprint as the serializer does."""
    return hmac.new(
        pepper.encode("utf-8"),
        raw_key.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def _masked(raw_key: str) -> str:
    """Compute the masked representation as the serializer does."""
    if len(raw_key) >= 4:
        return f"\u2022\u2022\u2022\u2022{raw_key[-4:]}"
    return "\u2022\u2022\u2022\u2022"


def _login_and_store_key(client: APIClient, user: User) -> None:
    """
    Authenticate the client as *user* and store a valid
    encryption key in the session.
    """
    client.force_login(user)
    session = client.session
    store_key_in_session(session, _TEST_FERNET_KEY)
    session.save()


# ============================================================================
# Model Tests
# ============================================================================


@override_settings(API_KEY_FINGERPRINT_PEPPER="test_pepper")
class UserApiKeyModelTests(TestCase):
    """Tests for the UserApiKey model — creation, string repr, constraints, indexes."""

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

    # --- creation -----------------------------------------------------------

    def test_create_with_all_fields(self):
        """Verify a fully populated UserApiKey can be created and read back."""
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
        """Verify a UUID primary key is auto-generated on creation."""
        key = self._create_key()
        self.assertIsNotNone(key.pk)
        # UUIDs are strings of length 36 (with dashes) or 32 (hex-only);
        # the model uses uuid.uuid4 which returns a UUID object stored as
        # a native UUID in the DB; check it's a valid-ish UUID.
        self.assertEqual(len(str(key.pk)), 36)
        self.assertEqual(str(key.pk).count("-"), 4)

    def test_str_returns_correct_format(self):
        """Verify __str__ returns 'username / provider / label'."""
        key = self._create_key()
        expected = f"{self.user.username} / {ProviderType.OPENAI} / My Test Key"
        self.assertEqual(str(key), expected)

    def test_get_masked_key_returns_masked_key(self):
        """Verify get_masked_key() returns the pre-computed masked_key field."""
        key = self._create_key()
        self.assertEqual(key.get_masked_key(), self.masked)

    # --- constraints & indexes ---------------------------------------------

    def test_unique_constraint_user_and_label(self):
        """Verify a duplicate (user, label) pair is rejected."""
        self._create_key()
        with self.assertRaises(Exception) as ctx:
            self._create_key()
        self.assertIn("UNIQUE constraint failed", str(ctx.exception))

    def test_unique_constraint_allows_same_label_different_user(self):
        """Verify different users CAN have the same label."""
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
        """Verify the default ordering is by -created_at (newest first)."""
        key1 = self._create_key(label="First Key")
        key2 = self._create_key(
            label="Second Key",
            encrypted_key=_encrypt_for_user("sk-" + "b" * 48),
            key_fingerprint=_make_fingerprint("sk-" + "b" * 48),
            masked_key=_masked("sk-" + "b" * 48),
        )
        qs = UserApiKey.objects.filter(user=self.user)
        self.assertEqual(qs[0], key2)  # newest first
        self.assertEqual(qs[1], key1)

    def test_index_on_user_is_active(self):
        """Verify the (user, is_active) index is declared on the model."""
        index_names = [idx.name for idx in UserApiKey._meta.indexes]
        self.assertIn("user_api_keys_active_idx", index_names)


# ============================================================================
# Encryption Tests
# ============================================================================


class EncryptionTests(TestCase):
    """Tests for encryption.py — derive, encrypt, decrypt, session helpers."""

    def setUp(self):
        self.password = "my_secure_password_42!"
        self.raw_key = "sk-" + "x" * 48
        self.salt = generate_encryption_salt()
        self.enc_key = derive_encryption_key(self.password, self.salt)

    # --- round-trip ---------------------------------------------------------

    def test_encrypt_decrypt_round_trip(self):
        """Verify encrypt_api_key → decrypt_api_key returns the original."""
        encrypted = encrypt_api_key(self.raw_key, self.enc_key)
        decrypted = decrypt_api_key(encrypted, self.enc_key)
        self.assertEqual(decrypted, self.raw_key)

    def test_wrong_key_fails_to_decrypt(self):
        """Verify decryption with a different key raises InvalidToken."""
        encrypted = encrypt_api_key(self.raw_key, self.enc_key)
        wrong_key = derive_encryption_key("different_password", self.salt)
        with self.assertRaises(InvalidToken):
            decrypt_api_key(encrypted, wrong_key)

    # --- derive_encryption_key ---------------------------------------------

    def test_derive_produces_consistent_output(self):
        """Verify the same password + salt always yields the same Fernet key."""
        key1 = derive_encryption_key(self.password, self.salt)
        key2 = derive_encryption_key(self.password, self.salt)
        self.assertEqual(key1, key2)

    def test_derive_produces_different_output_for_different_passwords(self):
        """Verify different passwords yield different keys."""
        key1 = derive_encryption_key(self.password, self.salt)
        key2 = derive_encryption_key("another_password_99!", self.salt)
        self.assertNotEqual(key1, key2)

    def test_derive_key_is_urlsafe_base64_and_32_bytes(self):
        """Verify the derived key is a 32-byte urlsafe-base64 encoded value."""
        key = derive_encryption_key(self.password, self.salt)
        # Fernet keys are 32 raw bytes, base64-encoded → 44 chars with padding
        self.assertEqual(len(key), 44)
        # Should be valid base64
        import base64

        decoded = base64.urlsafe_b64decode(key)
        self.assertEqual(len(decoded), 32)

    def test_derive_with_orm_salt_does_not_crash(self):
        """
        Verify that reading salt via the ORM (which returns ``memoryview``,
        not ``bytes``) works with ``derive_encryption_key``.

        Django's ``BinaryField`` returns a ``memoryview`` on read.  Callers
        must use ``bytes(user_salt.salt)``, not ``user_salt.salt`` directly.
        """
        user = User.objects.create_user(username="saltuser", password="pw123")
        from accounts.models import UserSalt

        salt_obj = UserSalt.objects.create(user=user, salt=generate_encryption_salt())
        # Refresh from DB to force ORM deserialisation → memoryview
        salt_obj.refresh_from_db()
        key = derive_encryption_key("pw123", salt=bytes(salt_obj.salt))
        self.assertEqual(len(key), 44)

    # --- session helpers ----------------------------------------------------

    def test_store_and_get_session_round_trip(self):
        """Verify store → get encryption key from session returns the key."""
        session = {}
        store_key_in_session(session, self.enc_key)
        self.assertIn(_SESSION_KEY_NAME, session)
        self.assertIn(_SESSION_EXPIRES_AT_NAME, session)

        retrieved = get_encryption_key_from_session(session)
        self.assertEqual(retrieved, self.enc_key)

    def test_get_encryption_key_returns_none_when_missing(self):
        """Verify get_encryption_key_from_session returns None when no key stored."""
        self.assertIsNone(get_encryption_key_from_session({}))

    def test_get_encryption_key_returns_none_when_expired(self):
        """Verify get_encryption_key_from_session returns None after TTL expiry."""
        session = {}
        store_key_in_session(session, self.enc_key)
        # Use a fixed timestamp well past TTL as the mock return value.
        # NOTE: patch("accounts.encryption.time.time") patches the *global*
        # time.time (since accounts.encryption.time and tests.time are the
        # same module object), so time.time() inside this `with` block is
        # also mocked and returns the MagicMock itself, not its return_value
        # at assignment time.  Use an absolute far-future value instead.
        FAR_FUTURE = 9999999999.0
        with patch("accounts.encryption.time.time", return_value=FAR_FUTURE):
            retrieved = get_encryption_key_from_session(session)
            self.assertIsNone(retrieved)

    def test_get_encryption_key_bumps_ttl_on_access(self):
        """Verify TTL is bumped forward when sufficient time has elapsed."""
        session = {}
        store_key_in_session(session, self.enc_key)
        original_expires = session[_SESSION_EXPIRES_AT_NAME]

        # Advance time by 11s so TTL extension threshold is crossed
        with patch("accounts.encryption.time.time", return_value=time.time() + 11):
            retrieved = get_encryption_key_from_session(session)
            self.assertEqual(retrieved, self.enc_key)
        # Verify the TTL was extended
        self.assertGreater(session[_SESSION_EXPIRES_AT_NAME], original_expires)

    def test_clear_key_from_session(self):
        """Verify clear_key_from_session removes both session entries."""
        session = {}
        store_key_in_session(session, self.enc_key)
        clear_key_from_session(session)
        self.assertNotIn(_SESSION_KEY_NAME, session)
        self.assertNotIn(_SESSION_EXPIRES_AT_NAME, session)

    # --- edge cases ---------------------------------------------------------

    def test_encrypt_empty_key_raises_value_error(self):
        """Verify encrypting an empty key raises ValueError."""
        with self.assertRaises(ValueError):
            encrypt_api_key("", self.enc_key)

    def test_decrypt_empty_cipher_raises_value_error(self):
        """Verify decrypting empty bytes raises ValueError."""
        with self.assertRaises(ValueError):
            decrypt_api_key(b"", self.enc_key)

    def test_encrypt_with_none_key_raises_runtime_error(self):
        """Verify encrypting with a None encryption key raises RuntimeError."""
        with self.assertRaises(RuntimeError):
            encrypt_api_key("sk-test", None)  # type: ignore[arg-type]


# ============================================================================
# Validation Tests
# ============================================================================


class ValidationTests(TestCase):
    """Tests for validation.py — provider-specific key format validation."""

    # --- OpenAI -------------------------------------------------------------

    def test_openai_valid_key(self):
        """Verify a well-formed OpenAI key passes validation."""
        valid, msg = validate_key_format("openai", "sk-" + "a" * 20)
        self.assertTrue(valid)
        self.assertEqual(msg, "")

    def test_openai_invalid_prefix(self):
        """Verify an OpenAI key without sk- prefix fails."""
        valid, msg = validate_key_format("openai", "ak-" + "a" * 20)
        self.assertFalse(valid)
        self.assertIn("sk-", msg)

    def test_openai_too_short(self):
        """Verify an OpenAI key shorter than 20 chars after sk- fails."""
        valid, msg = validate_key_format("openai", "sk-" + "a" * 19)
        self.assertFalse(valid)

    # --- Gemini -------------------------------------------------------------

    def test_gemini_valid_key(self):
        """Verify a well-formed Gemini key passes validation."""
        valid, msg = validate_key_format("gemini", "AIza" + "a" * 10)
        self.assertTrue(valid)
        self.assertEqual(msg, "")

    def test_gemini_invalid_prefix(self):
        """Verify a Gemini key without AIza prefix fails."""
        valid, msg = validate_key_format("gemini", "BIza" + "a" * 10)
        self.assertFalse(valid)
        self.assertIn("AIza", msg)

    def test_gemini_too_short(self):
        """Verify a Gemini key shorter than 10 chars after prefix fails."""
        valid, msg = validate_key_format("gemini", "AIza" + "a" * 9)
        self.assertFalse(valid)

    # --- Custom -------------------------------------------------------------

    def test_custom_valid_key(self):
        """Verify a custom key of ≥8 characters passes."""
        valid, msg = validate_key_format("custom", "a" * 8)
        self.assertTrue(valid)
        self.assertEqual(msg, "")

    def test_custom_too_short(self):
        """Verify a custom key shorter than 8 chars fails."""
        valid, msg = validate_key_format("custom", "a" * 7)
        self.assertFalse(valid)
        self.assertIn("at least 8", msg)

    # --- Morpheus (uses OpenAI pattern) -------------------------------------

    def test_morpheus_valid_key(self):
        """Verify a well-formed Morpheus key (OpenAI pattern) passes."""
        valid, msg = validate_key_format("morpheus", "sk-" + "b" * 25)
        self.assertTrue(valid)
        self.assertEqual(msg, "")

    # --- Whitespace ---------------------------------------------------------

    def test_whitespace_trimming_rejection(self):
        """Verify a key with leading whitespace fails."""
        valid, msg = validate_key_format("openai", " sk-" + "a" * 20)
        self.assertFalse(valid)
        self.assertIn("whitespace", msg)

    def test_trailing_whitespace_rejection(self):
        """Verify a key with trailing whitespace fails."""
        valid, msg = validate_key_format("openai", "sk-" + "a" * 20 + " ")
        self.assertFalse(valid)
        self.assertIn("whitespace", msg)

    # --- Empty --------------------------------------------------------------

    def test_empty_key_rejection(self):
        """Verify an empty key fails."""
        valid, msg = validate_key_format("openai", "")
        self.assertFalse(valid)
        self.assertIn("required", msg)

    def test_blank_key_rejection(self):
        """Verify a whitespace-only key fails."""
        valid, msg = validate_key_format("openai", "   ")
        self.assertFalse(valid)
        self.assertIn("required", msg)

    # --- Unknown provider ---------------------------------------------------

    def test_unknown_provider_passes_any_key(self):
        """Verify an unrecognised provider passes through without format checks."""
        valid, msg = validate_key_format("unknown_provider", "tiny")
        self.assertTrue(valid)
        self.assertEqual(msg, "")


# ============================================================================
# API Tests
# ============================================================================


@override_settings(
    API_KEY_FINGERPRINT_PEPPER="test_pepper",
    CACHES={"default": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"}},
)
class UserApiKeyAPITests(TestCase):
    """Tests for the ApiKeyViewSet CRUD and test endpoint."""

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

    def _test_url(self, key: UserApiKey) -> str:
        return f"/api/accounts/api-keys/{key.pk}/test/"

    # --- Authentication gate -----------------------------------------------

    def test_list_returns_401_when_unauthenticated(self):
        """Verify GET returns 401 for an anonymous user."""
        resp = self.client.get(self.list_url)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_returns_401_when_unauthenticated(self):
        """Verify POST returns 401 for an anonymous user."""
        resp = self.client.post(
            self.list_url, {"provider": "openai", "label": "X", "key": "sk-test"}
        )
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    # --- List ---------------------------------------------------------------

    def test_list_returns_users_keys(self):
        """Verify GET returns only the authenticated user's keys."""
        self._create_key_in_db()
        # Another user's key should NOT appear
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
        # DRF viewset returns a list (not wrapped in a key)
        self.assertEqual(len(resp.data), 1)

    def test_list_response_does_not_contain_raw_key(self):
        """Verify the list response never exposes the raw 'key' field."""
        self._create_key_in_db()
        _login_and_store_key(self.client, self.user)
        resp = self.client.get(self.list_url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        for entry in resp.data:
            self.assertNotIn("key", entry)

    def test_list_response_contains_masked_key(self):
        """Verify the response includes a masked_key field showing only last 4 chars."""
        self._create_key_in_db()
        _login_and_store_key(self.client, self.user)
        resp = self.client.get(self.list_url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        for entry in resp.data:
            self.assertIn("masked_key", entry)
            self.assertTrue(entry["masked_key"].endswith(self.raw_key[-4:]))
            self.assertNotIn(self.raw_key[:-4], entry["masked_key"])

    # --- Create -------------------------------------------------------------

    def test_create_creates_new_key(self):
        """Verify POST creates a new API key and returns it."""
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
        # Verify it was actually saved
        self.assertEqual(UserApiKey.objects.filter(user=self.user).count(), 1)

    def test_create_rejects_duplicate_fingerprint(self):
        """Verify creating a key with same raw key (same fingerprint) is rejected."""
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
        """Verify POST rejects a badly-formatted key before encryption."""
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
        """Verify POST returns 400 when session has no encryption key."""
        self.client.force_login(self.user)  # logged in but no enc key
        payload = {
            "provider": ProviderType.OPENAI,
            "label": "No Session Key",
            "key": self.raw_key,
        }
        resp = self.client.post(self.list_url, payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Session expired", str(resp.data))

    def test_create_allows_same_key_for_different_provider_label(self):
        """Verify that the same raw key value with a different label is allowed
        (duplicate detection is by fingerprint, which is the same, so this should
        actually still be rejected). This tests the fingerprint-based dedup."""
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
        """Verify POST for 'custom' provider requires base_url."""
        _login_and_store_key(self.client, self.user)
        payload = {
            "provider": ProviderType.CUSTOM,
            "label": "Custom No URL",
            "key": "abcdefgh",
        }
        resp = self.client.post(self.list_url, payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("base_url", str(resp.data))

    # --- Update (PATCH) -----------------------------------------------------

    def test_patch_updates_label_and_active_status(self):
        """Verify PATCH can update label and is_active."""
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
        """Verify updating other fields does not affect the encrypted key."""
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

    # --- Delete -------------------------------------------------------------

    def test_delete_removes_key(self):
        """Verify DELETE permanently removes the key."""
        key = self._create_key_in_db()
        _login_and_store_key(self.client, self.user)
        resp = self.client.delete(self._detail_url(key))
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(UserApiKey.objects.filter(user=self.user).count(), 0)

    def test_delete_other_users_key_returns_404(self):
        """Verify a user cannot delete another user's key."""
        key = self._create_key_in_db()
        other = _create_test_user("otheruser")
        _login_and_store_key(self.client, other)
        resp = self.client.delete(self._detail_url(key))
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    # --- Test endpoint ------------------------------------------------------

    @patch("accounts.views.test_provider_connection")
    def test_key_endpoint_returns_success(self, mock_test):
        """Verify POST to /test/ returns ok when provider connection succeeds."""
        mock_test.return_value = (True, "Connected successfully.")
        key = self._create_key_in_db()
        _login_and_store_key(self.client, self.user)
        resp = self.client.post(self._test_url(key))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["status"], "ok")

    @patch("accounts.views.test_provider_connection")
    def test_key_endpoint_returns_error_when_provider_fails(self, mock_test):
        """Verify POST to /test/ returns error when provider connection fails."""
        mock_test.return_value = (False, "Connection refused")
        key = self._create_key_in_db()
        _login_and_store_key(self.client, self.user)
        resp = self.client.post(self._test_url(key))
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(resp.data["status"], "error")

    def test_key_endpoint_requires_encryption_key(self):
        """Verify /test/ returns 401 when session has no encryption key."""
        key = self._create_key_in_db()
        self.client.force_login(self.user)
        resp = self.client.post(self._test_url(key))
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_key_endpoint_validates_key_format(self):
        """Verify /test/ validates the decrypted key format before making API calls."""
        # Create a key with invalid format (but still a valid Fernet cipher)
        bad_key_cipher = _encrypt_for_user("invalid_format")
        key = UserApiKey.objects.create(
            user=self.user,
            provider=ProviderType.OPENAI,
            label="Bad Format Key",
            encrypted_key=bad_key_cipher,
            key_fingerprint=_make_fingerprint("invalid_format"),
            masked_key=_masked("invalid_format"),
        )
        _login_and_store_key(self.client, self.user)
        resp = self.client.post(self._test_url(key))
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("sk-", str(resp.data))

    # --- Security: raw key never leaks --------------------------------------

    def test_retrieve_does_not_contain_raw_key(self):
        """Verify GET detail never exposes the raw key."""
        key = self._create_key_in_db()
        _login_and_store_key(self.client, self.user)
        resp = self.client.get(self._detail_url(key))
        self.assertNotIn("key", resp.data)

    # --- Models endpoint ----------------------------------------------------

    @patch("accounts.views._list_models_for_key")
    def test_models_endpoint_returns_model_list(self, mock_list_models):
        """Verify GET /models/ returns models from active keys."""
        m = MagicMock(provider="openai", type="cloud")
        m.name = "gpt-4o"
        mock_list_models.return_value = [m]
        self._create_key_in_db()
        _login_and_store_key(self.client, self.user)
        resp = self.client.get(self.list_url + "models/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("keys", resp.data)


# ============================================================================
# LLM Integration Tests
# ============================================================================


class UserLLMOrchestratorMixinTests(TestCase):
    """Tests for the UserLLMOrchestratorMixin."""

    def setUp(self):
        self.user = _create_test_user()
        self.factory = APIRequestFactory()

    def _make_mixin(self):
        """Import inside test to avoid import errors if dependencies missing."""
        from llm.mixins import UserLLMOrchestratorMixin

        return UserLLMOrchestratorMixin()

    def test_get_llm_orchestrator_raises_not_authenticated_when_no_key_in_session(self):
        """Verify NotAuthenticated is raised when session has no encryption key."""
        mixin = self._make_mixin()
        request = self.factory.get("/")
        request.user = self.user
        request.session = {}
        request.data = {}
        request.query_params = {}
        with self.assertRaises(NotAuthenticated):
            mixin.get_llm_orchestrator(request)

    def test_get_llm_orchestrator_reads_api_key_id_from_request_data(self):
        """Verify api_key_id is read from request.data when present."""
        mixin = self._make_mixin()
        request = self.factory.post("/", {"api_key_id": "some-uuid"})
        request.user = self.user
        # Store a valid encryption key in the session
        session = {}
        store_key_in_session(session, _TEST_FERNET_KEY)
        request.session = session
        request.data = {"api_key_id": "some-uuid"}
        request.query_params = {}

        with patch(
            "llm.mixins.get_encryption_key_from_session",
            return_value=_TEST_FERNET_KEY,
        ), patch(
            "llm.mixins.LLMOrchestrator.for_user_and_key",
        ) as mock_for_user_and_key:
            mixin.get_llm_orchestrator(request)
            mock_for_user_and_key.assert_called_once_with(
                self.user, "some-uuid", _TEST_FERNET_KEY
            )

    def test_get_llm_orchestrator_reads_api_key_id_from_query_params(self):
        """Verify api_key_id is read from request.query_params when not in data."""
        mixin = self._make_mixin()
        request = self.factory.get("/?api_key_id=uuid-from-query")
        request.user = self.user
        session = {}
        store_key_in_session(session, _TEST_FERNET_KEY)
        request.session = session
        request.data = {}
        request.query_params = {"api_key_id": "uuid-from-query"}

        with patch(
            "llm.mixins.get_encryption_key_from_session",
            return_value=_TEST_FERNET_KEY,
        ), patch(
            "llm.mixins.LLMOrchestrator.for_user_and_key",
        ) as mock_for_user_and_key:
            mixin.get_llm_orchestrator(request)
            mock_for_user_and_key.assert_called_once_with(
                self.user, "uuid-from-query", _TEST_FERNET_KEY
            )

    def test_get_llm_orchestrator_calls_for_user_when_no_api_key_id(self):
        """Verify for_user() is called when no api_key_id is provided."""
        mixin = self._make_mixin()
        request = self.factory.get("/")
        request.user = self.user
        session = {}
        store_key_in_session(session, _TEST_FERNET_KEY)
        request.session = session
        request.data = {}
        request.query_params = {}

        with patch(
            "llm.mixins.get_encryption_key_from_session",
            return_value=_TEST_FERNET_KEY,
        ), patch(
            "llm.mixins.LLMOrchestrator.for_user",
        ) as mock_for_user:
            mixin.get_llm_orchestrator(request)
            mock_for_user.assert_called_once_with(self.user, _TEST_FERNET_KEY)


# ============================================================================
# Throttling Tests
# ============================================================================


@override_settings(
    API_KEY_FINGERPRINT_PEPPER="test_pepper",
    CACHES={"default": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"}},
    REST_FRAMEWORK={
        "DEFAULT_THROTTLE_CLASSES": [
            "rest_framework.throttling.UserRateThrottle",
        ],
        "DEFAULT_THROTTLE_RATES": {
            "user": "100/minute",
            "api_key_test": "2/minute",  # Low limit for test
        },
    },
)
class ThrottlingTests(TestCase):
    """Basic throttling tests for the API key endpoints."""

    def setUp(self):
        self.client = APIClient()
        self.user = _create_test_user()
        _login_and_store_key(self.client, self.user)
        self.raw_key = "sk-" + "e" * 48
        self.encrypted = _encrypt_for_user(self.raw_key)
        self.fingerprint = _make_fingerprint(self.raw_key)
        self.masked = _masked(self.raw_key)

        self.key = UserApiKey.objects.create(
            user=self.user,
            provider=ProviderType.OPENAI,
            label="Throttle Test Key",
            encrypted_key=self.encrypted,
            key_fingerprint=self.fingerprint,
            masked_key=self.masked,
        )

    @patch("accounts.views.test_provider_connection")
    def test_anon_requests_rate_limited(self, mock_test):
        """Verify that unauthenticated requests get a 401 (not throttle)."""
        mock_test.return_value = (True, "Connected successfully.")
        # Anonymous user should get 401, not throttle
        resp = self.client.post(
            f"/api/accounts/api-keys/{self.key.pk}/test/",
        )
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch("accounts.views.test_provider_connection")
    def test_test_endpoint_rate_limited_after_limit(self, mock_test):
        """Verify the test endpoint is rate-limited after exceeding the limit."""
        mock_test.return_value = (True, "Connected successfully.")

        test_url = f"/api/accounts/api-keys/{self.key.pk}/test/"

        # Exhaust the 2/minute limit
        resp1 = self.client.post(test_url)
        self.assertEqual(resp1.status_code, status.HTTP_200_OK)

        resp2 = self.client.post(test_url)
        self.assertEqual(resp2.status_code, status.HTTP_200_OK)

        # Third request should be throttled (429)
        resp3 = self.client.post(test_url)
        self.assertEqual(resp3.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
