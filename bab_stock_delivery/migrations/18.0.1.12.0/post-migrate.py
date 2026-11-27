# Part of the o.s.admin add-ons.


def migrate(cr, version):
    # From this version the slips after a receipt only print what changed since
    # the previous slips (stock.move.matrix_printed_qty). What is reserved on an
    # open pick today is already on paper only where the receipts print the
    # slips (auto_print_matrix_after_receipt) and the receipt that brought it
    # had its slips printed. Elsewhere (Vasa: slips on a done pick only) nothing
    # of an open pick is on paper yet. A done receipt still waiting for its
    # slips keeps its received variants at 0, so its slips still print in full.
    cr.execute("""
        UPDATE stock_move m
           SET matrix_printed_qty = m.quantity
          FROM stock_picking p
          JOIN stock_warehouse w ON w.pick_type_id = p.picking_type_id
         WHERE p.id = m.picking_id
           AND m.state NOT IN ('done', 'cancel')
           AND m.quantity > 0
           AND EXISTS (
                SELECT 1
                  FROM stock_picking_type t
                 WHERE t.warehouse_id = w.id
                   AND t.code = 'incoming'
                   AND t.auto_print_matrix_after_receipt)
           AND m.product_id NOT IN (
                SELECT rm.product_id
                  FROM stock_move rm
                  JOIN stock_picking r ON r.id = rm.picking_id
                  JOIN stock_picking_type rt ON rt.id = r.picking_type_id
                 WHERE rt.warehouse_id = w.id
                   AND rt.code = 'incoming'
                   AND rt.auto_print_matrix_after_receipt
                   AND r.state = 'done'
                   AND r.matrix_printed IS NOT TRUE
                   AND rm.state = 'done')
    """)
