# * Ontbrekend stuk onderzoeken
#
# Code van de serveractie (Instellingen -> Technisch -> Serveracties), model
# Serveractie (ir.actions.server), type Python-code. Zo verschijnt op het
# formulier de knop Uitvoeren en hoef je geen record te selecteren.
#
# LEEST ALLEEN. Er wordt niets aangemaakt, gewijzigd of gevalideerd; de actie
# mag dus gerust meermaals lopen.
#
# WAAROM. Op batch 02473 stond artikel 51742-98-M niet als gescand; er zijn 30
# stuks vertrokken en 29 gefactureerd. De vraag is wat Odoo van dat 30ste stuk
# denkt te weten: staat het nog als openstaande vraag ergens in de keten, of is
# het weggevallen? Dat bepaalt of we het kunnen leveren+factureren (§7) dan wel
# een nieuwe lijn nodig hebben.
#
# WAT ZE VERZAMELT
#   1. de batch: status, en elke bon die eraan hangt;
#   2. het artikel: voorraad per locatie, ook de negatieve;
#   3. elke verplaatsing van dat artikel in de keten van deze orders --
#      geannuleerde en gesplitste inbegrepen -- met vraag, geboekt en de
#      keten-links, zodat zichtbaar wordt wáár het stuk is blijven steken;
#   4. de verkooporder(s): besteld / geleverd / gefactureerd per lijn;
#   5. de facturen met hun lijnen voor dit artikel;
#   6. de chatter van de betrokken bonnen: wie valideerde wat, wanneer, en of
#      er een backorder is aangemaakt;
#   7. alle orderlijnen van de batch waar besteld, geleverd en gefactureerd
#      niet gelijklopen -- dus of dit het enige vergeten stuk is.
#
# De uitvoer komt in het logboek terecht (Instellingen -> Technisch -> Logboek).
# De actie opent dat logboek meteen; open de bovenste lijn en kopieer het veld
# Bericht.

# Waarnaar we zoeken. De batchnaam mag een fragment zijn (BATCH/02473 en 02473
# vinden allebei hun bon).
BATCH_NAAM = '02473'
PRODUCT_CODE = '51742-98-M'

# Het order uit het prognoserapport. Laat leeg als je het niet kent: de orders
# worden sowieso ook via de verplaatsingen zelf gevonden.
ORDER_NAAM = 'S01533'

# De bon waarin het stuk is blijven hangen. §8 legt uit waarom die niet in de
# batch terechtkwam. Leeg laten slaat §8 over.
BON_NAAM = 'VAS/OUT/00300'

# Een levering kan honderden lijnen tellen; meer dan dit uitschrijven maakt het
# log onleesbaar zonder nog iets bij te leren.
MAX_LIJNEN = 60


def naam(rec):
    # display_name werkt voor elk model en blijft leeg-veilig.
    return rec.display_name if rec else '-'


def stempel(rec):
    return '%s door %s' % (rec.create_date, naam(rec.create_uid))


def plat(body):
    # Chatterberichten zijn HTML. Geen re-module in een serveractie, dus met de
    # hand de tags eruit halen.
    tekst = ''
    in_tag = False
    for teken in body or '':
        if teken == '<':
            in_tag = True
        elif teken == '>':
            in_tag = False
            tekst += ' '
        elif not in_tag:
            tekst += teken
    return ' '.join(tekst.split())[:400]


def waarde(volg, kant):
    # Een tracking-waarde staat in de kolom die bij het veldtype hoort; welke dat
    # is weten we hier niet, dus nemen we de eerste die gevuld is.
    for soort_kolom in ['char', 'text', 'integer', 'float', 'datetime']:
        gevonden = volg['%s_value_%s' % (kant, soort_kolom)]
        if gevonden:
            return gevonden
    return '(leeg)'


regels = []
add = regels.append

add('=== ONTBREKEND STUK ONDERZOEKEN — %s UTC ===' % time.strftime('%Y-%m-%d %H:%M:%S'))
add('Batch %s · artikel %s · order %s' % (BATCH_NAAM, PRODUCT_CODE, ORDER_NAAM or '-'))

# --- 1. De batch en zijn bonnen ----------------------------------------------
# sudo(): de bonnen kunnen bij een ander bedrijf horen dan het bedrijf dat nu
# actief staat, en dan verbergt de recordregel ze.
batches = env['stock.picking.batch'].sudo().search([('name', 'ilike', BATCH_NAAM)])

add('')
add('#' * 78)
add('# 1. BATCH')
add('#' * 78)
add('Gevonden batches: %s' % (', '.join(batches.mapped('name')) or 'GEEN'))

batch_bonnen = env['stock.picking'].sudo()
for batch in batches:
    add('')
    add('  BATCH %s (id %s) — status %s' % (batch.name, batch.id, batch.state))
    add('    bedrijf         : %s' % naam(batch.company_id))
    add('    verantwoordelijke: %s' % naam(batch.user_id))
    add('    bewerkingssoort : %s' % naam(batch.picking_type_id))
    add('    aangemaakt      : %s' % stempel(batch))
    add('    bonnen (%s):' % len(batch.picking_ids))
    for bon in batch.picking_ids.sorted('id'):
        add('      %-16s %-10s %-24s backorder van %s' % (
            bon.name, bon.state, bon.picking_type_id.display_name,
            bon.backorder_id.name if bon.backorder_id else 'geen'))
    batch_bonnen = batch_bonnen | batch.picking_ids

if not batches:
    # Misschien is 02473 geen batch maar een bonnummer; dan werken we daarmee
    # verder in plaats van met lege handen te staan.
    losse = env['stock.picking'].sudo().search([('name', 'ilike', BATCH_NAAM)])
    add('Bonnen met dezelfde naam: %s' % (', '.join(losse.mapped('name')) or 'geen'))
    for bon in losse.sorted('id'):
        add('      %-16s %-10s %-24s batch %s' % (
            bon.name, bon.state, bon.picking_type_id.display_name,
            bon.batch_id.name if bon.batch_id else 'geen'))
    batch_bonnen = batch_bonnen | losse

# --- 2. Het artikel en zijn voorraad ------------------------------------------
varianten = env['product.product'].sudo().with_context(active_test=False).search([
    '|', '|',
    ('default_code', '=', PRODUCT_CODE),
    ('barcode', '=', PRODUCT_CODE),
    ('default_code', 'ilike', PRODUCT_CODE),
])

add('')
add('#' * 78)
add('# 2. ARTIKEL EN VOORRAAD')
add('#' * 78)
add('Gevonden varianten: %s' % (len(varianten) or 'GEEN'))

for variant in varianten:
    add('')
    add('  %s (id %s) — code %s — actief %s' % (
        naam(variant), variant.id, variant.default_code or '-', variant.active))
    add('    beschikbaar / vrij / verwacht : %s / %s / %s' % (
        variant.qty_available, variant.free_qty, variant.virtual_available))
    add('    inkomend / uitgaand           : %s / %s' % (
        variant.incoming_qty, variant.outgoing_qty))

    quants = env['stock.quant'].sudo().search([('product_id', '=', variant.id)])
    add('    voorraadposten (%s) — ook klant- en transitlocaties:' % len(quants))
    for quant in quants.sorted(lambda q: q.location_id.complete_name or ''):
        add('      %-46s aanwezig %6s   gereserveerd %6s   (%s)' % (
            quant.location_id.complete_name, quant.quantity,
            quant.reserved_quantity, quant.location_id.usage))

# --- 3. De verplaatsingen van dit artikel -------------------------------------
# We willen álle verplaatsingen van de keten zien, ook de geannuleerde en de
# afgesplitste. Die hangen niet altijd aan een bon van de batch: bij een
# backorder verhuist het restant naar een nieuwe bon. De gemene deler is de
# orderlijn (en anders de aanvoergroep), dus verzamelen we die eerst.
batch_moves = env['stock.move'].sudo().search([
    ('picking_id', 'in', batch_bonnen.ids),
    ('product_id', 'in', varianten.ids),
])

orders = batch_moves.mapped('sale_line_id.order_id')
if ORDER_NAAM:
    orders = orders | env['sale.order'].sudo().search([('name', '=', ORDER_NAAM)])

order_lijnen = env['sale.order.line'].sudo().search([
    ('order_id', 'in', orders.ids),
    ('product_id', 'in', varianten.ids),
])
groepen = orders.mapped('procurement_group_id')

domein = [('product_id', 'in', varianten.ids)]
kandidaten = []
if order_lijnen:
    kandidaten.append(('sale_line_id', 'in', order_lijnen.ids))
if groepen:
    kandidaten.append(('group_id', 'in', groepen.ids))
if batch_moves:
    kandidaten.append(('id', 'in', batch_moves.ids))

# Handmatig een OR-keten bouwen: een wisselend aantal takken kan je niet in één
# literal domein gieten.
takken = []
for tak in kandidaten:
    takken.append(tak)
if takken:
    domein = domein + ['|'] * (len(takken) - 1) + takken
    moves = env['stock.move'].sudo().search(domein, order='date, id')
else:
    moves = env['stock.move'].sudo()

add('')
add('#' * 78)
add('# 3. VERPLAATSINGEN VAN DIT ARTIKEL (hele keten, ook geannuleerd)')
add('#' * 78)
add('Orders in beeld : %s' % (', '.join(orders.mapped('name')) or 'geen'))
add('Verplaatsingen  : %s' % len(moves))

if len(moves) > MAX_LIJNEN:
    add('(enkel de eerste %s worden uitgeschreven)' % MAX_LIJNEN)
    moves = moves[:MAX_LIJNEN]

for move in moves:
    bon = move.picking_id
    # Vraag versus geboekt: het verschil is precies het stuk dat we zoeken.
    add('')
    add('  LIJN %s — %s — %s' % (move.id, bon.name if bon else 'GEEN BON', move.state))
    add('    bon             : %s (%s)%s' % (
        bon.name if bon else '-',
        bon.picking_type_id.display_name if bon else '-',
        '  [backorder van %s]' % bon.backorder_id.name if bon and bon.backorder_id else ''))
    add('    vraag / geboekt / afgevinkt : %s / %s / %s' % (
        move.product_uom_qty, move.quantity, move.picked))
    add('    van -> naar     : %s -> %s' % (naam(move.location_id), naam(move.location_dest_id)))
    add('    aanvoermethode  : %s   regel: %s' % (
        move.procure_method, naam(move.rule_id) if move.rule_id else 'geen'))
    add('    keten           : gevoed door %s, voedt %s' % (
        move.move_orig_ids.ids or 'niets', move.move_dest_ids.ids or 'niets'))
    add('    orderlijn       : %s (%s)' % (
        move.sale_line_id.id or 'geen', naam(move.sale_line_id.order_id)))
    add('    datum           : %s   gemaakt %s' % (move.date, stempel(move)))
    for lijn in move.move_line_ids[:10]:
        add('      GEBOEKT %s %s van %s naar %s   (afgevinkt %s, %s)' % (
            lijn.quantity, naam(lijn.product_uom_id),
            naam(lijn.location_id), naam(lijn.location_dest_id),
            lijn.picked, stempel(lijn)))

# --- 4. De verkooporder(s) ----------------------------------------------------
add('')
add('#' * 78)
add('# 4. VERKOOPORDER — besteld / geleverd / gefactureerd')
add('#' * 78)

for order in orders.sorted('name'):
    add('')
    add('  ORDER %s (id %s) — status %s — facturatiestatus %s' % (
        order.name, order.id, order.state, order.invoice_status))
    add('    klant           : %s' % naam(order.partner_id))
    add('    magazijn        : %s' % naam(order.warehouse_id))
    add('    klantreferentie : %s' % (order.client_order_ref or '-'))
    add('    facturen        : %s' % (', '.join(order.invoice_ids.mapped('name')) or 'geen'))
    add('    lijnen van dit artikel:')
    for lijn in order.order_line:
        if lijn.product_id not in varianten:
            continue
        add('      lijn %s — %s' % (lijn.id, naam(lijn.product_id)))
        add('        besteld %s / geleverd %s / gefactureerd %s   status %s' % (
            lijn.product_uom_qty, lijn.qty_delivered, lijn.qty_invoiced, lijn.invoice_status))
        add('        te factureren %s   prijs %s   facturatiebeleid %s' % (
            lijn.qty_to_invoice, lijn.price_unit, lijn.product_id.invoice_policy))
        add('        factuurlijnen : %s' % (
            ', '.join(lijn.invoice_lines.mapped('move_id.name')) or 'geen'))

# --- 5. De facturen -----------------------------------------------------------
add('')
add('#' * 78)
add('# 5. FACTUREN')
add('#' * 78)

for factuur in orders.mapped('invoice_ids').sorted('id'):
    add('')
    add('  %s (id %s) — %s — %s — %s' % (
        factuur.name, factuur.id, factuur.move_type, factuur.state, factuur.invoice_date or '-'))
    for lijn in factuur.invoice_line_ids:
        if lijn.product_id not in varianten:
            continue
        add('    %s  aantal %s  prijs %s  subtotaal %s' % (
            naam(lijn.product_id), lijn.quantity, lijn.price_unit, lijn.price_subtotal))

# --- 6. Chatter van de betrokken bonnen ---------------------------------------
# Hier staat wie wanneer valideerde en of Odoo een backorder aanmaakte -- het
# antwoord op "kan je bevestigen zonder alles te scannen?".
bonnen = moves.mapped('picking_id') | batch_bonnen

add('')
add('#' * 78)
add('# 6. CHATTER VAN DE BETROKKEN BONNEN')
add('#' * 78)

for bon in bonnen.sorted('id'):
    add('')
    add('  BON %s (id %s) — %s — %s' % (
        bon.name, bon.id, bon.state, bon.picking_type_id.display_name))
    add('    gevalideerd op  : %s' % (bon.date_done or 'niet gevalideerd'))
    add('    laatst gewijzigd: %s door %s' % (bon.write_date, naam(bon.write_uid)))
    add('    backorder van   : %s' % (bon.backorder_id.name if bon.backorder_id else '-'))
    add('    backorders      : %s' % (', '.join(bon.backorder_ids.mapped('name')) or 'geen'))
    berichten = env['mail.message'].sudo().search(
        [('model', '=', 'stock.picking'), ('res_id', '=', bon.id)], order='id')
    for bericht in berichten[:25]:
        add('      [%s] %s: %s' % (
            bericht.date, naam(bericht.author_id) or 'systeem',
            plat(bericht.body) or '(enkel tracking of bijlagen)'))

# --- 7. Is dit het enige vergeten stuk? ---------------------------------------
# Elke orderlijn van deze batch waar besteld, geleverd en gefactureerd niet
# gelijklopen. Zo zie je in één blik of er nog maten zijn overgeslagen.
alle_orders = batch_bonnen.mapped('move_ids.sale_line_id.order_id')

add('')
add('#' * 78)
add('# 7. AFWIJKINGEN OP DE HELE BATCH (besteld <> geleverd <> gefactureerd)')
add('#' * 78)
add('Orders op de batch: %s' % (', '.join(alle_orders.mapped('name')) or 'geen'))

afwijkend = 0
for order in alle_orders.sorted('name'):
    for lijn in order.order_line:
        if lijn.display_type:
            continue
        if lijn.product_uom_qty == lijn.qty_delivered == lijn.qty_invoiced:
            continue
        afwijkend += 1
        add('  %-10s %-44s besteld %6s  geleverd %6s  gefactureerd %6s  (%s)' % (
            order.name, naam(lijn.product_id)[:44], lijn.product_uom_qty,
            lijn.qty_delivered, lijn.qty_invoiced, lijn.invoice_status))

add('Totaal afwijkende lijnen: %s' % afwijkend)

# --- 8. Waarom zat deze bon niet in de batch? ---------------------------------
# Odoo vormt de batches automatisch (bewerkingssoort -> "Automatische batches"),
# maar probeert dat maar op twee momenten: bij het bevestigen van de bon
# (action_confirm) en, voor een backorder, meteen na het valideren van zijn
# voorganger. Op zo'n moment neemt Odoo de bon enkel mee als die dan al op
# Klaar staat -- _is_auto_batchable() begint letterlijk met
# "if self.state != 'assigned': return False". Een bon die op dat ogenblik niets
# kon reserveren valt dus buiten de batch, en Odoo komt er nadien nooit op
# terug. Hieronder controleren we die voorwaarden stuk voor stuk op de bon zelf.
if BON_NAAM:
    add('')
    add('#' * 78)
    add('# 8. WAAROM ZAT %s NIET IN DE BATCH?' % BON_NAAM)
    add('#' * 78)

    doelbonnen = env['stock.picking'].sudo().search([('name', '=', BON_NAAM)])
    add('Gevonden: %s' % (', '.join(doelbonnen.mapped('name')) or 'GEEN'))

    for bon in doelbonnen:
        soort = bon.picking_type_id
        add('')
        add('  BON %s (id %s) — status %s' % (bon.name, bon.id, bon.state))
        add('    batch           : %s' % (bon.batch_id.name if bon.batch_id else 'geen'))
        add('    backorder van   : %s' % (bon.backorder_id.name if bon.backorder_id else 'geen'))
        add('    brondocument    : %s' % (bon.origin or '-'))
        add('    klant           : %s (id %s)' % (naam(bon.partner_id), bon.partner_id.id or 0))
        add('    aangemaakt      : %s' % stempel(bon))
        add('    gepland         : %s' % bon.scheduled_date)

        add('    instellingen van de bewerkingssoort %s:' % naam(soort))
        add('      automatische batches : %s' % soort.auto_batch)
        add('      groeperen per klant  : %s' % soort.batch_group_by_partner)
        add('      per bestemming/bron/doel : %s / %s / %s' % (
            soort.batch_group_by_destination, soort.batch_group_by_src_loc,
            soort.batch_group_by_dest_loc))
        add('      max lijnen / max bonnen : %s / %s' % (
            soort.batch_max_lines or 'geen', soort.batch_max_pickings or 'geen'))
        add('      batch meteen bevestigen : %s' % soort.batch_auto_confirm)
        add('      reserveringsmethode  : %s' % soort.reservation_method)

        add('    verplaatsingen op deze bon:')
        for move in bon.move_ids:
            add('      %s — %s — vraag %s / gereserveerd %s — %s' % (
                naam(move.product_id), move.state, move.product_uom_qty,
                move.quantity, move.procure_method))
            for bronlijn in move.move_orig_ids:
                # Bij een levering in twee stappen wacht de bon op zijn pickbon:
                # zolang die niet Gereed is, kan de levering niets reserveren.
                add('        wacht op lijn %s (%s) op bon %s' % (
                    bronlijn.id, bronlijn.state,
                    bronlijn.picking_id.name if bronlijn.picking_id else 'geen bon'))

        # Statusgeschiedenis: de enige harde bron voor de vraag of de bon ooit op
        # Klaar heeft gestaan op het moment dat Odoo een batch zocht.
        add('    statusgeschiedenis uit de chatter:')
        berichten = env['mail.message'].sudo().search(
            [('model', '=', 'stock.picking'), ('res_id', '=', bon.id)], order='id')
        for bericht in berichten:
            for volg in bericht.tracking_value_ids:
                add('      [%s] %s: %s -> %s' % (
                    bericht.date, volg.field_id.field_description or volg.field_id.name,
                    waarde(volg, 'old'), waarde(volg, 'new')))

        # Dezelfde controles die _is_auto_batchable() en _find_auto_batch() doen.
        add('    controle van de batchvoorwaarden (nu):')
        add('      automatische batches aan   : %s' % (
            'ja' if soort.auto_batch else 'NEE — batches worden hier met de hand gemaakt'))
        add('      groepeersleutel ingesteld  : %s' % (
            'ja' if (soort.batch_group_by_partner or soort.batch_group_by_destination
                     or soort.batch_group_by_src_loc or soort.batch_group_by_dest_loc)
            else 'NEE — zonder sleutel batcht Odoo niet'))
        add('      bon zit nog in geen batch  : %s' % ('ja' if not bon.batch_id else 'nee'))
        add('      bon staat op Klaar         : %s' % (
            'ja' if bon.state == 'assigned'
            else 'NEE (status %s) — hierop slaat Odoo de bon over' % bon.state))
        add('      max bonnen laat batchen toe: %s' % (
            'nee (max %s)' % soort.batch_max_pickings
            if soort.batch_max_pickings and soort.batch_max_pickings <= 1 else 'ja'))

        # Waar zou hij terechtgekomen zijn? De open batches van dezelfde soort en
        # dezelfde klant zijn de kandidaten uit _get_possible_batches_domain().
        kandidaat_batches = env['stock.picking.batch'].sudo().search([
            ('state', 'in', ('draft', 'in_progress')),
            ('picking_type_id', '=', soort.id),
            ('is_wave', '=', False),
            ('picking_ids.partner_id', '=', bon.partner_id.id),
        ])
        add('    open batches van dezelfde soort voor deze klant: %s' % (
            ', '.join(kandidaat_batches.mapped('name')) or 'geen'))

# --- 9. Waarom is de bon niet beschikbaar? ------------------------------------
# Een bon reserveert enkel uit zijn eigen bronlocatie. Bij een levering in twee
# stappen is dat de uitgaande zone, niet het rek: staat daar niets, dan blijft
# de bon In afwachting, hoe vaak de planner ook langskomt. Hieronder zetten we
# de vraag naast wat er echt in die bronlocatie ligt, en tellen we op wat de
# pickstappen er ooit hebben binnengebracht en wat de leveringen eruit haalden.
if BON_NAAM:
    add('')
    add('#' * 78)
    add('# 9. WAAROM IS %s NIET BESCHIKBAAR?' % BON_NAAM)
    add('#' * 78)

    for bon in env['stock.picking'].sudo().search([('name', '=', BON_NAAM)]):
        bron = bon.location_id
        add('')
        add('  BON %s — status %s' % (bon.name, bon.state))
        add('    bronlocatie : %s (%s)' % (naam(bron), bron.usage))
        add('    reserveringsmethode van de soort : %s' % bon.picking_type_id.reservation_method)

        for move in bon.move_ids:
            add('')
            add('    LIJN %s — %s — %s' % (move.id, naam(move.product_id), move.state))
            add('      vraag %s / gereserveerd %s' % (move.product_uom_qty, move.quantity))
            add('      aanvoermethode      : %s' % move.procure_method)
            add('      te reserveren vanaf : %s' % (move.reservation_date or '-'))
            add('      prognose beschikbaar: %s (verwacht %s)' % (
                move.forecast_availability, move.forecast_expected_date or '-'))

            # Wat ligt er nu echt in de bronlocatie? available_quantity is wat
            # nog vrij is na aftrek van wat andere bonnen al gereserveerd hebben.
            posten = env['stock.quant'].sudo().search([
                ('product_id', '=', move.product_id.id),
                ('location_id', 'child_of', bron.id),
            ])
            add('      voorraad in de bronlocatie (%s posten):' % len(posten))
            for post in posten:
                add('        %-40s aanwezig %s   gereserveerd %s   vrij %s' % (
                    post.location_id.complete_name, post.quantity,
                    post.reserved_quantity, post.available_quantity))
            if not posten:
                add('        NIETS — daarom kan deze lijn niets reserveren.')

            # Waar wacht de lijn op? Een keten-lijn wacht op zijn voorganger; is
            # die al Gereed, dan komt er nooit nog iets bij en blijft de bon
            # hangen tot iemand de voorraad rechtzet.
            add('      voedende lijnen:')
            for bronlijn in move.move_orig_ids:
                add('        lijn %s op %s — %s — vraag %s / geboekt %s' % (
                    bronlijn.id,
                    bronlijn.picking_id.name if bronlijn.picking_id else 'geen bon',
                    bronlijn.state, bronlijn.product_uom_qty, bronlijn.quantity))
            if not move.move_orig_ids:
                add('        geen — deze lijn wacht op niets, enkel op voorraad.')

            # De balans van de uitgaande zone: alles wat er ooit voor dit artikel
            # is binnengekomen min alles wat eruit vertrok. Dit is het bewijs of
            # de pickstap er wel degelijk minder heeft neergezet dan de levering
            # eruit moest halen.
            binnen = env['stock.move'].sudo().search([
                ('product_id', '=', move.product_id.id),
                ('state', '=', 'done'),
                ('location_dest_id', 'child_of', bron.id),
            ])
            buiten = env['stock.move'].sudo().search([
                ('product_id', '=', move.product_id.id),
                ('state', '=', 'done'),
                ('location_id', 'child_of', bron.id),
            ])
            totaal_in = 0
            for lijn in binnen:
                totaal_in += lijn.quantity
            totaal_uit = 0
            for lijn in buiten:
                totaal_uit += lijn.quantity
            add('      balans van %s voor dit artikel: %s binnen - %s buiten = %s' % (
                naam(bron), totaal_in, totaal_uit, totaal_in - totaal_uit))
            for lijn in binnen.sorted('date'):
                add('        IN   %s  %s  %s' % (
                    lijn.date, lijn.quantity,
                    lijn.picking_id.name if lijn.picking_id else 'geen bon'))
            for lijn in buiten.sorted('date'):
                add('        UIT  %s  %s  %s' % (
                    lijn.date, lijn.quantity,
                    lijn.picking_id.name if lijn.picking_id else 'geen bon'))

    # De planner: die probeert wachtende lijnen opnieuw te reserveren. Hij maakt
    # geen voorraad bij, dus hij lost bovenstaande niet op -- maar zijn interval
    # bepaalt wel hoe snel een bon beschikbaar wordt zodra er wél iets ligt.
    planner = env.ref('stock.ir_cron_scheduler_action', raise_if_not_found=False)
    add('')
    add('  GEPLANDE ACTIE "Aanvullen: start planner"')
    if planner:
        add('    actief        : %s' % planner.active)
        add('    interval      : elke %s %s' % (planner.interval_number, planner.interval_type))
        add('    laatste ronde : %s' % (planner.lastcall or '-'))
        add('    volgende ronde: %s' % (planner.nextcall or '-'))
    else:
        add('    NIET GEVONDEN')

add('')
add('=== EINDE ===')

log('\n'.join(regels))

# Open meteen het logboek, met de nieuwste lijn bovenaan.
action = {
    'type': 'ir.actions.act_window',
    'name': 'Logboek — ontbrekend stuk',
    'res_model': 'ir.logging',
    'view_mode': 'list,form',
    'domain': [('path', '=', 'action'), ('func', '=', '* Ontbrekend stuk onderzoeken')],
}
