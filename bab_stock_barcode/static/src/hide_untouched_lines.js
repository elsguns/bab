/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import BarcodePickingModel from "@stock_barcode/models/barcode_picking_model";

patch(BarcodePickingModel.prototype, {
    /**
     * Tells the header the filter button makes sense here. Only a transfer
     * knows a "nothing scanned yet" state; on an inventory count this getter
     * stays undefined and the button isn't rendered.
     */
    get hasUntouchedLinesFilter() {
        return true;
    },

    get hideUntouchedLines() {
        return Boolean(this._hideUntouchedLines);
    },

    toggleUntouchedLines() {
        this._hideUntouchedLines = !this._hideUntouchedLines;
        this.trigger("update");
    },

    /**
     * A line counts as touched as soon as a quantity was scanned on it. Package
     * lines carry the quantity of their first subline only, hence the check on
     * the sublines.
     */
    lineWasScannedOn(line) {
        if (line.lines) {
            return line.lines.some((subline) => this.getQtyDone(subline) > 0);
        }
        return this.getQtyDone(line) > 0;
    },

    /**
     * Display-only filter: this getter is read by the template alone, while
     * scanning, grouping and validating keep working from `pageLines`. A hidden
     * line is therefore still found and updated when its barcode is scanned,
     * and shows up again the moment it holds a quantity.
     */
    get groupedLinesByLocation() {
        const groups = super.groupedLinesByLocation;
        if (!this._hideUntouchedLines) {
            return groups;
        }
        const filteredGroups = [];
        for (const group of groups) {
            const lines = group.lines.filter((line) => this.lineWasScannedOn(line));
            if (lines.length) {
                filteredGroups.push(Object.assign({}, group, { lines }));
            }
        }
        return filteredGroups;
    },
});
