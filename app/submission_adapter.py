"""
submission_adapter.py
─────────────────────
Interfejs do wysyłki formularzy do systemu MF / e-Deklaracje / e-US.

STAN MVP: Metoda submit() zwraca komunikat placeholder.
Przed uruchomieniem produkcyjnym należy:
  1. Potwierdzić endpoint API MF (e-Deklaracje / bramka GIR).
  2. Skonfigurować certyfikat kwalifikowanego podpisu elektronicznego.
  3. Zaimplementować metodę sign_or_prepare_for_signature() z prawdziwym podpisem.
  4. Ustawić ENABLE_SUBMISSION = True w config.py.
"""
from __future__ import annotations
from typing import Tuple, Optional
from lxml import etree
import hashlib


class SubmissionAdapter:

    def validate_before_submission(self, xml_bytes: bytes) -> Tuple[bool, str]:
        """
        Dodatkowe sprawdzenia XML przed wysyłką.
        Zwraca (ok, komunikat).
        """
        try:
            doc = etree.fromstring(xml_bytes)
        except etree.XMLSyntaxError as e:
            return False, f"XML zawiera błędy składni: {e}"

        # Sprawdź, czy XML nie jest pusty
        if doc is None:
            return False, "Pusty dokument XML"

        # Oblicz hash do logu (bez logowania danych wrażliwych)
        sha = hashlib.sha256(xml_bytes).hexdigest()[:16]
        return True, f"Dokument gotowy do podpisu (SHA256-prefix: {sha})"

    def sign_or_prepare_for_signature(self, xml_bytes: bytes) -> Tuple[bytes, str]:
        """
        Placeholder dla podpisu elektronicznego.
        
        W wersji produkcyjnej należy zaimplementować:
        - podpis kwalifikowany XAdES / PKCS#7,
        - lub przygotowanie paczki do podpisania zewnętrznym narzędziem.
        
        Zwraca (xml_lub_paczka, komunikat).
        """
        msg = (
            "⚠️  PODPIS NIE JEST ZAIMPLEMENTOWANY W WERSJI MVP.\n"
            "Przed wysyłką dokument należy podpisać kwalifikowanym podpisem "
            "elektronicznym zgodnie z wymogami MF.\n"
            "Skonfiguruj ścieżkę certyfikatu w pliku config.py (CERT_PATH, CERT_KEY_PATH)."
        )
        return xml_bytes, msg

    def submit(
        self,
        xml_or_signed: bytes,
        form_type: str = "GLB-Z2",
        reference_id: Optional[str] = None,
    ) -> Tuple[bool, str]:
        """
        Wysyłka do systemu MF.

        W wersji MVP zawsze zwraca instrukcję manualną.
        Gdy ENABLE_SUBMISSION=True i SUBMISSION_ENDPOINT skonfigurowany,
        metoda wykona faktyczne żądanie HTTP.
        """
        from app.config import ENABLE_SUBMISSION, SUBMISSION_ENDPOINT

        if not ENABLE_SUBMISSION or not SUBMISSION_ENDPOINT:
            return False, (
                "🔒 WYSYŁKA AUTOMATYCZNA NIE JEST SKONFIGUROWANA.\n\n"
                "Instrukcja złożenia formularza ręcznie:\n"
                f"  • Formularz: {form_type}\n"
                "  • Pobierz wygenerowany plik XML z sekcji 'Pobierz XML'\n"
                "  • Podpisz kwalifikowanym podpisem elektronicznym\n"
                "  • Złóż przez portal e-Deklaracje MF: https://e-deklaracje.mf.gov.pl\n"
                "    lub właściwy kanał wskazany przez MF dla formularzy GloBE/Pillar Two\n\n"
                "Aby aktywować wysyłkę automatyczną, skonfiguruj:\n"
                "  SUBMISSION_ENDPOINT w config.py lub zmiennej środowiskowej MF_SUBMISSION_ENDPOINT\n"
                "  ENABLE_SUBMISSION = True (po weryfikacji z administratorem)"
            )

        # ── Właściwa wysyłka (do zaimplementowania) ─────────────────────────
        try:
            import urllib.request
            req = urllib.request.Request(
                SUBMISSION_ENDPOINT,
                data=xml_or_signed,
                headers={"Content-Type": "application/xml"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                body = resp.read().decode("utf-8", errors="replace")
                return True, f"Wysłano pomyślnie. Odpowiedź serwera:\n{body[:500]}"
        except Exception as e:
            return False, f"Błąd wysyłki: {e}"

    def get_status(self, reference_id: str) -> Tuple[bool, str]:
        """
        Sprawdzenie statusu złożonego dokumentu.
        Placeholder – wymaga implementacji zgodnie z API MF.
        """
        return False, (
            f"Sprawdzenie statusu (ref: {reference_id}) wymaga konfiguracji "
            "endpointu statusowego MF. Nie jest dostępny w wersji MVP."
        )


# Singleton
adapter = SubmissionAdapter()
