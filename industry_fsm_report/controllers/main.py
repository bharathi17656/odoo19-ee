# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo.http import route
from odoo.addons.web_studio.controllers import main

class WebStudioController(main.WebStudioController):
    @route()
    def edit_view(self, view_id, studio_view_arch, operations=None, model=None, context=None):
        return super().edit_view(view_id, studio_view_arch, operations, model, context)
