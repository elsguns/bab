# -*- coding: utf-8 -*-

{
    "name": "Babimex Website Sales",
    "version": "18.0.2.0.1",
    "summary": """
        Website Sale Related customization.
        """,
    "description": """
        Website Sale Related customization.
    """,
    "author": "Mainframe Monkey",
    "website": "https://www.mainframemonkey.com",
    "category": "Website/Website",
    "depends": [
        "website_sale",
        ],
    "data": [
        "views/res_config_settings_views.xml",
        "views/website_view.xml",
        "views/templates.xml",
        "views/product_template_inherit_views.xml",
        "views/website_sale_inherit_views.xml",
    ],
    'assets': {
        'web.assets_frontend': [
            'babimex_website_sale/static/src/js/website_sale.js',
        ],
    },
    "installable": True,
    "application": True,
    "license": "LGPL-3",
}
