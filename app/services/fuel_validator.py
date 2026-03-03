import re
from . import db

FUEL_KEYWORDS = {
    'diesel': ['diesel', 'on', 'olej napędowy', 'olej napedowy', 'b7', 'hvo'],
    'benzyna': ['benzyna', 'pb95', 'pb 95', 'pb98', 'pb 98', 'e10', 'e5', 'eurosuper', 'super plus', '95', '98'],
    'lpg': ['lpg', 'autogaz', 'gaz'],
    'cng': ['cng'],
    'elektryczny': ['ładowanie', 'ladowanie', 'energia', 'kwh', 'prąd', 'prad'],
}

FUEL_SELLER_KEYWORDS = [
    'stacja', 'paliw', 'orlen', 'bp ', 'shell', 'circle', 'lotos', 'moya',
    'amic', 'total', 'tankuj', 'fuel', 'benzin', 'station', 'petrol',
]

PLATE_PATTERN = re.compile(r'\b([A-Z]{2,3}[\s\-]?[A-Z0-9]{4,5})\b')


def validate_fuel_invoice(invoice_data, items=None):
    """
    Sprawdź fakturę paliwową pod kątem pojazdów użytkownika.
    Zwraca dict z wynikami walidacji:
    {
        'is_fuel_invoice': bool,
        'warnings': [{'type': str, 'message': str}],
        'detected_plates': [str],
        'detected_fuel_types': [str],
        'matched_vehicle': dict or None,
    }
    """
    result = {
        'is_fuel_invoice': False,
        'warnings': [],
        'detected_plates': [],
        'detected_fuel_types': [],
        'matched_vehicle': None,
    }

    all_text = _collect_text(invoice_data, items)

    if not _is_fuel_invoice(all_text, invoice_data):
        return result

    result['is_fuel_invoice'] = True
    vehicles = db.get_vehicles()

    if not vehicles:
        return result

    detected_plates = _find_plates_in_text(all_text)
    result['detected_plates'] = detected_plates

    detected_fuels = _detect_fuel_types(all_text)
    result['detected_fuel_types'] = detected_fuels

    known_plates = {v['plate'].replace(' ', '').upper(): v for v in vehicles}
    known_fuel_types = {v['fuel_type'].lower() for v in vehicles}

    if detected_plates:
        for plate in detected_plates:
            normalized = plate.replace(' ', '').replace('-', '').upper()
            matched = None
            for kp, vehicle in known_plates.items():
                if normalized == kp.replace('-', '') or normalized in kp.replace('-', '') or kp.replace('-', '') in normalized:
                    matched = vehicle
                    break

            if matched:
                result['matched_vehicle'] = matched
                if detected_fuels:
                    vehicle_fuel = matched['fuel_type'].lower()
                    if not _fuels_compatible(vehicle_fuel, detected_fuels):
                        result['warnings'].append({
                            'type': 'wrong_fuel',
                            'message': f"Niezgodność paliwa! Pojazd {matched['plate']} ({matched['brand']} {matched['model']}) "
                                       f"jeździ na {_fuel_label(vehicle_fuel)}, a na fakturze: {', '.join(detected_fuels)}"
                        })
            else:
                result['warnings'].append({
                    'type': 'unknown_plate',
                    'message': f"Tablica rejestracyjna {plate} nie pasuje do żadnego pojazdu w bazie!"
                })
    else:
        if detected_fuels and not _any_vehicle_uses_fuel(vehicles, detected_fuels):
            result['warnings'].append({
                'type': 'no_vehicle_for_fuel',
                'message': f"Faktura za {', '.join(detected_fuels)}, ale nie masz pojazdu na ten rodzaj paliwa!"
            })

    return result


def _collect_text(invoice_data, items):
    parts = [
        invoice_data.get('seller_name', ''),
        invoice_data.get('buyer_name', ''),
        invoice_data.get('invoice_number', ''),
        invoice_data.get('notes', ''),
    ]
    if items:
        for item in items:
            if isinstance(item, dict):
                parts.append(item.get('name', ''))
            else:
                parts.append(str(item))
    return ' '.join(parts).upper()


def _is_fuel_invoice(all_text, invoice_data):
    text_lower = all_text.lower()
    seller = (invoice_data.get('seller_name', '') or '').lower()

    for keyword in FUEL_SELLER_KEYWORDS:
        if keyword in seller:
            return True

    for fuel_type, keywords in FUEL_KEYWORDS.items():
        for kw in keywords:
            if kw in text_lower:
                return True

    return False


def _find_plates_in_text(text):
    text_clean = text.upper().replace('-', ' ')
    matches = PLATE_PATTERN.findall(text_clean)
    plates = []
    for m in matches:
        plate = m.replace(' ', '').replace('-', '')
        if 5 <= len(plate) <= 8 and not plate.isdigit():
            plates.append(plate)
    return list(set(plates))


def _detect_fuel_types(all_text):
    text_lower = all_text.lower()
    found = set()
    for fuel_type, keywords in FUEL_KEYWORDS.items():
        for kw in keywords:
            if kw in text_lower:
                found.add(fuel_type)
                break
    return list(found)


def _fuels_compatible(vehicle_fuel, detected_fuels):
    for df in detected_fuels:
        if df == vehicle_fuel:
            return True
        if vehicle_fuel == 'benzyna+lpg' and df in ('benzyna', 'lpg'):
            return True
    return False


def _any_vehicle_uses_fuel(vehicles, detected_fuels):
    for v in vehicles:
        vf = v['fuel_type'].lower()
        for df in detected_fuels:
            if df == vf or (vf == 'benzyna+lpg' and df in ('benzyna', 'lpg')):
                return True
    return False


def _fuel_label(fuel_type):
    labels = {
        'diesel': 'Diesel (ON)',
        'benzyna': 'Benzyna',
        'lpg': 'LPG',
        'cng': 'CNG',
        'elektryczny': 'Elektryczny',
        'benzyna+lpg': 'Benzyna + LPG',
    }
    return labels.get(fuel_type, fuel_type)
