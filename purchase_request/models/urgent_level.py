
from odoo import models,fields,api,_


class UrgentLevel(models.Model):
    _name = "urgent.level"
    _rec_name = 'name'

    name = fields.Char('Name', required=True)

