# -*- coding: utf-8 -*-
"""
    tests/test_production_plan.py

    :copyright: (C) 2015 by Openlabs Technologies & Consulting (P) Limited
    :license: BSD, see LICENSE for more details.
"""
import pytest


class TestQuickBooksPayroll:

    @pytest.mark.skipif(True, reason="No views defined yet")
    def test_views(self, install_module):
        "Test all tryton views"

        from trytond.tests.test_tryton import test_view
        test_view('production_plan')

    def test_depends(self, install_module):
        "Test missing depends on fields"

        from trytond.tests.test_tryton import test_depends
        test_depends()
