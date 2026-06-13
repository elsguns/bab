# Part of the o.s.admin add-ons.
from odoo import models


class ProductTemplateAttributeValue(models.Model):
    _inherit = 'product.template.attribute.value'

    def _grid_header_cell(self, *args, **kwargs):
        """Drop attribute values whose attribute carries a single value.

        On the Productenmatrix report a row label joins every non-size attribute
        value, e.g. "28 red comb. • 100%Viscose". An attribute that has only one
        value on the template (typically Kwaliteit/materiaal) is constant across
        the whole grid, so printing it on every row just wastes horizontal space.

        When called with context ``matrix_hide_single_value_attrs`` a value is
        kept only if its attribute line has more than one value OR it is the
        primary (first) attribute of the cell. Keeping the first one means a
        single-colour product still shows its colour while its (single-valued)
        material is dropped, and a multi-colour product drops only the constant
        material. Order is preserved and the matrix structure (ptav_ids, cells,
        quantities) is untouched -- this only shortens the displayed name.
        """
        records = self
        if self.env.context.get('matrix_hide_single_value_attrs') and self:
            primary = self[0]
            records = self.filtered(
                lambda v: v == primary
                or len(v.attribute_line_id.product_template_value_ids._only_active()) > 1
            )
        return super(ProductTemplateAttributeValue, records)._grid_header_cell(*args, **kwargs)
