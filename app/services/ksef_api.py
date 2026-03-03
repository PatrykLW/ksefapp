import requests
import base64
import json
import logging
from datetime import datetime, timedelta

logger = logging.getLogger('ksef_api')

ENVIRONMENTS = {
    'prod': 'https://ksef.mf.gov.pl',
    'demo': 'https://ksef-demo.mf.gov.pl',
    'test': 'https://ksef-test.mf.gov.pl',
}


class KSeFError(Exception):
    def __init__(self, message, status_code=None, details=None):
        super().__init__(message)
        self.status_code = status_code
        self.details = details


class KSeFAPI:
    def __init__(self, token, nip, environment='prod'):
        self.token = token
        self.nip = nip
        self.base_url = ENVIRONMENTS.get(environment, ENVIRONMENTS['prod'])
        self.session_token = None
        self.session_expiry = None
        self._session = requests.Session()
        self._session.headers.update({
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        })

    def _url(self, path):
        return f"{self.base_url}{path}"

    def _handle_response(self, resp, context=""):
        if resp.status_code >= 400:
            try:
                body = resp.json()
            except Exception:
                body = resp.text[:500] if resp.text else f"HTTP {resp.status_code}"
            raise KSeFError(
                f"Błąd KSeF API ({context}): HTTP {resp.status_code}",
                status_code=resp.status_code,
                details=body
            )
        return resp

    def _parse_json(self, resp, context=""):
        """Safely parse JSON from response, with clear error on HTML/other responses."""
        content_type = resp.headers.get('Content-Type', '')
        if 'json' not in content_type and 'octet-stream' not in content_type:
            raise KSeFError(
                f"KSeF zwrócił nieoczekiwany format ({context}): {content_type}",
                status_code=resp.status_code,
                details=resp.text[:300] if resp.text else ''
            )
        try:
            return resp.json()
        except Exception as e:
            raise KSeFError(
                f"Błąd parsowania odpowiedzi KSeF ({context}): {e}",
                status_code=resp.status_code,
                details=resp.text[:300] if resp.text else ''
            )

    # --- Authentication ---

    def authorize(self):
        """Full authorization flow: challenge -> init token -> get session."""
        challenge_data = self._get_challenge()
        self._init_token_session(challenge_data)
        return True

    def _get_challenge(self):
        """Step 1: Get authorization challenge."""
        resp = self._session.post(
            self._url('/api/online/Session/AuthorisationChallenge'),
            json={
                "contextIdentifier": {
                    "type": "onip",
                    "identifier": self.nip
                }
            }
        )
        self._handle_response(resp, "AuthorisationChallenge")
        return self._parse_json(resp, "AuthorisationChallenge")

    def _init_token_session(self, challenge_data):
        """Step 2: Initialize session with token."""
        timestamp = challenge_data.get('timestamp', '')
        challenge = challenge_data.get('challenge', '')

        init_request = self._build_init_token_xml(timestamp, challenge)

        resp = self._session.post(
            self._url('/api/online/Session/InitToken'),
            data=init_request,
            headers={
                'Content-Type': 'application/octet-stream',
                'Accept': 'application/json',
            }
        )
        self._handle_response(resp, "InitToken")
        data = self._parse_json(resp, "InitToken")

        session_token = data.get('sessionToken', {})
        self.session_token = session_token.get('token', '')
        self.session_expiry = datetime.now() + timedelta(minutes=30)

        self._session.headers['SessionToken'] = self.session_token
        logger.info("Sesja KSeF zainicjalizowana pomyślnie")

    def _build_init_token_xml(self, timestamp, challenge):
        """Build InitSessionTokenRequest XML with encrypted token."""
        token_b64 = base64.b64encode(self.token.encode('utf-8')).decode('utf-8')

        xml = f"""<?xml version="1.0" encoding="utf-8"?>
<ns3:InitSessionTokenRequest
    xmlns="http://ksef.mf.gov.pl/schema/gtw/svc/online/types/2021/10/01/0001"
    xmlns:ns2="http://ksef.mf.gov.pl/schema/gtw/svc/types/2021/10/01/0001"
    xmlns:ns3="http://ksef.mf.gov.pl/schema/gtw/svc/online/auth/request/2021/10/01/0001">
    <ns3:Context>
        <Challenge>{challenge}</Challenge>
        <Identifier xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                    xsi:type="ns2:SubjectIdentifierByCompanyType">
            <ns2:Identifier>{self.nip}</ns2:Identifier>
        </Identifier>
        <DocumentType>
            <ns2:Service>KSeF</ns2:Service>
            <ns2:FormCode>
                <ns2:SystemCode>FA (2)</ns2:SystemCode>
                <ns2:SchemaVersion>1-0E</ns2:SchemaVersion>
                <ns2:TargetNamespace>http://crd.gov.pl/wzor/2023/06/29/12648/</ns2:TargetNamespace>
                <ns2:Value>FA</ns2:Value>
            </ns2:FormCode>
        </DocumentType>
        <Token>{token_b64}</Token>
    </ns3:Context>
</ns3:InitSessionTokenRequest>"""
        return xml.encode('utf-8')

    def _ensure_session(self):
        """Make sure we have a valid session, re-authorize if needed."""
        if not self.session_token or (self.session_expiry and datetime.now() >= self.session_expiry):
            self.authorize()

    # --- Invoice Operations ---

    def query_invoices(self, date_from, date_to, subject_type='subject2', page_size=100, page_offset=0):
        """
        Query invoices from KSeF.
        subject_type: 'subject1' = sprzedaż (my jako sprzedawca), 'subject2' = zakup (my jako nabywca)
        """
        self._ensure_session()

        payload = {
            "queryCriteria": {
                "subjectType": subject_type,
                "type": "incremental",
                "acquisitionTimestampThresholdFrom": date_from,
                "acquisitionTimestampThresholdTo": date_to,
            },
            "pageSize": page_size,
            "pageOffset": page_offset
        }

        resp = self._session.post(
            self._url('/api/online/Query/Invoice/Sync'),
            json=payload
        )
        self._handle_response(resp, "Query/Invoice/Sync")
        return self._parse_json(resp, "Query/Invoice/Sync")

    def download_invoice(self, ksef_reference_number):
        """Download a single invoice by its KSeF reference number."""
        self._ensure_session()

        resp = self._session.get(
            self._url(f'/api/online/Invoice/Get/{ksef_reference_number}'),
            headers={**self._session.headers, 'Accept': 'application/octet-stream'}
        )
        self._handle_response(resp, f"Invoice/Get/{ksef_reference_number}")
        return resp.content.decode('utf-8')

    def fetch_all_invoices(self, date_from, date_to):
        """Fetch all invoices (both sales and purchases) for a date range."""
        all_invoices = []

        for subject_type, inv_type in [('subject1', 'sales'), ('subject2', 'purchase')]:
            page = 0
            while True:
                try:
                    result = self.query_invoices(
                        date_from=date_from,
                        date_to=date_to,
                        subject_type=subject_type,
                        page_offset=page
                    )
                except KSeFError as e:
                    logger.error(f"Błąd pobierania faktur ({inv_type}): {e}")
                    break

                invoices = result.get('invoiceHeaderList', [])
                if not invoices:
                    break

                for inv in invoices:
                    inv['_invoice_type'] = inv_type
                all_invoices.extend(invoices)

                if len(invoices) < 100:
                    break
                page += 1

        return all_invoices

    def close_session(self):
        """Close the KSeF session."""
        if not self.session_token:
            return
        try:
            resp = self._session.get(
                self._url('/api/online/Session/Terminate')
            )
            self._handle_response(resp, "Session/Terminate")
        except Exception as e:
            logger.warning(f"Błąd zamykania sesji: {e}")
        finally:
            self.session_token = None
            self.session_expiry = None

    def test_connection(self):
        """Test if we can connect and authorize with KSeF."""
        try:
            self.authorize()
            self.close_session()
            return True, "Połączenie z KSeF działa poprawnie!"
        except KSeFError as e:
            return False, f"Błąd: {e}\n{e.details if e.details else ''}"
        except requests.ConnectionError:
            return False, "Brak połączenia z serwerem KSeF. Sprawdź internet."
        except Exception as e:
            return False, f"Nieoczekiwany błąd: {e}"
