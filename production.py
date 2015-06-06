# -*- coding: utf-8 -*-
"""
    production.py

    :copyright: (c) 2015 by Openlabs Technologies & Consulting (P) Limited
    :license: BSD, see LICENSE for more details.
"""
import calendar

from trytond.pool import Pool, PoolMeta
from trytond.model import ModelSQL, ModelView, Workflow, fields
from trytond.pyson import Eval, Bool
from trytond.transaction import Transaction
from trytond.wizard import Wizard, \
    StateView, Button, StateTransition, StateAction

__metaclass__ = PoolMeta
__all__ = [
    'ProductionPlanPeriod', 'ProductionPlanPeriodStart',
    'ProductionPlanPeriodWizard', 'ProductionPlan',
    'ProductionPlanLine', 'Production'
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
        # TODO: v2.0 Implement more frequency options
        assert frequency == 'weekly', "Only weekly periods are implemented"

        # TODO: v1.0 Implement friendly error messages
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
        'production.plan.period', 'Period', required=True, select=True,
        states={
            'readonly': Eval('state') != 'draft',
        },
        depends=['state'])
    company = fields.Many2One(
        'company.company', 'Company', required=True,
        states={
            'readonly': Eval('state') != 'draft',
        },
        depends=['state'])
    warehouse = fields.Many2One(
        'stock.location', 'Warehouse', required=True,
        domain=[
            ('type', '=', 'warehouse'),
        ],
        states={
            'readonly': Eval('state') != 'draft',
        },
        depends=['state'])
    product = fields.Many2One(
        'product.product', 'Product',
        domain=[
            ('type', '!=', 'service'),
        ],
        states={
            'readonly': Eval('state') != 'draft',
        }, required=True)
    bom = fields.Many2One(
        'production.bom', 'BOM',
        domain=[
            ('output_products', '=', Eval('product', 0)),
        ],
        states={
            'readonly': Eval('state') != 'draft'
        }, depends=['product'], required=True)
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
            'readonly': Eval('state') != 'draft',
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
            'readonly': Eval('state') != 'draft',
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
    lines = fields.One2Many(
        'production.plan.line', 'plan', 'Lines',
        depends=['warehouse'],
        context={'warehouse': Eval('warehouse')}
    )

    @fields.depends('product')
    def on_change_product(self):
        res = {}
        if self.product:
            res['uom'] = self.product.default_uom.id
        return res

    @fields.depends('uom')
    def on_change_with_unit_digits(self, name=None):
        if self.uom:
            return self.uom.digits
        return 2

    @fields.depends('product')
    def on_change_with_uom_category(self, name=None):
        if self.product:
            return self.product.default_uom.category.id

    @classmethod
    def __setup__(cls):
        super(ProductionPlan, cls).__setup__()
        cls._transitions |= set((
            ('draft', 'plan'),
            ('draft', 'cancel'),
            ('plan', 'draft'),
            ('plan', 'running'),
            ('plan', 'cancel'),
            ('running', 'done'),
            ('running', 'cancel'),
            ('cancel', 'draft'),
        ))
        cls._buttons.update({
            'plan': {
                'invisible': ~Eval('state').in_(['draft']),
            },
            'draft': {
                'invisible': ~Eval('state').in_(['plan', 'cancel']),
            },
            'cancel': {
                'invisible': ~Eval('state').in_(['plan', 'running', 'draft']),
            },
            'running': {
                'invisible': ~Eval('state').in_(['plan']),
            },
            'done': {
                'invisible': ~Eval('state').in_(['running']),
            },
        })

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

    @classmethod
    @ModelView.button
    @Workflow.transition('cancel')
    def cancel(cls, productions):
        pass

    @classmethod
    @ModelView.button
    @Workflow.transition('draft')
    def draft(cls, productions):
        pass

    @classmethod
    @ModelView.button
    @Workflow.transition('running')
    def running(cls, productions):
        pass

    @classmethod
    @Workflow.transition('plan')
    def plan(cls, productions):
        for production in productions:
            production.generate_lines()

    @classmethod
    @ModelView.button
    @Workflow.transition('done')
    def done(cls, productions):
        pass

    def generate_lines(self):
        """
        Look into the BOM and iteratively create a BOM
        """
        PlanLine = Pool().get('production.plan.line')

        lines = []

        def add_bom_to_lines(bom, product, quantity, uom):
            """
            :param bom: The bom to add to plan
            :param product: The output product why this bom is needed
            :param quantity: The quantity of output needed
            :param uom: The uom of the output quantity
            """
            factor = bom.compute_factor(product, quantity or 0, uom)

            for output in bom.outputs:
                if output.product == product:
                    break
            else:
                # TODO: Make error more descriptive
                self.raise_user_error('output_not_in_bom')

            quantity = output.compute_quantity(factor)
            lines.append(PlanLine(
                warehouse=self.warehouse,
                quantity_needed=quantity,
                quantity_planned=quantity,
                product=output.product,
                bom=bom,
                plan=self,
            ))

            # Find any input that may need a nested production order.
            # The check is if it has a BOM.
            for input_ in bom.inputs:
                if input_.product.boms:
                    add_bom_to_lines(
                        input_.product.boms[0].bom,
                        input_.product,
                        input_.compute_quantity(factor),
                        input_.uom,
                    )

        # Start with the current BOM
        add_bom_to_lines(self.bom, self.product, self.quantity, self.uom)

        for index, line in enumerate(lines[::-1], 1):
            # Reverse the lines and apply a sequence
            line.sequence = index * 10

        self.lines = lines
        self.save()


class ProductionPlanLine(ModelSQL, ModelView):
    """Production Plan Line"""
    __name__ = 'production.plan.line'

    planned_date = fields.Date('Planned Date')
    warehouse = fields.Many2One('stock.location', 'Warehouse', domain=[
        ('type', '=', 'warehouse'),
    ], required=True)
    quantity_available = fields.Function(
        fields.Float('Quantity Available'), 'get_quantity_available'
    )
    quantity_needed = fields.Float('Quantity Needed', readonly=True)
    quantity_planned = fields.Float('Quantity Planned')
    quantity_wip = fields.Function(
        fields.Float('Quantity In Progress'), 'get_quantity_wip'
    )
    quantity_done = fields.Function(
        fields.Float('Quantity Done'), 'get_quantity_done'
    )
    bom = fields.Many2One('production.bom', 'BOM', domain=[
        ('output_products', '=', Eval('product', 0)),
    ], depends=['product'], required=True)
    product = fields.Many2One('product.product', 'Product', required=True)
    plan = fields.Many2One('production.plan', 'Plan')
    sequence = fields.Integer('Sequence', required=True, select=True)
    orders = fields.One2Many('production', 'production_plan_line', 'Orders')

    @classmethod
    def __setup__(cls):
        super(ProductionPlanLine, cls).__setup__()
        cls._order.insert(0, ('sequence', 'ASC'))

    # TODO: Build code for function fields
    def get_quantity_available(self, name):
        pass

    def get_quantity_wip(self, name):
        pass

    def get_quantity_done(self, name):
        pass

    @staticmethod
    def default_warehouse():
        return Transaction().context.get('warehouse')


class Production:
    "Production"
    __name__ = 'production'

    production_plan_line = fields.Many2One(
        'production.plan.line', 'Production Plan Line')
