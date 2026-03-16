from markupsafe import Markup, escape
from odoo import models, api, _


class Contact(models.AbstractModel):
    _inherit = 'ir.qweb.field.contact'

    @api.model
    def get_available_options(self):
        """ Inherit the method to add 'babimex_commercial_name' as t-options in Qweb. """
        options = super(Contact, self).get_available_options()

        # Add new boolean option
        options.update(
            babimex_commercial_name=dict(
                type='boolean',
                string=_('Display Commercial Name'),
                description=_('Display the Commercial name if available.'),
            )
        )

        return options

    @api.model
    def value_to_html(self, value, options):
        """ Overwritten the method to include the Commercial Name in address
        when requested in the t-options via 'babimex_commercial_name' in XML. """
        if not value:
            if options.get('null_text'):
                val = {
                    'options': options,
                }
                template_options = options.get('template_options', {})
                return self.env['ir.qweb']._render('base.no_contact', val, **template_options)
            return ''

        opf = options.get('fields') or ["name", "address", "phone", "mobile", "email"]
        sep = options.get('separator')
        if sep:
            opsep = escape(sep)
        elif options.get('no_tag_br'):
            # escaped joiners will auto-escape joined params
            opsep = escape(', ')
        else:
            opsep = Markup('<br/>')

        value = value.sudo().with_context(show_address=True)
        display_name = value.display_name or ''
        # Avoid having something like:
        # display_name = 'Foo\n  \n' -> This is a res.partner with a name and no address
        # That would return markup('<br/>') as address. But there is no address set.
        if any(elem.strip() for elem in display_name.split("\n")[1:]):
            address = opsep.join(display_name.split("\n")[1:]).strip()
        else:
            address = ''
        val = {
            'name': display_name.split("\n")[0],
            'address': address,
            'phone': value.phone,
            'mobile': value.mobile,
            'city': value.city,
            'country_id': value.country_id.display_name,
            'website': value.website,
            'email': value.email,
            'vat': value.vat,
            'vat_label': value.country_id.vat_label or _('VAT'),
            'fields': opf,
            'object': value,
            'options': options
        }
        # Custom Code Start
        # Add the Commercial name if it is requested during the address printing
        if options.get('babimex_commercial_name') and value.commercial_name_id:
            val.update({'address': value.commercial_name_id.name + opsep + address})
        # Custom Code End
        return self.env['ir.qweb']._render('base.contact', val, minimal_qcontext=True)
