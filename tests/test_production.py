# -*- coding: utf-8 -*-
"""
    tests/test_views_depends.py

    :copyright: (C) 2015 by Openlabs Technologies & Consulting (P) Limited
    :license: BSD, see LICENSE for more details.
"""
import pytest

from trytond.pool import Pool
from trytond.config import config
config.set('database', 'path', '/tmp')


class TestProductionPlan:

    @pytest.fixture(autouse=True)
    def transaction(self, request):
        from trytond.tests.test_tryton import USER, CONTEXT, DB_NAME
        from trytond.transaction import Transaction

        Transaction().start(DB_NAME, USER, context=CONTEXT)

        def finalizer():
            Transaction().cursor.rollback()
            Transaction().stop()

        request.addfinalizer(finalizer)

    def test_production_plan(self, bom, plan_period, company):
        """
        Test production plan by creating one
        """
        ProductionPlan = Pool().get('production.plan')

        plan = ProductionPlan(
            period=plan_period,
            product=bom.outputs[0].product,
            bom=bom,
            company=company,
            quantity=1,
            uom=bom.outputs[0].uom,
        )
        plan.save()
