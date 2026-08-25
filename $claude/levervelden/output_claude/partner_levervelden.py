#!/usr/bin/env python3
"""Zet de levervelden Sluitingsdagen en Leverinformatie op res.partner.

Maakt in een doel-database dezelfde twee manuele velden aan als in Babimex,
plus de erfview die ze op het contactformulier toont onder de
leveringsinstellingen.

    res.partner.x_studio_closing_days   (text)  Sluitingsdagen
    res.partner.x_studio_delivery_info  (text)  Leverinformatie

Gebruik (binnen odoo shell, env is dan al beschikbaar):

    odoo-bin shell -d <database> --addons-path=... < partner_levervelden.py

Gebruik (standalone, met odoo importeerbaar via PYTHONPATH of pip install):

    PYTHONPATH=/pad/naar/odoo python3 partner_levervelden.py \
        -d <database> --addons-path=addons,../enterprise,../osa

Het script werkt zonder neveneffect bij herhaling: bestaande velden/views worden bijgewerkt, niet
gedupliceerd.
"""

import logging

_logger = logging.getLogger("partner_levervelden")

# Klantcode voor de naamgeving van de afgeleide view (res.partner.form.<code>).
CODE = "osa"

# XML-id waaronder de view geregistreerd wordt, zodat een tweede run dezelfde
# view terugvindt in plaats van een nieuwe te maken.
VIEW_MODULE = "__custom__"
VIEW_XMLID = "res_partner_form_delivery_fields"

FIELDS = [
    {
        "name": "x_studio_closing_days",
        "ttype": "text",
        "labels": {"en_US": "Sluitingsdagen", "nl_BE": "Sluitingsdagen"},
    },
    {
        "name": "x_studio_delivery_info",
        "ttype": "text",
        "labels": {"en_US": "Delivery Info", "nl_BE": "Leverinformatie"},
    },
]

# Het contactformulier krijgt de velden achter het leveringsmethode-veld. Staat
# de module delivery niet geïnstalleerd, dan valt de xpath terug op het
# btw-nummer, dat altijd in base.view_partner_form zit.
ANCHORS = [
    "//field[@name='property_delivery_carrier_id']",
    "//field[@name='vat']",
]


def _create_fields(env):
    model_id = env["ir.model"]._get_id("res.partner")
    langs = [code for code, _name in env["res.lang"].get_installed()]

    for spec in FIELDS:
        field = env["ir.model.fields"].search(
            [("model", "=", "res.partner"), ("name", "=", spec["name"])], limit=1
        )
        values = {
            "name": spec["name"],
            "model_id": model_id,
            "ttype": spec["ttype"],
            "state": "manual",
            "store": True,
            "copied": True,
            "field_description": spec["labels"]["en_US"],
        }
        if field:
            if field.state != "manual":
                raise SystemExit(
                    "%s bestaat al als veld uit code (state=%s) — script afgebroken"
                    % (spec["name"], field.state)
                )
            field.with_context(lang="en_US").write(values)
            _logger.info("veld %s bijgewerkt", spec["name"])
        else:
            field = env["ir.model.fields"].with_context(lang="en_US").create(values)
            _logger.info("veld %s aangemaakt", spec["name"])

        # Vertaalde labels enkel zetten voor talen die effectief geïnstalleerd
        # zijn, anders slikt Odoo de waarde stil in.
        for lang, label in spec["labels"].items():
            if lang != "en_US" and lang in langs:
                field.with_context(lang=lang).field_description = label


def _create_view(env):
    view = env.ref("%s.%s" % (VIEW_MODULE, VIEW_XMLID), raise_if_not_found=False)
    fields_xml = "\n".join(
        '    <field name="%s"/>' % spec["name"] for spec in FIELDS
    )

    last_error = None
    for anchor in ANCHORS:
        arch = (
            "<data>\n"
            '  <xpath expr="%s" position="after">\n'
            "%s\n"
            "  </xpath>\n"
            "</data>" % (anchor, fields_xml)
        )
        values = {
            "name": "res.partner.form.%s" % CODE,
            "model": "res.partner",
            "type": "form",
            "inherit_id": env.ref("base.view_partner_form").id,
            "mode": "extension",
            "priority": 360,
            "arch_db": arch,
        }
        try:
            with env.cr.savepoint():
                if view:
                    view.write(values)
                else:
                    view = env["ir.ui.view"].create(values)
                    env["ir.model.data"].create({
                        "module": VIEW_MODULE,
                        "name": VIEW_XMLID,
                        "model": "ir.ui.view",
                        "res_id": view.id,
                        "noupdate": True,
                    })
        except Exception as exc:  # xpath vindt het ankerveld niet
            last_error = exc
            _logger.info("anker %s werkt niet, volgende proberen", anchor)
            continue
        _logger.info("view res.partner.form.%s geplaatst na %s", CODE, anchor)
        return

    raise SystemExit("geen bruikbaar anker gevonden op het contactformulier: %s" % last_error)


def main(env):
    _create_fields(env)
    _create_view(env)
    env.cr.commit()
    _logger.info("klaar")


if "env" in globals():
    # Draait binnen odoo shell.
    main(env)  # noqa: F821
else:
    import sys

    import odoo
    from odoo.api import Environment
    from odoo.modules.registry import Registry
    from odoo.tools import config

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    config.parse_config(sys.argv[1:])
    dbname = config["db_name"]
    if not dbname:
        raise SystemExit("geef de doel-database mee met -d <database>")

    odoo.service.server.load_server_wide_modules()
    with Registry(dbname).cursor() as cr:
        main(Environment(cr, odoo.SUPERUSER_ID, {}))
