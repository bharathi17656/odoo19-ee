# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo.http import request, route
from odoo.fields import Domain
from odoo.addons.web_studio.controllers import main

class WebStudioController(main.WebStudioController):

    @route()
    def edit_view(self, view_id, studio_view_arch, operations=None, model=None, context=None):
        action = super().edit_view(view_id, studio_view_arch, operations, model, context)
        model = model or request.env['ir.ui.view'].browse(view_id).model
        worksheet_template_domain = Domain('model_id', '=', model)
        if request.env.context.get('worksheet_template_id'):
            worksheet_template_domain &= Domain('id', '=', request.env.context['worksheet_template_id'])
        worksheet_template_to_change = request.env['worksheet.template'].sudo().search(worksheet_template_domain)
        if worksheet_template_to_change:
            worksheet_template_to_change._generate_qweb_report_template()
        return action
