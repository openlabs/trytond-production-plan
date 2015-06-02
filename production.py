# -*- coding: utf-8 -*-
"""
    production.py

    :copyright: (c) 2015 by Openlabs Technologies & Consulting (P) Limited
    :license: BSD, see LICENSE for more details.
"""
import calendar

from trytond.pool import Pool
from trytond.model import ModelSQL, ModelView, Workflow, fields
from trytond.pyson import Eval, Bool
from trytond.transaction import Transaction
from trytond.wizard import Wizard, \
    StateView, Button, StateTransition, StateAction

__all__ = [
    'ProductionPlanPeriod', 'ProductionPlanPeriodStart',
    'ProductionPlanPeriodWizard', 'ProductionPlan',
]


class ProductionPlanPeriod(ModelSQL, ModelView):
    "Production Plan Period"
    __name__ = 'production.plan.period'

    company = fields.Many2One(
        'company.company', 'Company', required=True, select=True
    )
    start_date = fields.Date('Start Date', required=True, select=True)
    end_date = fields.Date('End Date', required=True, select=True)
    name = fields.Char('Name', required=True)

    @classmethod
    def create_periods(cls, start_date, end_date, frequency):
        """
        Create and return production plan periods for the above
        date range divided over the frequency.
        """
        # TODO: Implement more frequency options
        assert frequency == 'weekly', "Only weekly periods are implemented"

        if start_date.weekday() != calendar.MONDAY:
            cls.raise_user_error('weekly_must_start_with_monday')
        if end_date.weekday() != calendar.FRIDAY:
            cls.raise_user_error('weekly_must_end_with_monday')

        # XXX: for each frequency period in the date range, create
        # a period.


class ProductionPlanPeriodStart(ModelView):
    'Production Plan Period'
    __name__ = 'production.plan.period.start'

    start_date = fields.Date('Start Date', required=True, select=True)
    end_date = fields.Date('End Date', required=True, select=True)
    frequency = fields.Selection([
        ('weekly', 'Weekly'),
    ], 'Frequency', required=True)


class ProductionPlanPeriodWizard(Wizard):
    "Production Plan Period"
    __name__ = 'production.plan.period.wizard'

    start = StateTransition()
    ask = StateView(
        'production.plan.period.start',
        'production_plan.production_plan_period_view_form', [
            Button('Cancel', 'end', 'tryton-cancel'),
            Button('Open', 'open_', 'tryton-ok', default=True),
        ]
    )
    open_ = StateAction('production_plan.act_plan_period_form')

    def transition_start(self):
        if(Transaction().context.get('active_model', '')
                == 'production.plan.period'
                and Transaction().context.get('active_id')):
            return 'open_'
        return 'ask'


class ProductionPlan(Workflow, ModelSQL, ModelView):
    "Production Plan"
    __name__ = 'production.plan'

    _rec_name = 'code'

    code = fields.Char('Code', select=True, readonly=True)
    period = fields.Many2One(
        'production.plan.period', 'Period', required=True, select=True
    )
    company = fields.Many2One(
        'company.company', 'Company', required=True,
        states={
            'readonly': ~Eval('state').in_(['request', 'draft']),
        },
        depends=['state'])
    warehouse = fields.Many2One(
        'stock.location', 'Warehouse', required=True,
        domain=[
            ('type', '=', 'warehouse'),
        ],
        states={
            'readonly': (
                ~Eval('state').in_(['request', 'draft'])
                | Eval('inputs', True) | Eval('outputs', True)
            ),
        },
        depends=['state'])
    product = fields.Many2One(
        'product.product', 'Product',
        domain=[
            ('type', '!=', 'service'),
        ],
        states={
            'readonly': ~Eval('state').in_(['request', 'draft']),
        })
    bom = fields.Many2One(
        'production.bom', 'BOM',
        domain=[
            ('output_products', '=', Eval('product', 0)),
        ],
        states={
            'readonly': (
                ~Eval('state').in_(['request', 'draft'])
                | ~Eval('warehouse', 0) | ~Eval('location', 0)
            ),
            'invisible': ~Eval('product'),
        },
        depends=['product'])
    uom_category = fields.Function(
        fields.Many2One('product.uom.category', 'Uom Category'),
        'on_change_with_uom_category'
    )
    uom = fields.Many2One(
        'product.uom', 'Uom',
        domain=[
            ('category', '=', Eval('uom_category')),
        ],
        states={
            'readonly': ~Eval('state').in_(['request', 'draft']),
            'required': Bool(Eval('bom')),
            'invisible': ~Eval('product'),
        },
        depends=['uom_category'])
    unit_digits = fields.Function(
        fields.Integer('Unit Digits'), 'on_change_with_unit_digits'
    )
    quantity = fields.Float(
        'Quantity',
        digits=(16, Eval('unit_digits', 2)),
        states={
            'readonly': ~Eval('state').in_(['request', 'draft']),
            'required': Bool(Eval('bom')),
            'invisible': ~Eval('product'),
        },
        depends=['unit_digits'])
    state = fields.Selection([
        ('draft', 'Draft'),
        ('plan', 'Plan'),
        ('running', 'Running'),
        ('cancel', 'Canceled'),
        ('done', 'Done'),
    ], 'State', readonly=True)

    @staticmethod
    def default_state():
        return 'draft'

    @classmethod
    def default_warehouse(cls):
        Location = Pool().get('stock.location')
        locations = Location.search(cls.warehouse.domain)
        if len(locations) == 1:
            return locations[0].id

    @staticmethod
    def default_company():
        return Transaction().context.get('company')

    @classmethod
    def create(cls, vlist):
        Sequence = Pool().get('ir.sequence')
        Config = Pool().get('production.configuration')

        vlist = [x.copy() for x in vlist]
        config = Config(1)
        for values in vlist:
            values['code'] = Sequence.get_id(config.production_plan_sequence.id)
        productions = super(ProductionPlan, cls).create(vlist)
        return productions
