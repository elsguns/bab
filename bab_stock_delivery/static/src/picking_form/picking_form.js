/** @odoo-module **/
// Part of the o.s.admin add-ons.
import { registry } from "@web/core/registry";
import { formView } from "@web/views/form/form_view";
import { FormController } from "@web/views/form/form_controller";

/**
 * Odoo lists an action of the gear menu for every transfer of the model. The
 * two slip actions of this module only fit one kind of transfer each (a pick,
 * a done receipt), so the server tells per transfer which ones to leave out
 * (stock.picking.matrix_hidden_action_ids).
 */
export class MatrixPickingFormController extends FormController {
    get actionMenuItems() {
        const items = super.actionMenuItems;
        const hidden = this.model.root.data.matrix_hidden_action_ids || [];
        if (!hidden.length || !items.action) {
            return items;
        }
        return { ...items, action: items.action.filter((item) => !hidden.includes(item.id)) };
    }
}

registry.category("views").add("bab_matrix_picking_form", {
    ...formView,
    Controller: MatrixPickingFormController,
});
