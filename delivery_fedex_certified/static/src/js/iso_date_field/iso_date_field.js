/** @odoo-module **/
import {DateTimeField, dateField} from '@web/views/fields/datetime/datetime_field'
import {formatDate} from "@web/core/l10n/dates";
import {registry} from "@web/core/registry";
import {xml} from "@odoo/owl"

export class IsoDateField extends DateTimeField {
    static template = xml`
        <p
            t-ref="start-date"
            t-if="value"
            t-out="value"
        />
        <input style="border: none; outline: none" t-ref="start-date" t-else=""/>
    `;

    get value() {
        return formatDate(this.state.value, {format: 'yyyy-MM-dd'})
    }
}

registry.category("fields").add("iso_date_field", {...dateField, component: IsoDateField});
