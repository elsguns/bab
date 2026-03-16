import publicWidget from '@web/legacy/js/public/public_widget';

publicWidget.registry.WebsiteSale.include({
    _onChangeCombination(ev, $parent, combination) {
        const res = this._super.apply(this, arguments);
        if(combination && combination.default_code) {
            $parent.find(".o_wsale_product_default_code").text(combination.default_code);
        }else {
            $parent.find(".o_wsale_product_default_code").text('');
        }
        if(combination && combination.barcode) {
            $parent.find(".o_wsale_product_barcode").text(combination.barcode);
        }else {
            $parent.find(".o_wsale_product_barcode").text('');
        }
        return res;
    }
});
