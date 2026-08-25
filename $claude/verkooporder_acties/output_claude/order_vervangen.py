# * Order vervangen
#
# Code van de contextuele serveractie op verkooporders (Instellingen -> Technisch
# -> Serveracties). Per geselecteerd order:
#   1. het order annuleren;
#   2. de klantreferentie van het geannuleerde order markeren met een "x";
#   3. een kopie maken die de oorspronkelijke klantreferentie overneemt;
#   4. die kopie meteen bevestigen.
#
# Werkt zowel op een enkel order als op een selectie uit de lijst.

new_orders = env['sale.order']

for order in records:
    # Onthouden vóór de annulatie: hierna wordt de referentie op het oude order
    # gewijzigd, en het nieuwe order moet de originele waarde krijgen.
    client_order_ref = order.client_order_ref

    # Annuleren zonder het annulatie-mailvenster (dat verschijnt normaal bij een
    # bevestigd order en zou de actie onderbreken). Een vergrendeld order geeft
    # hier vanzelf een duidelijke foutmelding; die laten we staan.
    order.with_context(disable_cancel_warning=True).action_cancel()

    # De "x" hangt aan het GEANNULEERDE order. Zo komt de referentie vrij voor
    # het nieuwe order en waarschuwt Odoo niet over twee orders met dezelfde
    # klantreferentie. Geen referentie ingevuld -> niets te markeren.
    if client_order_ref:
        order['client_order_ref'] = client_order_ref + 'x'

    # Een kopie start altijd als concept (state heeft copy=False).
    new_order = order.copy()
    # client_order_ref heeft copy=False, dus expliciet overnemen.
    new_order['client_order_ref'] = client_order_ref
    # Spoor terug naar het order dat vervangen werd.
    new_order['origin'] = order.name
    new_order.action_confirm()

    new_orders |= new_order

# Toon het resultaat: het nieuwe order zelf bij één vervanging, anders de lijst.
action = {
    'type': 'ir.actions.act_window',
    'name': 'Nieuwe orders',
    'res_model': 'sale.order',
    'view_mode': 'form' if len(new_orders) == 1 else 'list,form',
    'res_id': new_orders.id if len(new_orders) == 1 else False,
    'domain': [('id', 'in', new_orders.ids)],
}
