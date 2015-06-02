# -*- coding: utf-8 -*-
"""
    tests/test_plan_period.py

    :copyright: (C) 2014 by Openlabs Technologies & Consulting (P) Limited
    :license: BSD, see LICENSE for more details.
"""
import datetime

import pytest

from trytond.pool import Pool
from trytond.config import config
config.set('database', 'path', '/tmp')


from trytond.exceptions import UserError


class TestPlanPeriod:
    "Tests for Production Plan Period"

    @pytest.fixture(autouse=True)
    def transaction(self, request):
        from trytond.tests.test_tryton import USER, CONTEXT, DB_NAME
        from trytond.transaction import Transaction

        Transaction().start(DB_NAME, USER, context=CONTEXT)

        def finalizer():
            Transaction().cursor.rollback()
            Transaction().stop()

        request.addfinalizer(finalizer)

    def test_0010_raises_error_for_monthly_periods(self):
        "Raises Error for Periods other than weekly"

        ProductionPlanPeriod = Pool().get('production.plan.period')

        with pytest.raises(AssertionError):
            ProductionPlanPeriod.create_periods(
                datetime.date(2015, 6, 1),
                datetime.date(2015, 6, 7),
                'monthly'
            )

    def test_0020_no_error_for_weekly_periods(self):
        "No error will be raised for weekly periods"
        ProductionPlanPeriod = Pool().get('production.plan.period')

        ProductionPlanPeriod.create_periods(
            datetime.date(2015, 6, 1),
            datetime.date(2015, 6, 5),
            'weekly'
        )

    def test_0030_raise_error_if_start_date_not_monday(self):
        "Raises error if start date is not monday"

        ProductionPlanPeriod = Pool().get('production.plan.period')

        with pytest.raises(UserError):
            ProductionPlanPeriod.create_periods(
                datetime.date(2015, 6, 2),
                datetime.date(2015, 6, 7),
                'weekly'
            )

    def test_0040_no_error_if_start_date_is_monday(self):
        "No error will be raised if start date is monday"

        ProductionPlanPeriod = Pool().get('production.plan.period')

        ProductionPlanPeriod.create_periods(
            datetime.date(2015, 6, 1),
            datetime.date(2015, 6, 5),
            'weekly'
        )

    def test_0050_no_error_if_period_from_monday_to_friday(self):
        "No Error will be raised if start date is Monday and end date is Friday"

        ProductionPlanPeriod = Pool().get('production.plan.period')

        ProductionPlanPeriod.create_periods(
            datetime.date(2015, 6, 1),
            datetime.date(2015, 6, 5),
            'weekly'
        )
