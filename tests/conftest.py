# -*- coding: utf-8 -*-
"""
    tests/conftest.py

    :copyright: (C) 2015 by Openlabs Technologies & Consulting (P) Limited
    :license: BSD, see LICENSE for more details.
"""
import os
import time
import calendar
from datetime import date
from dateutil.relativedelta import relativedelta
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

    products = Product.search([('code', '=', 'A1533')])

    if products:
        return products[0]

    uom_unit, = Uom.search([('symbol', '=', 'u')])
    template = ProductTemplate(**{
        'name': 'iPhone 5',
        'type': 'goods',
        'list_price': Decimal('119'),
        'cost_price': Decimal('100'),
        'default_uom': uom_unit.id,
        'products': [],
    })
    product = Product(code='A1533', template=template)
    product.save()
    return product


@pytest.fixture()
def company(request):
    Party = Pool().get('party.party')
    Company = Pool().get('company.company')
    Country = Pool().get('country.country')
    Subdivision = Pool().get('country.subdivision')
    Currency = Pool().get('currency.currency')

    companies = Company.search([])
    if companies:
        return companies[0]

    usd, = Currency.create([{
        'name': 'US Dollar',
        'code': 'USD',
        'symbol': '$',
    }])
    country_us, = Country.create([{
        'name': 'United States',
        'code': 'US',
    }])
    subdivision_florida, = Subdivision.create([{
        'name': 'Florida',
        'code': 'US-FL',
        'country': country_us.id,
        'type': 'state'
    }])
    subdivision_california, = Subdivision.create([{
        'name': 'California',
        'code': 'US-CA',
        'country': country_us.id,
        'type': 'state'
    }])
    company_party, = Party.create([{
        'name': 'ABC Corp.',
        'addresses': [('create', [{
            'name': 'ABC Corp.',
            'street': '247 High Street',
            'zip': '94301-1041',
            'city': 'Palo Alto',
            'country': country_us.id,
            'subdivision': subdivision_california.id,
        }])],
        'contact_mechanisms': [('create', [{
            'type': 'phone',
            'value': '123456789'
        }])]
    }])
    employee_party, = Party.create([{
        'name': 'Prakash Pandey',
    }])
    company, = Company.create([{
        'party': company_party.id,
        'currency': usd.id,
    }])
    return company


@pytest.fixture()
def bom(request, product):
    """
    Returns a BOM for apple iphone 5 box
    """
    BOM = Pool().get('production.bom')
    BOMInput = Pool().get('production.bom.input')
    BOMOutput = Pool().get('production.bom.output')
    ProductTemplate = Pool().get('product.template')
    Product = Pool().get('product.product')
    ProductBOM = Pool().get('product.product-production.bom')
    Uom = Pool().get('product.uom')

    name = 'iPhone 5S'

    uom_unit, = Uom.search([('symbol', '=', 'u')])
    iphone_bom = BOM.search([('name', '=', name)])

    if iphone_bom:
        return iphone_bom[0]

    inputs = []
    for component in [
            'iPhone 5s with iOS 8',
            'Apple EarPods with Remote and Mic',
            'Lightning to USB Cable',
            'USB Power Adapter',
            'Documentation']:
        template = ProductTemplate(
            name=component,
            default_uom=uom_unit,
            list_price=Decimal('0'),
            cost_price=Decimal('5'),
        )
        input_product = Product(
            template=template
        )
        input_product.save()
        inputs.append(input_product)

    iphone_bom = BOM(
        name=name,
        inputs=[
            BOMInput(
                product=input,
                quantity=1,
                uom=input.default_uom,
            )
            for input in inputs
        ],
        outputs=[
            BOMOutput(
                product=product,
                quantity=1,
                uom=product.default_uom,
            )
        ],
    )
    iphone_bom.save()
    ProductBOM(product=product, bom=iphone_bom).save()
    return iphone_bom


@pytest.fixture()
def plan_period(request, company):
    """
    Return a plan period
    """
    Period = Pool().get('production.plan.period')

    start_date = date.today() + relativedelta(weekday=calendar.MONDAY)
    end_date = date.today() + relativedelta(weekday=calendar.FRIDAY)

    periods = Period.search([
        ('start_date', '=', start_date),
        ('end_date', '=', end_date),
    ])
    if periods:
        return periods[0]

    period = Period(
        start_date=start_date,
        end_date=end_date,
        company=company,
        name='Current Week',
    )
    period.save()
    return period


@pytest.fixture()
def dataset(request, customer, product):
    return {
        'customer': customer,
        'product': product,
    }
