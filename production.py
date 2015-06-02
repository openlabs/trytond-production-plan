# -*- coding: utf-8 -*-
"""
    production.py

    :copyright: (c) 2015 by Openlabs Technologies & Consulting (P) Limited
    :license: BSD, see LICENSE for more details.
"""

from trytond.model import ModelSQL, ModelView, fields
from trytond.transaction import Transaction
from trytond.wizard import Wizard, \
    StateView, Button, StateTransition, StateAction

__all__ = ['ProductionPlanPeriod', 'ProductionPlanPeriodStart',
    'ProductionPlanPeriodWizard']


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
