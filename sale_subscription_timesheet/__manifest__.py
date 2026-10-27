# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'Project Sales Subscription Timesheet',
    'version': '1.0',
    'category': 'Services/sales/subscriptions',
    'summary': 'Project sales subscriptions',
    'description': 'Bridge created to add computation of timesheet to subscription',
    'depends': ['project_sale_subscription', 'sale_timesheet'],
    'data': ['views/sale_subscription_portal_timesheet_templates.xml'],
    'installable': True,
    'auto_install': True,
    'author': 'Odoo S.A.',
    'license': 'OEEL-1',
}
