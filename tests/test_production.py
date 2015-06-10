# -*- coding: utf-8 -*-
"""
    tests/test_views_depends.py

    :copyright: (C) 2015 by Openlabs Technologies & Consulting (P) Limited
    :license: BSD, see LICENSE for more details.
"""
from decimal import Decimal
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

    def test_line_generation(self, bom, plan_period, company):
        """
        Get the BOM and add a layer of nesting into it and check if the
        BOM generation of lines work.

        - iPhone 5s
          |- iPhone 5s with iOS 8
          |- Apple EarPods with Remote and Mic
          |  |- Earpod
          |  |   |- Headphone
          |  |   |- Mic
          |  |- Clear Case Cover
          |  |- White base cover
          |- Lightning to USB Cable
          |- USB Power Adapter
          |- Documentation
        """
        BOM = Pool().get('production.bom')
        BOMInput = Pool().get('production.bom.input')
        BOMOutput = Pool().get('production.bom.output')
        ProductionPlan = Pool().get('production.plan')
        ProductTemplate = Pool().get('product.template')
        ProductBOM = Pool().get('product.product-production.bom')
        Product = Pool().get('product.product')
        Uom = Pool().get('product.uom')

        uom_unit, = Uom.search([('symbol', '=', 'u')])

        # Create all the none-existant products
        products = {}.fromkeys([
            'mic', 'headphone',
            'earpod', 'clear-case-cover', 'white-base-cover'
        ])
        for component in products.keys():
            products[component] = Product(
                template=ProductTemplate(
                    name=component,
                    default_uom=uom_unit,
                    list_price=Decimal('0'),
                    cost_price=Decimal('5'),
                ),
            )
            products[component].save()

        # Make the two BOMs which don't exist
        earpod_bom = BOM(
            name='Earpod',
            inputs=[
                BOMInput(
                    product=products['headphone'],
                    quantity=2,
                    uom=products['headphone'].default_uom,
                ),
                BOMInput(
                    product=products['mic'],
                    quantity=1,
                    uom=products['mic'].default_uom,
                ),
            ],
            outputs=[
                BOMOutput(
                    product=products['earpod'],
                    quantity=1,
                    uom=products['earpod'].default_uom,
                )
            ],
        )
        earpod_bom.save()
        ProductBOM(product=products['earpod'], bom=earpod_bom).save()

        apple_earpod_with_mic, = Product.search([
            ('name', '=', 'Apple EarPods with Remote and Mic')
        ])
        apple_earpod_boxed_bom = BOM(
            name='Apple EarPods with Remote and Mic',
            inputs=[
                BOMInput(
                    product=products['earpod'],
                    quantity=2,
                    uom=products['earpod'].default_uom,
                ),
                BOMInput(
                    product=products['clear-case-cover'],
                    quantity=1,
                    uom=products['clear-case-cover'].default_uom,
                ),
                BOMInput(
                    product=products['white-base-cover'],
                    quantity=1,
                    uom=products['white-base-cover'].default_uom,
                ),
            ],
            outputs=[
                BOMOutput(
                    product=apple_earpod_with_mic,
                    quantity=1,
                    uom=apple_earpod_with_mic.default_uom,
                )
            ],
        )
        apple_earpod_boxed_bom.save()
        ProductBOM(
            product=apple_earpod_with_mic,
            bom=apple_earpod_boxed_bom
        ).save()

        # Now create a production plan for iPhone
        plan = ProductionPlan(
            period=plan_period,
            product=bom.outputs[0].product,
            bom=bom,
            company=company,
            quantity=1,
            uom=bom.outputs[0].uom,
        )
        plan.save()

        # Generate the lines
        plan.generate_lines()

        # There should be 3 lines
        #
        # 1. Earpod - 2 qty
        # 2. Apple EarPods with Remote and Mic - 1 qty
        # 3. iPhone 5s - 1 qty
        assert len(plan.lines) == 3

        for line in plan.lines:
            if line.product == bom.outputs[0].product:
                assert line.quantity_needed == 1
            elif line.product == apple_earpod_with_mic:
                assert line.quantity_needed == 1
            elif line.product == products['earpod']:
                assert line.quantity_needed == 2

    def test_logic_for_buttons(self, company, plan_period, product, bom):
        '''
        Test if logic is implemented for plan and run button in production plan
        '''
        from trytond.transaction import Transaction

        Group = Pool().get('res.group')
        ProductionPlan = Pool().get('production.plan')
        Location = Pool().get('stock.location')
        User = Pool().get('res.user')
        Production = Pool().get('production')
        PlanLine = Pool().get('production.plan.line')

        with Transaction().set_context(company=company):
            user_group1, = Group.search([
                ('name', '=', 'Production Administration'),
            ])
            user1, = User.create([{
                'name': 'Test User',
                'login': 'test@domain.com',
                'password': 'password',
                'groups': [('add', [user_group1.id])],
            }])
            with Transaction().set_user(user1.id):

                warehouse, = Location.search([
                    ('type', '=', 'warehouse')
                    ], limit=1)

                plan = ProductionPlan(
                    period=plan_period,
                    company=company,
                    warehouse=warehouse,
                    product=product,
                    uom=product.default_uom,
                    bom=bom,
                    quantity=Decimal('1'),
                )
                plan.save()
                assert len(PlanLine.search([])) == 0

                ProductionPlan.plan([plan])
                assert len(PlanLine.search([])) == 1

                ProductionPlan.running([plan])
                assert len(Production.search([])) == 1
