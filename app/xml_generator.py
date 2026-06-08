"""
Generator XML dla formularzy GLB-Z2 i GIR.
"""
from __future__ import annotations
from lxml import etree
from app.models import GLBZ2_Form, GIR_Form

# ── Namespaces ────────────────────────────────────────────────────────────────
GLBZ2_NS = "http://crd.gov.pl/wzor/2025/11/07/13986/"
ETD_NS   = "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/09/13/eD/DefinicjeTypy/"
KPIT_NS  = "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2025/11/01/eD/KodyPanstwITerytoriow/"
GIR_NS   = "http://globe.mf.gov.pl/2025/03/31/03311/"


def _sub(parent, tag, text=None, ns=None, attrib=None):
    """Tworzy element potomny z opcjonalnym tekstem i atrybutami."""
    qname = f"{{{ns}}}{tag}" if ns else tag
    el = etree.SubElement(parent, qname, attrib or {})
    if text is not None:
        el.text = str(text)
    return el


# ════════════════════════════════════════════════════════════════════════════
#  GLB-Z2
# ════════════════════════════════════════════════════════════════════════════

def generate_glbz2_xml(form: GLBZ2_Form) -> bytes:
    NS = GLBZ2_NS
    nsmap = {
        None:  NS,
        "etd": ETD_NS,
        "kpit": KPIT_NS,
    }

    root = etree.Element(f"{{{NS}}}Deklaracja", nsmap=nsmap)

    # ── Nagłówek ─────────────────────────────────────────────────────────────
    nagl = _sub(root, "Naglowek", ns=NS)

    kod_f = _sub(nagl, "KodFormularza", text="GLB-Z2", ns=NS, attrib={
        "kodSystemowy": "GLB-Z2 (1)",
        "kodPodatku": "GLB",
        "rodzajZobowiazania": "Z",
        "wersjaSchemy": "1-0E",
    })

    _sub(nagl, "WariantFormularza", text="1", ns=NS)
    _sub(nagl, "CelZlozenia", text="1", ns=NS)

    okr_od = _sub(nagl, "OkresOd", text=form.naglowek.okres_od, ns=NS, attrib={"poz": "P_3"})
    okr_do = _sub(nagl, "OkresDo", text=form.naglowek.okres_do, ns=NS, attrib={"poz": "P_4"})

    _sub(nagl, "KodUrzedu", text="0471", ns=NS)

    # ── Podmiot1 ─────────────────────────────────────────────────────────────
    p1 = _sub(root, "Podmiot1", ns=NS, attrib={"rola": "Jednostka składająca zawiadomienie"})
    id_niefiz = _sub(p1, "IdentyfikatorNiefizyczny", ns=ETD_NS)
    _sub(id_niefiz, "NIP", text=form.podmiot1.nip, ns=ETD_NS)
    _sub(id_niefiz, "PelnaNazwa", text=form.podmiot1.pelna_nazwa, ns=ETD_NS)

    # ── PozycjeSzczegolowe ───────────────────────────────────────────────────
    poz = _sub(root, "PozycjeSzczegolowe", ns=NS)

    _sub(poz, "P_7", text=form.pozycje.nazwa_grupy, ns=NS)
    _sub(poz, "P_8", text=form.pozycje.rodzaj_jednostki_skladajacej, ns=NS)

    for jd in form.pozycje.jednostki_d:
        pd = _sub(poz, "P_D", ns=NS)
        _sub(pd, "P_D9",  text=jd.rodzaj_jednostki, ns=NS)
        _sub(pd, "P_D10", text=jd.pelna_nazwa, ns=NS)
        _sub(pd, "P_D11", text=jd.kraj_id, ns=NS)
        _sub(pd, "P_D12", text=jd.rodzaj_id, ns=NS)
        _sub(pd, "P_D13", text=jd.nr_id, ns=NS)
        _sub(pd, "P_D14", text=jd.adres_kraj, ns=NS)
        _sub(pd, "P_D15", text=jd.adres_miejscowosc, ns=NS)
        if jd.adres_kod:
            _sub(pd, "P_D16", text=jd.adres_kod, ns=NS)
        if jd.adres_ulica:
            _sub(pd, "P_D17", text=jd.adres_ulica, ns=NS)
        if jd.adres_nr_budynku:
            _sub(pd, "P_D18", text=jd.adres_nr_budynku, ns=NS)
        if jd.adres_nr_lokalu:
            _sub(pd, "P_D19", text=jd.adres_nr_lokalu, ns=NS)
        if jd.adres_inne:
            _sub(pd, "P_D20", text=jd.adres_inne, ns=NS)
        _sub(pd, "P_D21", text=jd.kod_jurysdykcji, ns=NS)

    if form.pozycje.liczba_zalacznikow is not None:
        _sub(poz, "P_22", text=str(form.pozycje.liczba_zalacznikow), ns=NS)

    if form.pozycje.email:
        _sub(poz, "P_23", text=form.pozycje.email, ns=NS)
    if form.pozycje.telefon:
        _sub(poz, "P_24", text=form.pozycje.telefon, ns=NS)

    return etree.tostring(root, pretty_print=True, xml_declaration=True, encoding="UTF-8")


# ════════════════════════════════════════════════════════════════════════════
#  GIR
# ════════════════════════════════════════════════════════════════════════════

def generate_gir_xml(form: GIR_Form) -> bytes:
    NS = GIR_NS
    nsmap = {None: NS}

    root = etree.Element(f"{{{NS}}}Deklaracja", nsmap=nsmap, attrib={"version": "1.0"})

    # ── Nagłówek ─────────────────────────────────────────────────────────────
    nagl = _sub(root, "Naglowek", ns=NS)
    _sub(nagl, "KodFormularza", text="GIR-1", ns=NS, attrib={
        "kodSystemowy": "GIR-1 (1)",
        "wersjaSchemy": "1-0",
    })
    _sub(nagl, "WariantFormularza", text="1", ns=NS)
    _sub(nagl, "OkresOd", text=form.okres_od, ns=NS)
    _sub(nagl, "OkresDo", text=form.okres_do, ns=NS)

    # ── Podmiot1 ─────────────────────────────────────────────────────────────
    p1 = _sub(root, "Podmiot1", ns=NS)
    _sub(p1, "NIP", text=form.nip, ns=NS)
    _sub(p1, "PelnaNazwa", text=form.pelna_nazwa, ns=NS)

    # ── GLOBEBody ─────────────────────────────────────────────────────────────
    body = _sub(root, "GLOBEBody", ns=NS)

    # FilingInfo
    fi = _sub(body, "FilingInfo", ns=NS)
    fce = _sub(fi, "FilingCE", ns=NS)
    _sub(fce, "ResCountryCode", text=form.filing_info.filing_ce.kraj, ns=NS)
    _sub(fce, "Name", text=form.filing_info.filing_ce.nazwa, ns=NS)
    _sub(fce, "TIN", text=_tin_elem(form.filing_info.filing_ce.tin, form.filing_info.filing_ce.kraj), ns=None)
    # TIN jest złożonym typem – uproszczamy do elementu inline
    fi_fce_tin = fce.find(f"{{{NS}}}TIN")
    if fi_fce_tin is not None:
        fce.remove(fi_fce_tin)
    tin_el = _build_tin(fce, form.filing_info.filing_ce.tin, form.filing_info.filing_ce.kraj, NS)

    _sub(fce, "Role", text=form.filing_info.filing_ce.rola, ns=NS)

    acc = _sub(fi, "AccountingInfo", ns=NS)
    _sub(acc, "CFSofUPE", text=form.filing_info.accounting_info.cfs_upe, ns=NS)
    _sub(acc, "FAS", text=form.filing_info.accounting_info.fas, ns=NS)
    _sub(acc, "Currency", text=form.filing_info.accounting_info.waluta, ns=NS)

    period = _sub(fi, "Period", ns=NS)
    _sub(period, "Start", text=form.filing_info.okres_od, ns=NS)
    _sub(period, "End",   text=form.filing_info.okres_do, ns=NS)

    _sub(fi, "NameMNE", text=form.filing_info.nazwa_mne, ns=NS)
    if form.filing_info.uwagi:
        _sub(fi, "AdditionalInfo", text=form.filing_info.uwagi, ns=NS)

    # DocSpec dla FilingInfo
    ds = _sub(fi, "DocSpec", ns=NS)
    _sub(ds, "DocTypeIndic", text=form.filing_info.doc_type, ns=NS)
    _sub(ds, "DocRefId", text=form.filing_info.doc_ref_id or _auto_docref("FI"), ns=NS)

    # GeneralSection (MVP – tylko RecJurCode + uproszczone CorporateStructure)
    if form.jurysdykcje_rec or form.upe_lista:
        gs = _sub(body, "GeneralSection", ns=NS)
        for jur in form.jurysdykcje_rec:
            _sub(gs, "RecJurCode", text=jur, ns=NS)
        corp = _sub(gs, "CorporateStructure", ns=NS)
        for upe in form.upe_lista:
            upe_el = _sub(corp, "UPE", ns=NS)
            inc_el = _sub(upe_el, "IncludedUPE", ns=NS)
            tin_upe = _build_tin(inc_el, upe.tin, upe.kraj, NS)
            _sub(inc_el, "ResCountryCode", text=upe.kraj, ns=NS)
            _sub(inc_el, "Name", text=upe.nazwa, ns=NS)
        ds_gs = _sub(gs, "DocSpec", ns=NS)
        _sub(ds_gs, "DocTypeIndic", text="OECD1", ns=NS)
        _sub(ds_gs, "DocRefId", text=_auto_docref("GS"), ns=NS)

    # Summary sekcje
    for s in form.summary_lista:
        summ = _sub(body, "Summary", ns=NS)
        _sub(summ, "RecJurCode", text=s.kod_jurysdykcji, ns=NS)
        jur_el = _sub(summ, "Jurisdiction", ns=NS)
        _sub(jur_el, "JurisdictionName", text=s.kod_jurysdykcji, ns=NS)
        if s.safe_harbour:
            _sub(summ, "SafeHarbour", text=s.safe_harbour, ns=NS)
        if s.etr_range:
            _sub(summ, "ETRRange", text=s.etr_range, ns=NS)
        if s.globe_tut:
            _sub(summ, "GLoBETut", text=s.globe_tut, ns=NS)
        ds_s = _sub(summ, "DocSpec", ns=NS)
        _sub(ds_s, "DocTypeIndic", text=s.doc_type, ns=NS)
        _sub(ds_s, "DocRefId", text=s.doc_ref_id or _auto_docref("SUM"), ns=NS)

    return etree.tostring(root, pretty_print=True, xml_declaration=True, encoding="UTF-8")


def _build_tin(parent, tin_val: str, country: str, ns: str):
    tin_el = etree.SubElement(parent, f"{{{ns}}}TIN")
    tin_el.set("issuedBy", country)
    tin_el.text = tin_val
    return tin_el


def _tin_elem(tin_val: str, country: str) -> str:
    return tin_val


def _auto_docref(prefix: str) -> str:
    import uuid
    return f"{prefix}-{uuid.uuid4().hex[:16].upper()}"
