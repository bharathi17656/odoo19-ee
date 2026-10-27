# Part of Odoo. See LICENSE file for full copyright and licensing details.
from werkzeug.urls import url_encode

from odoo import api, fields, models


class AppointmentInvite(models.Model):
    _inherit = 'appointment.invite'

    def _get_url_params(self):
        applicant_code = self.env.context.get('applicant_code')
        return {
            **super()._get_url_params(),
            **({'applicant_code': applicant_code} if applicant_code else {})
        }

    @api.depends_context('applicant_code')
    def _compute_book_url_params(self):
        return super()._compute_book_url_params()

    @api.depends_context('applicant_code')
    def _compute_base_book_url(self):
        return super()._compute_base_book_url()

    def get_base_url(self):
        if applicant_code := self.env.context.get('applicant_code'):
            applicant_sudo = self.env['hr.applicant'].sudo().search([
                ('interview_invite_code', '=', applicant_code)
            ], limit=1)
            if applicant_sudo:
                base_url = applicant_sudo.job_id.get_base_url()
                return base_url
        return super().get_base_url()
