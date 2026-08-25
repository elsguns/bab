# * Wachtende bon alsnog batchen
#
# Code van de serveractie achter de automatiseringsregel met dezelfde naam
# (Instellingen -> Technisch -> Automatiseringsregels).
#
# INSTELLINGEN VAN DE REGEL
#   Model               : Verplaatsing (stock.picking -- zo heet het model in
#                         het Nederlands bij BAB; "Voorraadverplaatsing" is
#                         stock.move en is hier niet de bedoeling)
#   Activeren           : Bij het opslaan (of Bij bijwerken, beide werken)
#   Bij het updaten     : enkel Status. Zet er GEEN Batchepicking bij: dan vuurt
#                         de regel ook wanneer iemand een bon bewust uit een
#                         batch haalt, en zet ze hem meteen weer in een batch.
#   Toe te passen op    : [("state", "=", "assigned"), ("batch_id", "=", False)]
#   Actie               : Python-code uitvoeren (deze code)
#
# WAAROM. Odoo zoekt maar op twee momenten een batch voor een bon: bij het
# bevestigen ervan, en voor een backorder meteen na het valideren van zijn
# voorganger. Op zo'n moment neemt hij de bon enkel mee als die dan al op Klaar
# staat -- _is_auto_batchable() begint met "if self.state != 'assigned':
# return False". Een bon die op dat ogenblik niets kon reserveren (0 op
# voorraad, of een levering die nog op haar pickbon wacht) valt dus buiten de
# batch, en Odoo komt daar nadien nooit op terug: hij blijft batchloos, staat op
# geen enkel briefje en wordt dus nooit gescand. Zo bleef bij BATCH/02473 één
# stuk 51742-98-M in VAS/OUT/00300 hangen -- ongeleverd en onfactureerbaar,
# terwijl het fysiek wél mee de deur uit was.
#
# WAT DEZE REGEL DOET. Ze geeft de bon die tweede kans op het enige moment
# waarop Odoo ze niet geeft: zodra hij alsnog Klaar wordt. Ze roept daarvoor
# exact dezelfde standaardmethode aan die Odoo bij het bevestigen gebruikt
# (_find_auto_batch), dus met dezelfde regels: enkel bewerkingssoorten waar
# "Automatische batches" aan staat, dezelfde groepering (bij BAB per klant),
# dezelfde maxima. Er komt geen eigen logica bij.
#
# WAAR DE BON TERECHTKOMT (afgesproken 14 augustus 2026). _find_auto_batch zoekt
# eerst een onafgewerkte batch van dezelfde soort voor dezelfde klant -- bij BAB
# zowel een batch in concept als een batch in uitvoering, omdat "batch meteen
# bevestigen" aanstaat -- dan een andere batchloze bon om mee te paren, en maakt
# pas als laatste redmiddel een nieuwe batch met die ene bon alleen. Dat is
# precies wat gevraagd is: aansluiten bij een bestaande onafgewerkte batch, en
# anders een nieuwe. Een restje van één stuk kan dus zijn eigen batch krijgen.
#
# De regel doet niets aan bonnen die al in een batch zitten, en niets aan
# bewerkingssoorten zonder automatische batches. Ze mag dus gerust blijven
# staan; ze vuurt alleen op de uitzonderingsgevallen.

# In een automatiseringsregel krijg je de gewijzigde bonnen in "records"; bij
# een handmatige uitvoering vanuit het Actie-menu kan dat één record zijn.
bonnen = records if records else record

for bon in bonnen:
    # Dubbele controle naast het domein van de regel: batch.action_confirm()
    # bevestigt de bonnen van de nieuwe batch opnieuw, en dan komen we hier een
    # tweede keer langs. Zonder deze controle zou dat een lus worden.
    if bon.state != 'assigned' or bon.batch_id:
        continue

    # sudo(): batches zijn zichtbaar per bedrijf, en de standaardmethode zoekt
    # zelf ook met sudo. Zonder dit vindt een gebruiker met één actief bedrijf
    # de open batch van het andere bedrijf niet.
    batch = bon.sudo()._find_auto_batch()

    if batch:
        # In de chatter blijft zichtbaar dat dit niet met de hand gebeurde --
        # anders lijkt het magazijn plots een batch te zien verschijnen.
        bon.message_post(body=(
            'Automatisch toegevoegd aan %s. Deze bon stond nog niet op Klaar '
            'toen hij bevestigd werd en viel daardoor buiten de batches.'
            % batch.name))
