# status — BAB (Babimex) · Odoo 18 (production project)

_Last updated: 2026-06-13_

## Open vraag na de $claude-herindeling (2026-08-23)

- `StoriesOfYou.be_Melanie+Jim_698.jpg` staat nu in `rapport_layout/input_klant/` — ik kon niet achterhalen bij welk onderwerp die foto hoort; zeg waar hij thuishoort.
- `traagheid/geen oplossing/` heet nu `traagheid/$old/`, volgens de vaste conventie voor vervangen werk.

## What this is
BAB prod runs on **Odoo 18** (live client). This project dir (`klanten/bab/18.0`,
git branch **18.0**) holds the client's own + 3rd-party modules:

- **babimex_custom** (18.0.1.0.7) — main client customization module.
- **babimex_website_sale** — client's webshop customization (overrides website_sale).
- **bab_stock_delivery** (18.0.1.0.0) — "Productenmatrix" delivery report. **Done +
  committed/pushed to branch 18.0** (see Done section below).
- 3rd-party/OCA: **mail_debrand**, **product_brand**, **website_odoo_debranding**.
- Loose data files at root: `account.email_template_edi_invoice_{de,en,fr,nl}.xml`,
  `product.template.form.xml`, `gls data.zip`.

⚠️ Several items still **untracked** in git (per `git status`): the account email
templates, `product.template.form.xml`, `.idea/`, `gls data.zip`. Commit/clean when
stable. (`bab_stock_delivery/` is now committed + pushed.)

## Run config (from `.idea/workspace.xml`)
- odoo-bin: `Odoo/18.0/odoo/odoo-bin` (venv: `Odoo/18.0/venv`)
- addons-path: `addons,../enterprise,../design-themes,../industry,../oca-osa,../oca,../oca/stock-logistics-warehouse,../osa,../tpa-osa,../tpa,$PROJECT_DIR$`
- **active dev DB: `odo18-20260105`** (port **5432**, `--dev all`); last `-u stock_quant_reservation_info`
- BAB prod snapshot also on 5432: **`bab18-20260207`**

## In flight — `website_sale_salesperson_order` (new module)
New osa module letting a **salesperson shop on the website on behalf of one of their
customers**. Lives in **`Odoo/18.0/osa/website_sale_salesperson_order`** (reachable via
`../osa` in the bab18 addons-path). Built & verified 2026-06-13.

- Clean v18 reimplementation of the old Probuse `shop_agents_sales_order_create`; dropped
  all custom agent fields, renamed everything to standard-Odoo conventions.
- "Customers" link sits in the **website account dropdown** (`portal.user_dropdown`),
  gated `sales_team.group_sale_salesman`. Dropdown lists only contacts where
  **`user_id` = logged-in salesperson**.
- Installed clean on `bab18-20260207` (`-i … --stop-after-init` → exit 0). Full rename map
  + design notes live in **`klanten/bab/19.0/$claude/status.md`** (2026-06-13 section).

### Open items for this module
1. **Coexistence with `babimex_website_sale`** not yet checked — both override website_sale.
   Re-test with the *full* bab18 addons-path (incl. `$PROJECT_DIR$` + oca) so babimex loads;
   my first install used a trimmed path, so babimex/mail_debrand/product_brand showed
   "not loaded" warnings (harmless for that test, but means coexistence is unverified).
2. Browser sanity check on the dev DB (account-dropdown link, dropdown = own customers only,
   non-salesperson redirected off `/shop/select_customer`, `user_id`=agent persists on SO).

## Done — `bab_stock_delivery` (Productenmatrix report) · 2026-06-13
Migrated from the bab19 project (19→18 = version bump only; all deps identical) and
finished off. Committed to branch **18.0** (`c002aa1` initial, `3290205` contact-dialog
field) and **pushed to `origin/18.0`** (`elsguns/bab`). Built/verified on dev DB
**`odo18-20260613`** (port 5432).

What it does:
- New **"Productenmatrix"** print action on `stock.picking` → prints the sale order
  variant matrix per hoofdproduct instead of the standard delivery slip. Standalone
  report on `web.basic_layout` (no company header/logo/footer, no move list); the
  standard Delivery Slip is untouched.
- One matrix per block = exactly **one A4 third (99mm)** so the sheet cuts into three
  equal strips; each strip repeats the **Customer + Order** heading. Quantities printed
  as **whole numbers**. Customer shown as `stock_location - name`. Order shown as
  `origin (picking name)` (the big picking-name title was dropped).
- **Bulk print** over several deliveries: matrices grouped/sorted **by hoofdproduct**
  (`stock.picking._get_matrix_blocks()`), with a **new page per hoofdproduct**.
- New field **`res.partner.stock_location`** (Integer): on the main partner form after
  `property_delivery_carrier_id`, AND on the Create-Contact dialog after "Contact Name",
  visible only for `type == 'delivery'`. Added `delivery` as a module dependency.

Gotchas hit (worth remembering):
- Exact mm thirds need the dedicated paperformat with **`disable_shrinking=True` +
  `dpi=96`** (Odoo passes `--zoom 96/dpi`; dpi 90 → 1.067× overflow). `vh`/`height:100%`
  are unreliable in wkhtmltopdf 0.12.5 (viewport ≠ page). See global memory
  `reference_odoo_wkhtmltopdf_mm_layout`.
- The Create-Contact dialog is the **inline form inside `view_partner_form`'s
  `child_ids`**, NOT `view_partner_address_form`; and `child_ids` also has a kanban with
  its own `name` field, so the xpath must be scoped to `/form` (`//field[@name='child_ids']/form//field[@name='name']`).

## Next steps (pick up here)
- _(switched here 2026-06-13 to continue bab18 work — add the day's focus below)_
- Back to **`website_sale_salesperson_order`** open items above (coexistence with
  `babimex_website_sale`, browser sanity check).

---

## 2026-08-06 — VASA op de bestaande stock.move-filters + orderlabels op transfers

Werkkopie **`bab18-20260618`** (port 5432).

- **stock.move favorieten**: de drie "Besteld"-filters (`ir_filters` id 8/9/13) staan op
  `location_id in [8, 11]` = Babimex WH/Stock + WH/Output. Voor VASA moeten `664`
  (VAS/Voorraad) en `667` (VAS/Uitgaand) erbij. De vier leverancier-filters (id 21/26/27/28)
  staan op `location_id in [4]` = Partners/Vendors, bedrijfsloos → werken al voor VASA.
  Nog **niet** toegepast in de werkkopie; enkel geadviseerd.
- **VASA levert in 2 stappen** — al zo geconfigureerd sinds 2026-07-10 in deze werkkopie
  (`stock.warehouse` 3, `delivery_steps=pick_ship`, route 11 met PICK 664→667 + OUT 667→5).
  De oude `664 → 5`-bewegingen dateren van vóór die omschakeling. **Check productie.**
  Let op: de en_US-routenaam zegt nog "Deliver in 1 step" — Odoo-kwaal, ook bij Babimex.
- **Orderlabels op transfers** (toegepast in de werkkopie): custom veld
  `stock.picking.x_sale_tag_ids`, many2many → `crm.tag`, related `sale_id.tag_ids`,
  **niet opgeslagen** (id 13590). Plus twee overervende weergaven `stock.picking.list.bab`
  (id 4006) en `stock.picking.internal.search.bab` (id 4007), beide op anker `origin`.
  308 transfers tonen labels. Zoeken werkt, groeperen/sorteren niet (niet opgeslagen).
- Guide: **`$claude/orderlabels/output_claude/transfers_orderlabels.html`**.

**Live in productie sinds 2026-08-06** — orderlabels op de transfers staan erop.
Studio 18 heeft trouwens wél een veldtype *Related Field* (eerdere notitie dat dat niet
kon, was fout); enige verschil is de gegenereerde naam `x_studio_related_field_<random>`.

## Next steps (pick up here)
- Filteraanpassing `[8, 11, 664, 667]` toepassen zodra bevestigd voor productie.
- Noteren welke technische veldnaam productie gekregen heeft (`x_sale_tag_ids` of de
  `x_studio_...`-variant) — bepaalt waar latere domeinen/rapporten op moeten mikken.
- Eventueel de VASA-uitbreiding toevoegen aan `$claude/backorders/output_claude/backorder_leverancier_filters.html`.

---

## 2026-08-06 (later die dag) — Productenmatrix naar de pickstap + stocklocatie per bedrijf

Twee losse eindjes, allebei met **hetzelfde patroon**: een tussenoplossing die
rechtstreeks in de database van productie is gezet, en een definitieve fix die in de
module klaarstaat maar nog **niet uitgerold** is. Zolang de module niet uitgerold is,
draait productie op de tussenoplossing.

### 1. Productenmatrix hoort op de pickbon, niet op de levering

VASA levert in twee stappen, dus de briefjes horen bij de **pickbon**, en pas als die
**klaar (`done`)** is. De guard in `report_delivery_matrix.py` liet enkel uitgaande
leveringen door (`picking_type_id.code != 'outgoing'` → `UserError`), en een pickbon
heeft code `internal`. Elke poging eindigde dus in de foutmelding.

`_get_report_values` is Python in de module en staat niet in de database, dus de
voorwaarde was niet rechtstreeks aan te passen. Omweg: Odoo zoekt bij het renderen een
model `report.<report_name>`; bestaat dat niet, dan valt het terug op een generieke
context en loopt het **niet door de guard**.

**Live in productie (enkel databankrecords, niets van de module gewijzigd):**
- QWeb-weergave `bab_stock_delivery.report_deliveryslip_matrix_pick` — roept enkel het
  bestaande sjabloon aan. Aangemaakt via code, want het veld `key` staat niet op het
  weergaveformulier.
- Kopie van de rapportactie, wijzend naar dat sjabloon.
- Serveractie `* Productenmatrix (pickbon)` — guard op picktype van het eigen magazijn
  (`picking_type_id.warehouse_id.pick_type_id`, geen vast ID) + status `done`, weigert
  een herdruk, zet `matrix_printed`.
- Serveractie `* Productenmatrix (pickbon) - herdruk` — identiek, `ALLOW_REPRINT = True`.
- Binding van de oude `* Productenmatrix` weggehaald (de actie zelf laten staan: die
  hoort bij de module en komt bij elke update terug).

Wat je hierbij inlevert: de **herdruk-bevestigingswizard**. Die roept intern
`action_print_matrix()` aan en belandt weer bij de oude guard; een wizard valt niet
vanuit de database te maken. Vandaar de tweede, uitdrukkelijke herdrukactie.

Gids + plakklare code: **`$claude/productenmatrix/output_claude/productenmatrix_pickbon.html`**.

**Klaar in de module, nog niet uitgerold:**
- `report_delivery_matrix.py` — guard = picktype van het magazijn + status `done`, met
  per bon de reden in de melding.
- `stock_picking.py` — hook `_action_done()` geschrapt (die markeerde uitgaande
  leveringen als afgedrukt; zinloos nu, en op pickbonnen zou hij averechts werken: een
  pickbon wordt precies bij het valideren printbaar).
- `views/stock_picking_views.xml` — `matrix_printed` zichtbaar bij `internal` i.p.v.
  `outgoing`. Niet exact: er is geen veld dat een pickbon onderscheidt van pak-/
  kwaliteits-/interne overboekingen, dus het vinkje toont op alle interne overboekingen
  (blijft daar leeg). Strakker zou een computed `is_matrix_pick` op `stock.picking` zijn.

### 2. Stocklocatie-nummering enkel voor Vasa International

`sale_order.action_confirm()`/`write()` en `res_partner.write()` nummerden afleveradressen
zonder naar het bedrijf te kijken. Contacten zijn gedeeld (`company_id` leeg), en Babimex
bevestigt ~250-300 orders/maand tegen VASA 10-30, dus Babimex at de reeksen op (de
Belgische reeks loopt maar tot 1999).

- **Tussenoplossing beschreven maar NIET uitgerold** (bevestigd 2026-08-07): de
  automatiseringsregel `* Stocklocatie enkel voor Vasa` op `res.partner` staat niet in
  productie. Gids blijft staan als achtergrond: **`$claude/stocklocaties/output_claude/stocklocatie_enkel_vasa.html`**.
  Gevolg: de foute nummers staan er nog en moeten na de uitrol eenmalig opgekuist worden.
- **Definitief, gecommit in `b9c9781` maar nog niet uitgerold**: vinkje
  `res.company.stock_location_numbering`. Staat standaard **uit**, ook bij VASA — na de
  uitrol moet iemand het aanzetten, anders stopt de nummering stil zonder foutmelding.

## Next steps (pick up here)
- **Bij de volgende module-uitrol door de externe partij**: volg de nazorggids
  **`$claude/uitrol_stock_delivery/output_claude/uitrol_bab_stock_delivery.html`** — vinkje `stock_location_numbering` aanvinken
  bij Vasa International (staat standaard uit, loopt stil mis als je het vergeet),
  eenmalige opkuis van de foute nummers via de droogtest, en daarna de vier records van
  de Productenmatrix-omweg opruimen. De binding van `* Productenmatrix (briefjes)` komt
  vanzelf terug: die staat in de module-XML zonder noupdate.
- Openstaand van eerder vandaag: filteraanpassing `[8, 11, 664, 667]`, en noteren welke
  technische veldnaam productie kreeg voor de orderlabels.

---

## 2026-08-06 (avond) — waar we gebleven zijn

### Afgewerkt vandaag, in de code maar NOG NIET gecommit
Werkboom `klanten/bab/18.0`, gewijzigd en niet gecommit:
- `models/stock_picking.py` — de **o** van "Productenmatrix met reservaties" telt nu
  alles op wat van de **lopende aanvoer** ontvangen is (ketenwandeling terug over
  `move_orig_ids`, over de pickstap heen) in plaats van enkel de laatste ontvangstbon.
- `report/reservation_matrix_report.xml` — legende `o = ontvangen (van de aanvoer)`.
- `IMPLEMENTATIE.html` — omschrijving van de o + de vermelding dat goederen zonder
  aanvoerketen niet op dit Vasa-overzicht komen.
- `models/report_delivery_matrix.py` + `views/stock_picking_views.xml` — jouw eigen
  wijziging: briefjes enkel voor **afgewerkte pickbonnen**.

### Eerder vandaag al gecommit + gepusht (`b9c9781`)
Briefjes-fix: de aantallen komen uit de moves van de overboeking i.p.v. uit de
verkooporderlijnen. Zat al rechtstreeks in productie via de weergave.

### Klaargezet, nog niet in productie
- `$claude/pickketen/output_claude/pickstap_inschuiven.py` — serveractie `* Pickstap
  toevoegen`: schuift de pickstap achteraf in bij VAS-leveringen die onder de
  één-staps-configuratie zijn aangemaakt. Volledig getest (MTO-keten blijft, geen
  nieuwe aankooporder, deels picken → backorder in de pickstap, gemengde levering).
- `$claude/verkooporder_acties/output_claude/order_vervangen.py` — serveractie `* Order vervangen`.
  Getest, maar **afgeraden** voor de pickstap-backlog: bij MTO breekt dat de keten en
  komt er een tweede aankooporder.
- `$claude/reservaties/` — DB-route voor de o zonder deploy: berekend veld
  `x_ontvangen_aanvoer` op `stock.move` + aangepaste template-arch.

## Morgen verder
1. **Beslissen** over de DB-route voor de o: zo laten (684/685 sleutels gelijk aan de
   moduleversie; 1 afwijking waar twee leveringen aan dezelfde ontvangstlijn hangen →
   4 i.p.v. 2), of de exacte variant bouwen (veld geeft `ontvangstid:aantal`-paren, de
   template ontdubbelt op id).
2. **Committen + pushen** van de vier bestanden hierboven.
3. Pickstap-retrofit uitvoeren op de VAS-backlog: eerst één levering, dan in blokken
   van 10-20.

## 2026-08-07 — afgewerkt

- **Gecommit + gepusht** (`312732a`): o-lijn op de volledige aanvoer, briefjes enkel op een
  afgewerkte pickbon, IMPLEMENTATIE + PDF bij.
- **Tijdelijke oplossing o-lijn staat in productie**, opgezet via
  `$claude/reservaties/output_claude/reservatie_o_lijn.html` (berekend veld `x_ontvangst_lijnen` op
  `stock.move` + aangepaste arch van `report_reservation_matrix`). Bewust **niet** gecommit.
- **Pickstap-retrofit uitgevoerd in productie** op de VAS-backlog.
- `uitrol_bab_stock_delivery.html` uitgebreid met **stap 4 — Omweg reservatierapport
  opruimen**; Controleren werd stap 5.

### Enige openstaande punt
De module-uitrol door de externe partij, en daarna de uitrolgids afwerken.

## 2026-08-07 (namiddag) — tussenoplossing o-lijn teruggedraaid

De DB-tussenoplossing voor de o-lijn is **niet blijven staan**. Verloop:

1. Berekend veld `x_ontvangst_lijnen` op `stock.move` + aangepaste arch van
   `report_reservation_matrix` in productie gezet. Werkte functioneel.
2. Productie werd traag, met "Verbinding verbroken" en "Too many requests" op odoo.sh.
   Verdachte: de eerste versie van dat veld liep de verplaatsingsketen terug met een lus
   over `move_orig_ids`; bij ontvangsten van duizenden lijnen (VAS/IN/00075 had er 4996)
   haalt dat per verplaatsing enorme hoeveelheden records op.
3. Veld verwijderd door Kristof. Arch teruggezet naar de moduleversie
   (`traagheid_nakijken.html`, sectie 5). Rapport werkt weer.

**Stand nu**: productie draait volledig op modulecode. De o toont dus weer enkel de
laatste ontvangst, tot de uitrol.

Wat er wél uit geleerd is en in de code zit (`b6fd542`): de o hoort verankerd op de
**aankooporder**, niet op de verplaatsingsketen — die keten overleeft een deelvalidatie
niet (`_prepare_move_split_vals` neemt enkel niet-afgewerkte bestemmingen mee).

Bewaard voor het geval we ooit opnieuw een DB-tussenoplossing willen: als het veld
terugkomt, hoort het op `product.product` en niet op `stock.move` — het getal hangt af
van de aankoopbestellingen van die variant, en op de move betaalt elk voorraadscherm
ervoor. Zie `reservaties/reservatie_o_lijn.html`.

### Nog open
Enkel de module-uitrol door de externe partij, daarna `uitrol_bab_stock_delivery.html`
afwerken (stap 4 is nu een louter controlestap).

## 2026-08-07 — $claude opgeruimd

Mappen enkel nog waar meerdere bestanden bij hetzelfde onderwerp horen:

- `productenmatrix/` — briefje_ontbreekt, productenmatrix_pickbon, de twee voorbeeld-PDF's,
  en in `$old/` de weergave-versie van de briefjesfix (zit intussen in de module).
- `reservaties/` — reservatie_o_lijn, traagheid_nakijken, reservatie_klantprioriteit.
- `levervelden/` — ontvangst_closing_days_automatisering, partner_levervelden.
- `verkooporder_acties/` — order_vervangen, serveractie_aantallen_op_nul.

Mappen met één bestand zijn opgegaan in de root. Alle gidsen met code hebben nu een
kopieerknop per codeblok. Achterhaald werk gaat voortaan naar een `$old/`-map binnen zijn
onderwerpsmap.

## 2026-08-07 (avond) — trage ontvangsten: eigen code uitgesloten

Testdatabase **`bab18-20260807`** gemaakt (kopie van `bab18-20260618`, filestore gehardlinkt)
en daar in twee trappen alle niet-standaard code uit gehaald, om definitief uit te sluiten dat de
traagheid bij ontvangsten uit eigen code komt.

- **Trap A — eigen code weg**: modules `bab_stock_delivery`, `babimex_custom`,
  `babimex_website_sale`, `mail_debrand`, `product_brand`, `website_odoo_debranding`,
  `studio_customization`. Plús wat géén module kent en dus bij een uninstall blijft staan:
  **23 handmatige `x_`-velden** (waarvan er maar 8 van `studio_customization` waren),
  2 automatiseringsregels, 3 serveracties, 4 losse views.
- **Trap B — ook derden weg**: 11 OCA/tpa/osa-modules (`stock_no_negative`,
  `stock_quant_reservation_info`, `stock_picking_group_by_base`, `stock_warehouse_out_pull`,
  `gls_shipping_integration`, …). Daarna draait er zuiver standaard Odoo + Enterprise.

Gemeten op ontvangst **WH/IN/00099** (185 lijnen), telkens dezelfde ontvangst, teruggedraaid na
elke meting (script: `meet_ontvangst.py`):

| | quantity zetten (per lijn) | `button_validate` (185 lijnen) |
|---|---|---|
| mét maatwerk | 18,7 ms / 8,7 queries | 6393 ms / 4901 queries |
| trap A (eigen code weg) | 7,9 ms / 6,5 queries | 5838 ms / 4683 queries |
| trap B (alles weg) | 7,6 ms / 6,5 queries | 5713 ms / 4680 queries |

**Conclusie: het is standaard Odoo.** Eigen code kost ~11 ms per lijn bij het invullen van
aantallen (2,4×), maar dat is in absolute cijfers klein. De validatie — het echte pijnpunt — wordt
er 11% sneller van en blijft op **5,7 s voor 185 lijnen** hangen zonder één regel maatwerk.
cProfile op de gestripte database verdeelt die tijd zo:

- **`_trigger_assign` → `_action_assign` → `_update_reserved_quantity` — 4,2 s (45%)**: na het
  boeken hertriggert Odoo de reservatie van de vervolgverplaatsingen.
- **`stock_account._action_done` (voorraadwaardering, SVL) — 3,0 s.**
- **`purchase_order_line._track_qty_received` → `message_post_with_source` — 1,7 s**: één
  chatterbericht *per ontvangen aankooplijn*, dus 185 berichten.
- **`_compute_qty_received` — 1,7 s.**

Wil je hier écht iets aan doen, dan zit de winst dus in standaard-Odoo-gedrag afremmen
(bv. de qty_received-tracking op de aankooplijn), niet in eigen code opkuisen.

### qty_received-tracking uitgeschakeld — gemeten

Op dezelfde gestripte database `bab18-20260807`, `purchase_order_line._track_qty_received`
gemonkeypatcht naar een no-op (aan/uit/aan/uit, om cache-opwarming uit te sluiten):

| | `button_validate` | queries | PO-chatterberichten |
|---|---|---|---|
| tracking aan | 5969 / 5950 ms | 4879 / 4842 | 185 |
| tracking uit | 4720 / 4605 ms | 4096 | 0 |

**~1300 ms winst (22%) en 780 queries minder**, zeer reproduceerbaar. De 185 chatterberichten
per ontvangst verdwijnen daarmee volledig. Wat overblijft (~4,6 s) is vooral de hertrigger van de
reservatie van vervolgverplaatsingen (4,2 s in het cProfile) en de voorraadwaardering.

Permanent maken kan met een override van `_track_qty_received` in een eigen module — nog niet
gebouwd, nog niet afgestemd.

### Zelfde meting, maar over HTTP

De shell-meting hierboven mist de request-overhead. Daarom herhaald met een echte server
(poort 8072, `--workers=0`) op een **verse kopie per ronde** (`bab18-httptest`, gemaakt met
`createdb -T bab18-20260807`, filestore gehardlinkt), zodat elke ronde op identieke data start.
Aangeroepen zoals de webclient: `POST /web/dataset/call_button`, `stock.picking.button_validate`.

De tracking werd uitgezet met een server-wide `post_load`-patch
(`$scratchpad/meetaddons/bab_meet_geen_tracking`, geladen via `--load`), dus zonder één wijziging
in de database. Gecontroleerd: bij "uit" komen er 0 chatterberichten op `purchase.order` bij.

| ronde | tracking aan | tracking uit |
|---|---|---|
| 1 (koud) | 7197 ms | 6394 ms |
| 2 | 6717 ms | 5335 ms |
| 3 | 6857 ms | 5598 ms |
| mediaan | **6857 ms** | **5598 ms** |

**Winst ~1250 ms, oftewel ~18% van de validate-request.** Iets minder dan de 22% uit de shell,
want de HTTP-request draagt ~900 ms overhead die de tracking niet raakt.

⚠️ Voorbehoud: dit is de `call_button`-request. Het herladen van het formulier erna heb ik met een
vereenvoudigde `read` benaderd (13 ms) — dat is *niet* representatief voor wat de webclient
werkelijk ophaalt bij 185 lijnen. De volledige klikervaring is dus langer dan 6,9 s, en het
aandeel van de tracking daarin navenant kleiner dan 18%.

### Het herladen van het formulier: niet gemeten, spoor afgesloten

Poging om met een echte browser te meten wat het herladen ná de validatie kost. **Eén bruikbaar
resultaat, geen tijdscijfer.**

**Wel geleerd:** de webclient laadt de verplaatsingen **per 40**, niet alle 185 ("1-40 / 185").
Het herladen na een validatie leest dus 40 lijnen. De eerdere vrees dat het herlaadcijfer het
beeld sterk zou bijstellen, is daarmee grotendeels weg.

**Waarom het strandde:** de eerste ronde liep volledig (ingelogd, ontvangst geopend, gevalideerd),
maar de meetlaat hing aan `fetch` terwijl de Odoo-webclient XHR gebruikt — dus lege meting. Bij
elke poging daarna weigerde de backend-client te mounten: lege body, terwijl `get_views`/`web_read`
server-side 200 gaven, `odoo.loader` nul openstaande én nul gefaalde jobs meldde, en de
server-gerenderde `__session_info__` correct uid 6 / juiste db bevatte. Ook een verse databasekopie,
een verse tab, en het wissen van de service worker + `odoo-sw-cache` hielpen niet. Zonder
consolemeldingen (de extensie leverde er geen) viel het niet verder te herleiden. Vermoeden blijft
client-side caching, **niet** de database.

Onderweg fout gedacht: eerst leek `-i bab_meet_login` de boosdoener, tot de `__session_info__`-check
aantoonde dat server en database gezond zijn.

**Opgeruimd:** meetdatabase `bab18-httptest` en haar filestore weg, meetserver op 8072 gestopt,
`bab_meet_login` (tijdelijke inlogroute zonder wachtwoord, enkel voor deze meting) weer
gedeinstalleerd uit `bab18-20260807`. Die database staat klaar als gestripte testomgeving:
volledig standaard Odoo + Enterprise, ontvangst WH/IN/00099 nog op `assigned`.

**Wil je dit ooit hervatten:** hang de meetlaat aan `XMLHttpRequest` (niet `fetch`), en gebruik
twee even grote ontvangsten (VAS/IN/00053 = 118 lijnen, VAS/IN/00060 = 115) in kruisopzet, zodat
de database tussen de rondes niet hermaakt hoeft te worden — dat hermaken is wat de client sloopte.

### De grotere hefboom: `stock.picking_no_auto_reserve`

Vraag was of het ook zonder aan de standaard tracking te komen sneller kan. Ja, en die hefboom is
groter. `stock.move._trigger_assign` — de 45% uit het cProfile — is af te zetten met een
**standaard systeemparameter**: `stock.picking_no_auto_reserve = True`. Geen code, geen module.

Gemeten op `bab18-20260807` (gestript, ontvangst WH/IN/00099, 185 lijnen, alles teruggedraaid):

| | `button_validate` | queries |
|---|---|---|
| zoals vandaag | 5982 ms | 4842 |
| enkel tracking uit | ~4660 ms | 4096 |
| **enkel herreservatie uit** | **3223 ms** | **2595** |
| **beide uit** | **~2050 ms** | **1840** |

Dus: −22% met de tracking, **−46% met de herreservatie**, −66% samen.

⚠️ Meetfout om te onthouden: `ir.config_parameter.get_param` is ormcached, en een `cr.rollback()`
maakt die cache níét ongedaan. In de eerste combi-run bleef de parameter na de rollback in cache op
True staan, waardoor de rij "enkel tracking uit" in werkelijkheid *beide* uit had. De 4660 ms
hierboven komt daarom uit de aparte tracking-run, niet uit die combi-run.

**Wat het functioneel kost:** met de parameter aan reserveert een afgewerkte ontvangst de wachtende
leveringen niet meer meteen. Dat gebeurt dan via `Procurement: run scheduler`
(`_run_scheduler_tasks` → `_action_assign` op alle confirmed moves) of manueel via Controleer
beschikbaarheid. De cron staat standaard op **dagelijks** — voor BAB vermoedelijk te trage
terugkoppeling, dus die frequentie mee verhogen.

**Middenweg, niet gemeten:** alle bewerkingssoorten staan op `reservation_method = at_confirm`
(4 incoming, 24 internal, 5 outgoing). Zet je de uitgaande op `by_date`, dan valt in de
`_trigger_assign`-domein-OR enkel nog wat binnen zijn reservatiedatum valt. Op deze testdata
(maart 2026, dus alle reservatiedatums lang voorbij) levert dat niets zichtbaars op — vandaar
niet gemeten. In productie met actuele datums wél.

**Hardware:** het cProfile zet ~1,85 s van 9,62 s in `psycopg2 execute`; de rest is Python. Dit is
dus single-core CPU-werk. Meer workers of meer RAM doen hier **niets** — die helpen tegen wachtrij,
niet tegen de duur van één request. Een snellere kern helpt ongeveer lineair, en dat haalt geen
factor 3.

### `by_date` is een doodlopend spoor — gemeten

Getest op `bab18-20260807`, ontvangst WH/IN/00099, alles teruggedraaid.

**Zoals de data nu staat** (augustus, back-up van juni): elke reservatiedatum ligt in het verleden,
dus het kandidatenaantal in het `_trigger_assign`-domein blijft op **4661** en er verandert niets.

| | `button_validate` | queries |
|---|---|---|
| alles `at_confirm` | 5817 ms | 4842 |
| uitgaand `by_date` | 5873 ms | 4842 |
| uitgaand + intern `by_date` | 5876 ms | 4842 |
| alles `at_confirm` (controle) | 5929 ms | 4842 |

**Gesimuleerd op de snapshotdatum** (`fields.Date.today` bevroren op 2026-06-18, zodat de toen nog
toekomstige verplaatsingen wél buiten het domein vallen — beide scenario's met dezelfde bevroren
datum): kandidaten **4661 → 2935 (−37%)**, en tóch:

| | `button_validate` | queries |
|---|---|---|
| `at_confirm`, datum bevroren | 6014 ms | 4842 |
| `by_date`, datum bevroren | 5846 ms | 4836 |
| `by_date`, datum bevroren (controle) | 5903 ms | 4842 |

**Conclusie: `by_date` levert niets op, ook niet in productie.** De kost van `_trigger_assign` zit
niet in de omvang van de kandidatenpoel maar in `_action_assign` op de verplaatsingen die op
product + locatie matchen met de 185 ontvangen lijnen. De poel kleiner maken met verplaatsingen
voor ándere producten raakt die matchende set niet — zichtbaar aan het querycijfer, dat met 6
queries op 4842 nauwelijks beweegt.

Verhelderend cijfer voor de keuze: op de snapshotdatum stonden **0 van de 151** uitgaande wachtende
verplaatsingen in de toekomst (allemaal te laat), tegen 1726 van 4510 bij intern. Het uitgaande
advies raakte dus sowieso een lege verzameling.

**Daarmee blijft er voor die 45% één werkende hefboom over: `stock.picking_no_auto_reserve`,**
met de scheduler-frequentie als prijs. Eerder advies om met `by_date` te beginnen: ingetrokken.

### `no_auto_reserve` aan, tracking gewoon aan — over HTTP

Het scenario zonder enige ingreep in standaardgedrag: alleen de systeemparameter om, de
`qty_received`-tracking blijft draaien. Verse databasekopie per ronde, `POST /web/dataset/call_button`.

| | validate |
|---|---|
| anker: parameter uit (zelfde sessie) | 7006 ms |
| eerdere baseline (mediaan van 3) | 6857 ms |
| **parameter aan, ronde 1** | **3718 ms** |
| **parameter aan, ronde 2** | **3861 ms** |
| **parameter aan, ronde 3** | **3673 ms** |

**Mediaan 3718 ms tegen 6857: −46%, ~3,1 seconden weg met één systeemparameter en zonder één
regel standaardgedrag op te geven.** Sluit netjes aan bij de shell (3206 / 3223 / 3266 ms).

⚠️ Meetfout om te onthouden: `mail_message.create_date` staat in **UTC**, `now()` in psql geeft
lokale tijd (+2). Een controle als `create_date > now() - interval '15 minutes'` geeft daardoor
altijd 0 en lijkt te bewijzen dat er geen chatterberichten zijn. Zo is eerder ten onrechte
"0 berichten" gerapporteerd als bevestiging dat de tracking-patch werkte bij de HTTP-runs. Tel op
**bericht-id** (`id > vooraf hoogste id`), zoals het shell-script doet — daar stond 185 tegenover 0.
Bij deze run: 187 berichten op P00063, de tracking stond dus aan.

**Opgeruimd:** `bab18-httptest` en filestore weg, server op 8072 gestopt. `bab18-20260807` staat
onaangeroerd: parameter niet gezet, WH/IN/00099 nog op `assigned`.

## Morgen verder — waar we gebleven zijn (2026-08-07, einde dag)

**Stand.** De vraag "zit de traagheid van ontvangsten in eigen code?" is beantwoord: **nee**, het is
standaard Odoo, bewezen op de volledig gestripte `bab18-20260807`. Alle eigen code samen kost 555 ms
van 6393 (8,7%). Daarna is gezocht naar wat het wél sneller maakt, en dat is gevonden.

**De aanbeveling die klaarligt:** `stock.picking_no_auto_reserve = True`.
Over HTTP **6857 → 3718 ms mediaan (−46%)**, met de tracking gewoon aan, één systeemparameter,
geen code, in één handeling terug te draaien.

**De open beslissing is niet technisch maar functioneel** — die moet met Kristof:
met die parameter aan reserveert een afgewerkte ontvangst de wachtende leveringen niet meer meteen.
Dat schuift naar `Procurement: run scheduler`, en die staat standaard op **dagelijks**. Vraag aan
Kristof: hoeveel vertraging op de reservatie is aanvaardbaar, en mag de cron naar bv. elk uur?
Zonder dat antwoord heeft de parameter geen zin.

**Daarna pas te bespreken (tweede beslissing, niet vermengen):** de `qty_received`-tracking
uitzetten met een override van `_track_qty_received`. Nog eens −22% (samen ~2,0 s in de shell),
maar de prijs is dat de aankooporder niet meer logt wanneer er wat ontvangen werd. Module is
**niet** gebouwd en de aanpak is niet afgestemd.

**Doodlopend, niet opnieuw proberen:** `by_date` op de bewerkingssoorten (gemeten, nul effect,
ook gesimuleerd op de snapshotdatum). Meer workers of RAM (het is single-core Python-werk).

**Losse eindjes:** het herladen van het formulier is nooit gemeten (browserspoor gestrand; de
webclient laadt per 40 lijnen, dus het weegt licht). En `bab18-20260807` is nooit door de UI
uitgeprobeerd — de lege backend-client was Chrome-side, maar dat is niet bevestigd.

**Niet vergeten, staat los van dit onderzoek:** `bab_stock_delivery` wacht nog altijd op uitrol door
de externe partij, met de nazorglijst in `$claude/uitrol_stock_delivery/output_claude/`.

## 2026-08-08 — module `bab_stock_deferred_reservation` gebouwd en gemeten

Het cron-plan uitgewerkt: de herreservatie na een validatie blijft bestaan, maar verhuist uit de
request van de gebruiker. Module staat in `klanten/bab/18.0/bab_stock_deferred_reservation`
(nog niet gecommit).

**Ontwerp — geen schemawijziging nodig.** `_action_done` stempelt `date = now()` op afgewerkte
moves, dus de cron vindt zelf terug wat er te doen valt; er hoeft niets gevlagd of in een wachtrij
gezet te worden op `stock.move`.

- `stock.move._trigger_assign` override: doet niets inline en roept `ir.cron._trigger()` aan. De
  trigger leeft in dezelfde transactie, dus een teruggedraaide validatie neemt hem mee.
- Cron `_cron_deferred_reservation`: zoekt done moves vanaf een marker en roept dáárop het
  *standaard* `_trigger_assign` aan (via een contextvlag, tegen herintreding).
- Terugvalinterval van 1 uur voor verloren triggers; `_notifydb` in postcommit zorgt dat een
  trigger normaal binnen seconden opgepikt wordt.

**Zelfbedachte keuzes, expliciet:** batchplafond van 5000 moves per run (rest triggert een nieuwe
run); marker is de `date` van de laatst verwerkte move, **inclusief** vergeleken omdat Odoo
datetimes op hele seconden afkapt en alle lijnen van één validatie dus dezelfde stempel delen —
een exclusieve grens zou de rest van die seconde laten vallen. Overlap is onschadelijk: een
gereserveerde move is niet langer `confirmed`/`partially_available` en valt buiten het domein.
Systeemparameter `bab_stock_deferred_reservation.enabled` (`noupdate`) om het uit te zetten
zonder de-installeren.

**Gelijkwaardigheid bewezen**, niet op eindtoestand maar op aangeboden werk (`_trigger_assign` kan
werk doen dat geen enkele status verandert):

| | aan `_action_assign` aangeboden |
|---|---|
| standaard | 7 oproepen, 183 unieke moves |
| uitgesteld, tijdens de validatie | 5 oproepen, **0** moves |
| uitgesteld, na de cron | **dezelfde 183** |

**Winst.** Shell: `_trigger_assign` 2395 ms → 3 ms, validatie **5777 → 3101 ms**. Over HTTP,
verse databasekopie per ronde:

| | validate |
|---|---|
| anker (module uit) | 6854 ms |
| module aan | 3791 / 3701 / 3727 ms |

**Mediaan 3727 tegen 6854: −46%**, gelijk aan wat `stock.picking_no_auto_reserve` opleverde — maar
nu zonder de reservatie te laten liggen tot de dagelijkse scheduler. De cron doet het werk
alsnog, in 2,7 s, in de achtergrond.

**End-to-end getest** met `--max-cron-threads=1`: trigger aangemaakt, cron gestart, "done in
2.752s", marker gezet, triggers opgeruimd. De 68 s die ik tussen validatie en cron mat is **niet**
representatief — die server startte koud op en had andere crons (auto-vacuum) voor zich in de rij.

⚠️ Twee keer in dezelfde valstrik gelopen bij het testen: na `set_param('False')` + `rollback()`
staat de oude waarde weer in de DB, waardoor de volgende `set_param('True')` een **no-op-write** is
— geen wijziging, dus geen cache-invalidatie, en `get_param` blijft de oude waarde geven. De eerste
gelijkwaardigheidstest en de eerste trace draaiden daardoor **beide fasen inline** en toonden
vals-positief "identiek". Oplossing: `env.registry.clear_cache()` na elke parameterwissel.

**Eerlijk over wat je niet wint:** het totale serverwerk blijft gelijk (3,1 s + 2,7 s ≈ de 5,8 s
van voorheen). Je haalt het alleen weg bij de wachtende gebruiker. Op odoo.sh betekent dat extra
druk op de cron-workers.

**Testdatabase `bab18-defres`** (kopie van `bab18-20260807` + module) blijft staan om verder op te
werken.

## 2026-08-09 — de echte klacht: aantallen invullen, niet valideren

De gebruiker meldt dat het invullen van aantallen traag is, niet het valideren. Daarmee raakt
`bab_stock_deferred_reservation` de klacht **niet**. Onderzocht op `bab18-lijntest`, een
dump-kopie van de werkkopie (`createdb -T` kon niet, de server draaide).

**Eerste vaststelling: tikken kost de server niets.** Er is **geen `@api.onchange` op
`stock.move.quantity`**, en geen onchange op `stock.picking` die de lijnen aanraakt. Het invullen
blijft dus volledig client-side; de server ziet pas werk bij **Opslaan**.

**Opslaan in één keer is 4× goedkoper dan per lijn flushen** (2,3 tegen 9,2 ms/lijn op 30 lijnen),
dus de webclient doet het al optimaal. Mijn eerdere cijfer "18,7 tegen 7,9 ms/lijn" mat per-lijn
flushen — dat doet de UI niet, dus dat **overschatte de impact van het maatwerk**.

| opslaan | lijnen | tijd | per lijn | queries |
|---|---|---|---|---|
| WH/IN/00099 | 185 | 623 ms | 3,4 ms | 754 |
| VAS/IN/00083, eerste 185 | 185 | 1466 ms | 7,9 ms | 993 |
| **VAS/IN/00083, alles** | **2493** | **22180 ms** | **8,9 ms** | **17708** |

**Dát is de klacht: één Opslaan van 22 seconden op een ontvangst van 2493 lijnen.**

**Hoeveel daarvan is maatwerk? Nagenoeg niets** — behalve bij een picking in een batch.
WH/IN/00099 (185 lijnen, in BATCH/00730 met 636 moves), zelfde bewerking:

| | tijd | queries |
|---|---|---|
| gestripte DB, geen maatwerk | 608 ms | 753 |
| werkkopie, batchtotalen niet-opgeslagen | 607 ms | 754 |
| werkkopie, batchtotalen opgeslagen | 770 ms | 760 |

Dus het maatwerk kost **163 ms van 770 (21%)**, en dat is volledig toe te schrijven aan de vier
opgeslagen batchtotalen (`x_quantity_total`, `x_uom_qty_total`, `x_studio_move_quantity_total`,
`x_studio_move_uom_qty_total`), die bij elke schrijfbeweging over alle 636 moves van de batch
sommeren. Staat de picking **niet** in een batch, dan vuren ze niet en is het verschil nul.

⚠️ Correctie op mezelf: eerst schreef ik die velden 49% van de lijnkost toe, op basis van
cumulatieve tijd per compute. Dat dubbeltelde de geneste computes. Echt gemeten door ze op
niet-opgeslagen te zetten: 547 → 447 ms, dus **18%**, en op een volledige save 21%.

Ook fout gebleken onderweg: de hypothese dat batch-versus-geen-batch het verschil maakte, leek
weerlegd door 37,6 tegen 38,0 ms/lijn — maar die meting liep ónder cProfile, waarvan de overhead
het verschil wegdrukte. Zonder profiler klopt de hypothese wel.

**Wat dit betekent voor de keuzes:**

1. **Voor grote ontvangsten is de barcode-app juist wél interessant** — niet omdat het valideren
   sneller is (dat is identiek, zelfde `button_validate`), maar omdat elke scan een kleine schrijf
   is. Je wacht nooit één keer 22 seconden.
2. **De batchtotalen op niet-opgeslagen zetten** geeft 21% terug bij gebatchte pickings. Prijs: ze
   staan in een lijstweergave van `stock.picking.batch` (Studio-view), en niet-opgeslagen velden zijn
   daar niet sorteerbaar of filterbaar en worden per rij herrekend bij het openen van die lijst.
   `x_quantity_total` en `x_studio_move_quantity_total` lijken bovendien duplicaten — één ervan kan
   waarschijnlijk gewoon weg.
3. **De 22 s op 2493 lijnen is standaard Odoo**, ~9 ms per lijn, lineair. Daar is met configuratie
   niets aan te doen.

Testdatabase `bab18-lijntest` blijft staan (batchtotalen terug op opgeslagen, dus gelijk aan de
werkkopie).

### Batchtotalen: SQL-aggregaat in plaats van een Python-lus

De vier totalen op `stock.picking.batch` lusten over `record.move_ids` — in core een
**niet-opgeslagen berekende o2m**, dus elke herberekening bouwt die eerst opnieuw op. Herschreven
naar één `_read_group` over de opgeslagen `picking_ids`, en dat kan **rechtstreeks in de database**:
de compute-code van een handmatig veld staat in `ir.model.fields.compute`.

```python
totalen = {}
for picking, som in self.env['stock.move']._read_group(
        [('picking_id', 'in', self.picking_ids.ids)], ['picking_id'], ['quantity:sum']):
    totalen[picking.id] = som
for record in self:
    totaal = 0
    for picking in record.picking_ids:
        totaal += totalen.get(picking.id, 0)
    record['x_quantity_total'] = totaal
```

Opslaan van 185 lijnen op WH/IN/00099 (in BATCH/00730, 636 moves):

| variant | tijd |
|---|---|
| nu: Python-lus, opgeslagen | 770 ms |
| niet-opgeslagen maken | 607 ms |
| **SQL-aggregaat, blijft opgeslagen** | **596 ms** |
| gestripte DB, geen maatwerk | 608 ms |

**De velden kosten nu niets meer** — gelijk aan de database zonder maatwerk — en blijven
opgeslagen, dus sorteerbaar en filterbaar in de Studio-lijstweergave. Niet-opgeslagen maken is
daarmee overbodig geworden. Waarden gecontroleerd op 8 batches: identiek aan de opgeslagen
waarden.

**Twee valkuilen onderweg:**

- `safe_eval` geeft een generator-expressie een eigen scope, die de lokale variabelen niet ziet:
  `sum(totalen.get(p.id, 0) for p in record.picking_ids)` geeft
  `NameError: name 'totalen' is not defined`. Zelfde familie als de geneste comprehension in QWeb.
  Schrijf een gewone lus. (`safe_eval` verbiedt overigens alleen namen met *twee* underscores, dus
  `_read_group` mag wél.)
- **`x_quantity_total` en `x_studio_move_quantity_total` zijn géén duplicaten**, in tegenstelling
  tot wat eerder genoteerd stond: de eerste is een aantal (4, 1, 3), de tweede een waarde
  (100,76 = aantal × prijs). Geen van beide kan dus zomaar weg.

**Database of module?** De fix werkt vandaag in de database en vergt geen uitrol. Nadeel: die code
staat in `ir.model.fields.compute`, dus buiten versiebeheer en review, en `safe_eval` beperkt wat
je kan schrijven. Naar een module verhuizen maakt het duurzaam en testbaar, maar vergt een uitrol
via de externe partij én een plan voor de veldnamen (de Studio-views verwijzen naar `x_*`).

### Uitrolgids geschreven

`$claude/traagheid/$old/batchtotalen_versnellen.html` — stappen om de vier computes in productie aan te passen
via Instellingen → Technisch → Databasestructuur → Velden. Sticky TOC, afvinkbare stappen,
kopieerknop op elk codeblok, plus de originele code om terug te draaien.

Bij het schrijven nog een vondst: op **ontvangst**batches staan `x_studio_move_quantity_total` en
`x_studio_move_uom_qty_total` **altijd op 0** (BATCH/00156, 00730, 00993 alle drie 0), want ze
rekenen met de verkoopprijs van de verkooporderlijn en die bestaat niet bij een ontvangst — een
leveringsbatch als BATCH/01992 toont wel 428,23. Ze kosten daar dus rekentijd zonder iets op te
leveren. Of ze op ontvangsten weg mogen is een aparte vraag: ze staan in dezelfde batchlijst voor
alle soorten. Opgenomen als waarschuwing in de gids, niet als actiepunt.

### Toegepast in de werkkopie

De vier computes zijn op 2026-08-09 herschreven in **`bab18-20260618`** zelf, zodat de gebruiker
kan testen. Gecontroleerd: alle vier op de `_read_group`-versie, `depends` ongemoeid. Nagemeten in
die database (opslaan van 185 lijnen op WH/IN/00099, teruggedraaid): **632 ms**, tegen 770 ms met
de oude code. Productie is nog niet aangeraakt — daarvoor dient de gids.

## 2026-08-09 (later) — de echte oorzaak gevonden: onchange over álle lijnen

Met de ingebouwde profiler op de werkkopie (`ir.profile`, SQL + traces) is de klacht eindelijk
vastgepind. Bij het invullen van één aantal op VAS/IN/00084 (2484 lijnen, geen batch):

| request | duur |
|---|---|
| `stock.move/onchange` | 180 ms |
| **`stock.picking/onchange`** | **2773 ms** |

Daarvan is **maar 216 ms SQL** (51 queries); de rest is Python.

**Oorzaak, in `web/models/models.py` rond regel 889:** de onchange-implementatie neemt
`line_ids = OrderedSet(self[field_name].ids)` — dus **alle** ids van de one2many, niet alleen de
40 die het scherm toont — en leest daarna voor elk veld uit de sub-spec `line[field_name]` op elk
van die records. Elk niet-opgeslagen berekend veld in het tabblad Bewerkingen wordt dus voor alle
2484 lijnen herrekend, bij elke ingevulde hoeveelheid. Zichtbaar in het profiel als een
`fetch` met een IN-lijst van **2484 ids** vanuit `models.py:897 onchange`.

Verdeling uit de traces (172 samples, cumulatief in de stack):

| | aandeel |
|---|---|
| `models.py onchange` | 98,8% |
| `_compute_field_value` | 47,1% |
| `stock_move._compute_forecast_information` | 20,3% |
| `product._compute_quantities(_dict)` | 11,0% + 6,4% (onder de forecast) |
| `_compute_related` | 12,2% |
| `stock_picking._compute_show_next_pickings` | 5,2% |

**Geen enkel handmatig `x_`-veld in de lijst** — geen `safe_eval`, geen Studio-compute. Het
maatwerk speelt hier geen rol.

**Waarom het schaalt met de ontvangst en niet met het scherm:** 185 lijnen voelt vlot, 2484 niet.
De kost is (aantal lijnen) x (aantal berekende kolommen in de lijst).

**Wat hier wél aan te doen is:**

1. **Kolommen uit het tabblad Bewerkingen halen.** De forecast-keten
   (`forecast_availability` met `forecast_widget` + `forecast_expected_date`) is goed voor ~25%,
   dus ruwweg 700 ms. Prijs: de beschikbaarheidsindicator per lijn verdwijnt.
2. **De barcode-app voor grote ontvangsten.** Die gebruikt dit formulier niet en stuurt dus geen
   onchange met alle lijnen mee. Dit is nu het derde argument voor barcode, en het sterkste.
3. **Kleinere ontvangsten.** De kost is lineair in het aantal lijnen.

⚠️ Correctie op mezelf: ik schreef eerder "er is geen `@api.onchange` op `stock.move.quantity`,
dus tikken kost de server niets". Dat eerste klopt, het tweede niet — de webclient roept sowieso
`onchange` aan op het *bovenliggende* record bij een wijziging in een one2many. Drie hypotheses
(batchvelden, forecast op 40 lijnen, payloadgrootte) sneuvelden onderweg bij meting; pas de
profiler gaf het antwoord. Bij een volgende "traag scherm"-klacht: **eerst de profiler, dan pas
hypotheses.**

### Forecast uit de lijst: gemeten winst 23%

Meetopstelling gebouwd die de webclient naspeelt (`meet_onchange_echt.py`): de volledige o2m-staat
als `Command.link` plus een fields-spec met alle velden uit de lijst-arch, dan
`picking.onchange(...)`. Reproduceert 2405 ms tegen de 2773 ms uit het echte profiel — het verschil
is HTTP-overhead plus de tweede (goedkope) onchange op `stock.move`.

**Per veld gewogen** (spec-variant, mediaan van 3, ontvangst van 2484 lijnen):

| spec | duur |
|---|---|
| alle 36 velden | 2339 ms |
| zonder `forecast_*` | 1865 ms |
| zonder enkel `forecast_availability` | 1855 ms |
| zonder `move_line_ids` / `product_qty` / `show_quant` / `move_lines_count` / `product_packaging_id` | 2289-2378 ms (ruis) |

**Alles zit in `forecast_availability`: 474 ms, 20%.** Geen enkel ander veld weegt.

**Waarom het veld niet zomaar weg wilde.** Het wordt niet alleen als kolom gedeclareerd (die staat
op `optional="hide"` én `column_invisible` voor niet-uitgaande soorten, dus op ontvangsten
onzichtbaar), maar er staan ook **twee knoppen `action_product_forecast_report`** in de lijst —
`icon="fa-area-chart"` en `fa-area-chart text-danger`. **Dat is het grafiek-icoontje tussen
Gevraagd en Aantal**, geen kolom, vandaar zonder kop. Hun `invisible` verwijst naar
`forecast_availability`, waardoor Odoo het veld zelf terug in de arch injecteert met
`data-used-by="invisible=..."`. Zolang één element ernaar verwijst, wordt het voor alle lijnen
berekend.

**Override in de werkkopie** (`ir.ui.view` id 4014, `stock.picking.form.geen.forecast.bab`,
priority 99): de twee knoppen vervangen door één knop waarvan de `invisible` niet meer naar
`forecast_availability` verwijst, plus `forecast_availability` en `forecast_expected_date` uit de
lijst. Resultaat:

| | onchange | queries |
|---|---|---|
| voor | 2405 ms | 28 |
| **na** | **1848 ms** | **15** |

**~560 ms eraf, 23%.** Op de echte request zou dat 2773 → ~2200 ms zijn.

Prijs: de Forecast Report-knop blijft, maar verliest zijn kleurbepaling — hij was rood bij
tekort, nu altijd blauw. De rest (1,85 s) is 2484 lijnen x 35 velden en is met geen enkele
view-ingreep op te lossen.

### De onchange zelf is onvermijdelijk — en schaalt lineair

Waarom de webclient die dure onchange op de picking überhaupt stuurt: `ir_ui_view` zet
`on_change="1"` op een veld zodra `models._has_onchange()` waar is, en dat is waar als **een
afhankelijk veld ook in de view staat**. `stock.picking.state` is berekend uit `move_ids` en staat
als statusbalk in het formulier. Zolang die er staat, vuurt elke lijnwijziging de onchange van de
picking. Dat is niet weg te configureren.

De kost schaalt strikt lineair met het aantal lijnen (na de forecast-override):

| ontvangst | lijnen | onchange | per lijn |
|---|---|---|---|
| WH/IN/00099 | 185 | 145 ms | 0,78 ms |
| WH/IN/00184 | 450 | 309 ms | 0,69 ms |
| VAS/IN/00084 | 2484 | 1898 ms | 0,76 ms |

**De "Laden"-banner verschijnt bij ongeveer 250 ms.** Bij ~0,75 ms per lijn ligt de grens dus rond
**330 lijnen**: daaronder voelt het invullen onmiddellijk, daarboven zie je de banner bij elk
ingevuld aantal.

**Conclusie van het hele traject.** Voor grote ontvangsten zijn er nog maar twee echte remedies:
de ontvangst opsplitsen in stukken van hooguit ~300 lijnen, of de barcode-app gebruiken (die
gebruikt dit formulier niet en stuurt dus geen onchange over alle lijnen). Alle overige ingrepen
zijn uitgeput: de forecast-override haalde er 23% af, en geen enkel ander veld weegt.

### $claude opgeruimd: map `traagheid/`

Alles van dit onderzoek staat nu bij elkaar:

```
$claude/traagheid/
  output_claude/
    overzicht.md                      klacht, oorzaak, wat wel/niet hielp, met cijfers
    forecast_uit_ontvangstlijst.html  productiegids voor de fix die wél werkte (23%)
    traagheid_nakijken.html           werkwijze om dit soort klachten uit te zoeken
  $old/
    batchtotalen_versnellen.html      echte winst (770 -> 596 ms), maar op het opslaan
                                      van gebatchte overdrachten, niet op de klacht
```

`status.md` blijft in de hoofdmap: het is het dagboek van het hele project, niet van dit
onderwerp.

Over `$old/`: die batchtotalen-gids is **geen weggegooid werk**. De winst is echt en de
aanpassing staat in de werkkopie; ze raakt alleen een andere handeling dan waarover geklaagd werd.
Hetzelfde geldt voor `bab_stock_deferred_reservation` en `stock.picking_no_auto_reserve`, die geen
eigen bestand hebben en enkel in `overzicht.md` en dit dagboek staan. Wat écht niets opleverde —
`by_date`, meer workers, upgraden naar 19/20 — staat daar ook opgesomd, zodat het niet opnieuw
onderzocht wordt.

## 14 augustus 2026 — het ontbrekende stuk van batch 02473

**De klacht.** Op batch 02473 stond artikel 51742-98-M niet als gescand; 29 stuks gefactureerd
in plaats van 30. Kristof zag het artikel wél in de zending zitten, en het prognoserapport toonde
-1 met "gebruikt door S01533" (Aphrodite).

**De oorzaak — niet wat het leek.** Er zijn 3 stuks ontvangen (VAS/IN/00097) en er is voor elke
klant netjes 1 stuk naar de uitgaande zone gepickt (PICK/00150 Beir Boutique, PICK/00142
Aphrodite, PICK/00183 Textilhaus Kaulmann, alle Gereed). Op de levering van Textilhaus Kaulmann
(**VAS/OUT/00270**) staat echter **gevraagd 1, verzonden 2**: daar is één stuk te veel gescand,
en dat was het stuk dat voor Aphrodite klaarlag. Odoo waarschuwt niet wanneer je méér scant dan
gevraagd. Toen Aphrodite's levering aan de beurt kwam was de uitgaande zone leeg → backorder
VAS/OUT/00300, die nu op "In afwachting van beschikbaarheid" staat.

Fysiek klopt alles: het stuk zat in de doos van Aphrodite, maar staat in Odoo op naam van
Kaulmann. **Herstel:** 1 stuk retour op VAS/OUT/00270 met bestemming VAS/Uitgaand (enkel een
boeking, magazijn doet niets) → Kaulmann komt op 1 (creditnota als hij voor 2 gefactureerd is) →
OUT/00300 wordt beschikbaar → bevestigen → factureerbaar bij Aphrodite. **Nog uit te voeren.**

**Onderweg weerlegd.** Twee hypotheses die eerst logisch leken maar niet klopten: het was géén
voorraadtekort (dus geen voorraadaanpassing nodig), en het lag niet aan de ontbrekende keten
tussen pick en levering — ook een geketende levering had die extra scan aanvaard. De planner-cron
(1×/dag, actief) is evenmin de oorzaak; die maakt geen voorraad bij.

**Nieuw inzicht dat blijft gelden.** Odoo zoekt maar op twee momenten een batch voor een bon: bij
`action_confirm` en, voor een backorder, na het valideren van de voorganger — en enkel als de bon
op dat ogenblik al op *Klaar* staat (`_is_auto_batchable` → `state != 'assigned'` → False). Een bon
die toen niets kon reserveren blijft voorgoed batchloos, staat op geen enkel briefje en wordt dus
nooit gescand. Daarom kwam er ook niets op de pdf bij een herafdruk.

### Map `ontbrekend_stuk_batch/`

```
ontbrekend_stuk_onderzoeken.py     diagnose-serveractie (leest alleen), §1-9
wachtende_bonnen_alsnog_batchen.py automatiseringsregel: batcht een bon alsnog
                                   zodra hij Klaar wordt. NOG TE ACTIVEREN
nota_hilde.html / .pdf             uitleg voor Hilde en Kristof, met de tabel
```

**Openstaand:** (1) de regel activeren — staat aangemaakt maar **gearchiveerd**, en de Python-actie
hangt er nog niet aan; Els doet dit na overleg met Hilde. (2) de retour op VAS/OUT/00270. (3) twee
losse punten die ik nog niet uitgezocht heb: hoeveel Vasa-leveringen ongeketend (`make_to_stock`)
zijn, en of de planner van 1 dag naar 1 uur moet.

### Nog te doen bij de volgende sessie

1. **Vinkje aanzetten** — na het uitrollen van `bab_stock_barcode` staat *Meer scannen dan gevraagd
   blokkeren* standaard **uit**. Aanzetten op Babimex Leveringen + Picken en Vasa International
   Leveringen + Picken; op Ontvangsten bewust uit laten.
2. **Automatiseringsregel activeren** — `* Wachtende bon alsnog batchen` staat aangemaakt maar
   gearchiveerd, en de Python-actie hangt er nog niet aan.
3. **De retour op VAS/OUT/00270** (1 stuk, bestemming VAS/Uitgaand) en daarna OUT/00300 bevestigen.

## 14 augustus 2026 (namiddag) — de 5 "op stock" bij 58913/49

**De klacht van Hilde.** Na een ontvangst toonde het briefje 5 stuks op stock voor
58913/49, terwijl er niets ligt. Klopt: de 6 stuks van P00043 kwamen binnen op 12-08
(VAS/IN/00103), gingen dezelfde dag naar de uitgaande zone (VAS/PICK/00240) en
vertrokken op 13-08 naar Beir Boutique (VAS/OUT/00267). Aanwezig en vrij staan overal op 0.

**Wat die 5 is.** De s-kolom (+overschot / vrije voorraad) van het geprinte briefje. Een
herprint op 14-08 gaf exact dezelfde cijfers terwijl alles al weg was, dus die s komt niet
uit de vrije voorraad van dat moment. Het patroon — 1 bij S t/m XXL, niets bij 3XL — valt
samen met de openstaande aankooporder **P00081** (28 april, 5 maten, 3XL staat er niet op),
precies wat de module in de **i**-kolom zet. Er zijn dus 5 stuks besteld en nog niet
ontvangen; voorraad is er niet.

**Waarom het briefje andere cijfers geeft dan de modulecode.** Er staat een vierde,
handmatig aangemaakt rapport in productie: `* Productenmatrix met reservaties
(TIJDELIJKE FIX)` (`bab_stock_delivery.report_reservation_matrix_fix`, geen xmlid,
11-08 15:44). Dat sjabloon **rekent zelf in QWeb** — het bevat `free_qty`, wat het
moduleslabloon niet doet — en toont daarom o=6 waar de modulecode o=0 geeft. De arch zelf
is nog niet uitgelezen (§8 van de serveractie staat klaar).

**De echte oorzaak blijft de uitrol.** Productie draait nog code van vóór c013c29 (11 aug).
Els heeft maar beperkte rechten op odoo.sh en haar repo hangt er niet aan; elke versie moet
bij de derde partij aangevraagd worden. Ze laat de **overdracht van het odoo.sh-project
aanvragen**. Dit is de tweede klacht in vier dagen die enkel bestaat omdat gecommitte code
niet live raakt.

**Beslist:** niet de tijdelijke fix repareren maar **de module deployen** (`b580325`, met
c013c29 en `bab_stock_barcode` erin). Daarna de TIJDELIJKE FIX verwijderen — nu staan er
twee rapporten met dezelfde bestandsnaam en verschillende cijfers.

**Nieuw bestand:** `$claude/voorraadcijfers/output_claude/voorraadcijfer_onderzoeken.py` — serveractie die alleen leest,
§1-8: voorraad per locatie, quants, alle verplaatsingen, wie reserveert, de aankooplijnen,
de exacte cijfers die de modulecode zou drukken, alle matrixrapporten met hun herkomst, en
de volledige arch van een opgegeven sjabloon.

## 18 augustus 2026 — backorder die niet meer nageleverd wordt (P00050 / 13735-TAF)

Kristof vraagt de correcte werkwijze om een backorder die de leverancier niet meer levert uit
het inkooporder én uit de batch te halen (P00050 Miracle, 24 × `13735-TAF`, WH/IN/00277).

**Antwoord:** eerst de ontvangstbon opruimen (regel wissen of de bon annuleren), dan pas op de
inkooporder het bestelde aantal gelijkzetten aan het ontvangen aantal, dan de bon uit de batch
halen. Beide volgordes nagespeeld op `bab18-20260807`.

**Waarom die volgorde.** Verlaag je het bestelde aantal terwijl de ontvangst nog openstaat, dan
maakt Odoo 18 een negatieve beweging die de openstaande beweging moet absorberen. Dat lukt alleen
als de mergesleutel gelijk is — en `price_unit` zit in die sleutel. Is de eenheidsprijs op de
bestelregel intussen gewijzigd, dan matcht ze niet, wordt de negatieve beweging omgedraaid en
belandt ze als **teruggave aan de leverancier** in een uitgaande bon; de ontvangstbon blijft op
het oude aantal staan.

**Dat is hier echt gebeurd.** 19-05: P00050 regel `13735-TAF` van 72 → 48 verlaagd (chatter
mail_message 99996). Move 39394 op WH/IN/00074 bleef 72 vragen (`price_unit` 5,67), en move 64732
werd de teruggave van 24 stuks naar Miracle in **WH/OUT/01962** (`price_unit` 4,59, `confirmed`,
gepland 1 maart). Die bon staat er nog. Enige geval in de database — query op `location_dest_id=4`
met open bon geeft alleen deze.

**Waarschijnlijke verklaring van de klacht:** de 24 in backorder zijn geen tekortlevering maar het
restant van die verlaging (bon vroeg 72, besteld was 48). Kristof kan het zelf zien: staat er nu
48 besteld / 48 ontvangen, dan is er niets tekort.

**Bijkomend risico bij Vasa:** alle 3782 gekoppelde IN→OUT-bewegingen liggen op VAS/Voorraad
(dest = src), dus daar propageert een annulatie naar de klantlevering. Bij Babimex loopt de
levering in twee stappen (WH/Stock → Output) en bestaat die koppeling niet.

**Nieuw bestand:** `$claude/backorders/output_claude/backorder_niet_naleveren.html` — klantnota met de werkwijze, de reden
voor de volgorde, en de twee punten die Kristof op P00050 zelf moet nakijken.

**Bevestigd (18-08, screenshots van Kristof).** WH/IN/00277 heeft één regel (24 × 13735-TAF,
backorder van WH/IN/00272, BATCH/02060, Beschikbaar). Op P00050 staat 13735-TAF op
**48 besteld / 48 ontvangen / 48 gefactureerd**, prijs nu 5,10 (bon 5,67, mei 4,59 — drie prijzen,
vandaar dat de merge nooit kon slagen). De backorder is dus géén tekortlevering: enkel
WH/IN/00277 annuleren + uit BATCH/02060 halen, en de bestelling ongemoeid laten (verlagen zou
onder het gefactureerde aantal gaan en een creditnota-taak uitlokken). WH/OUT/01962 blijft te
annuleren. Klantnota §4 aangepast van hypothese naar vaststelling.

**Tweede helft van het correctie-overzicht opgezet (18-08).** Els corrigeert P00050 zelf (bon +
spookretour annuleren) in plaats van Kristof en Hilde er nu mee lastig te vallen — de spookbon
stond op Beschikbaar en hield 24 stuks gereserveerd. Nieuw bestand
`$claude/correcties/output_claude/correcties_ontvangst_inkoop.html`: de inkoopkant als tegenhanger van
`correcties_pick_out.html`, gevallen A–G, samenvattende tabel, valkuilen, en §7 met wat nog te
beslissen valt met Kristof en Hilde. **Werkversie** — nog niet rondsturen.

Nagespeeld op `bab18-20260807` voor dit document: méér ontvangen dan besteld mag (96 besteld → 106
ontvangen → 106 te factureren); het aantal op een **gevalideerde** ontvangst mag nog gewijzigd
worden en de voorraad volgt meteen (540 → 545, quant 0 → 5, geen `account_move_ids`, dus geen
spoor); knop Retour maakt WH/OUT met type Leveringen, WH/Stock → Partners/Vendors, **mét** partner
(zo herken je een echte retour van de spookbon); `purchase.order.button_cancel` weigert zodra er
één ontvangst done is. Vasa: 26 openstaande VAS/OUT-bonnen (feb–apr) hangen rechtstreeks aan
openstaande ontvangsten (1-staps, VAS/Voorraad → Customers) → daar propageert een annulatie wél
naar de klantlevering.

## 23 augustus 2026 — twee onderwerpen: overdracht dear digital + Karntner S27

### 1. Overdracht van dear digital naar osadmin — afgerond behalve de opzeg zelf

Els kreeg van Kristof een uittreksel van het partnercontract (`$claude/overdracht_osadmin/input_klant/contract dear digital.pdf`,
p. 16–23 = de algemene voorwaarden §7–21; de commerciële delen ontbreken). Vraag: zitten er
haken en ogen aan een overdracht van het partnerschap.

**Antwoord: nee.** §10.4 legt alle rechten op "Provider's applications" bij de leverancier en §9.2
zondert die uit van het gebruiksrecht van de klant, maar dat blijft hier zonder gevolg: de twee
modules van dear digital, `babimex_custom` (18.0.1.0.7) en `babimex_website_sale` (18.0.2.0.1),
dragen in hun eigen `__manifest__.py` de licentie **LGPL-3**. Die is onherroepelijk. Nagekeken over
alle 233 geïnstalleerde modules van `bab18-20260618`: geen enkele gesloten module van dear digital.
De contractnaam **Mainframe Monkey** is de oorspronkelijke partner die met dear digital is
samengegaan; §18.1 laat die overdracht uitdrukkelijk toe, dus geen bezwaar.

`gls_shipping_integration` (Vraja Technologies, OPL-1) is de enige betalende module — **niet
relevant**, wordt niet gebruikt, op vraag van Els uit de takenlijst gehaald.

**Nota voor Kristof:** `$claude/overdracht_osadmin/output_claude/overdracht_dear_digital.html` (+ pdf),
met een afvinkbare lijst van zes punten voor bij de opzeg: schriftelijk naar info@deardigital.com
met 2 kalendermaanden (§13.9), §9.4 inroepen voor Github/odoo.sh/DB binnen 5 werkdagen, eigenaarschap
apart laten overzetten (§9.4 geeft enkel "administration access"), de keuze onder §12.4 meesturen
(anders houdt dd de persoonsgegevens nog 6 maanden), navragen onder welke organisatie repo en
odoo.sh-project vandaag staan, en na de overdracht controleren dat alle takken meegekomen zijn.

**Nog te doen:** de opzeg zelf — dat ligt bij Kristof.

### 2. `maak-pdf.sh` omgezet naar headless Chrome

Het gedeelde script `klanten/$claude/maak-pdf.sh` draaide op wkhtmltopdf 0.12.5, die sporadisch de
spatie vóór een inline-tag opeet. In `IMPLEMENTATIE.pdf` zaten **11 samengeplakte woorden**
(`klantnaam opProductenmatrix`, `veldAutomatisch`, `verkooptrioBesteld`, …). Script gebruikt nu
headless Chrome, met een tijdelijke `--user-data-dir` (anders start Chrome niet zolang de browser
openstaat) en een geïnjecteerde `@page{size:A4}`-regel op een tijdelijke kopie — **Chrome heeft geen
papierformaat-vlag en valt zonder die regel terug op US Letter.** PDF opnieuw gegenereerd (20 p. A4),
gecommit en gepusht als `35931b8`. Het script zelf staat buiten elke repo.

### 3. Karntner Summer 27 — procedure klaar, wacht op exports

Els moet de collectie Summer 27 van Textil Karntner opladen, zoals ze S26 deed. Bronbestanden in
`$claude/opladen_producten/input_klant/`: `Textil Karntner S27.xlsx` (nieuw, 1 tabblad, 7598 rijen)
en `Karntner S26 Odoo - vb. Excel Els.xlsx` (het model, 14 tabbladen met een tabblad *Procedure*
van 11 regels). Uitgeschreven in
**`$claude/opladen_producten/output_claude/opladen_karntner_s27.html`**.

**Waar het nu op wacht: acht exports uit productie.** De kopie hier is van 18 juni en loopt achter.
`product.attribute.value` (3 kenmerken, via een serveractie — dat model heeft in v18 geen menu),
`product.template` + `product.product` gefilterd op Karntner **met gearchiveerde records**, plus
`product.brand`, `product.category`, `product.tag`, `product.pricelist`, `res.country`. Een negende
export volgt halverwege: de varianten, pas nadat Odoo ze bij stap C zelf heeft aangemaakt.

**Vaststellingen over S27** (tegen de junikopie): 272 hoofdproducten, 7598 varianten, **geen overlap
met S26**. Alle 15 maten en alle 5 merken (incl. `M.X.O. neu`) bestaan al; 196 van de 284 kleuren zijn
nieuw. Van de 72 kwaliteiten bestaan er 8 letterlijk en 29 na vertaling — **het bestand is Duitstalig**:
`100%Baumwolle` i.p.v. `100%Cotton`, en 6 van de 7 landen (`Bangladesch`, `Indien`, `Griechenland`,
`Türkiye`, `Italien`, `Myanmar`) matchen niet. Kolom *Art. Variant nr.* is leeg en moet opgebouwd
worden. De matrix is volledig (7598 rijen = 7598 combinaties), dus stap 9 — varianten zonder barcode
archiveren — valt deze keer weg.

**Twee fouten uit de S26-oplading, in de databank vastgesteld:**
- **229 van de 233 S26-templates hebben gewicht 0.** Het gewicht stond als tekst met komma
  (`0,1500`) en Odoo las dat als nul. S27 heeft echte getallen, dus dat gaat vanzelf goed — maar
  S26 is nog recht te zetten.
- **Kledingmaat heeft een waarde met naam `39` en code `42`**, gebruikt door 84 templates; een waarde
  `42` bestaat niet. S27 bevat maat 42 — naam corrigeren vóór de import, dat raakt de referenties niet
  (die staan op de code).

Verder: de VLOOKUPs op het S26-tabblad *import product.template* wijzen naar verkeerde kolomnummers
(4/5/13 i.p.v. N/O/P — er zijn later kolommen ingevoegd), en de prijslijst *Adviesprijzen (incl btw.)
Vasa* bestaat niet meer (de S26-adviesprijzen staan in de junikopie op *Standaard*).

**Vijf keuzes staan open** (§Openstaande keuzes in de html): naam van het seizoenslabel
(`Spring/Summer 27` of `Summer 27`), kwaliteiten vertalen of Duits laten, `M.X.O. neu` apart houden,
wat met artikel 72255 (12 rijen met dummy-EAN `1000000000009`…, elk twee keer gebruikt), en welke twee
prijslijsten de VKP en de adviesprijs krijgen.

## 25 augustus 2026 — Karntner S27: de afbeeldingen

Karntner stuurde de foto's na, in `opladen_producten/input_klant/wetransfer_…/`: twee zips (DAMEN
4422, HERREN 4423) met samen **463 JPEG's**, alle 853×1280 en 100–345 kB, met het artikelnummer als
bestandsnaam (`71102 S1.jpg`). Eén foto per hoofdproduct, geen foto per kleur — zoals S26 in productie
staat (451 van de 452 bestaande Karntner-templates dragen een `image_1920`, geen enkele variant).

**Aansluiting:** 261 van de 272 S27-artikelen hebben een foto. Elf blijven zonder (175, 71144, 71226,
71923, 71952, 71964, 71995, 72281, 72725, 72903, 73310) — beslist door Els: zo laten. De overige 202
foto's zijn artikelen die BAB niet afneemt; de zip is de volledige catalogus.

**Nieuw: stap F.** `import_F_afbeeldingen.xlsx` (261 rijen, `id` + `image_1920`) plus de uitgepakte map
`afbeeldingen_s27/` (44,5 MB). In de kolom `image_1920` staat de *bestandsnaam*; de jpg's gaan apart mee
via *Bestanden importeren → Upload your files* in de zijbalk van de wizard. Odoo 18 koppelt ze achteraf
in schijven van 10 MB.

**Waarom apart en niet als kolom in C:** Odoo koppelt de bestanden **op rijnummer** — bestandsnaam van
rij *n* naar het *n*-de aangemaakte record. `import_C_hoofdproducten.xlsx` heeft 813 rijen voor 272
producten (twee vervolgregels per artikel voor de maten- en kwaliteitslijn), dus vanaf het tweede
artikel schuift alles op, zonder foutmelding. Staat als valkuil in de html.

De gids `opladen_karntner_s27.html` is bijgewerkt: bronbestandentabel, §De afbeeldingen, rij F in het
bestandenoverzicht, stap 9 in de importvolgorde, procedurestap F, de valkuil en een extra controle.

### Later die dag — de negende export is binnen

Els draaide `* Karntner-varianten opnieuw ophalen` op productie; `karntner_varianten.xls` staat in
`opladen_producten/output_claude/`. **7 598 rijen over 272 artikelen** — exact het aantal dat uit de
bron voorspeld was, dus stap C is volledig geland en Odoo maakte elke matrixcombinatie aan.

126 varianten dragen al een barcode: die van artikel 175, het Winter 26-artikel. Ze komen tot op het
cijfer overeen met `koppeltabel_D_barcodes.xlsx`.

**`import_D_barcodes.xlsx` gebouwd:** 7 460 rijen, `id` + `barcode`. De 138 die wegvallen zijn de twee
groepen die al voorspeld waren — 126 van 175 (staat er al op) en 12 van 72255 (enkel dummy-EAN's,
`1000000000009`… elk twee keer gebruikt). Ze staan met hun reden op het tabblad *niet mee*.

Gecontroleerd: elke referentie uit de koppeltabel teruggevonden in de export, geen dubbele
`default_code`, de 7 460 barcodes onderling uniek, en **geen botsing** met een barcode die al bij een
Karntner-variant in productie staat.

Gids bijgewerkt: §De negende export toont nu de uitkomst i.p.v. de vraag om het bestand, D1 staat
afgevinkt, D2 is een gewone import geworden (geen VLOOKUP-handwerk meer), en er staat een kader bij
waarom het er 7 460 zijn en geen 7 598.

### Nog die dag — vinkjes en MTO waren niet mee

Els merkte na de oplading dat *Verkoop* uit stond en de MTO-route ontbrak. Ze zitten wél in een
bestand — `import_productinstellingen.xlsx`, 271 rijen met `sale_ok`, `purchase_ok` en `route_ids/id` —
maar dat stond **niet in het bestandenoverzicht** van de gids, enkel als stap 7 verderop in de
volgordetabel. Zelfde voor `import_175_gewicht.xlsx`. Dat is de reden dat het over het hoofd gezien is.

Rechtgezet: beide staan nu als **G** en **H** in het overzicht, met een letter in de volgordetabel, en G
heeft een eigen procedurestap met een waarschuwing bovenaan. De valkuil zelf (*ir.default* zet `sale_ok`
op false bij elk nieuw product) stond er al.

Nog te draaien in productie: `import_productinstellingen.xlsx`. Herhaalbaar, gewone update op externe
ID. Artikel 175 hoort er niet in — dat draagt beide vinkjes en MTO al sinds Winter 26; in de
proefoplading (`bab18-20260618`) was het ook het enige van de 272 met `sale_ok` aan.
