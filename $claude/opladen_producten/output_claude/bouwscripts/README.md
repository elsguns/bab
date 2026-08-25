# Bouwscripts voor de Karntner-oplading

De gids `../opladen_karntner_s27.html` beschrijft *wat* er moet gebeuren en waarom.
Deze twee scripts zijn het *hoe* voor de twee bestanden die niet met de hand te
maken zijn.

| Script | Maakt | Draaien vanuit |
|---|---|---|
| `bouw_D_barcodes.py` | `import_D_barcodes.xlsx` | `output_claude/` |
| `bouw_F_afbeeldingen.py` | `import_F_afbeeldingen.xlsx` + de map `afbeeldingen_s27/` | `opladen_producten/` |

Beide hebben alleen `openpyxl` nodig en lezen de bronbestanden uit
`input_klant/` en de exports uit `output_claude/`. Die staan met opzet **niet** in
git — ze zijn groot en verouderen bij de eerste wijziging in de databank. Bij een
volgende collectie zijn ze opnieuw op te halen: de leverancier stuurt zijn bestand,
en de twee serveracties in de gids leveren de exports.

## Wat hier niet staat

De bestanden **B** (kenmerkwaarden), **C** en **C2** (hoofdproducten), **E1** en
**E2** (prijzen), `import_productinstellingen.xlsx` en `import_175_gewicht.xlsx`
zijn in een eerdere sessie gemaakt; die code is niet bewaard. De bestanden zelf
staan er wel, en de gids beschrijft per bestand welke kolommen erin horen en waar
de waarden vandaan komen — genoeg om ze opnieuw op te bouwen, maar het is meer
werk dan een script draaien.

Wordt er een volgende collectie geladen, dan is dat het moment om ook die stappen
te scripten.
