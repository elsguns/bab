# Part of the o.s.admin add-ons.


def migrate(cr, version):
    # The receipt form view of 18.0.1.4.0 reads picking_type_matrix_slips_on_request,
    # which is gone. Its stored arch would break the validation of the other
    # transfer form views before its own record is reloaded, so drop it: the
    # update creates it again from the XML.
    cr.execute("""
        DELETE FROM ir_ui_view
         WHERE id IN (SELECT res_id
                        FROM ir_model_data
                       WHERE module = 'bab_stock_delivery'
                         AND name = 'view_picking_form_receipt_slips_printed'
                         AND model = 'ir.ui.view')
    """)
    cr.execute("""
        DELETE FROM ir_model_data
         WHERE module = 'bab_stock_delivery'
           AND name = 'view_picking_form_receipt_slips_printed'
           AND model = 'ir.ui.view'
    """)
