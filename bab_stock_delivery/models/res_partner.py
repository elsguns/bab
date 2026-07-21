# Part of the o.s.admin add-ons.
from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # Babimex stock location code, shown before the customer name on the
    # Productenmatrix delivery report.
    stock_location = fields.Integer(string="Stock Location")

    # Country-specific numbering ranges for the stock location code.
    # Each entry is (lower bound, upper bound), both inclusive; an upper bound
    # of None means the range is open-ended. Countries not listed fall back to
    # _STOCK_LOCATION_RANGE_OTHER.
    #   Belgian customers  : 1-1999
    #   Dutch customers    : 2000-3999
    #   Customers elsewhere: from 4000 on
    # Keep these in sync with the "* Stocklocatie toekennen" server action,
    # which renumbers every address from scratch.
    _STOCK_LOCATION_RANGES = {
        'BE': (1, 1999),
        'NL': (2000, 3999),
    }
    _STOCK_LOCATION_RANGE_OTHER = (4000, None)

    def _stock_location_range(self):
        """Return the (low, high) numbering range for this partner's country."""
        self.ensure_one()
        country_code = self.country_id.code
        return self._STOCK_LOCATION_RANGES.get(
            country_code, self._STOCK_LOCATION_RANGE_OTHER
        )

    def _stock_location_in_range(self):
        """Whether this partner's current number sits in its country range."""
        self.ensure_one()
        low, high = self._stock_location_range()
        return low <= self.stock_location and (high is None or self.stock_location <= high)

    def _assign_stock_location(self):
        """Give each partner that has no stock_location yet the next free
        number in its country-specific range.

        The next number is the highest number currently in use within the
        range plus one, or the range's lower bound when the range is still
        empty. Partners that already carry a number are left untouched, so a
        code assigned once stays stable. When several partners in ``self`` need
        a number, they are handled one by one: the search re-reads the range
        each time (the ORM flushes the pending write first because
        stock_location is in the domain), so they receive consecutive numbers.
        """
        Partner = self.env['res.partner']
        for partner in self:
            if partner.stock_location:
                continue
            low, high = partner._stock_location_range()
            domain = [('stock_location', '>=', low)]
            if high is not None:
                domain.append(('stock_location', '<=', high))
            highest = Partner.search(
                domain, order='stock_location desc', limit=1
            ).stock_location
            partner.stock_location = highest + 1 if highest else low

    def write(self, vals):
        """When a partner's country changes, its existing stock location code
        may no longer belong to the right range. Typical case: an address is
        first created without a country, gets a number in the 4000 range, and
        the country is only filled in afterwards. Re-number such addresses into
        the range of their new country; addresses whose number still fits, or
        that never had one, are left alone.
        """
        res = super().write(vals)
        if 'country_id' in vals:
            for partner in self:
                if partner.stock_location and not partner._stock_location_in_range():
                    partner.stock_location = 0
                    partner._assign_stock_location()
        return res
