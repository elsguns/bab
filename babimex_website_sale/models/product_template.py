from odoo import models, fields

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    long_description = fields.Html(
        string='Long Description',
        translate=True
    )

    def _get_combination_info(
        self,
        combination=False,
        product_id=False,
        add_qty=1,
        parent_combination=False,
        only_template=False,
    ):
        combination_info = super()._get_combination_info(
            combination=combination,
            product_id=product_id,
            add_qty=add_qty,
            parent_combination=parent_combination,
            only_template=only_template,
        )
        product_id = self.env['product.product'].browse(combination_info['product_id'])
        combination_info.update(
            {
                "default_code": product_id.default_code,
                "barcode": product_id.barcode,
            }
        )
        return combination_info
