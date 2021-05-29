

from odoo import _, api, exceptions, fields, models

from odoo.exceptions import ValidationError


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"


    cfo_confirm = fields.Boolean(string="CFO Confirm",tracking=True , copy=False)

    chairman_confirm = fields.Boolean(string="Chairman Confirm", tracking=True,copy=False)


    def _track_subtype(self, init_values):
        # OVERRIDE to log a different message when an invoice is paid using SDD.
        self.ensure_one()
        if 'cfo_confirm' in init_values:
            return self.env.ref('chairman_cfo_approve.tracking_cfo_chairman')

        if 'chairman_confirm' in init_values:
            return self.env.ref('chairman_cfo_approve.tracking_cfo_chairman_confirm')
        return super(PurchaseOrder, self)._track_subtype(init_values)


    def button_confirm(self):
        res = super(PurchaseOrder, self).button_confirm()
        if self.amount_total > 250000 and self.amount_total < 500000:
            if not self.cfo_confirm:
                raise ValidationError("Please, Wait CFO Approve")
        if self.amount_total >= 500000:
            if not self.cfo_confirm:
                raise ValidationError("Please, Wait CFO Approve")
            if not self.chairman_confirm:
                raise ValidationError("Please, Wait Chairman Approve")
        return res

