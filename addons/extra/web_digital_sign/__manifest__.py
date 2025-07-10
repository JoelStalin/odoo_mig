# See LICENSE file for full copyright and licensing details.

{
    'name': 'Web Digital Signature',
    'version': '17.0.1.0.0',
    "category": "Tools",
    "sequence": 3,
    "summary": """
        Touch screen enable so user can add signature with touch devices.
        Digital signature can be very usefull for documents.
    """,
     "description": """
     This module provides the functionality to store digital signature
     Example can be seen into the User's form view where we have
        added a test field under signature.
    """,
    "author": "Serpent Consulting Services Pvt. Ltd.",
    "website": "http://www.serpentcs.com/",
    'license': 'LGPL-3',
    'depends': ['web', 'account','exo_api'],
    "images": ["static/description/Digital_Signature.jpg"],
    "data": [
            "views/account_move_view.xml",
            "views/res_partner_view.xml",
             
             ],
    "assets": {
        "web.assets_backend": [
            "/web_digital_sign/static/src/js/digital_sign.js",
            "/web_digital_sign/static/src/components/digital_signature/digital_signature.js",
            "/web_digital_sign/static/src/components/digital_signature/digital_signature.xml",
            "/web_digital_sign/static/src/components/digital_signature/digital_signature_field.xml",
        ],
    },
    'installable': True,
    'application': True,
}
