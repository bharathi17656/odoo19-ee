# Part of Odoo. See LICENSE file for full copyright and licensing details.


def _pre_init_account_iso20022_account_accountant(env):
    # The statement line list view used to live in account_iso20022. Take over its
    # record so loading our data updates it instead of adding a duplicate column.
    env.cr.execute(
        """
        UPDATE ir_model_data
           SET module = 'account_iso20022_account_accountant'
         WHERE module = 'account_iso20022'
           AND name = 'account_bank_statement_line_view_list_inherit'
        """
    )
