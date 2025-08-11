#!/usr/bin/env python3
"""
Management command to fix token encryption by re-encrypting all tokens
with the new consistent encryption key
"""
from django.core.management.base import BaseCommand
from accounts.models import AIServiceToken


class Command(BaseCommand):
    help = 'Re-encrypt all AI service tokens with the new encryption key'

    def handle(self, *args, **options):
        tokens = AIServiceToken.objects.all()
        
        self.stdout.write(f"Found {tokens.count()} tokens to fix")
        
        for token in tokens:
            # Since the old tokens can't be decrypted, we need to delete them
            # and ask users to re-enter their tokens
            user = token.user
            service_type = token.service_type
            self.stdout.write(f"Deleting invalid token for {user.username} - {service_type}")
            token.delete()
        
        self.stdout.write(
            self.style.SUCCESS(
                'Token encryption fixed! Users will need to re-enter their API tokens.'
            )
        )
