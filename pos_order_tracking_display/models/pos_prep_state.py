from odoo import models


class PosPreparationState(models.Model):
    _inherit = 'pos.prep.state'

    def change_state_stage(self, stages, prep_display_id):
        res = super().change_state_stage(stages, prep_display_id)
        self.env['pos.prep.display'].browse(int(prep_display_id))._send_orders_to_customer_display()
        return res

    def change_state_status(self, todos, prep_display_id):
        res = super().change_state_status(todos, prep_display_id)
        # When lines are marked done (todo=False) in the last stage, the order must be
        # removed from the "Ready" section of the Customer Order Status screen.
        self.env['pos.prep.display'].browse(int(prep_display_id))._send_orders_to_customer_display()
        return res
