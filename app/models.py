"""
Modele danych dla formularzy GLB-Z2 i GIR.
"""
from __future__ import annotations
from typing import Optional, List
from pydantic import BaseModel, Field


# ════════════════════════════════════════════════════════════════════════════
#  GLB-Z2
# ════════════════════════════════════════════════════════════════════════════

class GLBZ2_Podmiot1(BaseModel):
    """Dane identyfikacyjne jednostki składającej zawiadomienie (Podmiot1)."""
    nip: str = Field("", description="NIP jednostki składającej (10 cyfr)")
    pelna_nazwa: str = Field("", description="Pełna nazwa jednostki składającej")

class GLBZ2_JednostkaD(BaseModel):
    """Dane jednej jednostki składowej (sekcja D, element P_D)."""
    rodzaj_jednostki: str = Field("1", description="Rodzaj jednostki: 1 lub 2")
    pelna_nazwa: str = Field("", description="Pełna nazwa jednostki")
    kraj_id: str = Field("", description="Kod państwa wydania nr identyfikacyjnego (ISO 3166-1 alpha-2)")
    rodzaj_id: str = Field("1", description="Rodzaj zagranicznego nr id")
    nr_id: str = Field("", description="Zagraniczny numer identyfikacyjny")
    adres_kraj: str = Field("", description="Kraj/terytorium siedziby")
    adres_miejscowosc: str = Field("", description="Miejscowość siedziby")
    adres_kod: str = Field("", description="Kod pocztowy (opcjonalnie)")
    adres_ulica: str = Field("", description="Ulica (opcjonalnie)")
    adres_nr_budynku: str = Field("", description="Nr domu (opcjonalnie)")
    adres_nr_lokalu: str = Field("", description="Nr lokalu (opcjonalnie)")
    adres_inne: str = Field("", description="Inne dane adresowe (opcjonalnie)")
    kod_jurysdykcji: str = Field("", description="Kod jurysdykcji lokalizacji jednostki")

class GLBZ2_PozycjeSzczegolowe(BaseModel):
    nazwa_grupy: str = Field("", description="Nazwa grupy (P_7)")
    rodzaj_jednostki_skladajacej: str = Field("1", description="Rodzaj jednostki składającej: 1 lub 2 (P_8)")
    jednostki_d: List[GLBZ2_JednostkaD] = Field(default_factory=list)
    liczba_zalacznikow: Optional[int] = Field(None, description="Liczba składanych załączników GLB/ZZ2")
    email: str = Field("", description="Adres e-mail kontaktowy")
    telefon: str = Field("", description="Telefon kontaktowy")

class GLBZ2_Naglowek(BaseModel):
    okres_od: str = Field("", description="Pierwszy dzień okresu (RRRR-MM-DD)")
    okres_do: str = Field("", description="Ostatni dzień okresu (RRRR-MM-DD)")

class GLBZ2_Form(BaseModel):
    """Kompletny model formularza GLB-Z2."""
    naglowek: GLBZ2_Naglowek = Field(default_factory=GLBZ2_Naglowek)
    podmiot1: GLBZ2_Podmiot1 = Field(default_factory=GLBZ2_Podmiot1)
    pozycje: GLBZ2_PozycjeSzczegolowe = Field(default_factory=GLBZ2_PozycjeSzczegolowe)


# ════════════════════════════════════════════════════════════════════════════
#  GIR  (MVP – Etap 1)
# ════════════════════════════════════════════════════════════════════════════

class GIR_FilingCE(BaseModel):
    kraj: str = Field("PL", description="Kod kraju rejestracji jednostki składającej GIR")
    nazwa: str = Field("", description="Nazwa jednostki składającej GIR")
    tin: str = Field("", description="TIN (numer identyfikacji podatkowej) jednostki składającej")
    rola: str = Field("UPE", description="Rola jednostki składającej (UPE / Designated / Local)")

class GIR_AccountingInfo(BaseModel):
    cfs_upe: str = Field("IFRS", description="Standard rachunkowości (IFRS/GAAP/etc.)")
    fas: str = Field("", description="Standardy rachunkowości – opis")
    waluta: str = Field("EUR", description="Waluta sprawozdawcza (kod ISO 4217)")

class GIR_FilingInfo(BaseModel):
    filing_ce: GIR_FilingCE = Field(default_factory=GIR_FilingCE)
    accounting_info: GIR_AccountingInfo = Field(default_factory=GIR_AccountingInfo)
    okres_od: str = Field("", description="Początek roku fiskalnego (RRRR-MM-DD)")
    okres_do: str = Field("", description="Koniec roku fiskalnego (RRRR-MM-DD)")
    nazwa_mne: str = Field("", description="Nazwa grupy MNE")
    uwagi: str = Field("", description="Dodatkowe informacje (opcjonalnie)")
    doc_ref_id: str = Field("", description="DocRefId – unikalny identyfikator dokumentu")
    doc_type: str = Field("OECD1", description="DocTypeIndic (OECD1=nowy, OECD2=korekta, OECD3=usunięcie)")

class GIR_UPE(BaseModel):
    tin: str = Field("", description="TIN jednostki dominującej najwyższego szczebla")
    kraj: str = Field("", description="Kraj rejestracji UPE")
    nazwa: str = Field("", description="Nazwa UPE")

class GIR_Summary_Jurysdykcja(BaseModel):
    kod_jurysdykcji: str = Field("", description="Kod jurysdykcji (ISO 3166-1)")
    safe_harbour: str = Field("", description="Rodzaj Safe Harbour (opcjonalnie)")
    etr_range: str = Field("", description="Przedział ETR (opcjonalnie)")
    globe_tut: str = Field("", description="GloBE Top-up Tax (opcjonalnie)")
    doc_ref_id: str = Field("", description="DocRefId sekcji Summary")
    doc_type: str = Field("OECD1", description="DocTypeIndic")

class GIR_Form(BaseModel):
    """Kompletny model formularza GIR (MVP Etap 1)."""
    # Nagłówek
    okres_od: str = Field("", description="Pierwszy dzień okresu")
    okres_do: str = Field("", description="Ostatni dzień okresu")
    # Podmiot1
    nip: str = Field("", description="NIP podmiotu składającego w Polsce")
    pelna_nazwa: str = Field("", description="Pełna nazwa podmiotu składającego")
    # GLOBEBody / FilingInfo
    filing_info: GIR_FilingInfo = Field(default_factory=GIR_FilingInfo)
    # GeneralSection – uproszczona lista UPE/jurysdykcji
    jurysdykcje_rec: List[str] = Field(default_factory=list, description="Kody jurysdykcji RecJurCode")
    upe_lista: List[GIR_UPE] = Field(default_factory=list, description="Lista jednostek UPE")
    # Summary
    summary_lista: List[GIR_Summary_Jurysdykcja] = Field(default_factory=list)
