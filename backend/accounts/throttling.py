"""Throttle classes for the accounts app.

Defines rate-limit policies specific to API-key testing endpoints,
preventing excessive usage that could burn through third-party API quotas.
"""

from rest_framework.throttling import UserRateThrottle


class ApiKeyTestRateThrottle(UserRateThrottle):
    """Rate limit for the API-key test endpoint.

    Prevents a single user from exhausting the daily third-party API quota
    by repeatedly testing invalid or valid keys. Applied on top of any
    global or user-level throttle classes.

    Scope:
        ``api_key_test`` — configured in Django settings
        (``DEFAULT_THROTTLE_RATES``).
    """

    scope = "api_key_test"
