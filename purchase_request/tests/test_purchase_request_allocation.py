# Copyright 2018-2019 ForgeFlow, S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)

from odoo.tests import common
from odoo.tools import SUPERUSER_ID


class TestPurchaseRequestToRfq(common.TransactionCase):
    def setUp(self):
        super(TestPurchaseRequestToRfq, self).setUp()
        self.purchase_request = self.env["purchase.request"]
        self.purchase_request_line = self.env["purchase.request.line"]
        self.wiz = self.env["purchase.request.line.make.purchase.order"].sudo()
        self.purchase_order = self.env["purchase.order"]
        vendor = self.env["res.partner"].create({"name": "Partner #2"})
        self.service_product = self.env["product.product"].create(
            {"name": "Product Service Test", "type": "service"}
        )
        self.product_product = self.env["product.product"].create(
            {
                "name": "Product Product Test",
                "type": "product",
                "description_purchase": "Test Description",
            }
        )
        self.env["product.supplierinfo"].create(
            {
                "name": vendor.id,
                "product_tmpl_id": self.service_product.product_tmpl_id.id,
            }
        )
        self.env["product.supplierinfo"].create(
            {
                "name": vendor.id,
                "product_tmpl_id": self.product_product.product_tmpl_id.id,
            }
        )

    def test_purchase_request_allocation(self):
        vals = {
            "picking_type_id": self.env.ref("stock.picking_type_in").id,
            "requested_by": SUPERUSER_ID,
        }
        purchase_request1 = self.purchase_request.create(vals)
        vals = {
            "request_id": purchase_request1.id,
            "product_id": self.product_product.id,
            "product_uom_id": self.env.ref("uom.product_uom_unit").id,
            "product_qty": 2.0,
        }
        purchase_request_line1 = self.purchase_request_line.create(vals)
        vals = {
            "picking_type_id": self.env.ref("stock.picking_type_in").id,
            "requested_by": SUPERUSER_ID,
        }
        purchase_request2 = self.purchase_request.create(vals)
        vals = {
            "request_id": purchase_request1.id,
            "product_id": self.product_product.id,
            "product_uom_id": self.env.ref("uom.product_uom_unit").id,
            "product_qty": 2.0,
        }
        purchase_request_line2 = self.purchase_request_line.create(vals)
        purchase_request1.button_approved()
        purchase_request2.button_approved()
        purchase_request1.action_view_purchase_request_line()
        vals = {"supplier_id": self.env.ref("base.res_partner_1").id}
        wiz_id = self.wiz.with_context(
            active_model="purchase.request.line",
            active_ids=[purchase_request_line1.id, purchase_request_line2.id],
        ).create(vals)
        wiz_id.make_purchase_order()
        purchase_request1.action_view_purchase_order()
        po_line = purchase_request_line1.purchase_lines[0]
        purchase = po_line.order_id
        purchase.order_line.action_openRequestLineTreeView()
        purchase.button_confirm()
        purchase_request1.action_view_stock_move()
        self.assertEqual(purchase_request_line1.qty_in_progress, 2.0)
        self.assertEqual(purchase_request_line2.qty_in_progress, 2.0)
        picking = purchase.picking_ids[0]
        picking.move_line_ids[0].write({"qty_done": 2.0})
        backorder_wiz_id = picking.button_validate()["res_id"]
        backorder_wiz = self.env["stock.backorder.confirmation"].browse(
            [backorder_wiz_id]
        )
        backorder_wiz.process()
        self.assertEqual(purchase_request_line1.qty_done, 2.0)
        self.assertEqual(purchase_request_line2.qty_done, 0.0)

        backorder_picking = purchase.picking_ids.filtered(lambda p: p.id != picking.id)
        backorder_picking.move_line_ids[0].write({"qty_done": 1.0})
        backorder_wiz_id2 = backorder_picking.button_validate()["res_id"]
        backorder_wiz2 = self.env["stock.backorder.confirmation"].browse(
            [backorder_wiz_id2]
        )
        backorder_wiz2.process()

        self.assertEqual(purchase_request_line1.qty_done, 2.0)
        self.assertEqual(purchase_request_line2.qty_done, 1.0)
        for pick in purchase.picking_ids:
            if pick.state == "assigned":
                pick.action_cancel()
        self.assertEqual(purchase_request_line1.qty_cancelled, 0.0)
        self.assertEqual(purchase_request_line2.qty_cancelled, 1.0)
        self.assertEqual(purchase_request_line1.pending_qty_to_receive, 0.0)
        self.assertEqual(purchase_request_line2.pending_qty_to_receive, 1.0)

    def test_purchase_request_allocation_services(self):
        vals = {
            "picking_type_id": self.env.ref("stock.picking_type_in").id,
            "requested_by": SUPERUSER_ID,
            "assigned_to": SUPERUSER_ID,
        }
        purchase_request1 = self.purchase_request.create(vals)
        vals = {
            "request_id": purchase_request1.id,
            "product_id": self.service_product.id,
            "product_uom_id": self.env.ref("uom.product_uom_unit").id,
            "product_qty": 2.0,
        }
        purchase_request_line1 = self.purchase_request_line.create(vals)
        vals = {"supplier_id": self.env.ref("base.res_partner_1").id}
        purchase_request1.button_approved()
        purchase_request1.action_view_purchase_request_line()
        wiz_id = self.wiz.with_context(
            active_model="purchase.request.line", active_ids=[purchase_request_line1.id]
        ).create(vals)
        wiz_id.make_purchase_order()
        purchase_request1.action_view_purchase_order()
        po_line = purchase_request_line1.purchase_lines[0]
        purchase = po_line.order_id
        purchase.button_confirm()
        self.assertEqual(purchase_request_line1.qty_in_progress, 2.0)
        purchase_request1.action_view_stock_move()
        # manually set in the PO line
        po_line.write({"qty_received": 0.5})
        self.assertEqual(purchase_request_line1.qty_done, 0.5)
        purchase.button_cancel()
        self.assertEqual(purchase_request_line1.qty_cancelled, 1.5)
        self.assertEqual(purchase_request_line1.pending_qty_to_receive, 1.5)
        # Case revieve 2 product
        vals = {
            "picking_type_id": self.env.ref("stock.picking_type_in").id,
            "requested_by": SUPERUSER_ID,
            "assigned_to": SUPERUSER_ID,
        }
        purchase_request2 = self.purchase_request.create(vals)
        vals = {
            "request_id": purchase_request2.id,
            "product_id": self.service_product.id,
            "product_uom_id": self.env.ref("uom.product_uom_unit").id,
            "product_qty": 2.0,
        }
        purchase_request_line2 = self.purchase_request_line.create(vals)
        vals = {"supplier_id": self.env.ref("base.res_partner_1").id}
        purchase_request2.button_approved()
        purchase_request2.action_view_purchase_request_line()
        wiz_id = self.wiz.with_context(
            active_model="purchase.request.line", active_ids=[purchase_request_line2.id]
        ).create(vals)
        wiz_id.make_purchase_order()
        purchase_request2.action_view_purchase_order()
        po_line = purchase_request_line2.purchase_lines[0]
        purchase2 = po_line.order_id
        purchase2.button_confirm()
        self.assertEqual(purchase_request_line2.qty_in_progress, 2.0)
        purchase_request1.action_view_stock_move()
        # manually set in the PO line
        po_line.write({"qty_received": 2.0})
        self.assertEqual(purchase_request_line2.qty_done, 2.0)

    def test_purchase_request_allocation_min_qty(self):
        vals = {
            "picking_type_id": self.env.ref("stock.picking_type_in").id,
            "requested_by": SUPERUSER_ID,
        }
        purchase_request1 = self.purchase_request.create(vals)
        vals = {
            "request_id": purchase_request1.id,
            "product_id": self.product_product.id,
            "product_uom_id": self.env.ref("uom.product_uom_unit").id,
            "product_qty": 2.0,
        }
        purchase_request_line1 = self.purchase_request_line.create(vals)
        # add a vendor
        vendor1 = self.env.ref("base.res_partner_1")
        self.env["product.supplierinfo"].create(
            {
                "name": vendor1.id,
                "product_tmpl_id": self.product_product.product_tmpl_id.id,
                "min_qty": 8,
            }
        )
        vals = {"supplier_id": self.env.ref("base.res_partner_1").id}
        purchase_request1.button_approved()
        wiz_id = self.wiz.with_context(
            active_model="purchase.request.line", active_ids=[purchase_request_line1.id]
        ).create(vals)
        wiz_id.make_purchase_order()
        self.assertEqual(
            purchase_request_line1.purchase_request_allocation_ids[0].open_product_qty,
            2.0,
        )

    def test_purchase_request_stock_allocation(self):
        product = self.env.ref("product.product_product_6")
        product.uom_po_id = self.env.ref("uom.product_uom_dozen")

        vals = {
            "picking_type_id": self.env.ref("stock.picking_type_in").id,
            "requested_by": SUPERUSER_ID,
        }
        purchase_request = self.purchase_request.create(vals)
        vals = {
            "request_id": purchase_request.id,
            "product_id": product.id,
            "product_uom_id": self.env.ref("uom.product_uom_unit").id,
            "product_qty": 12.0,
        }
        purchase_request_line1 = self.purchase_request_line.create(vals)
        vals = {
            "request_id": purchase_request.id,
            "product_id": product.id,
            "product_uom_id": self.env.ref("uom.product_uom_dozen").id,
            "product_qty": 1,
        }
        purchase_request_line2 = self.purchase_request_line.create(vals)
        vals = {"supplier_id": self.env.ref("base.res_partner_1").id}
        purchase_request.button_approved()
        wiz_id = self.wiz.with_context(
            active_model="purchase.request.line",
            active_ids=[purchase_request_line1.id, purchase_request_line2.id],
        ).create(vals)
        # Create PO
        wiz_id.make_purchase_order()
        po_line = purchase_request_line1.purchase_lines[0]
        self.assertEquals(po_line.product_qty, 2, "Quantity should be 2")
        self.assertEquals(
            po_line.product_uom,
            self.env.ref("uom.product_uom_dozen"),
            "The purchase UoM should be Dozen(s).",
        )
        self.assertEquals(
            purchase_request_line1.purchase_request_allocation_ids[
                0
            ].requested_product_uom_qty,
            12.0,
        )
        self.assertEquals(
            purchase_request_line2.purchase_request_allocation_ids[
                0
            ].requested_product_uom_qty,
            1.0,
        )
        purchase = po_line.order_id
        # Cancel PO allocation requested quantity is set to 0.
        purchase.button_cancel()
        self.assertEquals(
            purchase_request_line1.purchase_request_allocation_ids[0].open_product_qty,
            0,
        )
        self.assertEquals(
            purchase_request_line2.purchase_request_allocation_ids[0].open_product_qty,
            0,
        )
        # Set to draft allocation requested quantity is set
        purchase.button_draft()
        self.assertEquals(
            purchase_request_line1.purchase_request_allocation_ids[0].open_product_qty,
            12.0,
        )
        self.assertEquals(
            purchase_request_line2.purchase_request_allocation_ids[0].open_product_qty,
            1.0,
        )
        purchase.button_confirm()
        picking = purchase.picking_ids[0]
        picking.move_line_ids[0].write({"qty_done": 24.0})
        picking.button_validate()
        self.assertEquals(
            purchase_request_line1.purchase_request_allocation_ids[
                0
            ].allocated_product_qty,
            purchase_request_line1.purchase_request_allocation_ids[
                0
            ].requested_product_uom_qty,
        )
        self.assertEquals(
            purchase_request_line2.purchase_request_allocation_ids[
                0
            ].allocated_product_qty,
            purchase_request_line2.purchase_request_allocation_ids[
                0
            ].requested_product_uom_qty,
        )

    def test_purchase_request_stock_allocation_unlink(self):
        product = self.env.ref("product.product_product_6")
        product.uom_po_id = self.env.ref("uom.product_uom_dozen")

        vals = {
            "picking_type_id": self.env.ref("stock.picking_type_in").id,
            "requested_by": SUPERUSER_ID,
        }
        purchase_request = self.purchase_request.create(vals)
        vals = {
            "request_id": purchase_request.id,
            "product_id": product.id,
            "product_uom_id": self.env.ref("uom.product_uom_unit").id,
            "product_qty": 12.0,
        }
        purchase_request_line1 = self.purchase_request_line.create(vals)
        vals = {"supplier_id": self.env.ref("base.res_partner_1").id}
        purchase_request.button_approved()
        wiz_id = self.wiz.with_context(
            active_model="purchase.request.line", active_ids=[purchase_request_line1.id]
        ).create(vals)
        # Create PO
        wiz_id.make_purchase_order()
        po_line = purchase_request_line1.purchase_lines[0]
        self.assertEquals(
            purchase_request_line1.purchase_request_allocation_ids[
                0
            ].requested_product_uom_qty,
            12.0,
        )
        purchase = po_line.order_id
        purchase.button_cancel()
        # Delete PO: allocation and Purchase Order Lines are unlinked from PRL
        purchase.unlink()
        self.assertEquals(len(purchase_request_line1.purchase_lines), 0)
        self.assertEquals(
            len(purchase_request_line1.purchase_request_allocation_ids), 0
        )

    def test_onchange_product_id(self):
        vals = {
            "picking_type_id": self.env.ref("stock.picking_type_in").id,
            "requested_by": SUPERUSER_ID,
        }
        purchase_request1 = self.purchase_request.create(vals)
        vals = {
            "request_id": purchase_request1.id,
            "product_id": self.product_product.id,
            "product_uom_id": self.env.ref("uom.product_uom_unit").id,
            "product_qty": 2.0,
        }
        purchase_request_line1 = self.purchase_request_line.create(vals)
        purchase_request_line1.onchange_product_id()
