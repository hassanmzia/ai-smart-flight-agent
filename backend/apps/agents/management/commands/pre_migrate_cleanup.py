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
    '0006_contentitem_comments_count_and_more',
)

# Migrations to fake when their sentinel table already exists in the DB.
# Each entry maps migration_name -> a table that the migration creates.
MIGRATIONS_TO_FAKE = {
    '0004_commercialization_models': 'agent_conversations',
    '0005_healthinsuranceinfo_userpreference_dietary_allergies_and_more': 'health_insurance_info',
}


# Idempotent DDL for migration 0006 — used when the DB has partial state
# from a previously-failed run (e.g. `comments_count` column already added
# to `content_items` but the new comment/vote/dislike tables were never
# created, so the whole migration rolls back and can't replay cleanly).
#
# Every statement is `IF NOT EXISTS` so it's safe to run even if the
# operations have already been applied.
MIGRATION_0006_DDL = [
    # --- Columns on existing tables ---
    "ALTER TABLE content_items ADD COLUMN IF NOT EXISTS comments_count integer NOT NULL DEFAULT 0",
    "ALTER TABLE travel_stories_generated ADD COLUMN IF NOT EXISTS comments_count integer NOT NULL DEFAULT 0",
    "ALTER TABLE travel_stories_generated ADD COLUMN IF NOT EXISTS dislikes_count integer NOT NULL DEFAULT 0",
    "ALTER TABLE trip_templates ADD COLUMN IF NOT EXISTS comments_count integer NOT NULL DEFAULT 0",
    "ALTER TABLE trip_templates ADD COLUMN IF NOT EXISTS dislikes_count integer NOT NULL DEFAULT 0",

    # --- New tables ---
    """
    CREATE TABLE IF NOT EXISTS content_comments (
        id bigserial PRIMARY KEY,
        content text NOT NULL,
        created_at timestamptz NOT NULL,
        content_item_id bigint NOT NULL REFERENCES content_items(id) DEFERRABLE INITIALLY DEFERRED,
        user_id bigint NOT NULL REFERENCES users(id) DEFERRABLE INITIALLY DEFERRED
    )
    """,
    "CREATE INDEX IF NOT EXISTS content_comments_content_item_id_idx ON content_comments(content_item_id)",
    "CREATE INDEX IF NOT EXISTS content_comments_user_id_idx ON content_comments(user_id)",

    """
    CREATE TABLE IF NOT EXISTS template_comments (
        id bigserial PRIMARY KEY,
        content text NOT NULL,
        created_at timestamptz NOT NULL,
        template_id bigint NOT NULL REFERENCES trip_templates(id) DEFERRABLE INITIALLY DEFERRED,
        user_id bigint NOT NULL REFERENCES users(id) DEFERRABLE INITIALLY DEFERRED
    )
    """,
    "CREATE INDEX IF NOT EXISTS template_comments_template_id_idx ON template_comments(template_id)",
    "CREATE INDEX IF NOT EXISTS template_comments_user_id_idx ON template_comments(user_id)",

    """
    CREATE TABLE IF NOT EXISTS content_votes (
        id bigserial PRIMARY KEY,
        vote varchar(4) NOT NULL,
        created_at timestamptz NOT NULL,
        content_item_id bigint NOT NULL REFERENCES content_items(id) DEFERRABLE INITIALLY DEFERRED,
        user_id bigint NOT NULL REFERENCES users(id) DEFERRABLE INITIALLY DEFERRED,
        CONSTRAINT content_votes_user_content_uniq UNIQUE (user_id, content_item_id)
    )
    """,
    "CREATE INDEX IF NOT EXISTS content_votes_content_item_id_idx ON content_votes(content_item_id)",
    "CREATE INDEX IF NOT EXISTS content_votes_user_id_idx ON content_votes(user_id)",

    """
    CREATE TABLE IF NOT EXISTS story_dislikes (
        id bigserial PRIMARY KEY,
        created_at timestamptz NOT NULL,
        story_id bigint NOT NULL REFERENCES travel_stories_generated(id) DEFERRABLE INITIALLY DEFERRED,
        user_id bigint NOT NULL REFERENCES users(id) DEFERRABLE INITIALLY DEFERRED,
        CONSTRAINT story_dislikes_user_story_uniq UNIQUE (user_id, story_id)
    )
    """,
    "CREATE INDEX IF NOT EXISTS story_dislikes_story_id_idx ON story_dislikes(story_id)",
    "CREATE INDEX IF NOT EXISTS story_dislikes_user_id_idx ON story_dislikes(user_id)",

    """
    CREATE TABLE IF NOT EXISTS template_dislikes (
        id bigserial PRIMARY KEY,
        created_at timestamptz NOT NULL,
        template_id bigint NOT NULL REFERENCES trip_templates(id) DEFERRABLE INITIALLY DEFERRED,
        user_id bigint NOT NULL REFERENCES users(id) DEFERRABLE INITIALLY DEFERRED,
        CONSTRAINT template_dislikes_user_template_uniq UNIQUE (user_id, template_id)
    )
    """,
    "CREATE INDEX IF NOT EXISTS template_dislikes_template_id_idx ON template_dislikes(template_id)",
    "CREATE INDEX IF NOT EXISTS template_dislikes_user_id_idx ON template_dislikes(user_id)",

    """
    CREATE TABLE IF NOT EXISTS template_likes (
        id bigserial PRIMARY KEY,
        created_at timestamptz NOT NULL,
        template_id bigint NOT NULL REFERENCES trip_templates(id) DEFERRABLE INITIALLY DEFERRED,
        user_id bigint NOT NULL REFERENCES users(id) DEFERRABLE INITIALLY DEFERRED,
        CONSTRAINT template_likes_user_template_uniq UNIQUE (user_id, template_id)
    )
    """,
    "CREATE INDEX IF NOT EXISTS template_likes_template_id_idx ON template_likes(template_id)",
    "CREATE INDEX IF NOT EXISTS template_likes_user_id_idx ON template_likes(user_id)",
]


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

                # Handle migration 0006 separately — it has partial-state risk
                # because a prior failed run may have added some columns before
                # rolling back. Apply its DDL idempotently, then fake-record it.
                self._reconcile_migration_0006(cursor)

        except Exception as e:
            self.stdout.write(f'Pre-migrate cleanup skipped: {e}')

    def _reconcile_migration_0006(self, cursor):
        """
        Idempotently apply migration 0006's schema changes and fake-record
        it if needed.

        We look for a sentinel column (`content_items.comments_count`) that
        would only exist if any part of 0006 previously ran. If it exists,
        the transaction-rollback semantics of a failed migration might still
        have left partial state (though PG DDL is usually atomic, past bugs
        or manual ALTERs can produce drift). Running IF NOT EXISTS DDL is
        always safe whether or not the schema is already converged.
        """
        migration_name = '0006_contentitem_comments_count_and_more'

        cursor.execute(
            "SELECT EXISTS(SELECT 1 FROM django_migrations "
            "WHERE app='agents' AND name=%s)",
            [migration_name],
        )
        already_recorded = cursor.fetchone()[0]

        if already_recorded:
            self.stdout.write(f'{migration_name} already recorded, nothing to do')
            return

        # Look for any sentinel that indicates partial application of 0006
        cursor.execute(
            "SELECT EXISTS(SELECT 1 FROM information_schema.columns "
            "WHERE table_name='content_items' AND column_name='comments_count')"
        )
        column_exists = cursor.fetchone()[0]

        cursor.execute(
            "SELECT EXISTS(SELECT 1 FROM information_schema.tables "
            "WHERE table_name='content_votes')"
        )
        table_exists = cursor.fetchone()[0]

        if not column_exists and not table_exists:
            self.stdout.write(f'{migration_name} tables not found, will run normally')
            return

        # Partial or full state found — ensure every piece of the migration
        # exists, then fake-record it so Django's executor skips it.
        # Every statement uses IF NOT EXISTS, so this is safe to re-run.
        self.stdout.write(
            f'{migration_name} has partial state, reconciling schema...'
        )
        for ddl in MIGRATION_0006_DDL:
            cursor.execute(ddl)

        cursor.execute(
            "INSERT INTO django_migrations (app, name, applied) "
            "VALUES ('agents', %s, NOW())",
            [migration_name],
        )
        self.stdout.write(self.style.SUCCESS(
            f'Faked agents.{migration_name} (schema reconciled)'
        ))
