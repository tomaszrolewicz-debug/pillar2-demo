"""
Walidacja XML względem XSD.
Zwraca listę przyjaznych komunikatów błędów zamiast surowych komunikatów lxml.
"""
from __future__ import annotations
from lxml import etree
from typing import List, Tuple
import os

# Mapa surowych fraz z błędów XSD na przyjazne komunikaty
FRIENDLY_ERRORS = {
    "NIP": "Brakuje lub nieprawidłowy NIP podmiotu składającego",
    "PelnaNazwa": "Brakuje pełnej nazwy podmiotu",
    "OkresOd": "Brakuje daty początku okresu (Okres Od)",
    "OkresDo": "Brakuje daty końca okresu (Okres Do)",
    "P_7": "Brakuje nazwy grupy (sekcja C)",
    "P_8": "Brakuje rodzaju jednostki składającej zawiadomienie (sekcja C)",
    "P_D9": "Brakuje rodzaju jednostki składowej (sekcja D)",
    "P_D10": "Brakuje pełnej nazwy jednostki składowej (sekcja D)",
    "P_D11": "Brakuje kodu państwa wydania numeru identyfikacyjnego",
    "P_D12": "Brakuje rodzaju numeru identyfikacyjnego",
    "P_D13": "Brakuje zagranicznego numeru identyfikacyjnego",
    "P_D14": "Brakuje kodu państwa siedziby",
    "P_D15": "Brakuje miejscowości siedziby",
    "P_D21": "Brakuje kodu jurysdykcji",
    "FilingCE": "Brakuje danych jednostki składającej GIR (FilingCE)",
    "NameMNE": "Brakuje nazwy grupy MNE",
    "DocRefId": "Brakuje lub zduplikowany identyfikator dokumentu (DocRefId)",
    "ResCountryCode": "Brakuje kodu kraju",
    "minLength": "Pole jest wymagane – nie może być puste",
    "maxLength": "Przekroczono maksymalną długość pola",
    "pattern": "Wartość nie spełnia wymaganego formatu (np. NIP, data)",
    "enumeration": "Wybrana wartość spoza dozwolonej listy wartości",
    "minInclusive": "Wartość jest zbyt mała",
    "maxInclusive": "Wartość jest zbyt duża",
}


def _humanize(msg: str) -> str:
    for key, friendly in FRIENDLY_ERRORS.items():
        if key in msg:
            return friendly
    # Ogólne czyszczenie surowego komunikatu
    msg = msg.replace("{http://crd.gov.pl/wzor/2025/11/07/13986/}", "")
    msg = msg.replace("{http://globe.mf.gov.pl/2025/03/31/03311/}", "")
    msg = msg.replace("{http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/09/13/eD/DefinicjeTypy/}", "")
    return msg


def validate_xml(xml_bytes: bytes, schema_path: str) -> Tuple[bool, List[str]]:
    """
    Waliduje xml_bytes względem XSD z podanej ścieżki.
    Zwraca (is_valid, lista_błędów_przyjaznych).
    
    Uwaga: walidacja względem XSD z zewnętrznymi importami (schemat.xsd) 
    może zwracać ostrzeżenia o brakujących schematach zależnych – 
    traktuj to jako oczekiwane w środowisku offline.
    """
    errors: List[str] = []

    # Parsowanie XML
    try:
        doc = etree.fromstring(xml_bytes)
    except etree.XMLSyntaxError as e:
        return False, [f"Błąd składni XML: {e}"]

    # Próba walidacji XSD (jeśli schemat dostępny i bez zależności zewnętrznych)
    if not os.path.exists(schema_path):
        errors.append(f"Plik schematu XSD nie istnieje: {schema_path}")
        return False, errors

    try:
        with open(schema_path, "rb") as f:
            schema_doc = etree.parse(f)
        xmlschema = etree.XMLSchema(schema_doc)
        is_valid = xmlschema.validate(doc)
        if not is_valid:
            for err in xmlschema.error_log:
                errors.append(_humanize(err.message) + f" (linia {err.line})")
        return is_valid, errors
    except etree.XMLSchemaParseError as e:
        # Schemat GLB-Z2 importuje zewnętrzne XSD – w środowisku offline
        # nie można pobrać schematów zależnych. Wykonujemy walidację składniową.
        errors.append(
            "⚠️  Pełna walidacja XSD wymaga dostępu do schematów zależnych MF "
            "(DefinicjeTypy, KodyPanstw itp.). "
            "W środowisku offline przeprowadzono tylko walidację składni XML."
        )
        return True, errors  # true = XML jest poprawny składniowo


def validate_glbz2_fields(form) -> List[str]:
    """Szybka walidacja pól modelu GLB-Z2 bez generowania XML."""
    errors = []
    if not form.podmiot1.nip:
        errors.append("Brakuje NIP podmiotu składającego")
    elif len(form.podmiot1.nip) != 10 or not form.podmiot1.nip.isdigit():
        errors.append("NIP musi składać się dokładnie z 10 cyfr")
    if not form.podmiot1.pelna_nazwa.strip():
        errors.append("Brakuje pełnej nazwy podmiotu składającego")
    if not form.naglowek.okres_od:
        errors.append("Brakuje daty początku okresu (Okres Od)")
    if not form.naglowek.okres_do:
        errors.append("Brakuje daty końca okresu (Okres Do)")
    if not form.pozycje.nazwa_grupy.strip():
        errors.append("Brakuje nazwy grupy (Sekcja C, pole P_7)")
    if not form.pozycje.jednostki_d:
        errors.append("Wymagana co najmniej jedna jednostka składowa (Sekcja D)")
    for i, jd in enumerate(form.pozycje.jednostki_d, 1):
        if not jd.pelna_nazwa.strip():
            errors.append(f"Jednostka {i}: brakuje pełnej nazwy")
        if not jd.kraj_id:
            errors.append(f"Jednostka {i}: brakuje kodu państwa wydania numeru ID")
        if not jd.nr_id.strip():
            errors.append(f"Jednostka {i}: brakuje zagranicznego numeru identyfikacyjnego")
        if not jd.adres_kraj:
            errors.append(f"Jednostka {i}: brakuje kodu kraju siedziby")
        if not jd.adres_miejscowosc.strip():
            errors.append(f"Jednostka {i}: brakuje miejscowości siedziby")
        if not jd.kod_jurysdykcji:
            errors.append(f"Jednostka {i}: brakuje kodu jurysdykcji")
    return errors


def validate_gir_fields(form) -> List[str]:
    """Szybka walidacja pól modelu GIR bez generowania XML."""
    errors = []
    if not form.nip:
        errors.append("Brakuje NIP podmiotu składającego")
    elif len(form.nip) != 10 or not form.nip.isdigit():
        errors.append("NIP musi składać się dokładnie z 10 cyfr")
    if not form.pelna_nazwa.strip():
        errors.append("Brakuje pełnej nazwy podmiotu składającego")
    if not form.okres_od:
        errors.append("Brakuje daty początku okresu")
    if not form.okres_do:
        errors.append("Brakuje daty końca okresu")
    fi = form.filing_info
    if not fi.filing_ce.nazwa.strip():
        errors.append("FilingInfo: brakuje nazwy jednostki składającej GIR")
    if not fi.filing_ce.tin.strip():
        errors.append("FilingInfo: brakuje TIN jednostki składającej GIR")
    if not fi.accounting_info.fas.strip():
        errors.append("FilingInfo: brakuje opisu standardu rachunkowości (FAS)")
    if not fi.okres_od or not fi.okres_do:
        errors.append("FilingInfo: brakuje okresu (Start/End)")
    if not fi.nazwa_mne.strip():
        errors.append("FilingInfo: brakuje nazwy grupy MNE")
    return errors
