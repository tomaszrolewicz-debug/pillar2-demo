"""
Pillar Two / GloBE – Aplikacja MVP
===================================
Uruchomienie: streamlit run app/main.py --server.headless true
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import streamlit as st
from datetime import date

from app.models import (
    GLBZ2_Form, GLBZ2_Naglowek, GLBZ2_Podmiot1,
    GLBZ2_PozycjeSzczegolowe, GLBZ2_JednostkaD,
    GIR_Form, GIR_FilingInfo, GIR_FilingCE, GIR_AccountingInfo,
    GIR_UPE, GIR_Summary_Jurysdykcja,
)
from app.xml_generator import generate_glbz2_xml, generate_gir_xml
from app.validator import validate_xml, validate_glbz2_fields, validate_gir_fields
from app.storage import (
    save_draft, list_drafts, load_draft,
    import_jednostki_from_excel, import_summary_from_excel,
    generate_excel_template,
)
from app.submission_adapter import adapter
from app.config import GLB_Z2_SCHEMA, GIR_SCHEMA, APP_VERSION

# ── Stałe UI ─────────────────────────────────────────────────────────────────
COUNTRIES = [
    "AD","AE","AF","AG","AL","AM","AO","AR","AT","AU","AZ",
    "BA","BB","BD","BE","BF","BG","BH","BJ","BM","BN","BO","BR","BS","BT","BW","BY","BZ",
    "CA","CD","CF","CG","CH","CI","CL","CM","CN","CO","CR","CU","CV","CY","CZ",
    "DE","DJ","DK","DM","DO","DZ",
    "EC","EE","EG","ER","ES","ET",
    "FI","FJ","FM","FR",
    "GA","GB","GD","GE","GH","GM","GN","GQ","GR","GT","GW","GY",
    "HN","HR","HT","HU",
    "ID","IE","IL","IN","IQ","IR","IS","IT",
    "JM","JO","JP",
    "KE","KG","KH","KI","KM","KN","KP","KR","KW","KZ",
    "LA","LB","LC","LI","LK","LR","LS","LT","LU","LV",
    "MA","MC","MD","ME","MG","MH","MK","ML","MM","MN","MR","MT","MU","MV","MW","MX","MY","MZ",
    "NA","NE","NG","NI","NL","NO","NP","NR","NZ",
    "OM",
    "PA","PE","PG","PH","PK","PL","PT","PW","PY",
    "QA",
    "RO","RS","RU","RW",
    "SA","SB","SC","SD","SE","SG","SI","SK","SL","SM","SN","SO","SR","SS","ST","SV",
    "SY","SZ",
    "TD","TG","TH","TJ","TL","TM","TN","TO","TR","TT","TV","TZ",
    "UA","UG","US","UY","UZ",
    "VA","VC","VE","VN","VU",
    "WS",
    "YE",
    "ZA","ZM","ZW",
]

RODZAJ_ID_OPTIONS = {
    "1": "TIN – numer identyfikacyjny podatkowy",
    "2": "Numer ubezpieczeniowy",
    "3": "Paszport",
    "4": "Urzędowy dokument tożsamości",
    "8": "Inny rodzaj identyfikacji podatkowej",
    "9": "Inny dokument tożsamości",
}

FILING_CE_ROLE = {
    "UPE": "UPE – Jednostka dominująca najwyższego szczebla",
    "Designated": "Wyznaczona jednostka składowa (Designated Filing Entity)",
    "Local": "Lokalna jednostka składowa",
}

SAFE_HARBOUR = {
    "": "(brak)",
    "STSH": "STSH – Transitional Safe Harbour",
    "DMSH": "DMSH – De Minimis Safe Harbour",
    "SBIE": "SBIE – Substance-Based Income Exclusion",
}

ETR_RANGE = {
    "": "(brak)",
    "A": "A – ETR = 0%",
    "B": "B – 0% < ETR < 15%",
    "C": "C – ETR ≥ 15%",
}

CFS_UPE = {
    "IFRS": "IFRS",
    "GAAP": "US GAAP",
    "LOCAL": "Lokalne standardy rachunkowości",
    "OTHER": "Inne",
}


# ════════════════════════════════════════════════════════════════════════════
#  Helpers
# ════════════════════════════════════════════════════════════════════════════

def tip(text: str):
    st.caption(f"ℹ️ {text}")


def required_label(label: str) -> str:
    return f"{label} *"


def show_checklist(errors: list):
    if not errors:
        st.success("✅ Wszystkie wymagane pola są wypełnione – formularz gotowy do wygenerowania XML.")
    else:
        st.warning(f"⚠️ Uzupełnij {len(errors)} brakujących elementów przed wygenerowaniem XML:")
        for e in errors:
            st.markdown(f"- ❌ {e}")


def section(title: str, icon: str = "📋"):
    st.markdown(f"### {icon} {title}")
    st.markdown("---")


# ════════════════════════════════════════════════════════════════════════════
#  FORMULARZ GLB-Z2
# ════════════════════════════════════════════════════════════════════════════

def render_glbz2():
    st.markdown(
        "**GLB-Z2** – Zawiadomienie o danych jednostki składowej składającej "
        "informację o opodatkowaniu wyrównawczym  \n"
        "*Naczelnik Kujawsko-Pomorskiego Urzędu Skarbowego w Bydgoszczy (kod 0471)*"
    )
    st.markdown("")

    # ── Ładowanie draftu ─────────────────────────────────────────────────────
    with st.expander("📂 Wczytaj zapisany draft"):
        drafts = list_drafts("GLBZ2")
        if drafts:
            opts = {d["filename"]: d["path"] for d in drafts}
            chosen = st.selectbox("Wybierz draft", list(opts.keys()))
            if st.button("Wczytaj draft"):
                raw = load_draft(opts[chosen])
                st.session_state["glbz2_data"] = raw
                st.success("Draft wczytany!")
                st.rerun()
        else:
            st.info("Brak zapisanych draftów.")

    # ── Inicjalizacja stanu ───────────────────────────────────────────────────
    if "glbz2_data" not in st.session_state:
        st.session_state["glbz2_data"] = GLBZ2_Form().model_dump()
    d = st.session_state["glbz2_data"]

    # ════ A. NAGŁÓWEK ═════════════════════════════════════════════════════════
    section("A. Nagłówek", "📅")
    col1, col2 = st.columns(2)
    with col1:
        d["naglowek"]["okres_od"] = st.text_input(
            required_label("Okres Od (data od)"),
            value=d["naglowek"].get("okres_od", ""),
            placeholder="np. 2024-01-01",
            key="z2_od",
        )
        tip("Pierwszy dzień okresu rozliczeniowego – format RRRR-MM-DD")
    with col2:
        d["naglowek"]["okres_do"] = st.text_input(
            required_label("Okres Do (data do)"),
            value=d["naglowek"].get("okres_do", ""),
            placeholder="np. 2024-12-31",
            key="z2_do",
        )
        tip("Ostatni dzień okresu rozliczeniowego – format RRRR-MM-DD")

    st.info("📌 Urząd skarbowy: **Naczelnik Kujawsko-Pomorskiego US w Bydgoszczy** (stały, wynika ze schematu XSD).")

    # ════ B. PODMIOT1 ═════════════════════════════════════════════════════════
    section("B. Podmiot składający zawiadomienie", "🏢")
    col1, col2 = st.columns(2)
    with col1:
        d["podmiot1"]["nip"] = st.text_input(
            required_label("NIP"),
            value=d["podmiot1"].get("nip", ""),
            placeholder="np. 1234567890",
            key="z2_nip",
        )
        tip("10-cyfrowy NIP polskiej jednostki składającej zawiadomienie")
    with col2:
        d["podmiot1"]["pelna_nazwa"] = st.text_input(
            required_label("Pełna nazwa"),
            value=d["podmiot1"].get("pelna_nazwa", ""),
            placeholder="np. Spółka ABC S.A.",
            key="z2_nazwa",
        )
        tip("Pełna nazwa prawna zgodna z rejestrem (maks. 240 znaków)")

    # ════ C. POZYCJE SZCZEGÓŁOWE ══════════════════════════════════════════════
    section("C. Dane jednostki składającej zawiadomienie", "📊")
    d["pozycje"]["nazwa_grupy"] = st.text_input(
        required_label("Nazwa grupy (P_7)"),
        value=d["pozycje"].get("nazwa_grupy", ""),
        placeholder="np. ABC Group",
        key="z2_p7",
    )
    tip("Nazwa grupy multinarodowej (MNE Group)")

    rodzaj_skladajacy_opts = {
        "1": "1 – Jednostka składowa grupy, zlokalizowana w Polsce",
        "2": "2 – Upoważniona jednostka składowa zlokalizowana w Polsce",
    }
    d["pozycje"]["rodzaj_jednostki_skladajacej"] = st.selectbox(
        required_label("Rodzaj jednostki składającej (P_8)"),
        options=list(rodzaj_skladajacy_opts.keys()),
        format_func=lambda x: rodzaj_skladajacy_opts[x],
        index=int(d["pozycje"].get("rodzaj_jednostki_skladajacej", "1")) - 1,
        key="z2_p8",
    )
    tip("Art. 133 ust. 3 ustawy: jednostka składowa lub upoważniona")

    # ════ D. JEDNOSTKI SKŁADOWE ═══════════════════════════════════════════════
    section("D. Dane jednostek składowych (art. 133 ust. 4 ustawy)", "🏗️")

    # Import z Excel
    with st.expander("📥 Import jednostek z pliku Excel / CSV"):
        col_dl, col_up = st.columns(2)
        with col_dl:
            tpl = generate_excel_template("GLBZ2")
            st.download_button("⬇️ Pobierz szablon Excel", data=tpl,
                               file_name="szablon_jednostki_GLB_Z2.xlsx",
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        with col_up:
            uf = st.file_uploader("Wgraj plik Excel / CSV", type=["xlsx", "csv"], key="z2_excel_up")
        if uf is not None:
            rows, errs = import_jednostki_from_excel(uf.read(), uf.name)
            if errs:
                for e in errs:
                    st.warning(e)
            if rows:
                d["pozycje"]["jednostki_d"] = rows
                st.success(f"Zaimportowano {len(rows)} jednostek.")
                st.rerun()

    # Inicjalizacja listy
    if not d["pozycje"].get("jednostki_d"):
        d["pozycje"]["jednostki_d"] = [GLBZ2_JednostkaD().model_dump()]

    jednostki = d["pozycje"]["jednostki_d"]

    def render_jednostka(idx: int, jd: dict):
        with st.container():
            st.markdown(f"**Jednostka {idx + 1}**")
            col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 4])
            with col_btn1:
                if st.button("🗑️ Usuń", key=f"z2_del_{idx}"):
                    jednostki.pop(idx)
                    st.rerun()
            with col_btn2:
                if st.button("📋 Duplikuj", key=f"z2_dup_{idx}"):
                    import copy
                    jednostki.insert(idx + 1, copy.deepcopy(jd))
                    st.rerun()

            rod_opts = {
                "1": "1 – Jednostka dominująca najwyższego szczebla (UPE) w innej jurysdykcji",
                "2": "2 – Wyznaczona jednostka składowa w innej jurysdykcji",
            }
            jd["rodzaj_jednostki"] = st.selectbox(
                required_label("Rodzaj jednostki (D.1)"),
                options=["1", "2"],
                format_func=lambda x: rod_opts[x],
                index=int(jd.get("rodzaj_jednostki", "1")) - 1,
                key=f"z2_d9_{idx}",
            )

            c1, c2 = st.columns(2)
            with c1:
                jd["pelna_nazwa"] = st.text_input(
                    required_label("Pełna nazwa (D.2)"),
                    value=jd.get("pelna_nazwa", ""),
                    key=f"z2_d10_{idx}",
                )
                tip("Pełna nazwa prawna jednostki (maks. 240 znaków)")
                jd["kraj_id"] = st.selectbox(
                    required_label("Kraj wydania nr ID"),
                    options=COUNTRIES,
                    index=COUNTRIES.index(jd.get("kraj_id", "DE")) if jd.get("kraj_id", "DE") in COUNTRIES else 0,
                    key=f"z2_d11_{idx}",
                )
                tip("Kod ISO 3166-1 alpha-2 kraju wydającego numer identyfikacyjny")
            with c2:
                jd["rodzaj_id"] = st.selectbox(
                    required_label("Rodzaj numeru ID"),
                    options=list(RODZAJ_ID_OPTIONS.keys()),
                    format_func=lambda x: RODZAJ_ID_OPTIONS[x],
                    index=list(RODZAJ_ID_OPTIONS.keys()).index(jd.get("rodzaj_id", "1")),
                    key=f"z2_d12_{idx}",
                )
                jd["nr_id"] = st.text_input(
                    required_label("Numer identyfikacyjny"),
                    value=jd.get("nr_id", ""),
                    key=f"z2_d13_{idx}",
                )
                tip("Zagraniczny numer podatkowy (TIN) lub inny numer identyfikacyjny")

            st.markdown("**Adres siedziby (D.3)**")
            ca, cb, cc = st.columns(3)
            with ca:
                jd["adres_kraj"] = st.selectbox(
                    required_label("Kraj siedziby"),
                    options=COUNTRIES,
                    index=COUNTRIES.index(jd.get("adres_kraj", "DE")) if jd.get("adres_kraj", "DE") in COUNTRIES else 0,
                    key=f"z2_d14_{idx}",
                )
            with cb:
                jd["adres_miejscowosc"] = st.text_input(
                    required_label("Miejscowość"),
                    value=jd.get("adres_miejscowosc", ""),
                    key=f"z2_d15_{idx}",
                )
            with cc:
                jd["adres_kod"] = st.text_input(
                    "Kod pocztowy",
                    value=jd.get("adres_kod", ""),
                    key=f"z2_d16_{idx}",
                )
            cd, ce, cf, cg = st.columns(4)
            with cd:
                jd["adres_ulica"] = st.text_input("Ulica", value=jd.get("adres_ulica", ""), key=f"z2_d17_{idx}")
            with ce:
                jd["adres_nr_budynku"] = st.text_input("Nr domu", value=jd.get("adres_nr_budynku", ""), key=f"z2_d18_{idx}")
            with cf:
                jd["adres_nr_lokalu"] = st.text_input("Nr lokalu", value=jd.get("adres_nr_lokalu", ""), key=f"z2_d19_{idx}")
            with cg:
                jd["adres_inne"] = st.text_input("Inne dane", value=jd.get("adres_inne", ""), key=f"z2_d20_{idx}")

            jd["kod_jurysdykcji"] = st.selectbox(
                required_label("Kod jurysdykcji lokalizacji (D.4)"),
                options=COUNTRIES,
                index=COUNTRIES.index(jd.get("kod_jurysdykcji", "DE")) if jd.get("kod_jurysdykcji", "DE") in COUNTRIES else 0,
                key=f"z2_d21_{idx}",
            )
            tip("Jurysdykcja, w której zlokalizowana jest jednostka składowa")
            st.markdown("---")

    for idx, jd in enumerate(jednostki):
        render_jednostka(idx, jd)

    if st.button("➕ Dodaj kolejną jednostkę", key="z2_add"):
        jednostki.append(GLBZ2_JednostkaD().model_dump())
        st.rerun()

    # ════ E. LICZBA ZAŁĄCZNIKÓW ═══════════════════════════════════════════════
    section("E. Załączniki GLB/ZZ2", "📎")
    tip("Wypełnij, jeśli jednostka składająca jest wyznaczona na podstawie art. 133 ust. 3 ustawy.")
    lz = d["pozycje"].get("liczba_zalacznikow")
    lz_input = st.number_input(
        "Liczba składanych załączników GLB/ZZ2",
        min_value=0, max_value=999,
        value=int(lz) if lz is not None else 0,
        key="z2_p22",
    )
    d["pozycje"]["liczba_zalacznikow"] = lz_input if lz_input > 0 else None

    # ════ F. DANE KONTAKTOWE ══════════════════════════════════════════════════
    section("F. Dane kontaktowe", "📞")
    c1, c2 = st.columns(2)
    with c1:
        d["pozycje"]["email"] = st.text_input(
            "Adres e-mail",
            value=d["pozycje"].get("email", ""),
            key="z2_email",
        )
    with c2:
        d["pozycje"]["telefon"] = st.text_input(
            "Telefon (maks. 16 znaków)",
            value=d["pozycje"].get("telefon", ""),
            key="z2_tel",
        )

    st.markdown("---")

    # ════ CHECKLIST + AKCJE ════════════════════════════════════════════════════
    section("✅ Gotowość formularza", "🎯")

    # Budujemy model z aktualnego stanu
    form = _build_glbz2_form(d)
    errors_f = validate_glbz2_fields(form)
    show_checklist(errors_f)

    col_save, col_gen = st.columns(2)
    with col_save:
        draft_name = st.text_input("Nazwa draftu (opcjonalnie)", key="z2_draft_name", value="")
        if st.button("💾 Zapisz draft", key="z2_save"):
            path = save_draft("GLBZ2", d, name=draft_name)
            st.success(f"Draft zapisany: {os.path.basename(path)}")

    with col_gen:
        if st.button("⚙️ Generuj XML", key="z2_gen", disabled=bool(errors_f)):
            with st.spinner("Generowanie XML..."):
                try:
                    xml_bytes = generate_glbz2_xml(form)
                    st.session_state["glbz2_xml"] = xml_bytes

                    ok, val_errors = validate_xml(xml_bytes, GLB_Z2_SCHEMA)
                    st.session_state["glbz2_val_errors"] = val_errors
                    st.session_state["glbz2_val_ok"] = ok
                except Exception as e:
                    st.error(f"Błąd generowania XML: {e}")

    # Wyniki walidacji i pobieranie
    if "glbz2_xml" in st.session_state:
        xml_bytes = st.session_state["glbz2_xml"]
        val_ok = st.session_state.get("glbz2_val_ok", False)
        val_errs = st.session_state.get("glbz2_val_errors", [])

        st.markdown("### 📄 Wynik")
        if val_ok and not [e for e in val_errs if "⚠️" not in e]:
            st.success("✅ XML wygenerowany pomyślnie.")
        elif val_errs:
            for ve in val_errs:
                if "⚠️" in ve:
                    st.warning(ve)
                else:
                    st.error(ve)
        else:
            st.success("✅ XML wygenerowany – składnia poprawna.")

        st.download_button(
            "⬇️ Pobierz XML (GLB-Z2)",
            data=xml_bytes,
            file_name=f"GLB_Z2_{date.today().isoformat()}.xml",
            mime="application/xml",
            key="z2_dl_xml",
        )

        with st.expander("🔍 Podgląd XML"):
            st.code(xml_bytes.decode("utf-8"), language="xml")

        # Draft JSON
        st.download_button(
            "⬇️ Pobierz draft JSON",
            data=json.dumps(d, ensure_ascii=False, indent=2),
            file_name=f"GLB_Z2_draft_{date.today().isoformat()}.json",
            mime="application/json",
            key="z2_dl_json",
        )

        # Moduł wysyłki
        st.markdown("### 📤 Wysyłka")
        if st.button("📤 Przygotuj do wysyłki / wyślij", key="z2_submit"):
            ok_pre, msg_pre = adapter.validate_before_submission(xml_bytes)
            if ok_pre:
                signed, msg_sign = adapter.sign_or_prepare_for_signature(xml_bytes)
                ok_sub, msg_sub = adapter.submit(signed, form_type="GLB-Z2")
                if ok_sub:
                    st.success(msg_sub)
                else:
                    st.info(msg_sub)
                if "⚠️" in msg_sign:
                    st.warning(msg_sign)
            else:
                st.error(msg_pre)


def _build_glbz2_form(d: dict) -> GLBZ2_Form:
    from app.models import GLBZ2_JednostkaD
    form = GLBZ2_Form(
        naglowek=GLBZ2_Naglowek(**d.get("naglowek", {})),
        podmiot1=GLBZ2_Podmiot1(**d.get("podmiot1", {})),
        pozycje=GLBZ2_PozycjeSzczegolowe(
            nazwa_grupy=d["pozycje"].get("nazwa_grupy", ""),
            rodzaj_jednostki_skladajacej=d["pozycje"].get("rodzaj_jednostki_skladajacej", "1"),
            jednostki_d=[GLBZ2_JednostkaD(**j) for j in d["pozycje"].get("jednostki_d", [])],
            liczba_zalacznikow=d["pozycje"].get("liczba_zalacznikow"),
            email=d["pozycje"].get("email", ""),
            telefon=d["pozycje"].get("telefon", ""),
        ),
    )
    return form


# ════════════════════════════════════════════════════════════════════════════
#  FORMULARZ GIR
# ════════════════════════════════════════════════════════════════════════════

def render_gir():
    st.markdown(
        "**GIR-1** – GloBE Information Return (Informacja o opodatkowaniu wyrównawczym)  \n"
        "*Etap 1 MVP: dane identyfikacyjne, FilingInfo, GeneralSection (UPE), Summary*"
    )
    st.info(
        "ℹ️ **Etap 1 MVP** obejmuje sekcje: Nagłówek, Podmiot1, FilingInfo, "
        "GeneralSection (uproszczone) i Summary. "
        "Pełne sekcje kalkulacyjne ETR/UTPR/JurisdictionSection są zaplanowane w Etapie 2."
    )
    st.markdown("")

    # ── Ładowanie draftu ─────────────────────────────────────────────────────
    with st.expander("📂 Wczytaj zapisany draft"):
        drafts = list_drafts("GIR")
        if drafts:
            opts = {d2["filename"]: d2["path"] for d2 in drafts}
            chosen = st.selectbox("Wybierz draft", list(opts.keys()), key="gir_draft_sel")
            if st.button("Wczytaj draft", key="gir_load"):
                raw = load_draft(opts[chosen])
                st.session_state["gir_data"] = raw
                st.success("Draft wczytany!")
                st.rerun()
        else:
            st.info("Brak zapisanych draftów.")

    if "gir_data" not in st.session_state:
        st.session_state["gir_data"] = GIR_Form().model_dump()
    d = st.session_state["gir_data"]

    # ════ A. NAGŁÓWEK ═════════════════════════════════════════════════════════
    section("A. Nagłówek", "📅")
    c1, c2 = st.columns(2)
    with c1:
        d["okres_od"] = st.text_input(
            required_label("Rok fiskalny – data od"),
            value=d.get("okres_od", ""),
            placeholder="2024-01-01",
            key="gir_od",
        )
        tip("Pierwszy dzień roku fiskalnego GloBE – format RRRR-MM-DD")
    with c2:
        d["okres_do"] = st.text_input(
            required_label("Rok fiskalny – data do"),
            value=d.get("okres_do", ""),
            placeholder="2024-12-31",
            key="gir_do",
        )

    # ════ B. PODMIOT1 ═════════════════════════════════════════════════════════
    section("B. Podmiot składający (Podmiot1)", "🏢")
    c1, c2 = st.columns(2)
    with c1:
        d["nip"] = st.text_input(
            required_label("NIP (polska jednostka składająca)"),
            value=d.get("nip", ""),
            placeholder="1234567890",
            key="gir_nip",
        )
        tip("NIP 10-cyfrowy polskiej jednostki składającej GIR")
    with c2:
        d["pelna_nazwa"] = st.text_input(
            required_label("Pełna nazwa"),
            value=d.get("pelna_nazwa", ""),
            key="gir_nazwa",
        )

    # ════ C. FILING INFO ══════════════════════════════════════════════════════
    section("C. Informacje o złożeniu (FilingInfo)", "📋")

    fi = d.setdefault("filing_info", GIR_FilingInfo().model_dump())

    st.markdown("**C.1. Jednostka składająca GIR (FilingCE)**")
    fce = fi.setdefault("filing_ce", GIR_FilingCE().model_dump())
    c1, c2, c3 = st.columns(3)
    with c1:
        fce["kraj"] = st.selectbox(
            required_label("Kraj rejestracji"),
            options=COUNTRIES,
            index=COUNTRIES.index(fce.get("kraj", "PL")) if fce.get("kraj", "PL") in COUNTRIES else COUNTRIES.index("PL"),
            key="gir_fce_kraj",
        )
    with c2:
        fce["nazwa"] = st.text_input(
            required_label("Nazwa jednostki"),
            value=fce.get("nazwa", ""),
            key="gir_fce_nazwa",
        )
        tip("Pełna nazwa prawna jednostki składającej GIR")
    with c3:
        fce["tin"] = st.text_input(
            required_label("TIN"),
            value=fce.get("tin", ""),
            key="gir_fce_tin",
        )
        tip("Numer identyfikacji podatkowej w kraju rejestracji")

    fce["rola"] = st.selectbox(
        required_label("Rola jednostki (FilingCE Role)"),
        options=list(FILING_CE_ROLE.keys()),
        format_func=lambda x: FILING_CE_ROLE[x],
        index=list(FILING_CE_ROLE.keys()).index(fce.get("rola", "UPE")) if fce.get("rola", "UPE") in FILING_CE_ROLE else 0,
        key="gir_fce_rola",
    )

    st.markdown("**C.2. Informacje rachunkowe**")
    acc = fi.setdefault("accounting_info", GIR_AccountingInfo().model_dump())
    c1, c2, c3 = st.columns(3)
    with c1:
        acc["cfs_upe"] = st.selectbox(
            required_label("Standard sprawozdawczości (CFSofUPE)"),
            options=list(CFS_UPE.keys()),
            format_func=lambda x: CFS_UPE[x],
            index=list(CFS_UPE.keys()).index(acc.get("cfs_upe", "IFRS")) if acc.get("cfs_upe", "IFRS") in CFS_UPE else 0,
            key="gir_cfs",
        )
    with c2:
        acc["fas"] = st.text_input(
            required_label("Opis standardu rachunkowości (FAS)"),
            value=acc.get("fas", ""),
            placeholder="np. IFRS as adopted by EU",
            key="gir_fas",
        )
    with c3:
        acc["waluta"] = st.text_input(
            required_label("Waluta sprawozdawcza"),
            value=acc.get("waluta", "EUR"),
            placeholder="EUR",
            key="gir_waluta",
        )
        tip("Kod ISO 4217, np. EUR, USD, PLN")

    st.markdown("**C.3. Okres i dane grupy**")
    c1, c2 = st.columns(2)
    with c1:
        fi["okres_od"] = st.text_input(
            required_label("Okres FilingInfo – od"),
            value=fi.get("okres_od", d.get("okres_od", "")),
            key="gir_fi_od",
        )
        fi["okres_do"] = st.text_input(
            required_label("Okres FilingInfo – do"),
            value=fi.get("okres_do", d.get("okres_do", "")),
            key="gir_fi_do",
        )
    with c2:
        fi["nazwa_mne"] = st.text_input(
            required_label("Nazwa grupy MNE"),
            value=fi.get("nazwa_mne", ""),
            key="gir_mne",
        )
        tip("Oficjalna nazwa grupy multinarodowej")
        fi["uwagi"] = st.text_area(
            "Uwagi dodatkowe (opcjonalnie)",
            value=fi.get("uwagi", ""),
            height=80,
            key="gir_uwagi",
        )

    st.markdown("**C.4. DocSpec (identyfikatory dokumentu)**")
    c1, c2 = st.columns(2)
    with c1:
        fi["doc_ref_id"] = st.text_input(
            "DocRefId (jeśli puste – wygenerowane automatycznie)",
            value=fi.get("doc_ref_id", ""),
            key="gir_docref",
        )
        tip("Unikalny identyfikator tego dokumentu w ramach grupy. Wygenerowany automatycznie jeśli puste.")
    with c2:
        fi["doc_type"] = st.selectbox(
            "Rodzaj dokumentu (DocTypeIndic)",
            options=["OECD1", "OECD2", "OECD3"],
            format_func=lambda x: {
                "OECD1": "OECD1 – Nowy dokument",
                "OECD2": "OECD2 – Korekta",
                "OECD3": "OECD3 – Usunięcie",
            }[x],
            index=["OECD1", "OECD2", "OECD3"].index(fi.get("doc_type", "OECD1")),
            key="gir_doctype",
        )

    # ════ D. GENERAL SECTION – UPE ════════════════════════════════════════════
    section("D. Struktura korporacyjna – jednostki UPE (GeneralSection)", "🌍")
    tip("Lista jurysdykcji i jednostek dominujących najwyższego szczebla (UPE)")

    # RecJurCode
    jur_rec_raw = st.text_input(
        "Kody jurysdykcji (RecJurCode) – oddziel przecinkiem",
        value=", ".join(d.get("jurysdykcje_rec", [])),
        key="gir_recjur",
        placeholder="np. PL, DE, FR",
    )
    d["jurysdykcje_rec"] = [x.strip().upper() for x in jur_rec_raw.split(",") if x.strip()]

    if not d.get("upe_lista"):
        d["upe_lista"] = [GIR_UPE().model_dump()]

    for idx, upe in enumerate(d["upe_lista"]):
        with st.container():
            st.markdown(f"**UPE {idx + 1}**")
            cb1, cb2 = st.columns([1, 5])
            with cb1:
                if st.button("🗑️ Usuń UPE", key=f"gir_upe_del_{idx}"):
                    d["upe_lista"].pop(idx)
                    st.rerun()
            c1, c2, c3 = st.columns(3)
            with c1:
                upe["kraj"] = st.selectbox(
                    "Kraj UPE",
                    options=COUNTRIES,
                    index=COUNTRIES.index(upe.get("kraj", "DE")) if upe.get("kraj", "DE") in COUNTRIES else 0,
                    key=f"gir_upe_kraj_{idx}",
                )
            with c2:
                upe["nazwa"] = st.text_input("Nazwa UPE", value=upe.get("nazwa", ""), key=f"gir_upe_nazwa_{idx}")
            with c3:
                upe["tin"] = st.text_input("TIN UPE", value=upe.get("tin", ""), key=f"gir_upe_tin_{idx}")
            st.markdown("---")

    if st.button("➕ Dodaj UPE", key="gir_upe_add"):
        d["upe_lista"].append(GIR_UPE().model_dump())
        st.rerun()

    # ════ E. SUMMARY ══════════════════════════════════════════════════════════
    section("E. Sekcja Summary (jurysdykcje)", "📊")
    tip("Podsumowanie per jurysdykcja – wypełnij dla każdej jurysdykcji grupy.")

    with st.expander("📥 Import Summary z pliku Excel / CSV"):
        col_dl2, col_up2 = st.columns(2)
        with col_dl2:
            tpl2 = generate_excel_template("GIR")
            st.download_button("⬇️ Pobierz szablon Excel", data=tpl2,
                               file_name="szablon_summary_GIR.xlsx",
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                               key="gir_tpl_dl")
        with col_up2:
            uf2 = st.file_uploader("Wgraj plik Excel / CSV", type=["xlsx", "csv"], key="gir_excel_up")
        if uf2 is not None:
            rows2, errs2 = import_summary_from_excel(uf2.read(), uf2.name)
            if errs2:
                for e2 in errs2:
                    st.warning(e2)
            if rows2:
                d["summary_lista"] = rows2
                st.success(f"Zaimportowano {len(rows2)} wierszy Summary.")
                st.rerun()

    if not d.get("summary_lista"):
        d["summary_lista"] = [GIR_Summary_Jurysdykcja().model_dump()]

    for idx, s in enumerate(d["summary_lista"]):
        with st.container():
            st.markdown(f"**Summary {idx + 1}**")
            cbs1, cbs2 = st.columns([1, 5])
            with cbs1:
                if st.button("🗑️ Usuń", key=f"gir_sum_del_{idx}"):
                    d["summary_lista"].pop(idx)
                    st.rerun()
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                cur_jur = s.get("kod_jurysdykcji", "DE")
                s["kod_jurysdykcji"] = st.selectbox(
                    required_label("Kod jurysdykcji"),
                    options=COUNTRIES,
                    index=COUNTRIES.index(cur_jur) if cur_jur in COUNTRIES else 0,
                    key=f"gir_sum_jur_{idx}",
                )
            with c2:
                s["safe_harbour"] = st.selectbox(
                    "Safe Harbour",
                    options=list(SAFE_HARBOUR.keys()),
                    format_func=lambda x: SAFE_HARBOUR[x],
                    index=list(SAFE_HARBOUR.keys()).index(s.get("safe_harbour", "")) if s.get("safe_harbour", "") in SAFE_HARBOUR else 0,
                    key=f"gir_sum_sh_{idx}",
                )
            with c3:
                s["etr_range"] = st.selectbox(
                    "Przedział ETR",
                    options=list(ETR_RANGE.keys()),
                    format_func=lambda x: ETR_RANGE[x],
                    index=list(ETR_RANGE.keys()).index(s.get("etr_range", "")) if s.get("etr_range", "") in ETR_RANGE else 0,
                    key=f"gir_sum_etr_{idx}",
                )
            with c4:
                s["globe_tut"] = st.text_input(
                    "GloBE TuT",
                    value=s.get("globe_tut", ""),
                    key=f"gir_sum_tut_{idx}",
                )
            c5, c6 = st.columns(2)
            with c5:
                s["doc_ref_id"] = st.text_input(
                    "DocRefId Summary",
                    value=s.get("doc_ref_id", ""),
                    key=f"gir_sum_docref_{idx}",
                )
            with c6:
                s["doc_type"] = st.selectbox(
                    "DocType",
                    options=["OECD1", "OECD2", "OECD3"],
                    index=["OECD1", "OECD2", "OECD3"].index(s.get("doc_type", "OECD1")),
                    key=f"gir_sum_doctype_{idx}",
                )
            st.markdown("---")

    if st.button("➕ Dodaj jurysdykcję Summary", key="gir_sum_add"):
        d["summary_lista"].append(GIR_Summary_Jurysdykcja().model_dump())
        st.rerun()

    st.markdown("---")

    # ════ CHECKLIST + AKCJE ════════════════════════════════════════════════════
    section("✅ Gotowość formularza", "🎯")

    form = _build_gir_form(d)
    errors_f = validate_gir_fields(form)
    show_checklist(errors_f)

    col_save, col_gen = st.columns(2)
    with col_save:
        draft_name = st.text_input("Nazwa draftu (opcjonalnie)", key="gir_draft_name", value="")
        if st.button("💾 Zapisz draft", key="gir_save"):
            path = save_draft("GIR", d, name=draft_name)
            st.success(f"Draft zapisany: {os.path.basename(path)}")

    with col_gen:
        if st.button("⚙️ Generuj XML", key="gir_gen", disabled=bool(errors_f)):
            with st.spinner("Generowanie XML..."):
                try:
                    xml_bytes = generate_gir_xml(form)
                    st.session_state["gir_xml"] = xml_bytes
                    ok, val_errors = validate_xml(xml_bytes, GIR_SCHEMA)
                    st.session_state["gir_val_errors"] = val_errors
                    st.session_state["gir_val_ok"] = ok
                except Exception as e:
                    st.error(f"Błąd generowania XML: {e}")

    if "gir_xml" in st.session_state:
        xml_bytes = st.session_state["gir_xml"]
        val_ok = st.session_state.get("gir_val_ok", False)
        val_errs = st.session_state.get("gir_val_errors", [])

        st.markdown("### 📄 Wynik")
        if val_ok and not [e for e in val_errs if "⚠️" not in e]:
            st.success("✅ XML wygenerowany pomyślnie.")
        elif val_errs:
            for ve in val_errs:
                if "⚠️" in ve:
                    st.warning(ve)
                else:
                    st.error(ve)

        st.download_button(
            "⬇️ Pobierz XML (GIR)",
            data=xml_bytes,
            file_name=f"GIR_{date.today().isoformat()}.xml",
            mime="application/xml",
            key="gir_dl_xml",
        )

        with st.expander("🔍 Podgląd XML"):
            st.code(xml_bytes.decode("utf-8"), language="xml")

        st.download_button(
            "⬇️ Pobierz draft JSON",
            data=json.dumps(d, ensure_ascii=False, indent=2),
            file_name=f"GIR_draft_{date.today().isoformat()}.json",
            mime="application/json",
            key="gir_dl_json",
        )

        st.markdown("### 📤 Wysyłka")
        if st.button("📤 Przygotuj do wysyłki / wyślij", key="gir_submit"):
            ok_pre, msg_pre = adapter.validate_before_submission(xml_bytes)
            if ok_pre:
                signed, msg_sign = adapter.sign_or_prepare_for_signature(xml_bytes)
                ok_sub, msg_sub = adapter.submit(signed, form_type="GIR-1")
                if ok_sub:
                    st.success(msg_sub)
                else:
                    st.info(msg_sub)
                if "⚠️" in msg_sign:
                    st.warning(msg_sign)
            else:
                st.error(msg_pre)


def _build_gir_form(d: dict) -> GIR_Form:
    fi_d = d.get("filing_info", {})
    return GIR_Form(
        okres_od=d.get("okres_od", ""),
        okres_do=d.get("okres_do", ""),
        nip=d.get("nip", ""),
        pelna_nazwa=d.get("pelna_nazwa", ""),
        filing_info=GIR_FilingInfo(
            filing_ce=GIR_FilingCE(**fi_d.get("filing_ce", {})),
            accounting_info=GIR_AccountingInfo(**fi_d.get("accounting_info", {})),
            okres_od=fi_d.get("okres_od", ""),
            okres_do=fi_d.get("okres_do", ""),
            nazwa_mne=fi_d.get("nazwa_mne", ""),
            uwagi=fi_d.get("uwagi", ""),
            doc_ref_id=fi_d.get("doc_ref_id", ""),
            doc_type=fi_d.get("doc_type", "OECD1"),
        ),
        jurysdykcje_rec=d.get("jurysdykcje_rec", []),
        upe_lista=[GIR_UPE(**u) for u in d.get("upe_lista", [])],
        summary_lista=[GIR_Summary_Jurysdykcja(**s) for s in d.get("summary_lista", [])],
    )


# ════════════════════════════════════════════════════════════════════════════
#  GŁÓWNA APLIKACJA
# ════════════════════════════════════════════════════════════════════════════

def main():
    st.set_page_config(
        page_title="Pillar Two / GloBE – Generator formularzy",
        page_icon="🌍",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Sidebar
    with st.sidebar:
        st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/6/65/No-Image-Placeholder.svg/330px-No-Image-Placeholder.svg.png", width=60)
        st.markdown("## 🌍 Pillar Two / GloBE")
        st.markdown(f"**Wersja:** `{APP_VERSION}`")
        st.markdown("---")
        form_choice = st.radio(
            "Wybierz formularz",
            ["GLB-Z2 – Zawiadomienie", "GIR – Informacja GloBE"],
            key="form_choice",
        )
        st.markdown("---")
        st.markdown("### ⚠️ Ostrzeżenie")
        st.warning(
            "Przed użyciem produkcyjnym:\n"
            "- Zweryfikuj aktualność schematów XSD na stronie MF\n"
            "- Skonfiguruj certyfikat podpisu\n"
            "- Potwierdź kanał wysyłki z MF\n"
            "- Nie loguj danych wrażliwych"
        )
        st.markdown("---")
        st.markdown("### 📁 Eksport skonfigurowany")
        st.markdown(f"Drafty: `drafts/`")
        st.markdown(f"Eksport XML: `exports/`")

    st.title("🌍 Pillar Two / GloBE – Generator formularzy podatkowych")
    st.markdown(
        "Narzędzie do tworzenia, walidacji i pobierania plików XML "
        "zgodnych z polskimi schematami XSD dla formularzy GloBE."
    )
    st.markdown("---")

    if "GLB-Z2" in form_choice:
        render_glbz2()
    else:
        render_gir()


if __name__ == "__main__":
    main()
