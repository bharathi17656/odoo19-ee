# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api


class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    partner_company_name = fields.Char(string='Company Name', compute='_compute_partner_company_name', store=True, readonly=False)

    @api.depends('partner_id')
    def _compute_partner_company_name(self):
        for ticket in self:
            ticket.partner_company_name = ticket.partner_id.company_name

    def get_base_url(self):
        return self.team_id.get_base_url()
