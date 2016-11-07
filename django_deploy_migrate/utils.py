import collections


NOT_ON_DEPLOY = 'NOT_ON_DEPLOY'
RUN_ON_DEPLOY_ATTR = 'run_on_deploy'


class UnreachableMigrations(RuntimeError):
    def __init__(self, migrations):
        self.migrations = migrations
        msg = 'The following migrations are unreachable for a deploy migration: '
        msg += ' '.join('{}.{}'.format(migration.app_label, migration.name)
                        for migration in migrations)
        super().__init__(msg)


def get_stop_points(current_app_label, migrations, strict=True):
    """For the given django app, return the migration name where we should stop.

    This will be the migration before any NOT_ON_DEPLOY migrations.
    If all migrations for a given app are to be applied, then return with None.
    If there are any normal migrations after this stopping point, exit with an error.

    The provided migrations is an iterable of objecs with an 'app_label' and 'name' attribute.
    A migration is considered a stop point if its name contains a keyword (NOT_ON_DEPLOY)
    or has an attribute run_on_deploy=False.
    """
    apps_to_migrate = set()
    unreachable_migrations = collections.defaultdict(list)
    stop_points = {}

    migrations_with_previous = zip([None] + migrations, migrations)
    for previous, migration in migrations_with_previous:
        if is_flagged_for_no_deploy(migration):
            if previous is None:
                # Do not apply any migrations for this app
                # This isn't strictly necessary, but avoids running
                # migrated later when nothing will be migrated.
                stop_points.setdefault(migration.app_label, False)
            else:
                # Stop migrations before the current migration
                stop_points.setdefault(migration.app_label, previous.name)
        elif migration.app_label in stop_points:
            # We have a migration to apply after a stop point has been reached
            unreachable_migrations[migration.app_label].append(migration)
        else:
            # We have a migration to apply, and no stop points have been defined yet.
            apps_to_migrate.add(migration.app_label)

    # Apps that have migrations, but no stop point was defined should be
    # present, but define no stop point
    for app in apps_to_migrate:
        stop_points.setdefault(app, None)

    if unreachable_migrations and strict:
        raise UnreachableMigrations([migration
                                     for migrations in unreachable_migrations.values()
                                     for migration in migrations])

    return stop_points


def is_flagged_for_no_deploy(migration):
    if NOT_ON_DEPLOY in migration.name:
        return True
    if getattr(migration, RUN_ON_DEPLOY_ATTR, True) is False:
        return True
    return False
