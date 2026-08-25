# * Voorraadcijfer onderzoeken
#
# Code van de serveractie (Instellingen -> Technisch -> Serveracties), model
# Serveractie (ir.actions.server), type Python-code. Zo verschijnt op het
# formulier de knop Uitvoeren en hoef je geen record te selecteren.
#
# LEEST ALLEEN. Er wordt niets aangemaakt, gewijzigd of gevalideerd; de actie
# mag dus gerust meermaals lopen.
#
# WAAROM. Op de ontvangst van 58913/49 toont het briefje 5 stuks "op stock",
# terwijl er 6 ontvangen en 6 gereserveerd zijn en er in het rek dus niets meer
# ligt. De vraag is welk cijfer die 5 precies is en waar het vandaan komt.
# Belangrijk om te weten: het briefje leest de vrije voorraad van de variant,
# en dat cijfer telt ALLE interne locaties van het magazijn mee -- ook de
# uitgaande zone. Goederen die al gepickt zijn maar nog niet vertrokken staan
# fysiek niet meer in het rek, maar tellen daar wel in mee zolang geen enkele
# levering ze gereserveerd heeft. §1 en §2 zetten die twee naast elkaar.
#
# WAT ZE VERZAMELT
#   1. per variant de voorraadcijfers, eerst globaal en dan per interne locatie
#      apart -- het verschil tussen die twee is de kern van de vraag;
#   2. de voorraadposten per locatie: aanwezig, gereserveerd en vrij;
#   3. elke verplaatsing van deze varianten, afgewerkt en openstaand;
#   4. wie de voorraad vasthoudt: de openstaande lijnen met een reservatie;
#   5. de aankooplijnen -- dat is de o-lijn (ontvangen) van het briefje;
#   6. het briefje zelf: de exacte cijfers die de productenmatrix met
#      reservaties zou drukken voor de opgegeven bon (o / r / tekort / vrij / i).
#
# De uitvoer komt in het logboek terecht (Instellingen -> Technisch -> Logboek).
# De actie opent dat logboek meteen; open de bovenste lijn en kopieer het veld
# Bericht.

# Het artikel. Een fragment volstaat: 58913-49 vindt alle maten van die kleur.
PRODUCT_PREFIX = '58913-49'

# De bon waarop het briefje geprint is (de ontvangst). Vul die in, dan
# reproduceert §6 exact de cijfers van dat briefje. Leeg laten slaat §6 over.
BON_NAAM = 'VAS/IN/00103'

# Het magazijn waarvan we de locaties apart doorrekenen.
MAGAZIJN = 'Vasa'

# Het sjabloon waarvan §8 de volledige arch uitschrijft. Leeg laten slaat §8
# over. Dit is het met de hand aangemaakte rapport uit §7.
SJABLOON_KEY = 'bab_stock_delivery.report_reservation_matrix_fix'

MAX_LIJNEN = 80


def naam(rec):
    return rec.display_name if rec else '-'


regels = []
add = regels.append

add('=== VOORRAADCIJFER ONDERZOEKEN — %s UTC ===' % time.strftime('%Y-%m-%d %H:%M:%S'))
add('Artikel %s · bon %s' % (PRODUCT_PREFIX, BON_NAAM or '-'))

varianten = env['product.product'].sudo().with_context(active_test=False).search([
    ('default_code', 'ilike', PRODUCT_PREFIX),
])

magazijn = env['stock.warehouse'].sudo().search([('name', 'ilike', MAGAZIJN)], limit=1)
locaties = env['stock.location'].sudo().search([
    ('id', 'child_of', magazijn.view_location_id.id),
    ('usage', '=', 'internal'),
])

# --- 1. De voorraadcijfers, globaal en per locatie -----------------------------
# free_qty is het cijfer dat het briefje als "vrij" (groen) drukt. Zonder
# locatiecontext telt het élke interne locatie mee; met context enkel die ene.
add('')
add('#' * 78)
add('# 1. VOORRAADCIJFERS PER VARIANT')
add('#' * 78)
add('Magazijn : %s' % naam(magazijn))
add('Interne locaties: %s' % ', '.join(locaties.mapped('complete_name')))

for variant in varianten.sorted('default_code'):
    add('')
    add('  %s (id %s)' % (naam(variant), variant.id))
    add('    globaal (alle interne locaties samen):')
    add('      aanwezig %s / vrij %s / verwacht %s / inkomend %s / uitgaand %s' % (
        variant.qty_available, variant.free_qty, variant.virtual_available,
        variant.incoming_qty, variant.outgoing_qty))
    for locatie in locaties:
        # De contextsleutel is 'location'; product._get_domain_locations leest die.
        per_locatie = variant.with_context(location=locatie.id)
        if not (per_locatie.qty_available or per_locatie.free_qty
                or per_locatie.incoming_qty or per_locatie.outgoing_qty):
            continue
        add('    %-28s aanwezig %s / vrij %s / inkomend %s / uitgaand %s' % (
            locatie.complete_name, per_locatie.qty_available, per_locatie.free_qty,
            per_locatie.incoming_qty, per_locatie.outgoing_qty))

# --- 2. De voorraadposten -----------------------------------------------------
add('')
add('#' * 78)
add('# 2. VOORRAADPOSTEN (quants), ook klant- en leverancierslocaties')
add('#' * 78)

quants = env['stock.quant'].sudo().search([('product_id', 'in', varianten.ids)])
for quant in quants.sorted(lambda q: (q.product_id.default_code or '',
                                      q.location_id.complete_name or '')):
    add('  %-22s %-34s aanwezig %6s   gereserveerd %6s   vrij %6s   (%s)' % (
        quant.product_id.default_code or '?', quant.location_id.complete_name,
        quant.quantity, quant.reserved_quantity, quant.available_quantity,
        quant.location_id.usage))
if not quants:
    add('  GEEN voorraadposten.')

# --- 3. Alle verplaatsingen ---------------------------------------------------
add('')
add('#' * 78)
add('# 3. VERPLAATSINGEN (afgewerkt en openstaand, ook geannuleerd)')
add('#' * 78)

moves = env['stock.move'].sudo().search([
    ('product_id', 'in', varianten.ids),
], order='date, id')
add('Aantal: %s' % len(moves))
if len(moves) > MAX_LIJNEN:
    add('(enkel de eerste %s worden uitgeschreven)' % MAX_LIJNEN)
    moves = moves[:MAX_LIJNEN]

for move in moves:
    bon = move.picking_id
    add('  %-22s %-16s %-11s vraag %5s / geboekt %5s   %s -> %s' % (
        move.product_id.default_code or '?',
        bon.name if bon else 'geen bon', move.state,
        move.product_uom_qty, move.quantity,
        naam(move.location_id), naam(move.location_dest_id)))
    add('      datum %s   herkomst %s   orderlijn %s   aankooplijn %s' % (
        move.date, move.origin or '-',
        move.sale_line_id.id or '-', move.purchase_line_id.id or '-'))

# --- 4. Wie houdt de voorraad vast? -------------------------------------------
# Een openstaande lijn met een geboekt aantag houdt quants gereserveerd; dat is
# precies wat het verschil maakt tussen "aanwezig" en "vrij".
add('')
add('#' * 78)
add('# 4. OPENSTAANDE LIJNEN MET EEN RESERVATIE')
add('#' * 78)

open_moves = env['stock.move'].sudo().search([
    ('product_id', 'in', varianten.ids),
    ('state', 'not in', ('done', 'cancel', 'draft')),
], order='id')
gevonden = 0
for move in open_moves:
    if not move.quantity:
        continue
    gevonden += 1
    bon = move.picking_id
    add('  %-22s %-16s %-11s reserveert %s uit %s   (klant %s)' % (
        move.product_id.default_code or '?',
        bon.name if bon else 'geen bon', move.state, move.quantity,
        naam(move.location_id), naam(bon.partner_id) if bon else '-'))
add('Openstaande lijnen mét reservatie: %s van %s' % (gevonden, len(open_moves)))

for move in open_moves:
    if move.quantity:
        continue
    bon = move.picking_id
    add('  ZONDER reservatie: %-22s %-16s %-11s vraagt %s uit %s' % (
        move.product_id.default_code or '?',
        bon.name if bon else 'geen bon', move.state,
        move.product_uom_qty, naam(move.location_id)))

# --- 5. De aankooplijnen (de o-lijn van het briefje) --------------------------
add('')
add('#' * 78)
add('# 5. AANKOOPLIJNEN — hieruit komt het cijfer "ontvangen" (o)')
add('#' * 78)

po_lijnen = env['purchase.order.line'].sudo().search([
    ('product_id', 'in', varianten.ids),
    ('state', 'in', ('purchase', 'done')),
], order='id')
for lijn in po_lijnen:
    add('  %-22s %-14s %-9s besteld %5s / ontvangen %5s / gefactureerd %5s   (%s)' % (
        lijn.product_id.default_code or '?', lijn.order_id.name, lijn.state,
        lijn.product_qty, lijn.qty_received, lijn.qty_invoiced,
        lijn.order_id.date_order))
if not po_lijnen:
    add('  GEEN lopende of afgesloten aankooplijnen.')

# --- 6. Het briefje reproduceren ----------------------------------------------
# Dit roept exact dezelfde methode aan als de PDF, dus de cijfers hieronder zijn
# letterlijk wat er gedrukt wordt.
if BON_NAAM:
    add('')
    add('#' * 78)
    add('# 6. WAT DE PRODUCTENMATRIX MET RESERVATIES DRUKT VOOR %s' % BON_NAAM)
    add('#' * 78)

    bonnen = env['stock.picking'].sudo().search([('name', '=', BON_NAAM)])
    add('Gevonden: %s' % (', '.join(bonnen.mapped('name')) or 'GEEN'))

    for bon in bonnen:
        add('  BON %s — %s — %s lijnen' % (bon.name, bon.state, len(bon.move_ids)))
        blokken = bon._get_reservation_matrix_blocks()
        add('  Blokken op het briefje: %s' % len(blokken))
        for blok in blokken:
            maten = blok['sizes']
            add('')
            add('    PRODUCT %s' % naam(blok['template']))
            add('      maten: %s' % ', '.join([m['name'] for m in maten]))
            for rij in blok['rows']:
                add('      kleur %s:' % rij['colour_name'])
                for index in range(len(maten)):
                    cel = rij['cells'][index]
                    if not cel:
                        add('        %-10s (geen lijn op deze bon)' % maten[index]['name'])
                        continue
                    add('        %-10s o=%s  r=%s  tekort=%s  vrij=%s  i=%s' % (
                        maten[index]['name'], cel['received'], cel['reserved'],
                        cel['shortage'], cel['surplus'], cel['incoming']))

# --- 7. Welke rapporten bestaan er, en wat draaien ze? ------------------------
# Het briefje dat het magazijn print heet "(TIJDELIJKE FIX)" en is dus niet
# hetzelfde als het rapport uit de module. §6 hierboven roept de modulecode aan;
# deze paragraaf zegt of het geprinte rapport op diezelfde code steunt of op een
# eigen sjabloon met eigen cijfers.
add('')
add('#' * 78)
add('# 7. DE RAPPORTEN ZELF')
add('#' * 78)

rapporten = env['ir.actions.report'].sudo().search([
    '|', ('name', 'ilike', 'matrix'), ('report_name', 'ilike', 'matrix'),
])
add('Gevonden rapporten: %s' % len(rapporten))

for rapport in rapporten:
    add('')
    add('  RAPPORT %s (id %s)' % (rapport.name, rapport.id))
    add('    technische naam : %s' % rapport.report_name)
    add('    model / type    : %s / %s' % (rapport.model, rapport.report_type))
    add('    bestandsnaam    : %s' % (rapport.print_report_name or '-'))
    add('    aangemaakt      : %s door %s' % (rapport.create_date, naam(rapport.create_uid)))
    add('    gewijzigd       : %s door %s' % (rapport.write_date, naam(rapport.write_uid)))
    imd = env['ir.model.data'].sudo().search([
        ('model', '=', 'ir.actions.report'), ('res_id', '=', rapport.id)], limit=1)
    add('    xmlid           : %s' % (
        '%s.%s' % (imd.module, imd.name) if imd else 'GEEN (met de hand aangemaakt)'))

    # Het sjabloon achter het rapport: is de arch aangepast, en rekent hij zelf?
    sjablonen = env['ir.ui.view'].sudo().with_context(active_test=False).search([
        ('key', '=', rapport.report_name)])
    for sjabloon in sjablonen:
        arch = sjabloon.arch_db or ''
        add('    SJABLOON %s (id %s, type %s)' % (sjabloon.key, sjabloon.id, sjabloon.type))
        add('      naam          : %s' % sjabloon.name)
        add('      gewijzigd     : %s door %s' % (sjabloon.write_date, naam(sjabloon.write_uid)))
        add('      erft van      : %s' % (naam(sjabloon.inherit_id) if sjabloon.inherit_id else '-'))
        add('      lengte arch   : %s tekens' % len(arch))
        # Welke bron gebruikt hij voor zijn cijfers? Een eigen berekening
        # verraadt zich door een x_-veld of een eigen som in de arch.
        for sleutel in ['_get_reservation_matrix_blocks', 'surplus', 'free_qty',
                        'x_ontvangst', 'x_ontvangen', 'qty_available', 'received']:
            if sleutel in arch:
                add('      bevat "%s"' % sleutel)

# Handmatige velden die zo'n omweg zouden verraden.
add('')
add('  HANDMATIGE VELDEN op de betrokken modellen:')
handmatig = env['ir.model.fields'].sudo().search([
    ('state', '=', 'manual'),
    ('model', 'in', ('product.product', 'product.template', 'stock.move',
                     'stock.picking', 'stock.move.line')),
])
for veld in handmatig:
    add('    %-22s %-30s %s' % (veld.model, veld.name, veld.field_description))
if not handmatig:
    add('    geen')

# --- 8. De arch van het tijdelijke-fix-sjabloon -------------------------------
# §7 toonde dat dit sjabloon "free_qty" bevat en het moduleslabloon niet: het
# rekent dus zelf in QWeb in plaats van de cijfers van de modulecode over te
# nemen. Hieronder de volledige arch, regel per regel, zodat te lezen valt welk
# cijfer op welke regel van het briefje belandt. Geen giswerk.
if SJABLOON_KEY:
    add('')
    add('#' * 78)
    add('# 8. VOLLEDIGE ARCH VAN %s' % SJABLOON_KEY)
    add('#' * 78)

    sjablonen = env['ir.ui.view'].sudo().with_context(active_test=False).search([
        ('key', '=', SJABLOON_KEY)])
    add('Gevonden sjablonen: %s' % len(sjablonen))
    for sjabloon in sjablonen:
        add('')
        add('  SJABLOON %s (id %s) — %s' % (sjabloon.key, sjabloon.id, sjabloon.name))
        arch = sjabloon.arch_db or ''
        nummer = 0
        for lijn in arch.split('\n'):
            nummer += 1
            add('  %4s| %s' % (nummer, lijn.rstrip()))

add('')
add('=== EINDE ===')

log('\n'.join(regels))

action = {
    'type': 'ir.actions.act_window',
    'name': 'Logboek — voorraadcijfer',
    'res_model': 'ir.logging',
    'view_mode': 'list,form',
    'domain': [('path', '=', 'action'), ('func', '=', '* Voorraadcijfer onderzoeken')],
}
