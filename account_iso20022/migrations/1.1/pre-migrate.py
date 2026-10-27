from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    # The bank statement line list view moved to the bridge module. It won't be
    # auto-installed on update as all its dependencies are already installed.
    env = api.Environment(cr, SUPERUSER_ID, {})
    Module = env['ir.module.module']
    if Module.search_count([('name', '=', 'account_accountant'), ('state', 'in', ('installed', 'to upgrade'))]):
        Module.update_list()  # ensure new module is known.
        Module.search([('name', '=', 'account_iso20022_account_accountant'), ('state', '=', 'uninstalled')]).button_install()
