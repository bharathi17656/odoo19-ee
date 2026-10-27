import { _t } from "@web/core/l10n/translation";
import { useAutofocus, useService } from "@web/core/utils/hooks";
import { formatFloat, formatPercentage } from "@web/views/fields/formatters";
import { parseFloat, parseInteger } from "@web/views/fields/parsers";
import { Component, useRef, useState } from "@odoo/owl";

export class HelpdeskTeamTarget extends Component {
    static template = "helpdesk.HelpdeskTeamTarget";
    static props = {
        showDemo: { type: Boolean, optional: true },
        demoClass: { type: String, optional: true },
        update: Function,
        percentage: { type: Boolean, optional: true },
        rating: { type: Boolean, optional: true },
        value: Number,
        hotkey: { type: String, optional: true },
    };
    static defaultProps = {
        showDemo: false,
        demoClass: "",
        percentage: false,
        rating: false,
    };

    setup() {
        useAutofocus({ refName: 'inputRef', selectAll: true });
        this.inputRef = useRef("inputRef");
        this.notification = useService("notification");
        this.state = useState({
            isFocused: false,
            value: this.props.value,
        });
    }

    get valueString() {
        return this.props.rating
            ? `${this.state.value} / 5`
            : !this.props.percentage
            ? this.state.value
            : formatPercentage(this.state.value / 100);
    }

    get helpdeskTeamTargetTitle() {
        if (this.props.showDemo) {
            return _t("Average rating daily target");
        } else if (this.props.rating) {
            return _t("Click to Set Your Daily Rating Target");
        } else {
            return _t("Click to set");
        }
    }

    /**
     * @private
     */
    _toggleFocus() {
        this.state.isFocused = !this.state.isFocused;
    }

    /**
     * Handle the keydown event on the value input
     *
     * @private
     * @param {KeyboardEvent} ev
     */
    _onInputKeydown(ev) {
        if (ev.key === 'Enter') {
            this.inputRef.el.blur();
        }
    }

    /**
     * @private
     */
    async _onValueChange() {
        const inputValue = this.inputRef.el.value;
        let targetValue;
        try {
            targetValue = this.props.rating ? parseFloat(inputValue) : parseInteger(inputValue);
        } catch {
            this.notification.add(_t("Please enter a number."), { type: "danger" });
            return;
        }
        if (targetValue <= 0) {
            this.notification.add(_t("Please enter a positive value."), { type: "danger" });
            return;
        }
        if (this.props.percentage && targetValue > 100) {
            this.notification.add(_t("Please enter a percentage below 100."), { type: "danger" });
            return;
        } else if (this.props.rating && targetValue > 5) {
            this.notification.add(_t("Please enter a value less than or equal to 5."), {
                type: "danger",
            });
            return;
        }
        this.state.value = formatFloat(targetValue, { digits: [1, 0] });
        await this.props.update(targetValue);
    }
}
