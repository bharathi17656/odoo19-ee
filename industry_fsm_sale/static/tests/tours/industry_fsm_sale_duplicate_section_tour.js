import { registry } from "@web/core/registry";
import { stepUtils } from "@web_tour/tour_utils";

registry.category("web_tour.tours").add("industry_fsm_sale_duplicate_section_tour", {
    steps: () => [
        {
            trigger: ".o_list_section_options button",
            run: "click",
        },
        {
            trigger: ".o-dropdown-item:contains(Duplicate)",
            run: "click",
        },
        {
            trigger: ".o_data_row.o_is_line_section:eq(1)",
        },
        ...stepUtils.saveForm(),
    ],
});
