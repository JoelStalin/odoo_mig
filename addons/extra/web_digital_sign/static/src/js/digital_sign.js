/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { binaryField, BinaryField } from "@web/views/fields/binary/binary_field";
import { DigitalSignature } from "@web_digital_sign/components/digital_signature/digital_signature";

export class SignatureField extends BinaryField {
    static template = "web_digital_sign.SignatureField";
    static components = { ...super.components, DigitalSignature };

    setup() {
        super.setup();
        this.notification = useService("notification");
        this.env = useService("env"); // Odoo 16+ for env
    }

    get signatureValue() {
        return this.props.record.data[this.props.name] || null;
    }

    async updateSignature(signatureData) {
        await this.props.record.update({ [this.props.name]: signatureData });
        if (!signatureData) {
             this.notification.add(this.env._t("Signature cleared."), { type: "info" });
        } else {
             // For Odoo 17, no explicit save message is usually needed as it's reactive
             // this.notification.add(this.env._t("Signature updated."), { type: "success" });
        }
    }
}

SignatureField.props = {
    ...binaryField.props,
};

registry.category("fields").add("digital_signature", SignatureField);

// The XML template for SignatureField itself (web_digital_sign.SignatureField)
// should be created in an XML file and included in assets.
// Example: addons/extra/web_digital_sign/static/src/components/digital_signature/digital_signature_field.xml
// Content for digital_signature_field.xml:
/*
<templates xml:space="preserve">
    <t t-name="web_digital_sign.SignatureField" owl="1">
        <DigitalSignature
            value="signatureValue"
            readonly="props.readonly"
            update="(data) => this.updateSignature(data)"
        />
    </t>
</templates>
*/
