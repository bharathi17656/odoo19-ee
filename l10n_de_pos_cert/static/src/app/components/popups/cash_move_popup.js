import { _t } from "@web/core/l10n/translation";
import { CashMovePopup } from "@point_of_sale/app/components/popups/cash_move_popup/cash_move_popup";
import { parseFloat } from "@web/views/fields/parsers";
import { patch } from "@web/core/utils/patch";
import { uuidv4 } from "@point_of_sale/utils";
import { roundCurrency } from "@point_of_sale/app/models/utils/currency";

patch(CashMovePopup.prototype, {
    setup() {
        super.setup();
        this.state.reason_type = "";
        this.txnUuid = "";
    },
    onClickButton(type) {
        super.onClickButton(type);
        this.state.reason_type = "";
    },
    _prepareTryCashInOutPayload(type, amount, reason, partnerId, extras) {
        // used to retrieve the reason type in backend at the time of session closing
        // If we change the format of the reason here, we also need to change it in `get_cash_statement_cases` of pos.session
        const result = super._prepareTryCashInOutPayload(...arguments);
        if (this.pos.isCountryGermanyAndFiskaly()) {
            result[3] = `${this.state.reason_type}-${reason}`;
        }
        return result;
    },
    isValidCashMove() {
        if (this.pos.isCountryGermanyAndFiskaly()) {
            return (
                this.state.amount &&
                this.env.utils.isValidFloat(this.state.amount) &&
                this.state.reason_type.trim() !== ""
            );
        }
        return super.isValidCashMove();
    },
    get categoryReasons() {
        const commonOptions = [
            { value: "", label: _t("Select a category") },
            { value: "geldtransit", label: _t("Cash Transfer") },
        ];
        const outOptions = [
            { value: "privatentnahme", label: _t("Private Withdrawal") },
            { value: "auszahlung", label: _t("Payout") },
            { value: "lohnzahlung", label: _t("Wage Payment") },
        ];
        const inOptions = [
            { value: "privateinlage", label: _t("Private Deposit") },
            { value: "einzahlung", label: _t("Deposit") },
            { value: "zuschussEcht", label: _t("Cash Supplement") },
        ];
        return this.state.type === "out"
            ? [...commonOptions, ...outOptions]
            : [...commonOptions, ...inOptions];
    },
    async confirm() {
        if (!this.pos.isCountryGermanyAndFiskaly()) {
            return super.confirm();
        }

        const receipt = {
            receipt_type: "RECEIPT",
            amounts_per_vat_rate: [],
            amounts_per_payment_type: [],
        };
        const data = {
            state: "ACTIVE",
            client_id: this.pos.getClientId(),
            schema: {
                standard_v1: { receipt },
            },
            metadata: {
                "Cash Transfer Type": `Cash ${this.state.type}`,
                "Reason Type": this.state.reason_type,
                Reason: this.state.reason.trim(),
                Responsible: this.pos.getCashier()?.name,
            },
        };
        this.txnUuid = uuidv4();
        const txnUrl = `${this.txnUuid}?tx_revision=`;
        // Create receipt transaction
        await this.pos.transactionCall(`${txnUrl}1`, data, undefined, 0, true);

        // Finish receipt transaction
        const amount = parseFloat(
            this.state.type === "in" ? this.state.amount : "-" + this.state.amount
        );
        const currency = this.pos.currency;
        const formattedAmount = roundCurrency(amount, currency).toFixed(currency.decimal_places);
        data.state = "FINISHED";
        receipt.amounts_per_vat_rate = [{ vat_rate: "0", amount: formattedAmount }];
        receipt.amounts_per_payment_type = [{ payment_type: "CASH", amount: formattedAmount }];
        await this.pos.transactionCall(`${txnUrl}2`, data, undefined, 0, true);
        return super.confirm();
    },
    getMessage(formattedAmount) {
        const msg = super.getMessage(formattedAmount);
        if (this.pos.isCountryGermanyAndFiskaly()) {
            return `TSE: ${this.txnUuid} - ${msg}`;
        }
        return msg;
    },
    getMoveReceiptProps(formattedAmount) {
        const props = super.getMoveReceiptProps(formattedAmount);
        if (this.pos.isCountryGermanyAndFiskaly()) {
            return { ...props, txnUuid: this.txnUuid };
        }
        return props;
    },
});
