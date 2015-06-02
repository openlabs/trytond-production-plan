# -*- coding: utf-8 -*-
"""
    tests/conftest.py

    :copyright: (C) 2015 by Openlabs Technologies & Consulting (P) Limited
    :license: BSD, see LICENSE for more details.
"""
import os
import time
from decimal import Decimal
from trytond.pool import Pool

import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--db", action="store", default="sqlite",
        help="Run on database: sqlite or postgres"
    )


@pytest.fixture(scope='session', autouse=True)
def install_module(request):
    """Install tryton module in specified database.
    """
    if request.config.getoption("--db") == 'sqlite':
        os.environ['TRYTOND_DATABASE_URI'] = "sqlite://"
        os.environ['DB_NAME'] = ':memory:'

    elif request.config.getoption("--db") == 'postgres':
        os.environ['TRYTOND_DATABASE_URI'] = "postgresql://"
        os.environ['DB_NAME'] = 'test_' + str(int(time.time()))

    from trytond.tests import test_tryton
    test_tryton.install_module('production_plan')


@pytest.fixture()
def customer(request):
    """
    Create a customer and return it
    """
    Party = Pool().get('party.party')
    party = Party(name="Sharoon Thomas")
    party.save()
    return party


@pytest.fixture()
def product(request):
    """
    Return a product after saving it
    """
    ProductTemplate = Pool().get('product.template')
    Product = Pool().get('product.product')
    Uom = Pool().get('product.uom')

    uom_unit, = Uom.search([('symbol', '=', 'u')])

    template = ProductTemplate(**{
        'name': 'KindleFire',
        'type': 'goods',
        'list_price': Decimal('119'),
        'cost_price': Decimal('100'),
        'default_uom': uom_unit.id,
        'products': [],
    })

    product = Product(code='ABC', template=template)
    product.save()
    return product


@pytest.fixture()
def dataset(request, customer, product):
    return {
        'customer': customer,
        'product': product,
    }
