"""
One-time cleanup for the agents app migration state.

Handles the case where commercialization tables were created by a previous
auto-generated migration (from when makemigrations ran on Docker startup)
but our 0004_commercialization_models is not recorded in django_migrations.
"""
from django.core.management.base import BaseCommand
from django.db import connection


VALID_AGENT_MIGRATIONS = (
    '0001_initial',
    '0002_add_rag_document_model',
    '0003_rename_rag_documents_uploade_c1a2b3_idx_rag_documen_uploade_84f4bf_idx_and_more',
    '0004_commercialization_models',
)


class Command(BaseCommand):
    help = 'Clean up stale agent migration records and fake 0004 if tables exist'

    def handle(self, *args, **options):
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT EXISTS(SELECT 1 FROM information_schema.tables "
                    "WHERE table_name='agent_conversations')"
                )
                tables_exist = cursor.fetchone()[0]

                if not tables_exist:
                    self.stdout.write('Fresh database, no cleanup needed')
                    return

                # Remove stale records from auto-generated migrations
                cursor.execute(
                    "DELETE FROM django_migrations "
                    "WHERE app='agents' AND name NOT IN %s",
                    [VALID_AGENT_MIGRATIONS],
                )

                # Fake 0004 if not already recorded
                cursor.execute(
                    "SELECT EXISTS(SELECT 1 FROM django_migrations "
                    "WHERE app='agents' AND name='0004_commercialization_models')"
                )
                if not cursor.fetchone()[0]:
                    cursor.execute(
                        "INSERT INTO django_migrations (app, name, applied) "
                        "VALUES ('agents', '0004_commercialization_models', NOW())"
                    )
                    self.stdout.write(self.style.SUCCESS(
                        'Faked agents.0004_commercialization_models (tables already exist)'
                    ))
                else:
                    self.stdout.write('0004 already recorded, nothing to do')

        except Exception as e:
            self.stdout.write(f'Pre-migrate cleanup skipped: {e}')
