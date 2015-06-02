# -*- coding: utf-8 -*-
"""
    tests/test_views_depends.py

    :copyright: (C) 2015 by Openlabs Technologies & Consulting (P) Limited
    :license: BSD, see LICENSE for more details.
"""


class TestViewsDepends:
    '''
    Test views and depends
    '''

    def test0005views(self):
        '''
        Test views.
        '''
        from trytond.tests.test_tryton import test_view
        test_view('production_plan')

    def test0006depends(self):
        '''
        Test depends.
        '''
        from trytond.tests.test_tryton import test_depends
        test_depends()
