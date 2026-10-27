/** @odoo-module **/
import { Component } from "@odoo/owl";
import { toNotifications } from "@l10n_ch_hr_payroll/components/swissdec_format";

const ALERTS = {
    error: { className: "alert-danger", icon: "fa-times-circle" },
    warning: { className: "alert-warning", icon: "fa-exclamation-triangle" },
    info: { className: "alert-info", icon: "fa-info-circle" },
};

export class SwissdecNotification extends Component {
    static template = "l10n_ch_hr_payroll.SwissdecNotification";
    static props = {
        type: { type: String }, // "error", "warning" or "info"
        notifications: { type: [Array, Object], optional: true },
    };

    get alert() {
        return ALERTS[this.props.type] || ALERTS.info;
    }

    get notifications() {
        return toNotifications(this.props.notifications, this.props.type);
    }
}

export default SwissdecNotification;
