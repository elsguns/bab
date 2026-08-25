# * Backorder-briefjes herstellen
#
# Code van de serveractie op overboekingen (Instellingen -> Technisch ->
# Serveracties), model Verplaatsing, type Python-code. Zet het vinkje
# "Productenmatrix printed" terug op onwaar voor de bonnen die het ten onrechte
# dragen.
#
# EENMALIG. De automatiseringsregel "* Backorder-briefje opnieuw als
# niet-geprint" vangt alle nieuwe gevallen af, maar vuurt enkel bij een
# schrijfactie en beoordeelt het domein pas ná die actie: valideer je zo'n
# backorder, dan staat hij op dat moment al op Gereed en valt hij net buiten het
# domein. De bonnen die vandaag al fout staan raken dus nooit vanzelf hersteld —
# vandaar deze actie.
#
# ACHTERGROND. Tot commit 7e7f3da zette bab_stock_delivery elke nieuwe backorder
# meteen op "geprint", om te vermijden dat een deellevering een tweede briefje
# zou uitlokken. Bij BAB wordt echter per product ontvangen en bevestigd, zodat
# een pickbon zich telkens verder opsplitst: enkel de eerste bevestiging leverde
# nog een briefje op, de rest van de goederen ging zonder papier buiten.
#
# WELKE BONNEN. Het briefje kan alleen renderen op een pickbon die Gereed is
# (het rapport weigert de rest). Staat het vinkje aan terwijl de bon dat nog niet
# is, dan komt dat vinkje per definitie van de oude code en nooit van een echte
# afdruk. Datzelfde domein staat in de automatiseringsregel, zodat beide precies
# hetzelfde doen.
#
# UITVOEREN. Selectie speelt geen rol: de actie zoekt haar eigen bonnen. Open een
# willekeurige lijst van overboekingen, vink één regel aan en kies de actie in
# het Actie-menu. Herhalen mag: wat al hersteld is, valt buiten het domein.
#
# De actie opent het logboek (Instellingen -> Technisch -> Logboek) met de
# herstelde bonnen erin; open de bovenste lijn en lees het veld Bericht.

herstellen = env['stock.picking'].search([
    ('matrix_printed', '=', True),
    ('state', 'not in', ('done', 'cancel')),
], order='id')

regels = ['=== BACKORDER-BRIEFJES HERSTELLEN ===',
          'Gevonden: %s bonnen met een vinkje dat niet van een afdruk komt.' % len(herstellen)]
for bon in herstellen:
    regels.append('  %-16s %-10s %-24s backorder van %s' % (
        bon.name, bon.state, bon.picking_type_id.display_name,
        bon.backorder_id.name if bon.backorder_id else 'geen'))

# write() en niet "herstellen.matrix_printed = False": safe_eval verbiedt
# attribuuttoewijzing (STORE_ATTR) in een serveractie.
herstellen.write({'matrix_printed': False})

regels.append('Vinkje weggezet; deze bonnen verschijnen weer in de filter "Nog niet geprint".')
log('\n'.join(regels))

# Open meteen het logboek, met de nieuwste lijn bovenaan.
action = {
    'type': 'ir.actions.act_window',
    'name': 'Logboek — backorder-briefjes',
    'res_model': 'ir.logging',
    'view_mode': 'list,form',
    'domain': [('path', '=', 'action'), ('func', '=', '* Backorder-briefjes herstellen')],
}
