# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from collections import defaultdict

from odoo import fields, models, api


class ResPartner(models.Model):
    _inherit = 'res.partner'
    pos_orders_amount_due = fields.Float(string="Sum of customers PoS orders's due amount", compute="_compute_pos_orders_amount_due")
    invoices_amount_due = fields.Float(string="Sum of customers's invoice due amount", compute="_compute_invoices_amount_due")

    def _compute_pos_orders_amount_due(self):
        commercial_partner_ids = {p.id: p.commercial_partner_id.id for p in self}
        # Fetch the total sum of 'customer_due_total' grouped by 'commercial_partner_id'
        pos_orders = self.env['pos.order']._read_group(
            domain=[
                ('commercial_partner_id', 'in', set(commercial_partner_ids.values())),
                ('state', 'in', ['paid', 'done'])
            ],
            groupby=['commercial_partner_id'],
            aggregates=['customer_due_total:sum']
        )

        due_map = {order[0].id: order[1] for order in pos_orders}
        for partner in self:
            partner.pos_orders_amount_due = due_map.get(commercial_partner_ids[partner.id], 0.0)

    def _compute_invoices_amount_due(self):
        commercial_partner_ids = {p.id: p.commercial_partner_id.id for p in self}
        # Fetch the sum of 'pos_amount_unsettled' of unpaid invoices grouped by 'commercial_partner_id'
        invoices = self.env['account.move']._read_group(
            domain=[('commercial_partner_id', 'in', set(commercial_partner_ids.values())),
                    ('state', '=', 'posted'),
                    ('payment_state', 'in', ('not_paid', 'partial')),
                    ('move_type', 'in', self.env['account.move'].get_sale_types())],
            groupby=['commercial_partner_id'],
            aggregates=['pos_amount_unsettled:sum']
        )

        due_map = {inv[0].id: inv[1] for inv in invoices}
        for partner in self:
            partner.invoices_amount_due = due_map.get(commercial_partner_ids[partner.id], 0.0)

    def get_total_due(self, config_id):
        self.ensure_one()
        return self._get_total_due_data(config_id)[0]

    def get_all_total_due(self, config_id):
        return self.exists()._get_total_due_data(config_id)

    def _get_total_due_data(self, config_id):
        """ Return the PoS payload of ``self``, with 'total_due' expressed in the
        currency of the given config and including the not yet posted pay later
        payments. Everything is queried for the whole recordset at once. """
        if not self:
            return []

        config = self.env['pos.config'].browse(config_id)
        pos_currency = config.currency_id
        company_currency = self.env.company.currency_id
        date = fields.Date.today()

        pos_orders = self.env['pos.order'].search([
            ('commercial_partner_id', 'in', self.commercial_partner_id.ids), ('state', '=', 'paid'),
            ('session_id.state', '!=', 'closed')])
        # pos.payment.amount is expressed in the currency of its order, so it is
        # converted to the PoS currency instead of the company one.
        total_settled = defaultdict(float)
        for payment in pos_orders.payment_ids.filtered_domain([('payment_method_id.type', '=', 'pay_later')]):
            commercial_partner = payment.pos_order_id.commercial_partner_id
            total_settled[commercial_partner.id] += payment.currency_id._convert(
                payment.amount, pos_currency, self.env.company, date)

        self_sudo = self
        group_pos_user = self.env.ref('point_of_sale.group_pos_user')
        if group_pos_user in self.env.user.all_group_ids:
            self_sudo = self.sudo()  # allow POS users without accounting rights to settle dues

        # total_due comes from the accounting entries, it is in company currency.
        total_due_per_partner = {
            partner.id: (partner.parent_id or partner).total_due
            for partner in self_sudo
        }

        partners_data = {p['id']: p for p in self.env['res.partner']._load_pos_data_read(self, config)}
        due_amounts = []
        for partner in self:
            partner_data = partners_data.get(partner.id)
            if not partner_data:
                continue
            total_due = total_due_per_partner[partner.id]
            if company_currency != pos_currency:
                total_due = company_currency._convert(total_due, pos_currency, self.env.company, date)
            partner_data['total_due'] = total_due + total_settled[partner.commercial_partner_id.id]
            due_amounts.append({
                'res.partner': [partner_data],
            })
        return due_amounts

    def get_matching_paylater_orders(self):
        self.ensure_one()

        pay_later_refund_orders = self.env["pos.order"].search([
            ("commercial_partner_id", "=", self.id),
            ("state", "in", ["paid", "done"]),
        ]).filtered(
            lambda o: (
                o.refunded_order_id
                and any(
                    p.payment_method_id.type == "pay_later"
                    for p in o.payment_ids
                )
            )
        )

        original_orders = pay_later_refund_orders.mapped("refunded_order_id").filtered(lambda o: o.state in ["paid", "done"])

        orders_matched = []
        for order in original_orders:
            refund_orders = pay_later_refund_orders.filtered(lambda o: o.refunded_order_id.id == order.id)

            original_pay_later_amount = sum(order.payment_ids.filtered(lambda p: p.payment_method_id.type == "pay_later").mapped("amount"))
            refund_pay_later_amount = sum(refund_orders.mapped("payment_ids").filtered(lambda p: p.payment_method_id.type == "pay_later").mapped("amount"))

            if order.currency_id.is_zero(original_pay_later_amount + refund_pay_later_amount):
                orders_matched += order.ids + refund_orders.ids

        return orders_matched

    @api.model
    def _load_pos_data_fields(self, config):
        params = super()._load_pos_data_fields(config)
        if self.env.user.has_group('account.group_account_readonly') or self.env.user.has_group('account.group_account_invoice'):
            params += ['credit_limit', 'total_due', 'use_partner_credit_limit', 'pos_orders_amount_due', 'invoices_amount_due', 'commercial_partner_id']
        return params

    @api.model
    def _load_pos_data_read(self, records, config):
        read_records = super()._load_pos_data_read(records, config)

        if config.currency_id != self.env.company.currency_id and (self.env.user.has_group('account.group_account_readonly') or self.env.user.has_group('account.group_account_invoice')):
            for record in read_records:
                record['total_due'] = self.env.company.currency_id._convert(record['total_due'], config.currency_id, self.env.company, fields.Date.today())
        return read_records

    def _compute_has_moves(self):
        super()._compute_has_moves()
        for partner in self.filtered(lambda p: not p.has_moves):
            partner.has_moves = partner.total_due != 0
