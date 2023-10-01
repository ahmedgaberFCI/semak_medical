# -*- coding: utf-8 -*-

from odoo import fields, models, api,SUPERUSER_ID
from lxml import etree


class Users(models.Model):
    _inherit = 'res.users'


    new_journal_ids = fields.Many2many(
        'account.journal',
        'new_users_journals_restrict',
        'user_id',
        'journal_id',
        'Allowed Journals',
    )

class AccountMove(models.Model):
    _inherit = 'account.move'


    def fields_view_get(self, view_id=None, view_type='tree', toolbar=False, submenu=False):



        res = super(AccountMove, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=False)

        # group_id = self.env.user.has_group('account.group_account_user')
        group_id = self.env.user.has_group('product_journal_restrict.journal_enteries_restriction_group')

        doc = etree.XML(res['arch'])

        # if group_id and self.env.uid != 2:
        if group_id and not self.env.user.has_group('base.group_system') and self.env.uid != SUPERUSER_ID:

            if view_type == 'tree' or view_type == 'form' :

                nodes_tree = doc.xpath("//tree[@string='Journal Entries']")

                for node in nodes_tree:
                    node.set('create', '0')

                nodes_form = doc.xpath("//form[@string='Account Entry']")

                for node in nodes_form:
                    node.set('create', '0')
                    node.set('edit', '0')


                res['arch'] = etree.tostring(doc)

        return res
