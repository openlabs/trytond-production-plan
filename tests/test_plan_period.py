# -*- coding: utf-8 -*-
"""
    tests/test_plan_period.py

    :copyright: (C) 2014 by Openlabs Technologies & Consulting (P) Limited
    :license: BSD, see LICENSE for more details.
"""
import unittest
import trytond.tests.test_tryton
import datetime
from trytond.tests.test_tryton import POOL
from trytond.transaction import Transaction
from trytond.tests.test_tryton import DB_NAME, USER, CONTEXT
from trytond.exceptions import UserError


class TestPlanPeriod(unittest.TestCase):
    "Tests for Production Plan Period"

    def setUp(self):
        "Setup defaults"

        trytond.tests.test_tryton.install_module('production_plan')

    def test_0010_raises_error_for_monthly_periods(self):
        "Raises Error for Periods other than weekly"

        ProductionPlanPeriod = POOL.get('production.plan.period')

        with Transaction().start(DB_NAME, USER, context=CONTEXT):
            with self.assertRaises(AssertionError):
                ProductionPlanPeriod.create_periods(
                    datetime.date(2015, 6, 1),
                    datetime.date(2015, 6, 7),
                    'monthly'
                )

    def test_0020_no_error_for_weekly_periods(self):
        "No error will be raised for weekly periods"

        ProductionPlanPeriod = POOL.get('production.plan.period')

        with Transaction().start(DB_NAME, USER, context=CONTEXT):
                ProductionPlanPeriod.create_periods(
                    datetime.date(2015, 6, 1),
                    datetime.date(2015, 6, 5),
                    'weekly'
                )

    def test_0030_raise_error_if_start_date_not_monday(self):
        "Raises error if start date is not monday"

        ProductionPlanPeriod = POOL.get('production.plan.period')

        with Transaction().start(DB_NAME, USER, context=CONTEXT):
            with self.assertRaises(UserError):
                periods = ProductionPlanPeriod.create_periods(
                    datetime.date(2015, 6, 2),
                    datetime.date(2015, 6, 7),
                    'weekly'
                )
                self.assertRaises(UserError, periods.create_periods)

    def test_0040_no_error_if_start_date_is_monday(self):
        "No error will be raised if start date is monday"

        ProductionPlanPeriod = POOL.get('production.plan.period')

        with Transaction().start(DB_NAME, USER, context=CONTEXT):
            ProductionPlanPeriod.create_periods(
                datetime.date(2015, 6, 1),
                datetime.date(2015, 6, 5),
                'weekly'
            )

    def test_0050_no_error_if_period_from_monday_to_friday(self):
        "No Error will be raised if start date is Monday and end date is Friday"

        ProductionPlanPeriod = POOL.get('production.plan.period')

        with Transaction().start(DB_NAME, USER, context=CONTEXT):
            ProductionPlanPeriod.create_periods(
                datetime.date(2015, 6, 1),
                datetime.date(2015, 6, 5),
                'weekly'
            )
