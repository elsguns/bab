# Part of the o.s.admin add-ons.


def migrate(cr, version):
    # The flag on receipts is new. Every receipt done before this version had
    # its slips run at validation (printed straight away, or nothing to print),
    # so none of them may show up as "Slips to print".
    cr.execute("""
        UPDATE stock_picking p
           SET matrix_printed = TRUE
          FROM stock_picking_type t
         WHERE t.id = p.picking_type_id
           AND t.code = 'incoming'
           AND p.state = 'done'
           AND p.matrix_printed IS NOT TRUE
    """)
