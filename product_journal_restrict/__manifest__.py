# -*- coding: utf-8 -*-

{
    'name': "Product Journal Creation Restriction",
    'summary': """Product Journal Creation Restriction""",
    'description': """Product Journal Creation Restriction.""",
    'author': "Ahmed Gaber",
    'license': 'LGPL-3',
    'category': 'account',
    'version': '14.0',
    'depends': ['account','product','point_of_sale','purchase','sale','event_sale'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/users.xml',


    ],
    "images": [
    ],
    'installable': True,
    'application': False,
    'auto_install': True,
}
