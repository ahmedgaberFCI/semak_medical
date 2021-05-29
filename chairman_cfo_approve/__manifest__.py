# Copyright 2018-2019 ForgeFlow, S.L.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl-3.0).

{
    "name": "Chair Man & CFO Approve",
    "author": "Ahmed Gaber",
    "version": "14",
    "summary": "Use this module to make some constrains for chairman approve and CFO approve"
               ,
    "category": "Purchase ",
    "depends": ["purchase", "product", "purchase_stock"],
    "data": [
        "security/security.xml",

        "views/purchase_order_view.xml",
    ],
    "license": "LGPL-3",

    "installable": True,
    "application": True,
}
