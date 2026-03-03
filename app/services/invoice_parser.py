from lxml import etree

FA3_NS = 'http://crd.gov.pl/wzor/2023/06/29/12648/'
FA2_NS = 'http://crd.gov.pl/wzor/2021/11/29/11089/'

NAMESPACES_MAP = {
    'fa3': FA3_NS,
    'fa2': FA2_NS,
}

def parse_invoice_xml(xml_string):
    """Parse a KSeF invoice XML (FA2 or FA3) and extract key data."""
    try:
        root = etree.fromstring(xml_string.encode('utf-8') if isinstance(xml_string, str) else xml_string)
    except etree.XMLSyntaxError:
        return None

    ns = _detect_namespace(root)
    if not ns:
        return _parse_generic(root)

    nsmap = {'fa': ns}

    data = {
        'invoice_number': _text(root, './/fa:P_2', nsmap) or _text(root, './/fa:FaNumer', nsmap) or '',
        'issue_date': _text(root, './/fa:P_1', nsmap) or _text(root, './/fa:DataWystawienia', nsmap) or '',
        'seller_name': _text(root, './/fa:Podmiot1//fa:Nazwa', nsmap)
                        or _text(root, './/fa:Podmiot1//fa:PelnaNazwa', nsmap) or '',
        'seller_nip': _text(root, './/fa:Podmiot1//fa:NIP', nsmap) or '',
        'buyer_name': _text(root, './/fa:Podmiot2//fa:Nazwa', nsmap)
                       or _text(root, './/fa:Podmiot2//fa:PelnaNazwa', nsmap) or '',
        'buyer_nip': _text(root, './/fa:Podmiot2//fa:NIP', nsmap) or '',
        'net_amount': 0.0,
        'vat_amount': 0.0,
        'gross_amount': 0.0,
        'items': [],
    }

    net = _text(root, './/fa:P_13_1', nsmap) or _text(root, './/fa:P_15', nsmap)
    vat = _text(root, './/fa:P_13_2', nsmap) or _text(root, './/fa:P_16', nsmap)
    gross = _text(root, './/fa:P_15', nsmap) or _text(root, './/fa:P_17', nsmap)

    data['net_amount'] = _to_float(net)
    data['vat_amount'] = _to_float(vat)
    data['gross_amount'] = _to_float(gross)
    if data['gross_amount'] == 0 and data['net_amount'] > 0:
        data['gross_amount'] = data['net_amount'] + data['vat_amount']

    for item in root.findall('.//fa:FaWiersz', nsmap):
        line = {
            'name': _text(item, 'fa:P_7', nsmap) or '',
            'quantity': _to_float(_text(item, 'fa:P_8B', nsmap)),
            'unit': _text(item, 'fa:P_8A', nsmap) or 'szt.',
            'unit_price': _to_float(_text(item, 'fa:P_9A', nsmap) or _text(item, 'fa:P_9B', nsmap)),
            'net_value': _to_float(_text(item, 'fa:P_11', nsmap)),
            'vat_rate': _text(item, 'fa:P_12', nsmap) or '',
        }
        data['items'].append(line)

    return data

def _detect_namespace(root):
    tag = root.tag
    if FA3_NS in tag:
        return FA3_NS
    if FA2_NS in tag:
        return FA2_NS
    for ns_uri in root.nsmap.values():
        if 'crd.gov.pl/wzor' in str(ns_uri):
            return ns_uri
    return None

def _text(element, xpath, nsmap):
    found = element.find(xpath, nsmap)
    if found is not None and found.text:
        return found.text.strip()
    return None

def _to_float(val):
    if not val:
        return 0.0
    try:
        return float(val.replace(',', '.').replace(' ', ''))
    except (ValueError, AttributeError):
        return 0.0

def invoice_to_html(data):
    """Render invoice data as printable HTML."""
    items_html = ""
    for i, item in enumerate(data.get('items', []), 1):
        items_html += f"""
        <tr>
            <td style="padding:4px;border:1px solid #ccc;text-align:center">{i}</td>
            <td style="padding:4px;border:1px solid #ccc">{item['name']}</td>
            <td style="padding:4px;border:1px solid #ccc;text-align:center">{item['unit']}</td>
            <td style="padding:4px;border:1px solid #ccc;text-align:right">{item['quantity']}</td>
            <td style="padding:4px;border:1px solid #ccc;text-align:right">{item['unit_price']:.2f}</td>
            <td style="padding:4px;border:1px solid #ccc;text-align:right">{item['net_value']:.2f}</td>
            <td style="padding:4px;border:1px solid #ccc;text-align:center">{item['vat_rate']}</td>
        </tr>"""

    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Faktura {data.get('invoice_number','')}</title>
<style>body{{font-family:Arial,sans-serif;font-size:11px;margin:20px}}
h2{{margin:0 0 10px}}table{{border-collapse:collapse;width:100%}}
.header{{display:flex;justify-content:space-between;margin-bottom:20px}}
.box{{border:1px solid #ccc;padding:10px;width:45%}}
.summary{{text-align:right;margin-top:10px;font-size:13px}}</style></head>
<body>
<h2>Faktura nr {data.get('invoice_number','')}</h2>
<p>Data wystawienia: {data.get('issue_date','')}</p>
<div class="header">
<div class="box"><strong>Sprzedawca:</strong><br>{data.get('seller_name','')}<br>NIP: {data.get('seller_nip','')}</div>
<div class="box"><strong>Nabywca:</strong><br>{data.get('buyer_name','')}<br>NIP: {data.get('buyer_nip','')}</div>
</div>
<table>
<tr style="background:#f0f0f0"><th style="padding:4px;border:1px solid #ccc">Lp.</th>
<th style="padding:4px;border:1px solid #ccc">Nazwa</th>
<th style="padding:4px;border:1px solid #ccc">J.m.</th>
<th style="padding:4px;border:1px solid #ccc">Ilość</th>
<th style="padding:4px;border:1px solid #ccc">Cena netto</th>
<th style="padding:4px;border:1px solid #ccc">Wartość netto</th>
<th style="padding:4px;border:1px solid #ccc">Stawka VAT</th></tr>
{items_html}
</table>
<div class="summary">
<p>Netto: <strong>{data.get('net_amount',0):.2f} PLN</strong></p>
<p>VAT: <strong>{data.get('vat_amount',0):.2f} PLN</strong></p>
<p>Brutto: <strong>{data.get('gross_amount',0):.2f} PLN</strong></p>
</div></body></html>"""
