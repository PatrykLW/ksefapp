import os
import tempfile

def get_printers():
    """Return list of available Windows printers."""
    try:
        import win32print
        printers = []
        default = win32print.GetDefaultPrinter()
        for flags, desc, name, comment in win32print.EnumPrinters(
            win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
        ):
            printers.append({
                'name': name,
                'is_default': name == default,
            })
        return printers
    except ImportError:
        return [{'name': 'Brak modułu win32print (zainstaluj pywin32)', 'is_default': True}]
    except Exception as e:
        return [{'name': f'Błąd: {e}', 'is_default': True}]

def get_default_printer():
    try:
        import win32print
        return win32print.GetDefaultPrinter()
    except Exception:
        return None

def print_html(html_content, printer_name=None):
    """Print HTML content to specified printer using temp file + Windows ShellExecute."""
    tmp = tempfile.NamedTemporaryFile(suffix='.html', delete=False, mode='w', encoding='utf-8')
    tmp.write(html_content)
    tmp.close()

    try:
        import win32api
        import win32print
        if printer_name:
            win32print.SetDefaultPrinter(printer_name)
        win32api.ShellExecute(0, "print", tmp.name, None, ".", 0)
        return True, "Wysłano do drukarki"
    except ImportError:
        os.startfile(tmp.name, 'print')
        return True, "Wysłano do drukarki (tryb awaryjny)"
    except Exception as e:
        return False, f"Błąd drukowania: {e}"
    finally:
        try:
            os.unlink(tmp.name)
        except OSError:
            pass

def print_invoices_batch(html_contents, printer_name=None):
    """Print multiple invoices. Returns (success_count, error_count, messages)."""
    success = 0
    errors = 0
    messages = []
    for i, html in enumerate(html_contents):
        ok, msg = print_html(html, printer_name)
        if ok:
            success += 1
        else:
            errors += 1
            messages.append(f"Faktura {i+1}: {msg}")
    return success, errors, messages
