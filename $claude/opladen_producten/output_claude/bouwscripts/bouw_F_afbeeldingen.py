"""Bouwt import_F_afbeeldingen.xlsx en pakt de bijhorende foto's uit.

Draaien vanuit opladen_producten/. Zie opladen_karntner_s27.html, stap F.

De leverancier stuurt de foto's als zips met de volledige catalogus, één jpg per
artikel, bestandsnaam = artikelnummer + " S1.jpg". Alleen de artikelen die BAB
afneemt worden uitgepakt; de rest blijft in de zip zitten.

In de kolom image_1920 komt de *bestandsnaam*, niet de afbeelding. Odoo 18
koppelt de bestanden na de import: in de zijbalk van de wizard staat
"Bestanden importeren -> Upload your files", en daar gaan de uitgepakte jpg's in.

Waarom een apart bestand en geen kolom in C: Odoo koppelt op *rijnummer* --
bestandsnaam van rij n naar het n-de aangemaakte record. Het C-bestand heeft
drie rijen per artikel (de hoofdregel plus twee vervolgregels voor de maten- en
kwaliteitslijn), dus vanaf het tweede artikel schuift alles op. Zonder
foutmelding: elk product krijgt een geldige foto, alleen niet de zijne.
"""

import os
import re
import shutil
import zipfile

import openpyxl

ZIPMAP = 'input_klant/wetransfer_produktfotos-kategorie-damen_2027_fruehjahr-sommer-gesamt-4422-zip_2026-08-25_0630'
UIT = 'output_claude/afbeeldingen_s27'
IMPORT_C = 'output_claude/import_C_hoofdproducten.xlsx'
SUFFIX = re.compile(r'\s+S1\.jpg$', re.I)

# de artikelnummers in de volgorde waarin C ze aanmaakt
wb = openpyxl.load_workbook(IMPORT_C)
artikelen = [(str(r[0]), r[1]) for r in wb['controle'].iter_rows(min_row=2, values_only=True) if r[0]]

# de zips uitlezen zonder ze uit te pakken
fotos = {}
for bestand in sorted(os.listdir(ZIPMAP)):
    if not bestand.endswith('.zip'):
        continue
    z = zipfile.ZipFile(os.path.join(ZIPMAP, bestand))
    for zi in z.infolist():
        fotos[SUFFIX.sub('', zi.filename).strip()] = (z, zi)

if os.path.isdir(UIT):
    shutil.rmtree(UIT)
os.makedirs(UIT)

rijen, zonder = [], []
for artikel, naam in artikelen:
    if artikel not in fotos:
        zonder.append((artikel, naam))
        continue
    z, zi = fotos[artikel]
    # bestandsnaam onaangeroerd laten: de wizard matcht op precies die naam,
    # spatie inbegrepen
    with open(os.path.join(UIT, zi.filename), 'wb') as fh:
        fh.write(z.read(zi))
    rijen.append(('__export__.product_template_%s' % artikel, zi.filename))

nw = openpyxl.Workbook()
ws = nw.active
ws.title = 'import'
ws.append(['id', 'image_1920'])
for rij in rijen:
    ws.append(list(rij))
ws.column_dimensions['A'].width = 40
ws.column_dimensions['B'].width = 20

wsz = nw.create_sheet('zonder foto')
wsz.append(['artikel', 'naam'])
for rij in zonder:
    wsz.append(list(rij))
wsz.column_dimensions['A'].width = 12
wsz.column_dimensions['B'].width = 30

nw.save('output_claude/import_F_afbeeldingen.xlsx')

overtollig = len(fotos) - len(rijen)
print('import_F_afbeeldingen.xlsx: %d rijen, %d zonder foto' % (len(rijen), len(zonder)))
print('%s: %d bestanden (%d foto\'s in de zips horen bij artikelen buiten de collectie)'
      % (UIT, len(rijen), overtollig))
