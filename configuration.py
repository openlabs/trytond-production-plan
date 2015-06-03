# -*- coding: utf-8 -*-
"""
    configuration.py

    :copyright: (c) 2015 by Openlabs Technologies & Consulting (P) Limited
    :license: BSD, see LICENSE for more details.
"""

from trytond.model import fields
from trytond.pool import PoolMeta
from trytond.pyson import Eval

__all__ = ['Configuration']
__metaclass__ = PoolMeta


class Configuration:
    'Production Configuration'
    __name__ = 'production.configuration'

    production_plan_sequence = fields.Property(fields.Many2One(
        'ir.sequence', 'Production Plan Sequence', domain=[(
            'company', 'in', [
                Eval('context', {}).get('company', -1), None
            ]),
            ('code', '=', 'production'),
        ], required=True))
