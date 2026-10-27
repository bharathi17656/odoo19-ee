from lxml import etree

from freezegun import freeze_time
from .common import TestMxEdiCommon
from odoo import Command
from odoo.tests import tagged, Form


@tagged('post_install_l10n', 'post_install', '-at_install')
class TestCFDIAccountMove(TestMxEdiCommon):

    @freeze_time('2017-01-01')
    def test_extra_print_items(self):
        invoice = self._create_invoice()
        print_items_before = invoice.get_extra_print_items()
        with self.with_mocked_pac_sign_success():
            invoice._l10n_mx_edi_cfdi_invoice_try_send()
        print_items_after = invoice.get_extra_print_items()
        self.assertEqual(len(print_items_before) + 1, len(print_items_after))

    @freeze_time('2017-01-01')
    def test_get_invoice_legal_documents_cfdi(self):
        invoice_with_cfdi = self._create_invoice()
        invoice_without_cfdi = self._create_invoice()
        with self.with_mocked_pac_sign_success():
            invoice_with_cfdi._l10n_mx_edi_cfdi_invoice_try_send()
        self.assertEqual(invoice_with_cfdi._get_invoice_legal_documents('cfdi'), {
            'filename': invoice_with_cfdi.l10n_mx_edi_cfdi_attachment_id.name,
            'filetype': 'xml',
            'content': invoice_with_cfdi.l10n_mx_edi_cfdi_attachment_id.raw,
        })
        self.assertFalse(invoice_without_cfdi._get_invoice_legal_documents('cfdi'))

    def test_cfdi_origin(self):
        """ Test that the l10n_mx_edi_cfdi_origin field can be set correctly. """
        invoice = self._create_invoice(move_type='out_refund')
        invoice.l10n_mx_edi_cfdi_origin = '01|E19C50D2-1292-5817-BDDE-2666967C7471'
        invoice._l10n_mx_edi_get_refund_original_invoices()
        self.assertEqual(invoice.l10n_mx_edi_cfdi_origin, '01|E19C50D2-1292-5817-BDDE-2666967C7471')

    @freeze_time('2017-01-01')
    def test_invoice_tax_objects_required(self):
        """Test that the invoice can be save, when there is a move line with a total amount of 0 that without its field tax objects set"""
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner_mx.id,
            'currency_id': self.comp_curr.id,
        })
        with Form(invoice) as f:
            with f.invoice_line_ids.new() as line:
                line.price_unit = 0

    def test_invoice_cfdi_uom_translation(self):
        """ The CFDI must use the customer's language, just like the PDF. """
        self.env['res.lang']._activate_lang('es_MX')
        self.product.uom_id.with_context(lang='es_MX').name = 'Piezas'
        self.partner_mx.lang = 'es_MX'

        with self.mx_external_setup(self.frozen_today):
            invoice = self._create_invoice()
            with self.with_mocked_pac_sign_success():
                invoice.with_context(lang=None)._l10n_mx_edi_cfdi_invoice_try_send()

            document = invoice.l10n_mx_edi_invoice_document_ids.filtered(lambda x: x.state == 'invoice_sent')[:1]
            cfdi_node = self.get_xml_tree_from_string(document.attachment_id.raw)
            concepto = cfdi_node.xpath("//*[local-name()='Concepto']")[0]
            self.assertEqual(concepto.get('Unidad'), 'PIEZAS')

    @freeze_time('2017-01-01')
    def test_cfdi_line_name_partner_specific_code_not_duplicated(self):
        """ When a customer has their own product code (product.supplierinfo),
        the invoice line description uses it (e.g. "[CUSTOM-CODE] Product"),
        exactly like on a sale order line. _l10n_mx_edi_get_cfdi_line_name must
        not re-resolve the product's display_name without that customer in
        context, or it would find a different string ("[product_mx] product_mx")
        and prepend it, duplicating the product name in the CFDI Descripcion. """
        self.env['product.supplierinfo'].create({
            'partner_id': self.partner_mx.id,
            'product_tmpl_id': self.product.product_tmpl_id.id,
            'product_code': 'CUSTOM-CODE',
        })
        line_name = self.product.with_context(partner_id=self.partner_mx.id).display_name
        invoice = self._create_invoice(invoice_line_ids=[
            Command.create({'product_id': self.product.id, 'name': line_name}),
        ])
        with self.with_mocked_pac_sign_success():
            invoice._l10n_mx_edi_cfdi_invoice_try_send()
        self.assertEqual(invoice.l10n_mx_edi_cfdi_state, 'sent', f'Error: {invoice.l10n_mx_edi_document_ids.message}')

        xml_tree = self.get_xml_tree_from_string(invoice.l10n_mx_edi_cfdi_attachment_id.raw)
        concepto = xml_tree.xpath("//*[local-name()='Concepto']")[0]
        self.assertEqual(concepto.get('Descripcion'), line_name)

    @freeze_time('2017-01-01')
    def test_cfdi_line_name_standard_code_not_duplicated(self):
        """ An invoice line created without the customer in context keeps the
        product's standard name, even if the customer has their own product
        code: the CFDI Descripcion must not prepend the customer-specific name
        to it. """
        invoice = self._create_invoice(invoice_line_ids=[
            Command.create({'product_id': self.product.id}),
        ])
        line_name = invoice.invoice_line_ids.name
        self.env['product.supplierinfo'].create({
            'partner_id': self.partner_mx.id,
            'product_tmpl_id': self.product.product_tmpl_id.id,
            'product_code': 'CUSTOM-CODE',
        })
        with self.with_mocked_pac_sign_success():
            invoice._l10n_mx_edi_cfdi_invoice_try_send()
        self.assertEqual(invoice.l10n_mx_edi_cfdi_state, 'sent', f'Error: {invoice.l10n_mx_edi_document_ids.message}')

        xml_tree = self.get_xml_tree_from_string(invoice.l10n_mx_edi_cfdi_attachment_id.raw)
        concepto = xml_tree.xpath("//*[local-name()='Concepto']")[0]
        self.assertEqual(concepto.get('Descripcion'), line_name)

    def test_import_cfdi_line_keeps_original_description(self):
        """ Importing a vendor bill's CFDI must preserve the exact text of its
        Descripcion attribute, even one starting with a bracketed note that
        isn't a product code (e.g. "[URGENT] ..."). Leaving 'name' unset on
        the created line would let account.move.line._compute_name overwrite
        it with the matched product's own display_name, silently dropping
        the original text. """
        bill = self.env['account.move'].create({'move_type': 'in_invoice', 'partner_id': self.partner_mx.id})
        line = self.env['account.move.line'].create({'move_id': bill.id, 'company_id': bill.company_id.id})
        concepto = etree.Element('Concepto', {
            'NoIdentificacion': self.product.default_code,
            'ClaveProdServ': self.product.unspsc_code_id.code,
            'Descripcion': f'[URGENT] {self.product.display_name}',
            'Cantidad': '1',
            'ValorUnitario': '100.0',
            'Importe': '100.0',
            'Descuento': '0',
        })
        bill._l10n_mx_edi_import_cfdi_fill_invoice_line(concepto, line)
        self.assertEqual(line.name, f'[URGENT] {self.product.display_name}')
