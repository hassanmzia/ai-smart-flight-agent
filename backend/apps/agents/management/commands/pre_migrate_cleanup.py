"""
One-time cleanup for the agents app migration state.

Handles the case where tables were created by previous auto-generated
migrations (from when makemigrations ran on Docker startup) but our
canonical migrations (0004, 0005, etc.) are not recorded in django_migrations.
"""
from django.core.management.base import BaseCommand
from django.db import connection


VALID_AGENT_MIGRATIONS = (
    '0001_initial',
    '0002_add_rag_document_model',
    '0003_rename_rag_documents_uploade_c1a2b3_idx_rag_documen_uploade_84f4bf_idx_and_more',
    '0004_commercialization_models',
    '0005_healthinsuranceinfo_userpreference_dietary_allergies_and_more',
)

# Migrations to fake when their sentinel table already exists in the DB.
# Each entry maps migration_name -> a table that the migration creates.
MIGRATIONS_TO_FAKE = {
    '0004_commercialization_models': 'agent_conversations',
    '0005_healthinsuranceinfo_userpreference_dietary_allergies_and_more': 'health_insurance_info',
}


class Command(BaseCommand):
    help = 'Clean up stale agent migration records and fake migrations whose tables already exist'

    def handle(self, *args, **options):
        try:
            with connection.cursor() as cursor:
                # Check if the DB has any agents tables at all
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

                # Fake each canonical migration if its tables already exist
                for migration_name, sentinel_table in MIGRATIONS_TO_FAKE.items():
                    cursor.execute(
                        "SELECT EXISTS(SELECT 1 FROM information_schema.tables "
                        "WHERE table_name=%s)",
                        [sentinel_table],
                    )
                    table_exists = cursor.fetchone()[0]

                    cursor.execute(
                        "SELECT EXISTS(SELECT 1 FROM django_migrations "
                        "WHERE app='agents' AND name=%s)",
                        [migration_name],
                    )
                    already_recorded = cursor.fetchone()[0]

                    if table_exists and not already_recorded:
                        cursor.execute(
                            "INSERT INTO django_migrations (app, name, applied) "
                            "VALUES ('agents', %s, NOW())",
                            [migration_name],
                        )
                        self.stdout.write(self.style.SUCCESS(
                            f'Faked agents.{migration_name} (tables already exist)'
                        ))
                    elif already_recorded:
                        self.stdout.write(f'{migration_name} already recorded, nothing to do')
                    else:
                        self.stdout.write(f'{migration_name} tables not found, will run normally')

        except Exception as e:
            self.stdout.write(f'Pre-migrate cleanup skipped: {e}')
