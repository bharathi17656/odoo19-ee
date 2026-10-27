# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details

from datetime import timedelta
from odoo import Command, fields
from odoo.addons.industry_fsm_sale.tests.common import TestFsmFlowCommon
from odoo.tests import tagged, HttpCase, new_test_user


@tagged('-at_install', 'post_install')
class TestFsmSaleProducts(HttpCase, TestFsmFlowCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.my_custom_currency = cls.env['res.currency'].create({
            'name': "TK",
            'symbol': '~M~',
        })
        cls.task.write({
            'user_ids': [Command.link(cls.env.ref("base.user_admin").id)],
            'planned_date_begin': fields.Datetime.today() + timedelta(days=1),
            'date_deadline': fields.Datetime.today() + timedelta(days=2),
        })
        cls.consu_product_ordered.is_favorite = True
        cls.my_custom_price_list = cls.env['product.pricelist'].create({
            'name': 'TKPriceList',
            'currency_id': cls.my_custom_currency.id,
            'item_ids': [
                Command.create({
                    'name': 'Reduced 2 Individual Workplace Test',
                    'applied_on': '0_product_variant',
                    'product_id': cls.consu_product_ordered.id,
                    'min_quantity': 1,
                    'fixed_price': '1000',
                }),
                Command.create({
                    'name': 'Reduced 2 Individual Workplace Test',
                    'applied_on': '0_product_variant',
                    'product_id': cls.consu_product_ordered.id,
                    'min_quantity': 2,
                    'fixed_price': '500',
                }),
            ]
        })
        cls.partner_1.property_product_pricelist = cls.my_custom_price_list
        cls.task.partner_id = cls.partner_1

    def test_industry_fsm_sale_products_tour(self):
        self.start_tour("/odoo", 'industry_fsm_sale_products_tour', login="admin")

    def test_industry_fsm_sale_quantity_products_tour(self):
        self.start_tour("/odoo", 'industry_fsm_sale_quantity_products_tour', login="admin")

    def test_industry_fsm_sale_products_from_fsm_tour(self):
        """
        Checks that the catalogs associated to field services tasks generated from the same main SO
        do not share their catalogs.
        """
        self.partner_1.name = "fsm tester"
        admin = self.env.ref('base.user_admin')
        field_service = self.env.ref('industry_fsm_sale.field_service_product')
        main_so = self.env['sale.order'].with_context(default_user_id=admin.id).create({
            'partner_id': self.partner_1.id,
            'order_line': [
                Command.create({
                    'name': 'task 1',
                    'product_id': field_service.id,
                }),
                Command.create({
                    'name': 'task 2',
                    'product_id': field_service.id,
                }),
                Command.create({
                    'name': 'task 3',
                    'product_id': field_service.id,
                }),
            ]
        })
        main_so.action_confirm()
        super_product = self.env['product.product'].create({
                'name': 'Super Product',
                'invoice_policy': 'delivery',
                'list_price': 100.0,
        })
        super_product.product_tmpl_id.is_favorite = True
        self.start_tour("/odoo", 'industry_fsm_sale_products_compute_catalog_tour', login="admin")
        self.assertTrue(main_so.order_line.filtered(lambda sol: 'task 1' in sol.task_id.name and sol.product_id == super_product))
        self.assertTrue(main_so.order_line.filtered(lambda sol: 'task 2' in sol.task_id.name and sol.product_id == super_product))
        self.assertTrue(main_so.order_line.filtered(lambda sol: 'task 3' in sol.task_id.name and sol.product_id == super_product))

    def test_industry_fsm_sale_duplicate_section_tour(self):
        """ Duplicating a section of a confirmed SO should create a task for the duplicated lines. """
        sale_order = self.env['sale.order'].create({
            'partner_id': self.partner_1.id,
            'order_line': [
                Command.create({'display_type': 'line_section', 'name': 'Section'}),
                Command.create({
                    'product_id': self.env['product.product'].create({
                        'name': 'Service Task',
                        'type': 'service',
                        'project_id': self.fsm_project.id,
                        'service_tracking': 'task_global_project',
                    }).id,
                }),
            ],
        })
        sale_order.action_confirm()
        self.start_tour(f"/odoo/sales/{sale_order.id}", 'industry_fsm_sale_duplicate_section_tour', login="admin")
        self.assertEqual(len(sale_order.order_line.task_id), 2)

    def test_sol_sequence(self):
        sale_order = self.env['sale.order'].create({
            'partner_id': self.partner_1.id,
            'order_line': [
                Command.create({
                    'name': '',
                    'product_id': self.env['product.product'].create({
                        'name': 'pet',
                        'type': 'service',
                        'list_price': 100,
                        'service_policy': 'ordered_prepaid',
                        'project_id': self.fsm_project.id,
                        'service_tracking': 'task_global_project',
                    }).id,
                    'product_uom_qty': 1.0,
                }),
                Command.create({
                    'name': '',
                    'product_id': self.consu_product_ordered.id,
                    'product_uom_qty': 1.0,
                }),
            ],
        })
        previous_sale_order_line_ids = sale_order.order_line.ids
        sale_order.action_confirm()
        self.consu_product_delivered.with_context(fsm_task_id=sale_order.order_line.task_id.id).set_fsm_quantity(1)

        self.assertNotIn(
            sale_order.order_line.ids[-1], previous_sale_order_line_ids,
            "The last SOL should be the one that was added after the confirmation of the SO."
        )

    def test_industry_fsm_sale_add_product_on_invoice(self):
        """
        Checks that we can add the products in the draft invoice.
        """
        self.env['product.product'].create({
            'name': 'Sale Product',
            'invoice_policy': 'order',
            'list_price': 100,
            'sale_ok': True,
            'purchase_ok': False,
        })
        sale_order_1 = self.env['sale.order'].create({
            'partner_id': self.partner_1.id,
            'order_line': [
                Command.create({
                    'product_id': self.consu_product_ordered.id,
                    'product_uom_qty': 10,
                })
            ]
        })

        self.task.update({
            'sale_order_id': sale_order_1.id,
        })
        sale_order_1.action_confirm()
        sale_order_1._create_invoices()
        self.start_tour("/odoo/field-service", 'test_industry_fsm_sale_add_product_on_invoice_tour', login="admin")

    def test_catalog_routes_with_restricted_sales_user(self):
        """
        Checks that a "Sales: Own Documents Only" user can open the catalog of a task whose SO
        belongs to another salesperson.
        """
        restricted_user = new_test_user(
            self.env, 'restricted_salesman',
            groups='industry_fsm.group_fsm_user,sales_team.group_sale_salesman',
        )
        sale_order = self.env['sale.order'].create({
            'partner_id': self.partner_1.id,
            'order_line': [Command.create({
                'product_id': self.env['product.product'].create({
                    'name': 'Field Service',
                    'type': 'service',
                    'project_id': self.fsm_project.id,
                    'service_tracking': 'task_global_project',
                }).id,
            })],
        })
        sale_order.action_confirm()
        task = sale_order.order_line.task_id
        task.user_ids = restricted_user
        self.consu_product_ordered.with_context(fsm_task_id=task.id).set_fsm_quantity(2)
        self.assertFalse(sale_order.with_user(restricted_user).has_access('read'))

        self.authenticate(restricted_user.login, restricted_user.login)
        catalog_params = {
            'res_model': 'sale.order',
            'order_id': sale_order.id,
            'child_field': 'order_line',
            'task_id': task.id,
        }
        sections = self.make_jsonrpc_request('/product/catalog/get_sections', catalog_params)
        self.assertEqual(
            [(section['id'], section['line_count']) for section in sections],
            [(False, 2)],
        )
        order_lines_info = self.make_jsonrpc_request('/product/catalog/order_lines_info', {
            **catalog_params,
            'product_ids': self.consu_product_ordered.ids,
            'section_id': False,
        })
        self.assertEqual(order_lines_info[str(self.consu_product_ordered.id)]['quantity'], 2)
