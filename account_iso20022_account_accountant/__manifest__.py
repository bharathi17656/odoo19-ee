{
        'name': "SEPA Credit Transfer / ISO20022 Invoicing",
        'summary': """Bridge module for account_iso20022 and account_accountant""",
        'description': """
        Bridge module for account_iso20022 and account_accountant
        """,
        'category': 'Accounting/Accounting',
        'depends': ['account_iso20022', 'account_accountant'],
        'auto_install': True,
        'pre_init_hook': '_pre_init_account_iso20022_account_accountant',
        'author': 'Odoo S.A.',
        'license': 'OEEL-1',
        'data': [
            'views/account_bank_statement_line_views.xml',
        ]
}
