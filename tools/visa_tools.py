from typing import Dict


def get_visa_information(context: Dict[str, str]) -> Dict[str, str]:
    origin = context.get('origin_country') or 'your nationality'
    destination = context.get('destination_country') or 'the destination'
    return {
        'summary': f'Visa information for travelers from {origin} to {destination} should be verified using official embassy, airline, and immigration sources.',
        'disclaimer': 'This is informational only and should not be treated as final travel authorization advice.',
        'recommended_checks': 'Verify passport validity, visa rules, transit rules, entry forms, and health requirements before travel.',
    }
