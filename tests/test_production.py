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

    def test_production_plan(self, dataset):
        """
        Test production plan workflow
        """
        Party = Pool().get('party.party')
        Product = Pool().get('product.product')

        print Party.search([])
        print Product.search([])
