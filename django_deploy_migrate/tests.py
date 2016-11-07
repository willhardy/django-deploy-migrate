#!/usr/bin/env py.test

from collections import namedtuple
import pytest
from django_deploy_migrate.utils import get_stop_points


StandardMigration = namedtuple('Migration',
                               ['app_label', 'name'])
AnnotatedMigration = namedtuple('Migration',
                                ['app_label', 'name', 'run_on_deploy'])


def mig(app, name, run_on_deploy=None):
    if run_on_deploy is None:
        return StandardMigration(app_label=app, name=name)
    else:
        return AnnotatedMigration(app_label=app,
                                  name=name,
                                  run_on_deploy=run_on_deploy)


class TestGetStopPoints:
    def test_empty(self):
        output = get_stop_points('appname', [])
        assert output == {}

    def test_only_stop(self):
        migrations = [
            mig('app02', '0002_two_NOT_ON_DEPLOY'),
        ]
        output = get_stop_points('appname', migrations)
        assert output == {'app02': False}

    def test_normal(self):
        migrations = [
            mig('app01', '0001_initial'),
            mig('app01', '0002_two'),
            mig('app02', '0001_initial'),
        ]
        output = get_stop_points('appname', migrations)
        assert output == {'app01': None, 'app02': None}

    def test_stop(self):
        migrations = [
            mig('app01', '0001_initial'),
            mig('app01', '0002_two'),
            mig('app02', '0001_initial'),
            mig('app02', '0002_two_NOT_ON_DEPLOY'),
        ]
        output = get_stop_points('appname', migrations)
        assert output == {'app01': None, 'app02': '0001_initial'}

    def test_stop_2(self):
        migrations = [
            mig('app01', '0001_initial'),
            mig('app01', '0002_two'),
            mig('app02', '0001_initial'),
            mig('app02', '0002_two_NOT_ON_DEPLOY'),
            mig('app02', '0003_three_NOT_ON_DEPLOY'),
        ]
        output = get_stop_points('appname', migrations)
        assert output == {'app01': None, 'app02': '0001_initial'}

    def test_stop_attr(self):
        migrations = [
            mig('app01', '0001_initial'),
            mig('app01', '0002_two'),
            mig('app02', '0001_initial'),
            mig('app02', '0002_two', run_on_deploy=False),
        ]
        output = get_stop_points('appname', migrations)
        assert output == {'app01': None, 'app02': '0001_initial'}

    def test_no_stop_attr(self):
        migrations = [
            mig('app01', '0001_initial'),
            mig('app01', '0002_two'),
            mig('app02', '0001_initial'),
            mig('app02', '0002_two', run_on_deploy=True),
        ]
        output = get_stop_points('appname', migrations)
        assert output == {'app01': None, 'app02': None}

    def test_unreachable(self):
        migrations = [
            mig('app01', '0001_initial'),
            mig('app01', '0002_two'),
            mig('app02', '0001_initial'),
            mig('app02', '0002_two_NOT_ON_DEPLOY'),
            mig('app02', '0003_three'),
        ]
        with pytest.raises(RuntimeError):
            get_stop_points('appname', migrations, strict=True)

    def test_unreachable_2(self):
        migrations = [
            mig('app01', '0001_initial'),
            mig('app01', '0002_two'),
            mig('app02', '0001_initial'),
            mig('app02', '0002_two_NOT_ON_DEPLOY'),
            mig('app02', '0003_three'),
        ]
        output = get_stop_points('appname', migrations, strict=False)

        assert output == {'app01': None, 'app02': '0001_initial'}

    def test_unreachable_attr(self):
        migrations = [
            mig('app01', '0001_initial'),
            mig('app01', '0002_two'),
            mig('app02', '0001_initial'),
            mig('app02', '0002_two', run_on_deploy=False),
            mig('app02', '0003_three'),
        ]
        with pytest.raises(RuntimeError):
            get_stop_points('appname', migrations, strict=True)

    def test_unreachable_attr_2(self):
        migrations = [
            mig('app01', '0001_initial'),
            mig('app01', '0002_two'),
            mig('app02', '0001_initial'),
            mig('app02', '0002_two', run_on_deploy=False),
            mig('app02', '0003_three'),
        ]
        output = get_stop_points('appname', migrations, strict=False)

        assert output == {'app01': None, 'app02': '0001_initial'}
