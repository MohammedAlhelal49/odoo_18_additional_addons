/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { Many2OneField } from "@web/views/fields/many2one/many2one_field";

// Product fields in these models' lines can only be selected, never created.
const RESTRICTED_MODELS = [
    "sale.order.line",
    "purchase.order.line",
    "account.move.line",
    "stock.move",
    "stock.move.line",
    "stock.quant",
    "stock.picking",
];
const PRODUCT_MODELS = ["product.product", "product.template"];

patch(Many2OneField.prototype, {
    get lorcaSelectOnly() {
        return (
            PRODUCT_MODELS.includes(this.relation) &&
            RESTRICTED_MODELS.includes(this.props.record?.resModel)
        );
    },
    computeActiveActions(props) {
        super.computeActiveActions(props);
        if (this.lorcaSelectOnly) {
            this.state.activeActions.create = false;
            this.state.activeActions.createEdit = false;
        }
    },
    get Many2XAutocompleteProps() {
        const props = super.Many2XAutocompleteProps;
        if (this.lorcaSelectOnly) {
            props.quickCreate = null;
        }
        return props;
    },
});
