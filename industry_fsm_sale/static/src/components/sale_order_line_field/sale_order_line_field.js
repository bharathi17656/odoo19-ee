import { SaleOrderLineListRenderer } from "@sale/js/sale_order_line_field/sale_order_line_field";
import { patch } from "@web/core/utils/patch";

patch(SaleOrderLineListRenderer.prototype, {
    setup() {
        super.setup();
        // the task of the original line must not be linked to the duplicated one
        this.noCopyFields.push("task_id");
    },
});
