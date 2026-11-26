# Part of the o.s.admin add-ons.


def migrate(cr, version):
    # Everything reserved on an open pick today went out on the slips of the
    # receipts before this version (they printed the full reservation). Count it
    # as printed, so the next receipt only prints what it adds.
    cr.execute("""
        UPDATE stock_move m
           SET matrix_printed_qty = m.quantity
          FROM stock_picking p
          JOIN stock_warehouse w ON w.pick_type_id = p.picking_type_id
         WHERE p.id = m.picking_id
           AND m.state NOT IN ('done', 'cancel')
           AND m.quantity > 0
    """)
