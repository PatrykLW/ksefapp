import os
import sqlite3
from contextlib import contextmanager

DB_NAME = 'ksef_panel.db'

def _get_db_path():
    base = os.environ.get('KSEFAPP_BASE_PATH', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, DB_NAME)

def init_db():
    with get_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS invoices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ksef_number TEXT UNIQUE NOT NULL,
                invoice_number TEXT,
                seller_name TEXT,
                seller_nip TEXT,
                buyer_name TEXT,
                buyer_nip TEXT,
                issue_date TEXT,
                net_amount REAL DEFAULT 0,
                vat_amount REAL DEFAULT 0,
                gross_amount REAL DEFAULT 0,
                invoice_type TEXT DEFAULT 'purchase',
                status TEXT DEFAULT 'new',
                xml_content TEXT,
                fetched_at TEXT,
                printed INTEGER DEFAULT 0,
                notes TEXT DEFAULT ''
            );
            CREATE TABLE IF NOT EXISTS sync_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sync_date TEXT NOT NULL,
                invoices_fetched INTEGER DEFAULT 0,
                status TEXT DEFAULT 'success',
                message TEXT DEFAULT ''
            );
        """)

@contextmanager
def get_connection():
    conn = sqlite3.connect(_get_db_path())
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def insert_invoice(data):
    with get_connection() as conn:
        conn.execute("""
            INSERT OR IGNORE INTO invoices
            (ksef_number, invoice_number, seller_name, seller_nip, buyer_name, buyer_nip,
             issue_date, net_amount, vat_amount, gross_amount, invoice_type, xml_content, fetched_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
        """, (
            data.get('ksef_number'), data.get('invoice_number'),
            data.get('seller_name'), data.get('seller_nip'),
            data.get('buyer_name'), data.get('buyer_nip'),
            data.get('issue_date'),
            data.get('net_amount', 0), data.get('vat_amount', 0), data.get('gross_amount', 0),
            data.get('invoice_type', 'purchase'),
            data.get('xml_content', '')
        ))

def get_invoices(filters=None):
    query = "SELECT * FROM invoices WHERE 1=1"
    params = []
    if filters:
        if filters.get('status'):
            query += " AND status = ?"
            params.append(filters['status'])
        if filters.get('invoice_type'):
            query += " AND invoice_type = ?"
            params.append(filters['invoice_type'])
        if filters.get('date_from'):
            query += " AND issue_date >= ?"
            params.append(filters['date_from'])
        if filters.get('date_to'):
            query += " AND issue_date <= ?"
            params.append(filters['date_to'])
        if filters.get('search'):
            query += " AND (seller_name LIKE ? OR buyer_name LIKE ? OR invoice_number LIKE ? OR ksef_number LIKE ?)"
            s = f"%{filters['search']}%"
            params.extend([s, s, s, s])
    query += " ORDER BY issue_date DESC"
    if filters and filters.get('limit'):
        query += f" LIMIT {int(filters['limit'])}"
    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()
    return [dict(r) for r in rows]

def get_invoice_by_id(invoice_id):
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM invoices WHERE id = ?", (invoice_id,)).fetchone()
    return dict(row) if row else None

def update_invoice_status(invoice_id, status, notes=''):
    with get_connection() as conn:
        conn.execute(
            "UPDATE invoices SET status = ?, notes = ? WHERE id = ?",
            (status, notes, invoice_id)
        )

def mark_invoice_printed(invoice_id):
    with get_connection() as conn:
        conn.execute("UPDATE invoices SET printed = 1 WHERE id = ?", (invoice_id,))

def get_stats(month=None, year=None):
    date_filter = ""
    params = []
    if month and year:
        date_filter = "AND strftime('%m', issue_date) = ? AND strftime('%Y', issue_date) = ?"
        params = [f"{int(month):02d}", str(year)]

    with get_connection() as conn:
        sales = conn.execute(f"""
            SELECT COUNT(*) as cnt, COALESCE(SUM(net_amount),0) as net,
                   COALESCE(SUM(vat_amount),0) as vat, COALESCE(SUM(gross_amount),0) as gross
            FROM invoices WHERE invoice_type='sales' {date_filter}
        """, params).fetchone()

        purchases = conn.execute(f"""
            SELECT COUNT(*) as cnt, COALESCE(SUM(net_amount),0) as net,
                   COALESCE(SUM(vat_amount),0) as vat, COALESCE(SUM(gross_amount),0) as gross
            FROM invoices WHERE invoice_type='purchase' {date_filter}
        """, params).fetchone()

        new_count = conn.execute(
            f"SELECT COUNT(*) as cnt FROM invoices WHERE status='new' {date_filter}", params
        ).fetchone()

        unprinted = conn.execute(
            f"SELECT COUNT(*) as cnt FROM invoices WHERE printed=0 {date_filter}", params
        ).fetchone()

    return {
        'sales': dict(sales),
        'purchases': dict(purchases),
        'new_count': new_count['cnt'],
        'unprinted_count': unprinted['cnt'],
    }

def get_monthly_stats(year):
    results = []
    with get_connection() as conn:
        for m in range(1, 13):
            month_str = f"{m:02d}"
            sales = conn.execute("""
                SELECT COALESCE(SUM(net_amount),0) as net, COALESCE(SUM(gross_amount),0) as gross
                FROM invoices
                WHERE invoice_type='sales'
                AND strftime('%m', issue_date) = ? AND strftime('%Y', issue_date) = ?
            """, (month_str, str(year))).fetchone()
            purchases = conn.execute("""
                SELECT COALESCE(SUM(net_amount),0) as net, COALESCE(SUM(gross_amount),0) as gross
                FROM invoices
                WHERE invoice_type='purchase'
                AND strftime('%m', issue_date) = ? AND strftime('%Y', issue_date) = ?
            """, (month_str, str(year))).fetchone()
            results.append({
                'month': m,
                'sales_net': sales['net'],
                'sales_gross': sales['gross'],
                'purchases_net': purchases['net'],
                'purchases_gross': purchases['gross'],
            })
    return results

def get_top_contractors(limit=10, invoice_type=None):
    type_filter = ""
    params = []
    if invoice_type:
        type_filter = "AND invoice_type = ?"
        params.append(invoice_type)

    with get_connection() as conn:
        if invoice_type == 'sales':
            col_name, col_nip = 'buyer_name', 'buyer_nip'
        else:
            col_name, col_nip = 'seller_name', 'seller_nip'

        rows = conn.execute(f"""
            SELECT {col_name} as name, {col_nip} as nip,
                   COUNT(*) as cnt, SUM(gross_amount) as total
            FROM invoices WHERE 1=1 {type_filter}
            GROUP BY {col_nip}
            ORDER BY total DESC LIMIT ?
        """, params + [limit]).fetchall()
    return [dict(r) for r in rows]

def log_sync(count, status='success', message=''):
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO sync_history (sync_date, invoices_fetched, status, message) VALUES (datetime('now'), ?, ?, ?)",
            (count, status, message)
        )
