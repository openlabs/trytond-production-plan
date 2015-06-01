# -*- coding: utf-8 -*-
"""
    __init__.py

    :copyright: (c) 2015 by Openlabs Technologies & Consulting (P) Limited
    :license: BSD, see LICENSE for more details.
"""
from trytond.pool import Pool
from production import ProductionPlanPeriod, ProductionPlanPeriodStart, \
    ProductionPlanPeriodWizard


def register():
    Pool.register(
        ProductionPlanPeriod,
        ProductionPlanPeriodStart,
        module='production_plan', type_='model'
    )

    Pool.register(
        ProductionPlanPeriodWizard,
        module='production_plan', type_='wizard'
    )
