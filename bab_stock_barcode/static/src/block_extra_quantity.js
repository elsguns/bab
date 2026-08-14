/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { patch } from "@web/core/utils/patch";
import BarcodePickingModel from "@stock_barcode/models/barcode_picking_model";

patch(BarcodePickingModel.prototype, {
    /**
     * Refuses the part of a scan that goes over a line's demand.
     *
     * Standard Odoo has no setting for this: "Allow extra products" only stops
     * products that are not on the transfer at all, and a product that IS on it
     * can be scanned without limit. What core does with the excess is fill the
     * line up to its demand and put the rest on a COPY of that line
     * (_processBarcode -> _createNewLine with copyOf), silently. Refusing that
     * copy is therefore the one place where an overscan can be stopped without
     * reimplementing the 280-line _processBarcode.
     *
     * splitLine() copies a line as well, but only one that is not complete yet
     * (shouldSplitLine requires qty_done < reserved_uom_qty), while the copy we
     * want to block always follows a line that was just filled to its demand.
     * That is what tells the two apart -- hence the check on the copied line
     * rather than a flag set earlier in the scan.
     *
     * The scan is not lost: whatever fitted within the demand has already been
     * booked by then, only the surplus is dropped. Returning the original line
     * instead of false keeps it selected, so the picker sees the red message on
     * the line it belongs to.
     */
    async _createNewLine(params) {
        const line = params.copyOf;
        if (this.config.barcode_block_extra_quantity && line &&
                this.getQtyDemand(line) && this.getQtyDone(line) >= this.getQtyDemand(line)) {
            const product = line.product_id;
            const productName = (product.code ? `[${product.code}] ` : "") + product.display_name;
            this.notification(
                _t("%(product)s is already fully scanned (%(qty)s). The extra scan was refused.",
                    { product: productName, qty: this.getQtyDemand(line) }),
                { type: "danger" });
            this.trigger("playSound", "error");
            return line;
        }
        return super._createNewLine(...arguments);
    },
});
