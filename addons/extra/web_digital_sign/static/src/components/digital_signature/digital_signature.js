/** @odoo-module **/

import { Component, useState, useRef, onMounted, onWillUnmount, onWillUpdateProps } from "@odoo/owl";
import { loadJS } from "@web/core/assets";

// Placeholder for a signature pad library. Example: SignaturePad by szimek
// import SignaturePad from 'signature_pad'; // This would be a real import if using a library

export class DigitalSignature extends Component {
    static template = "web_digital_sign.DigitalSignature";
    static props = {
        value: { type: String, optional: true },
        readonly: { type: Boolean, optional: true },
        update: { type: Function, optional: true },
    };

    setup() {
        this.signaturePad = null;
        this.canvasRef = useRef("signatureCanvas");
        this.state = useState({
            isEmpty: true,
        });

        onMounted(() => {
            this.initSignaturePad();
            if (this.props.value) {
                this.setSignatureData(this.props.value);
            }
        });

        onWillUpdateProps(async (nextProps) => {
            if (this.signaturePad && nextProps.value !== this.props.value) {
                if (nextProps.value) {
                    this.setSignatureData(nextProps.value);
                } else {
                    this.signaturePad.clear();
                    this.state.isEmpty = true;
                }
            }
            if (nextProps.readonly !== this.props.readonly) {
                if (nextProps.readonly) {
                    this.signaturePad?.off();
                } else {
                    this.signaturePad?.on();
                }
            }
        });

        onWillUnmount(() => {
            // Clean up if necessary, e.g. signaturePad.off()
        });
    }

    async initSignaturePad() {
        // Example using SignaturePad library
        // await loadJS('/path/to/signature_pad.umd.js'); // Load the library if not globally available
        // this.signaturePad = new SignaturePad(this.canvasRef.el, {
        //     backgroundColor: 'rgb(255, 255, 255)',
        //     penColor: 'rgb(0, 0, 0)',
        //     onEnd: () => {
        //         if (this.props.update && !this.props.readonly) {
        //             const data = this.signaturePad.toDataURL('image/png'); // or 'image/jpeg'
        //             // Odoo typically stores base64 without the data URL prefix
        //             const base64Data = data.split(',')[1];
        //             this.props.update(base64Data);
        //             this.state.isEmpty = this.signaturePad.isEmpty();
        //         }
        //     }
        // });

        // Placeholder for direct canvas drawing or other library
        // For now, this is a conceptual placeholder.
        // A real implementation would draw on the canvas and extract data.
        console.log("DigitalSignature component mounted. Canvas element:", this.canvasRef.el);
        // Simulate a simple pad for structure
        if (this.canvasRef.el) {
            const canvas = this.canvasRef.el;
            const ctx = canvas.getContext("2d");
            // Simple drawing example (replace with actual signature logic)
            // ctx.fillRect(10, 10, 50, 50);
            // This is just to show the canvas is accessible.
             this.signaturePad = { // Mock signature pad
                clear: () => {
                    if(canvas){
                        const context = canvas.getContext('2d');
                        context.clearRect(0, 0, canvas.width, canvas.height);
                        this.state.isEmpty = true;
                        if (this.props.update && !this.props.readonly) this.props.update(false);
                    }
                    console.log("Signature cleared (mock)");
                },
                fromDataURL: (dataUrl) => {
                    console.log("Signature set from data URL (mock)", dataUrl ? dataUrl.substring(0,30) + "..." : "empty");
                    // In a real scenario, you'd draw the image onto the canvas
                    this.state.isEmpty = !dataUrl;
                },
                toDataURL: (type) => {
                    console.log("Signature toDataURL called (mock)");
                    // In a real scenario, you'd get canvas.toDataURL()
                    return canvas && !this.state.isEmpty ? canvas.toDataURL(type) : "data:image/png;base64,"; // return empty image
                },
                isEmpty: () => this.state.isEmpty,
                on: () => console.log("Signature pad enabled (mock)"),
                off: () => console.log("Signature pad disabled (mock)"),
            };

            // Simulate drawing for visual feedback during conceptual dev
            canvas.addEventListener('mousedown', () => {
                if (!this.props.readonly && this.signaturePad) {
                    this.state.isEmpty = false; // Assume drawing started
                    // Simulate a change for update prop
                    if (this.props.update) {
                         // A real implementation would get data from canvas
                        this.props.update("SIMULATED_SIGNATURE_DATA_" + new Date().getTime());
                    }
                }
            });
        }

        if (this.props.readonly) {
            this.signaturePad?.off();
        }
    }

    setSignatureData(dataUrl) {
        if (this.signaturePad) {
            // Assuming dataUrl is base64 data without prefix for fromDataURL
            // or with prefix if the library expects it.
            // For Odoo, it's usually just the base64 string.
            if (dataUrl && !dataUrl.startsWith('data:')) {
                this.signaturePad.fromDataURL('data:image/png;base64,' + dataUrl);
            } else if (dataUrl) {
                this.signaturePad.fromDataURL(dataUrl);
            } else {
                this.signaturePad.clear();
            }
            this.state.isEmpty = this.signaturePad.isEmpty();
        }
    }

    clearSignature() {
        if (this.signaturePad && !this.props.readonly) {
            this.signaturePad.clear();
            if (this.props.update) {
                this.props.update(false); // Send false or empty string for cleared signature
            }
            this.state.isEmpty = true;
        }
    }
}

// Helper function to convert base64 to a Blob (if needed for a library)
function base64ToBlob(base64, type = 'application/octet-stream') {
    const byteCharacters = atob(base64);
    const byteNumbers = new Array(byteCharacters.length);
    for (let i = 0; i < byteCharacters.length; i++) {
        byteNumbers[i] = byteCharacters.charCodeAt(i);
    }
    const byteArray = new Uint8Array(byteNumbers);
    return new Blob([byteArray], { type });
}
