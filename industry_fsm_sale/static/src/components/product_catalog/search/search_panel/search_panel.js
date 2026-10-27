import { user } from "@web/core/user";
import { onWillStart } from "@odoo/owl";

import { AccountProductCatalogSearchPanel } from "@account/components/product_catalog/search/search_panel";

export class FSMProductCatalogSearchPanel extends AccountProductCatalogSearchPanel {
    static template = "industry_fsm_sale.ProductCatalogSearchPanel";

    setup() {
        super.setup();
        onWillStart(async () => {
            this.canCreateSections = await user.hasGroup("sales_team.group_sale_salesman");
        });
    }

    _getSectionInfoParams(extra = {}) {
        return {
            ...super._getSectionInfoParams(extra),
            task_id: this.env.model.config.context.fsm_task_id,
        };
    }
}
