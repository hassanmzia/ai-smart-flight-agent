"""
Django management command to index user travel data for chat RAG.
Usage:
  python manage.py index_user_data                  # Index all users
  python manage.py index_user_data --user=email     # Index specific user
  python manage.py index_user_data --reset          # Clear and re-index all
  python manage.py index_user_data --stats          # Show indexing stats
"""

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model

import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class Command(BaseCommand):
    help = 'Index user travel data (bookings, itineraries, feedback) into ChromaDB for chat RAG'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user',
            type=str,
            help='Index only this user (by email)',
        )
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Delete all existing user embeddings before re-indexing',
        )
        parser.add_argument(
            '--stats',
            action='store_true',
            help='Show indexing stats without modifying anything',
        )

    def handle(self, *args, **options):
        from apps.agents.chat_rag import get_user_data_rag

        rag = get_user_data_rag()

        # Stats only
        if options['stats']:
            self._show_stats(rag, options.get('user'))
            return

        # Determine which users to index
        if options['user']:
            try:
                users = [User.objects.get(email=options['user'])]
            except User.DoesNotExist:
                raise CommandError(f"User with email '{options['user']}' not found")
        else:
            users = User.objects.all()

        self.stdout.write(self.style.SUCCESS(
            f"Indexing user data for {len(users)} user(s)..."
        ))

        total_chunks = 0
        for i, user in enumerate(users, 1):
            if options['reset']:
                deleted = rag.delete_user_data(user)
                if deleted:
                    self.stdout.write(f"  Cleared {deleted} old chunks for {user.email}")

            count = rag.index_user_data(user)
            total_chunks += count
            self.stdout.write(
                f"  [{i}/{len(users)}] {user.email}: {count} chunks indexed"
            )

        self.stdout.write(self.style.SUCCESS(
            f"\nDone! Indexed {total_chunks} total chunks for {len(users)} user(s)."
        ))

    def _show_stats(self, rag, user_email=None):
        if user_email:
            try:
                user = User.objects.get(email=user_email)
            except User.DoesNotExist:
                raise CommandError(f"User with email '{user_email}' not found")
            stats = rag.get_user_stats(user)
            self.stdout.write(self.style.SUCCESS(f"\nStats for {user_email}:"))
            self.stdout.write(f"  Total chunks: {stats['total_chunks']}")
            self.stdout.write(f"  Index fresh: {stats.get('is_fresh', False)}")
            if stats.get('data_types'):
                for dt, count in stats['data_types'].items():
                    self.stdout.write(f"    {dt}: {count}")
        else:
            self.stdout.write(self.style.SUCCESS("\nStats for all users:"))
            for user in User.objects.all():
                stats = rag.get_user_stats(user)
                if stats['total_chunks'] > 0:
                    self.stdout.write(
                        f"  {user.email}: {stats['total_chunks']} chunks "
                        f"(fresh: {stats.get('is_fresh', False)})"
                    )
