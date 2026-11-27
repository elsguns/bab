/** @odoo-module **/
// Part of the o.s.admin add-ons.
import { patch } from "@web/core/utils/patch";
import { FormController } from "@web/views/form/form_controller";

/**
 * Odoo lists an action of the gear menu for every transfer of the model. The
 * two slip actions of this module only fit one kind of transfer each (a pick,
 * a done receipt), so the server tells per transfer which ones to leave out
 * (stock.picking.matrix_hidden_action_ids).
 *
 * A patch rather than a js_class on the transfer form: another module setting
 * its own js_class on that form would silently replace this one (or be
 * replaced by it). Any form without the field is left alone.
 */
patch(FormController.prototype, {
    get actionMenuItems() {
        const items = super.actionMenuItems;
        if (this.props.resModel !== "stock.picking") {
            return items;
        }
        const hidden = this.model.root.data.matrix_hidden_action_ids || [];
        if (!hidden.length || !items.action) {
            return items;
        }
        return { ...items, action: items.action.filter((item) => !hidden.includes(item.id)) };
    },
});
