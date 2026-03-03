from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class InvoiceItem:
    name: str = ''
    quantity: float = 0.0
    unit: str = 'szt.'
    unit_price: float = 0.0
    net_value: float = 0.0
    vat_rate: str = ''

@dataclass
class Invoice:
    id: Optional[int] = None
    ksef_number: str = ''
    invoice_number: str = ''
    seller_name: str = ''
    seller_nip: str = ''
    buyer_name: str = ''
    buyer_nip: str = ''
    issue_date: str = ''
    net_amount: float = 0.0
    vat_amount: float = 0.0
    gross_amount: float = 0.0
    invoice_type: str = 'purchase'
    status: str = 'new'
    xml_content: str = ''
    fetched_at: str = ''
    printed: bool = False
    notes: str = ''
    items: List[InvoiceItem] = field(default_factory=list)
