from rest_framework.throttling import UserRateThrottle


class ApiKeyTestRateThrottle(UserRateThrottle):
    scope = "api_key_test"
