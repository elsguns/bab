# Part of the o.s.admin add-ons.
{
    'name': 'Delivery Slip with Variant Matrix',
    'version': '18.0.1.25.0',
    'category': 'Inventory/Delivery',
    'summary': "Adds a delivery report showing the product variant matrix of the sales order",
    'description': """
Delivery Slip with Variant Matrix
=================================

Adds a separate "Delivery Slip with Variant Matrix" print action on deliveries
(stock.picking). It renders the standard delivery slip plus the same variant
grid (matrix) that ``sale_product_matrix`` already prints on the sales order
report, taking its quantities from the linked sales order.

The standard "Delivery Slip" report is left untouched: the matrix only shows on
the new report.
    """,
    'author': 'o.s.admin',
    'website': 'www.osadmin.be',
    # sale_stock -> stock.picking.sale_id (link picking to its sales order)
    # sale_product_matrix -> product_matrix.matrix template + sale.order.get_report_matrixes()
    # delivery -> res.partner.property_delivery_carrier_id (anchor for stock_location field)
    # purchase -> purchase.order.line.qty_received (the o-line of the reservation
    #             matrix reads what has already come in per purchase order)
    # stock_picking_batch -> the "Pick batches" button of a done receipt
    # (stock_quant_reservation_info adds the "Reserved Moves" button to the list
    # the "Stock" button opens, but nothing here needs it: no dependency, so a
    # database without it, such as Vasa's, updates as before.)
    'depends': ['stock', 'sale_stock', 'sale_product_matrix', 'delivery', 'purchase',
                'stock_picking_batch'],
    'data': [
        'security/ir.model.access.csv',
        'data/sale_order_stock_location_action.xml',
        'views/res_company_views.xml',
        'views/res_partner_views.xml',
        'views/stock_picking_views.xml',
        'views/stock_picking_type_views.xml',
        'wizard/matrix_reprint_confirm_views.xml',
        'report/delivery_report_matrix.xml',
        # reservation_matrix must load BEFORE product_overview so its report
        # action gets a lower id and lands first in the Print menu (report
        # bindings are ordered by action id); see reservation_matrix_report.xml.
        'report/reservation_matrix_report.xml',
        'report/product_overview_report.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'bab_stock_delivery/static/src/picking_form/*',
            'bab_stock_delivery/static/src/download_and_reload/*',
        ],
    },
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
}
