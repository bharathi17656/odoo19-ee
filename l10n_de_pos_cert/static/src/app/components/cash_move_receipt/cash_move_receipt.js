import { patch } from "@web/core/utils/patch";
import { usePos } from "@point_of_sale/app/hooks/pos_hook";
import { CashMoveReceipt } from "@point_of_sale/app/components/popups/cash_move_popup/cash_move_receipt/cash_move_receipt";

patch(CashMoveReceipt, {
    props: {
        ...CashMoveReceipt.props,
        txnUuid: { type: String, optional: true },
    },
});

patch(CashMoveReceipt.prototype, {
    setup() {
        super.setup();
        this.pos = usePos();
    },
});
