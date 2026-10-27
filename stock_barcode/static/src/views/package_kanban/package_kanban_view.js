import { Component, useState } from "@odoo/owl";
import { Pager } from "@web/core/pager/pager";
import { registry } from "@web/core/registry";
import { kanbanView } from "@web/views/kanban/kanban_view";

export class PackageKanbanControlPanel extends Component {
    static components = { Pager };
    static props = ["*"];
    static template = "stock_barcode.PackageKanbanControlPanel";

    setup() {
        this.pagerProps = useState(this.env.config.pagerProps);
    }
}

export const packageKanbanView = {
    ...kanbanView,
    ControlPanel: PackageKanbanControlPanel,
};

registry.category("views").add("stock_barcode_package_kanban", packageKanbanView);
