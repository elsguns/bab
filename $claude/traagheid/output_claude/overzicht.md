# Traagheid bij ontvangsten — overzicht

_Onderzoek 2026-08-07 t/m 2026-08-09. Volledig dagboek: `$claude/status.md`._

## De klacht

"Ontvangsten gaan traag." Na doorvragen bleek dat te gaan over **het invullen van aantallen,
lijn per lijn** — niet over het valideren. Dat onderscheid is dagen te laat gemaakt, en het
verklaart waarom de eerste drie ingrepen niets deden aan wat de gebruiker voelde.

## De oorzaak

Bij elk ingevuld aantal stuurt de webclient een `onchange` naar de server voor de **picking**.
De implementatie in `web/models/models.py` neemt daar **alle** ids van de one2many — niet de
veertig op het scherm — en herrekent elk berekend veld uit de lijstweergave voor **alle** regels.

Onvermijdelijk: `models._has_onchange()` vuurt zodra een veld dat van `move_ids` afhangt óók in
de weergave staat, en `stock.picking.state` (de statusbalk) is precies dat.

Kost: **~0,75 ms per regel**, strikt lineair. De melding *Laden* verschijnt rond 250 ms, dus de
grens ligt rond **330 regels**.

| ontvangst | regels | onchange |
|---|---|---|
| WH/IN/00099 | 185 | 145 ms |
| WH/IN/00184 | 450 | 309 ms |
| VAS/IN/00084 | 2484 | 1898 ms |

## Wat wél hielp

**`forecast_uit_ontvangstlijst.html`** — `forecast_availability` uit de lijst van het tabblad
Bewerkingen. **2405 → 1848 ms, 23%.** Het enige veld in die lijst dat meetbaar weegt. Prijs: het
prognose-icoontje verliest zijn kleurbepaling. Toegepast in de werkkopie als view
`stock.picking.form.geen.forecast.bab`; nog niet in productie.

## Wat overblijft

Voor ontvangsten van duizenden regels zijn er nog maar twee remedies, en beide zijn
organisatorisch, niet technisch:

1. **Opsplitsen tot ~300 regels** per ontvangst → onder de drempel, melding verdwijnt.
2. **De barcode-app** → gebruikt dit formulier niet, dus geen onchange over alle regels.

## Wat geen oplossing bleek

In `geen oplossing/` staat wat wel een echte, gemeten verbetering is maar **de klacht niet raakt**.
Niet weggooien dus — het is alleen het verkeerde probleem.

- **`batchtotalen_versnellen.html`** — de vier totalen op `stock.picking.batch` van een Python-lus
  naar een SQL-aggregaat. Opslaan van 185 regels: **770 → 596 ms**. Raakt alleen het *opslaan* van
  overdrachten **in een batch**; het invullen niet, en ontvangsten buiten een batch al helemaal
  niet. Toegepast in de werkkopie.

Zonder eigen bestand, alleen in `status.md`:

- **`bab_stock_deferred_reservation`** (module in de projectmap) — herreservatie na het valideren
  naar een cron. Valideren **6857 → 3727 ms, 46%**. Raakt het *valideren*, niet het invullen.
  Gebouwd en gemeten, niet uitgerold.
- **`stock.picking_no_auto_reserve`** — dezelfde 46% met één systeemparameter, maar de reservatie
  blijft dan liggen tot de scheduler.
- **`by_date` op de bewerkingssoorten** — gemeten, **nul effect**, ook gesimuleerd op de
  snapshotdatum. Niet opnieuw proberen.
- **Meer workers of RAM** — het is single-core Python-werk in één request. Doet niets.
- **Upgrade naar 19 of 20** — `_update_reserved_quantity` en `_track_qty_received` zijn
  byte-identiek in 18.0 en 19.0. Het read-replica van 20 schaalt leesverkeer, terwijl dit
  schrijfwerk is.

## Methode

`traagheid_nakijken.html` beschrijft hoe je dit soort klachten uitzoekt. Kort: vraag eerst welke
handeling traag is, kijk dan in het netwerktabblad welke oproep vuurt, en zet pas daarna de
profiler aan. In dit onderzoek sneuvelden drie hypotheses bij meting voordat de profiler het
antwoord gaf.
