from django.apps import apps
from django.core import management
from django.core.management.base import BaseCommand, CommandError
from django.db import DEFAULT_DB_ALIAS, connections
from django.db.migrations.executor import MigrationExecutor

from django_deploy_migrate.utils import get_stop_points


class Command(BaseCommand):
    help = "like migrate but does not run migrations tagged NOT_ON_DEPLOY"

    def add_arguments(self, parser):
        parser.add_argument('--noinput', '--no-input',
                            action='store_false', dest='interactive', default=True,
                            help='Tells Django to NOT prompt the user for input of any kind.')

    def handle(self, *args, **options):
        # Get the database we're operating from
        connection = connections[DEFAULT_DB_ALIAS]

        # Run through each app one-by-one to ensure every migration has its best
        # chance of being run.
        something_done = False
        for current_app in apps.get_app_configs():
            apps_migrations = get_all_unapplied_migrations(connection, current_app.label)
            try:
                stop_points = get_stop_points(current_app.label, apps_migrations, strict=True)
            except RuntimeError as e:
                if current_app.label in e.migrations:
                    raise CommandError(e.msg)

            for app_label, stop_point in stop_points.items():
                # Do not apply any migrations for this app
                if stop_point is False:
                    msg = 'Did not migrate {} because a migration was flagged NOT_ON_DEPLOY'
                    print(msg.format(current_app.label))
                    continue
                # Apply all migrations for this app
                if stop_point is None:
                    management.call_command('migrate', app_label, **options)
                    something_done = True
                # Apply specific migration for this app
                else:
                    management.call_command('migrate', app_label, stop_point, **options)
                    msg = 'Migrated {}, but stopped before a migration flagged NOT_ON_DEPLOY'
                    print(msg.format(current_app.label))
                    something_done = True

        if not something_done:
            print('Nothing to migrate.')


def get_all_unapplied_migrations(connection, app_label):
    executor = MigrationExecutor(connection)
    if app_label not in executor.loader.migrated_apps:
        return []
    targets = [key for key in executor.loader.graph.leaf_nodes() if key[0] == app_label]
    plan = executor.migration_plan(targets)
    return [migration for migration, backwards in plan]
