# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import date
from odoo import Command
from odoo.tests import tagged
from .common import TestLuPayrollCommon


@tagged('post_install_l10n', 'post_install', '-at_install')
class TestLuPayrollIndexation(TestLuPayrollCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.rule_parameter_index = cls.env.ref('l10n_lu_hr_payroll.rule_parameter_lu_index')

        # Helper to overwrite original data (to ensure deterministic test values)
        def _set_parameter_value(date_from, value):
            existing_value = cls.env['hr.rule.parameter.value'].search([
                ('rule_parameter_id', '=', cls.rule_parameter_index.id),
                ('date_from', '=', date_from),
            ], limit=1)

            if existing_value:
                existing_value.write({'parameter_value': str(value)})
            else:
                cls.env['hr.rule.parameter.value'].create({
                    'rule_parameter_id': cls.rule_parameter_index.id,
                    'date_from': date_from,
                    'parameter_value': str(value),
                })

        cls.env['hr.rule.parameter.value'].search([
            ('rule_parameter_id', '=', cls.rule_parameter_index.id),
        ]).unlink()

        _set_parameter_value('2023-09-01', '944.43')
        _set_parameter_value('2025-05-01', '968.04')
        _set_parameter_value('2026-08-01', '1000.00')

        cls.employee_frida = cls.env['hr.employee'].create({
            'name': 'Frida Poirish',
            'private_country_id': cls.env.ref('base.lu').id,
            'company_id': cls.lux_company.id,
            'identification_id': 123456789,
        })

        cls.version_frida = cls.env['hr.version'].create({
            'name': 'Contract Frida',
            'employee_id': cls.employee_frida.id,
            'company_id': cls.lux_company.id,
            'structure_type_id': cls.env.ref('l10n_lu_hr_payroll.structure_type_employee_lux').id,
            'contract_date_start': '2024-01-01',
            'date_version': '2024-01-01',
            'wage': 5000.0,
            'l10n_lu_tax_classification': '1',
        })

    def test_payslip_indexation_monthly_salary(self):
        """
        Verify that a payslip evaluated for December 2025 uses the active index in December (968.04)
        and NOT the latest global index present in DB (1000.00 effective from August 2026).
        """
        self.version_frida.generate_work_entries(date(2025, 12, 1), date(2025, 12, 31))

        payslip = self.env['hr.payslip'].create({
            'name': 'Payslip December 2025',
            'employee_id': self.employee_frida.id,
            'version_id': self.version_frida.id,
            'date_from': '2025-12-01',
            'date_to': '2025-12-31',
            'struct_id': self.env.ref('l10n_lu_hr_payroll.hr_payroll_structure_lux_employee_salary').id,
        })
        payslip.compute_sheet()

        # The basic salary in December should be 5000 * (968.04 / 944.43) = 5125.00 EUR
        basic_line = payslip.line_ids.filtered(lambda l: l.code == 'BASIC')
        self.assertEqual(len(basic_line), 1)
        self.assertAlmostEqual(basic_line.total, 5125.00, places=2)

    def test_payslip_indexation_gratification(self):
        """
        Verify that Gratification structure preserves manual BASIC input
        while non-period tax uses the indexed annual wage at date_to (index 1000.00 in Sept 2026).
        """
        self.version_frida.generate_work_entries(date(2026, 9, 1), date(2026, 9, 30))

        payslip = self.env['hr.payslip'].create({
            'name': 'Gratification September 2026',
            'employee_id': self.employee_frida.id,
            'version_id': self.version_frida.id,
            'date_from': '2026-09-01',
            'date_to': '2026-09-30',
            'struct_id': self.env.ref('l10n_lu_hr_payroll.hr_payroll_structure_lux_employee_gratification').id,
            'input_line_ids': [Command.create({
                'input_type_id': self.env.ref('l10n_lu_hr_payroll.input_gratification').id,
                'amount': 5000.0,
            })],
        })
        payslip.compute_sheet()

        # BASIC line must match the manual input
        basic_line = payslip.line_ids.filtered(lambda l: l.code == 'BASIC')
        self.assertEqual(len(basic_line), 1)
        self.assertEqual(basic_line.total, 5000.00)

        # Non-period tax calculated based on September 2026 indexed wage (5294.20 * 12)
        tax_line = payslip.line_ids.filtered(lambda l: l.code == 'TAX_ON_NON_PERIOD_REVENUE')
        self.assertEqual(len(tax_line), 1)
        self.assertAlmostEqual(tax_line.total, -1752.00, places=2)
