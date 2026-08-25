# * Pickketen loggen
#
# Code van de contextuele serveractie op verkooporders (Instellingen -> Technisch
# -> Serveracties), model Verkooporder, type Python-code.
#
# LEEST ALLEEN. Er wordt niets aangemaakt, gewijzigd of gevalideerd; de actie mag
# dus gerust meermaals lopen.
#
# Wat ze verzamelt, per geselecteerd order (en per order dat het vervangt):
#   1. het order zelf: status, herkomst, klantreferentie, wie het aanmaakte;
#   2. elke bon eraan: soort, status, bron- en bestemmingslocatie, en of die twee
#      afwijken van wat de bewerkingssoort normaal invult -- dat is de vlag die een
#      omgekeerde bon verraadt;
#   3. elke verplaatsingslijn: aantallen, ketenlinks (waar ze vandaan komt en
#      waar ze naartoe voedt), aanvoermethode, regel, retourherkomst;
#   4. voor afgewerkte lijnen: wat er echt geboekt is, van locatie naar locatie;
#   5. de chatter van elke bon, zodat zichtbaar wordt wie wat wanneer deed;
#   6. tot slot een scan over alle recente VASA-bonnen met afwijkende locaties,
#      om te zien of er nog van dezelfde soort openstaan.
#
# De uitvoer komt in het logboek terecht (Instellingen -> Technisch -> Logboek).
# De actie opent dat logboek meteen; open de bovenste lijn en kopieer het veld
# Bericht.

# Vervangingsorders die onderzocht worden als er niets geselecteerd is.
ORDER_NAMES = ['S03694', 'S03695', 'S03696']

# Vanaf wanneer de slotscan naar afwijkende bonnen kijkt.
SCAN_VANAF = '2026-08-01 00:00:00'

# Een levering kan honderden lijnen tellen; meer dan dit uitschrijven maakt het
# log onleesbaar zonder nog iets bij te leren.
MAX_LIJNEN = 40


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
    return ' '.join(tekst.split())[:300]


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

# --- 1. Welke orders bekijken we? -------------------------------------------
orders = records if records else (record if record else None)
if not orders:
    orders = env['sale.order'].search([('name', 'in', ORDER_NAMES)])

# Een vervangingsorder draagt de naam van het order dat het verving in Herkomst.
# Dat oude order hoort erbij: daar zit de geschiedenis van vóór de pickstap.
vervangen_namen = [o.origin for o in orders if o.origin]
if vervangen_namen:
    orders = orders | env['sale.order'].search([('name', 'in', vervangen_namen)])

add('=== PICKKETEN LOGGEN — %s UTC ===' % time.strftime('%Y-%m-%d %H:%M:%S'))
add('Orders: %s' % ', '.join(orders.mapped('name')))

for order in orders.sorted('name'):
    add('')
    add('#' * 78)
    add('# VERKOOPORDER %s (id %s)' % (order.name, order.id))
    add('#' * 78)
    add('  status           : %s' % order.state)
    add('  herkomst         : %s' % (order.origin or '-'))
    add('  klantreferentie  : %s' % (order.client_order_ref or '-'))
    add('  klant            : %s' % naam(order.partner_id))
    add('  magazijn         : %s' % naam(order.warehouse_id))
    add('  aangemaakt       : %s' % stempel(order))
    add('  laatst gewijzigd : %s door %s' % (order.write_date, naam(order.write_uid)))
    add('  groep            : %s (id %s)' % (naam(order.procurement_group_id),
                                             order.procurement_group_id.id or 0))

    # picking_ids toont enkel de bonnen die nog aan het order hangen; via de
    # groep zien we ook wat losgekoppeld of geannuleerd raakte.
    bonnen = order.picking_ids
    if order.procurement_group_id:
        bonnen = bonnen | env['stock.picking'].search(
            [('group_id', '=', order.procurement_group_id.id)])
    bonnen = bonnen.sorted('id')
    add('  bonnen           : %s' % (', '.join(bonnen.mapped('name')) or 'geen'))

    for bon in bonnen:
        soort = bon.picking_type_id
        # De kern van het onderzoek: wijken de locaties af van wat de
        # bewerkingssoort standaard invult? Bij een uitgaande bon is een
        # afwijkende bestemming normaal (dat is het klantadres); bij een interne
        # bon betekent een afwijking dat iemand de locaties heeft aangepast, of
        # dat de bon als retour is aangemaakt.
        afwijkende_bron = bon.location_id != soort.default_location_src_id
        afwijkende_best = bon.location_dest_id != soort.default_location_dest_id
        vlag = ''
        if afwijkende_bron or afwijkende_best:
            vlag = '   <== LOCATIES WIJKEN AF VAN DE BEWERKINGSSOORT'
        if (bon.location_id == soort.default_location_dest_id
                and bon.location_dest_id == soort.default_location_src_id):
            vlag = '   <== BRON EN BESTEMMING ZIJN OMGEWISSELD'

        add('')
        add('  ' + '-' * 74)
        add('  BON %s (id %s) — %s%s' % (bon.name, bon.id, bon.state, vlag))
        add('  ' + '-' * 74)
        add('    bewerkingssoort : %s (id %s, code %s)' % (naam(soort), soort.id, soort.code))
        add('    standaard       : %s -> %s' % (naam(soort.default_location_src_id),
                                                naam(soort.default_location_dest_id)))
        add('    op deze bon     : %s -> %s' % (naam(bon.location_id), naam(bon.location_dest_id)))
        add('    brondocument    : %s' % (bon.origin or '-'))
        add('    retour van      : %s' % (naam(bon.return_id) if bon.return_id else 'niet als retour aangemaakt'))
        add('    backorder van   : %s' % (naam(bon.backorder_id) if bon.backorder_id else '-'))
        add('    groep           : %s (id %s)' % (naam(bon.group_id), bon.group_id.id or 0))
        add('    gepland         : %s' % bon.scheduled_date)
        add('    afgewerkt op    : %s' % (bon.date_done or '-'))
        add('    aangemaakt      : %s' % stempel(bon))
        add('    gewijzigd       : %s door %s' % (bon.write_date, naam(bon.write_uid)))

        # Leveringen worden per klant gegroepeerd, dus een bon kan ook lijnen van
        # andere orders bevatten. Die tellen we enkel; uitschrijven maakt het log
        # onleesbaar (en op productie loopt dat in de duizenden lijnen).
        eigen = bon.move_ids.filtered(lambda m: m.sale_line_id.order_id == order)
        vreemd = bon.move_ids - eigen
        add('    lijnen          : %s van dit order, %s van andere orders' % (
            len(eigen), len(vreemd)))
        if not eigen:
            # Geen enkele lijn van dit order: dan tonen we de eerste vijftig,
            # anders blijft een handmatig aangemaakte bon (die geen orderlijn
            # draagt) volledig onzichtbaar.
            eigen = bon.move_ids[:50]

        if len(eigen) > MAX_LIJNEN:
            add('    (enkel de eerste %s lijnen worden uitgeschreven)' % MAX_LIJNEN)
            eigen = eigen[:MAX_LIJNEN]

        for move in eigen.sorted('id'):
            add('    * lijn %s  %s  [%s]  vraag %s / geboekt %s / afgevinkt %s' % (
                move.id, naam(move.product_id), move.state,
                move.product_uom_qty, move.quantity, move.picked))
            add('        %s -> %s  (eind %s)  aanvoer %s  regel: %s' % (
                naam(move.location_id), naam(move.location_dest_id),
                naam(move.location_final_id), move.procure_method,
                naam(move.rule_id) if move.rule_id else 'geen (handmatig aangemaakt)'))
            add('        keten: gevoed door %s, voedt %s | retour van lijn %s | orderlijn %s' % (
                move.move_orig_ids.ids or 'niets', move.move_dest_ids.ids or 'niets',
                move.origin_returned_move_id.id or '-', move.sale_line_id.id or 'geen'))
            add('        gemaakt %s | gewijzigd %s door %s' % (
                stempel(move), move.write_date, naam(move.write_uid)))
            if move.state == 'done':
                # Wat er echt geboekt is. Dit is de enige bron die vertelt welke
                # kant de goederen op zijn gegaan.
                for lijn in move.move_line_ids[:10]:
                    add('        GEBOEKT %s %s van %s naar %s' % (
                        lijn.quantity, naam(lijn.product_uom_id),
                        naam(lijn.location_id), naam(lijn.location_dest_id)))

        berichten = env['mail.message'].search(
            [('model', '=', 'stock.picking'), ('res_id', '=', bon.id)], order='id')
        add('    chatter (%s berichten):' % len(berichten))
        for bericht in berichten[:40]:
            add('      [%s] %s: %s' % (bericht.date, naam(bericht.author_id) or 'systeem',
                                       plat(bericht.body) or '(enkel bijlagen of tracking)'))
            for volg in bericht.tracking_value_ids:
                add('           veld %s: %s -> %s' % (volg.field_id.name or '?',
                                                      waarde(volg, 'old'), waarde(volg, 'new')))

# --- 6. Staan er nog meer bonnen met afwijkende locaties open? ---------------
add('')
add('#' * 78)
add('# SCAN — bonnen met afwijkende locaties, aangemaakt vanaf %s' % SCAN_VANAF)
add('#' * 78)

vasa = env['stock.warehouse'].search([('name', 'ilike', 'Vasa')], limit=1)
soorten = env['stock.picking.type'].search([('warehouse_id', '=', vasa.id)])
kandidaten = env['stock.picking'].search([
    ('picking_type_id', 'in', soorten.ids),
    ('state', '!=', 'cancel'),
    ('create_date', '>=', SCAN_VANAF),
], order='id')

gevonden = 0
for bon in kandidaten:
    soort = bon.picking_type_id
    # Enkel interne bonnen: bij in- en uitgaande bonnen is een afwijkende
    # partnerlocatie de normale gang van zaken.
    if soort.code != 'internal':
        continue
    if (bon.location_id == soort.default_location_src_id
            and bon.location_dest_id == soort.default_location_dest_id):
        continue
    gevonden += 1
    add('  %-16s %-10s %-28s %s -> %s   (retour van %s, %s)' % (
        bon.name, bon.state, bon.origin or '-',
        naam(bon.location_id), naam(bon.location_dest_id),
        naam(bon.return_id) if bon.return_id else 'geen',
        stempel(bon)))

add('  Totaal afwijkend: %s van %s onderzochte VASA-bonnen.' % (gevonden, len(kandidaten)))
add('')
add('=== EINDE ===')

log('\n'.join(regels))

# Open meteen het logboek, met de nieuwste lijn bovenaan.
action = {
    'type': 'ir.actions.act_window',
    'name': 'Logboek — pickketen',
    'res_model': 'ir.logging',
    'view_mode': 'list,form',
    'domain': [('path', '=', 'action'), ('func', '=', '* Pickketen loggen')],
}
