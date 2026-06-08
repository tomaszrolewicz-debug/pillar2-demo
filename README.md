# 🌍 Pillar Two / GloBE – Generator formularzy podatkowych MVP

> **Wersja:** 0.1.0-MVP  
> **Formularze:** GLB-Z2 (zawiadomienie) | GIR-1 (GloBE Information Return)

---

## Architektura rozwiązania

```
┌─────────────────────────────────────────────────────────────┐
│                      Streamlit UI                           │
│    Formularz GLB-Z2          Formularz GIR-1                │
│    (Naglowek / Podmiot1 /    (FilingInfo / Summary /        │
│     PozycjeSzczegolowe)       GeneralSection / UPE)         │
└──────────────┬──────────────────────────┬───────────────────┘
               │                          │
       ┌───────▼──────────┐    ┌──────────▼──────────┐
       │  xml_generator   │    │     validator        │
       │  (lxml / etree)  │    │  (XSD + przyjazne    │
       │  → bytes XML     │    │   komunikaty błędów) │
       └───────┬──────────┘    └──────────────────────┘
               │
    ┌──────────▼──────────┐     ┌─────────────────────┐
    │    storage.py        │     │  submission_adapter  │
    │  (draft JSON +       │     │  validate / sign /   │
    │   import Excel/CSV)  │     │  submit → placeholder│
    └──────────────────────┘     └─────────────────────┘
```

**Przepływ danych:**
1. Doradca podatkowy wypełnia formularz w Streamlit
2. Aplikacja buduje model Pydantic z danych formularza
3. Szybka walidacja pól → lista błędów po ludzku
4. Generowanie XML (lxml) → walidacja XSD
5. Pobieranie XML + JSON draftu
6. (Opcjonalnie) wysyłka przez `submission_adapter`

---

## Struktura katalogów

```
pillar2_tool/
├── app/
│   ├── main.py               # Aplikacja Streamlit (punkt wejścia)
│   ├── models.py             # Modele danych Pydantic (GLB-Z2, GIR)
│   ├── xml_generator.py      # Generator XML (lxml)
│   ├── validator.py          # Walidacja XSD + przyjazne błędy
│   ├── storage.py            # Drafty JSON + import Excel/CSV
│   ├── submission_adapter.py # Interfejs wysyłki do MF (placeholder)
│   └── config.py             # Konfiguracja ścieżek i endpointów
├── schemas/
│   ├── GLB_Z2_schemat.xsd    # Schemat XSD formularza GLB-Z2
│   └── GIR_schemat.xsd       # Schemat XSD formularza GIR-1
├── drafts/                   # Zapisane drafty JSON
│   ├── GLBZ2_przyklad_draft.json
│   └── GIR_przyklad_draft.json
├── exports/                  # Eksportowane pliki XML
├── requirements.txt
└── README.md
```

---

## Instrukcja uruchomienia

### Wymagania

- Python 3.10+
- pip

### Instalacja

```bash
# 1. Przejdź do katalogu projektu
cd pillar2_tool

# 2. Utwórz środowisko wirtualne (zalecane)
python -m venv .venv
source .venv/bin/activate        # Linux/Mac
# lub: .venv\Scripts\activate   # Windows

# 3. Zainstaluj zależności
pip install -r requirements.txt

# 4. Uruchom aplikację
streamlit run app/main.py
```

Aplikacja otworzy się pod adresem: **http://localhost:8501**

---

## Konfiguracja (config.py / zmienne środowiskowe)

| Parametr | Opis | Domyślnie |
|---|---|---|
| `MF_SUBMISSION_ENDPOINT` | URL API MF do wysyłki | *(pusty)* |
| `MF_API_KEY` | Klucz API MF | *(pusty)* |
| `CERT_PATH` | Ścieżka do certyfikatu podpisu | *(pusty)* |
| `CERT_KEY_PATH` | Ścieżka do klucza prywatnego | *(pusty)* |
| `ENABLE_SUBMISSION` | Czy włączyć wysyłkę automatyczną | `False` |

---

## Import danych z Excel/CSV

Dla GLB-Z2 (jednostki D) i GIR (Summary) aplikacja obsługuje import z pliku Excel/CSV.

**Pobierz szablon Excel** z aplikacji (przycisk "Pobierz szablon Excel" w sekcji importu).

### Kolumny szablonu GLB-Z2 (Jednostki_D)

| Kolumna | Opis |
|---|---|
| Rodzaj jednostki (1/2) | 1 = UPE, 2 = wyznaczona |
| Pełna nazwa | Pełna nazwa prawna |
| Kraj nr ID (ISO) | Kod ISO 3166-1 alpha-2 |
| Rodzaj ID (1/2/3/4/8/9) | Rodzaj numeru identyfikacyjnego |
| Numer identyfikacyjny | Zagraniczny TIN lub inny numer |
| Kraj siedziby (ISO) | Kod ISO kraju siedziby |
| Miejscowość | Miasto siedziby |
| Kod pocztowy | Opcjonalnie |
| Ulica | Opcjonalnie |
| Nr domu | Opcjonalnie |
| Nr lokalu | Opcjonalnie |
| Inne dane adresowe | Opcjonalnie |
| Kod jurysdykcji (ISO) | Kod jurysdykcji lokalizacji |

---

## Moduł wysyłki (submission_adapter)

Interfejs posiada 4 metody:

```python
adapter.validate_before_submission(xml_bytes) → (bool, str)
adapter.sign_or_prepare_for_signature(xml_bytes) → (bytes, str)
adapter.submit(xml_bytes, form_type) → (bool, str)
adapter.get_status(reference_id) → (bool, str)
```

W wersji MVP metoda `submit()` zwraca instrukcję złożenia ręcznego.
Aby podpiąć realny endpoint MF:
1. Ustaw `MF_SUBMISSION_ENDPOINT` i `MF_API_KEY`
2. Zaimplementuj `sign_or_prepare_for_signature()` z podpisem kwalifikowanym
3. Zmień `ENABLE_SUBMISSION = True` w `config.py`

---

## Bezpieczeństwo

- ✅ Aplikacja działa **wyłącznie lokalnie** – nie wysyła danych do zewnętrznych API
- ✅ Dane wrażliwe (NIP, TIN) nie są logowane (`LOG_SENSITIVE_DATA = False`)
- ✅ Brak fikcyjnego podpisu – `sign_or_prepare_for_signature()` zwraca jasny komunikat
- ⚠️ Przed użyciem produkcyjnym zweryfikuj aktualność schematów XSD na: https://www.podatki.gov.pl

---

## Plan dalszego rozwoju

### Etap 2 – Pełne kalkulacje GIR
- [ ] Sekcja `JurisdictionSection` – pełne kalkulacje ETR
- [ ] Sekcja `LowTaxJurisdiction` – IIR/UTPR obliczenia
- [ ] Sekcja `UTPRAttribution` – alokacja UTPR
- [ ] Pełna walidacja XSD (ze schematami zależnymi MF)
- [ ] Formularz ZZ2 (załącznik do GLB-Z2)

### Etap 3 – Import Excel i produkcja
- [ ] Template Excel z logiką kalkulacyjną (ETR, SBIE)
- [ ] Walidacja krzyżowa między sekcjami
- [ ] Integracja z podpisem kwalifikowanym (np. xades4j, PyKCS11)
- [ ] Rzeczywisty endpoint MF / e-Deklaracje
- [ ] Historia złożeń i statusy UPO
- [ ] Multi-użytkownik / role (doradca vs. approver)

---

*⚠️ To narzędzie jest prototypem MVP. Przed użyciem produkcyjnym skonsultuj z działem podatkowym i IT w zakresie aktualności schematów XSD, wymogów podpisu i kanału wysyłki.*
