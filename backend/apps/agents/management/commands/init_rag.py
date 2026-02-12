"""
Django management command to initialize and seed the RAG knowledge base
Usage: python manage.py init_rag [--reset] [--seed-sample]
"""

from django.core.management.base import BaseCommand, CommandError
from apps.agents.rag_system import TravelKnowledgeBase, KnowledgeBaseSeeder
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Initialize and seed the RAG knowledge base with travel information'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Reset the knowledge base before seeding',
        )
        parser.add_argument(
            '--seed-sample',
            action='store_true',
            help='Seed with sample destination data',
        )
        parser.add_argument(
            '--seed-file',
            type=str,
            help='Path to JSON file with destination data to seed',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Initializing RAG Knowledge Base...'))

        try:
            # Initialize knowledge base
            kb = TravelKnowledgeBase()
            self.stdout.write(self.style.SUCCESS(f'✓ Knowledge base initialized'))

            # Reset if requested
            if options['reset']:
                self.stdout.write(self.style.WARNING('Resetting knowledge base...'))
                kb.delete_collection()
                kb = TravelKnowledgeBase()  # Recreate
                self.stdout.write(self.style.SUCCESS('✓ Knowledge base reset'))

            # Get current stats
            stats = kb.get_collection_stats()
            self.stdout.write(f"Current documents: {stats.get('total_documents', 0)}")

            # Seed with sample data if requested
            if options['seed_sample']:
                self.stdout.write('Seeding with sample destination data...')
                seeder = KnowledgeBaseSeeder(kb)
                seeder.seed_sample_destinations()
                self.stdout.write(self.style.SUCCESS('✓ Sample data seeded'))

                # Show updated stats
                stats = kb.get_collection_stats()
                self.stdout.write(self.style.SUCCESS(
                    f"✓ Total documents: {stats.get('total_documents', 0)}"
                ))

            # Seed from file if provided
            if options['seed_file']:
                self.stdout.write(f"Seeding from file: {options['seed_file']}")
                seeder = KnowledgeBaseSeeder(kb)
                seeder.seed_from_file(options['seed_file'])
                self.stdout.write(self.style.SUCCESS('✓ Data seeded from file'))

                # Show updated stats
                stats = kb.get_collection_stats()
                self.stdout.write(self.style.SUCCESS(
                    f"✓ Total documents: {stats.get('total_documents', 0)}"
                ))

            self.stdout.write(self.style.SUCCESS('\n=== RAG Knowledge Base Ready ==='))
            self.stdout.write(f"Collection: {stats.get('name')}")
            self.stdout.write(f"Total Documents: {stats.get('total_documents', 0)}")
            self.stdout.write(f"Embedding Function: {stats.get('embedding_function', 'N/A')}")

        except Exception as e:
            raise CommandError(f'Error initializing RAG system: {str(e)}')
