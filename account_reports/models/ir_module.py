import datetime
from dateutil.relativedelta import relativedelta
from odoo import models


class IrModuleModule(models.Model):
    _inherit = "ir.module.module"

    def _load_module_terms(self, modules, langs, overwrite=False):
        super()._load_module_terms(modules, langs, overwrite=overwrite)
        if not langs or langs == ['en_US'] or not modules or 'account_reports' not in modules:
            return

        for lang in langs:
            # sudo: installing a language is a system operation, the user triggering it is not
            # required to have accounting access to get the return names translated.
            self.env['account.return'].sudo().search([
                ('date_to', '>=', datetime.date.today() - relativedelta(years=1),
            )]).with_context({'update_returns_translation_lang': lang})._update_translated_name()
