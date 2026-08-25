# * Pickstap toevoegen
#
# Code van de contextuele serveractie op leveringen (Instellingen -> Technisch ->
# Serveracties). Eenmalige opkuis: leveringen die zijn aangemaakt toen het
# magazijn nog in ÉÉN stap leverde, vertrekken rechtstreeks uit de voorraad. Nu
# het magazijn op twee stappen staat, ontbreekt bij die leveringen de pickstap.
#
# Per geselecteerde levering:
#   1. de reservatie vrijgeven;
#   2. een pickbon aanmaken (voorraad -> uitgaand) met dezelfde lijnen;
#   3. de aanvoer die vandaag de levering voedt (bv. de ontvangst van de
#      leverancier) laten voeden op de pickbon, en de pickbon op de levering;
#   4. de levering laten vertrekken uit uitgaand, wachtend op de pickbon;
#   5. bevestigen en opnieuw laten reserveren.
#
# Het verkooporder, de aankooporder en de MTO-keten blijven volledig intact:
# er wordt niets geannuleerd en geen enkele nieuwe aanvoerbehoefte gemaakt.
#
# Leveringen die al in orde zijn (of al klaar/geannuleerd) worden overgeslagen,
# dus de actie mag gerust twee keer op dezelfde selectie lopen.

new_picks = env['stock.picking']
skipped = []

for picking in records:
    warehouse = picking.picking_type_id.warehouse_id
    output_location = warehouse.wh_output_stock_loc_id

    # Enkel openstaande uitgaande leveringen van een magazijn dat in twee stappen
    # levert. Al de rest raken we niet aan.
    if (picking.picking_type_id.code != 'outgoing'
            or picking.state in ('done', 'cancel')
            or warehouse.delivery_steps != 'pick_ship'
            or not output_location):
        skipped.append(picking.name)
        continue

    # De te herwerken lijnen: alles wat nog loopt en nog niet uit uitgaand vertrekt.
    moves = picking.move_ids.filtered(
        lambda m: m.state not in ('done', 'cancel') and m.location_id != output_location)
    if not moves:
        skipped.append(picking.name)
        continue

    # De goederen moeten straks door de pickbon gereserveerd worden, niet meer
    # rechtstreeks door de levering. Enkel de lijnen die we herwerken: een
    # levering kan intussen ook lijnen bevatten die al wél uit uitgaand
    # vertrekken (een order dat vandaag bevestigd wordt, wordt door de
    # groepering per klant bij een bestaande levering gezet), en die mogen hun
    # reservatie houden.
    moves._do_unreserve()

    pick_type = warehouse.pick_type_id
    source_location = pick_type.default_location_src_id or warehouse.lot_stock_id
    # De pull-regel van de pickstap, zodat de nieuwe lijnen dezelfde herkomst
    # tonen als een pickbon die Odoo vandaag zelf zou aanmaken.
    pick_rule = warehouse.delivery_route_id.rule_ids.filtered(
        lambda r: r.picking_type_id == pick_type)[:1]

    pick = env['stock.picking'].create({
        'picking_type_id': pick_type.id,
        'partner_id': picking.partner_id.id,
        'origin': picking.origin,
        'group_id': picking.group_id.id,
        'location_id': source_location.id,
        'location_dest_id': output_location.id,
        'scheduled_date': picking.scheduled_date,
        'company_id': picking.company_id.id,
    })

    for move in moves:
        # De pickmove neemt de aanvoer van de levering over: had de levering een
        # bronmove (MTO vanaf de ontvangst), dan hangt die nu aan de pickbon.
        # Zonder bronmove wordt er gewoon uit de voorraad gereserveerd. Zo kan er
        # nooit een nieuwe aanvoerbehoefte -- en dus geen tweede aankooporder --
        # ontstaan; zie ook bypass_procurement_creation hieronder.
        origin_moves = move.move_orig_ids
        pick_move = env['stock.move'].create({
            'name': move.name,
            'picking_id': pick.id,
            'picking_type_id': pick_type.id,
            'product_id': move.product_id.id,
            'product_uom': move.product_uom.id,
            'product_uom_qty': move.product_uom_qty,
            'location_id': source_location.id,
            'location_dest_id': output_location.id,
            'location_final_id': move.location_dest_id.id,
            'procure_method': 'make_to_order' if origin_moves else 'make_to_stock',
            'rule_id': pick_rule.id,
            'group_id': move.group_id.id,
            'sale_line_id': move.sale_line_id.id,
            'origin': move.origin,
            'date': move.date,
            'date_deadline': move.date_deadline,
            'company_id': move.company_id.id,
            'warehouse_id': warehouse.id,
            'move_orig_ids': [(6, 0, origin_moves.ids)],
            'move_dest_ids': [(6, 0, move.ids)],
        })
        # De levering vertrekt voortaan uit uitgaand en wacht op de pickbon. De
        # oude link met de ontvangst wordt hier vervangen -- die hangt nu aan de
        # pickmove, die we net hierboven gemaakt hebben.
        move['location_id'] = output_location.id
        move['procure_method'] = 'make_to_order'
        move['move_orig_ids'] = pick_move

    picking['location_id'] = output_location.id
    moves._recompute_state()

    # bypass_procurement_creation: extra slot op de deur. De pickmoves met een
    # bronmove worden sowieso enkel op "wachtend" gezet (stock.move._action_confirm
    # kijkt eerst naar move_orig_ids), maar met deze context kan het bevestigen
    # onder geen beding een aanvoerbehoefte afvuren.
    pick.with_context(bypass_procurement_creation=True).action_confirm()
    pick.action_assign()
    # Herstelt de reservatie van lijnen die al uit uitgaand vertrokken; voor de
    # zonet herwerkte lijnen valt er nog niets te reserveren (die wachten op de
    # pickbon), dus dit is voor hen een lege bewerking.
    picking.action_assign()

    new_picks |= pick

if skipped:
    # Geen fout: gewoon melden wat overgeslagen werd, zodat je het verschil ziet
    # tussen "niets te doen" en "vergeten te selecteren".
    log("Overgeslagen (al in orde, of niet van toepassing): %s" % ', '.join(skipped))

action = {
    'type': 'ir.actions.act_window',
    'name': 'Nieuwe pickbonnen',
    'res_model': 'stock.picking',
    'view_mode': 'form' if len(new_picks) == 1 else 'list,form',
    'res_id': new_picks.id if len(new_picks) == 1 else False,
    'domain': [('id', 'in', new_picks.ids)],
}
