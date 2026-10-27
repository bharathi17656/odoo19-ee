# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime

from odoo.tests import TransactionCase, tagged


@tagged('post_install_l10n', 'post_install', '-at_install')
class TestResourceCalendar(TransactionCase):

    def test_flexible_calendar_work_intervals(self):
        """Test that the work hours of a flexible calendar are not emptied in a HK company."""
        company_hk = self.env['res.company'].create({
            'name': 'HK Co',
            'country_id': self.env.ref('base.hk').id,
        })
        flexible_calendar = self.env['resource.calendar'].create({
            'name': 'Flexible 40 hours/week',
            'company_id': company_hk.id,
            'tz': 'UTC',
            'flexible_hours': True,
            'hours_per_day': 8,
            'hours_per_week': 40,
        })

        # Monday to Sunday
        work_hours = flexible_calendar.get_work_hours_count(datetime(2025, 1, 6), datetime(2025, 1, 13))
        self.assertEqual(work_hours, 40)
