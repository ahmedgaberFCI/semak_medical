
from odoo import models,fields,api,_


class PurchaseTypes(models.Model):
    _name = "purchase.types"
    _rec_name = 'name'

    name = fields.Char('Name', required=True)

    checked= fields.Boolean(string="Checked")
    mps_checked= fields.Boolean(string="MPS Checked")

    budget_controller = fields.Boolean(string="Budget Controller")


