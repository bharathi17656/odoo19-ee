import { patch } from "@web/core/utils/patch";
import { hootPosModels } from "@point_of_sale/../tests/unit/data/generate_model_definitions";
import { models } from "@web/../tests/web_test_helpers";

export class PlatformOrderProvider extends models.ServerModel {
    _name = "platform.order.provider";
    _records = [{ id: 1, name: "FoodPanda", code: "gofood" }];

    _load_pos_data_fields() {
        return ["name", "code"];
    }
}

patch(hootPosModels, [...hootPosModels, PlatformOrderProvider]);
