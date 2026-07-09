"""CSV / Excel dosyalarını Türkçe Excel ayarlarına uygun okur."""

import csv
import io
import re
from typing import BinaryIO

import pandas as pd

from database import KOLONLAR

KOLON_ESLEMELERI = {
    "ID": ["ID", "KOD", "NO", "SIRA", "SIRA_NO"],
    "ADI": ["ADI", "AD", "ADİ", "ISIM", "İSİM", "URUN_ADI", "ÜRÜN_ADI", "NAME"],
    "TIP": ["TIP", "TİP", "TUR", "TÜR", "TYPE", "KATEGORI", "KATEGORİ"],
    "BOY": ["BOY", "UZUNLUK", "OLCU", "ÖLÇÜ", "BOYUT"],
    "EN": ["EN", "GENISLIK", "GENİŞLİK", "WIDTH"],
    "BIRIM": ["BIRIM", "BİRİM", "UNIT"],
    "FIYAT": ["FIYAT", "FİYAT", "PRICE", "URUN_FIYAT", "ÜRÜN_FİYAT"],
    "MONTAJ": ["MONTAJ", "ISCILIK", "İŞÇİLİK", "MONTAJ_FIYAT", "MONTAJ_FİYAT"],
}

SAYISAL_KOLONLAR = ["ID", "EN", "FIYAT", "MONTAJ"]
ENCODING_ADAYLARI = ("utf-8-sig", "cp1254", "utf-8", "latin-1")
AYRAC_ADAYLARI = (";", ",", "\t", "|")
BEKLENEN_ALAN_SAYISI = len(KOLONLAR)
OKUYUCU_SURUM = "3.3"


class DosyaOkumaHatasi(ValueError):
    """Kullanıcıya gösterilecek dosya okuma hatası."""


def _kolon_adi_normalize(metin: str) -> str:
    metin = str(metin).strip().upper()
    metin = (
        metin.replace("İ", "I")
        .replace("Ş", "S")
        .replace("Ğ", "G")
        .replace("Ü", "U")
        .replace("Ö", "O")
        .replace("Ç", "C")
    )
    return re.sub(r"[^A-Z0-9_]", "_", metin)


def _satir_ayir(metin: str, ayirac: str) -> list[str]:
    try:
        okuyucu = csv.reader(
            [metin],
            delimiter=ayirac,
            quotechar='"',
            doublequote=True,
            skipinitialspace=True,
        )
        return [a.strip() for a in next(okuyucu, [])]
    except csv.Error:
        return [p.strip() for p in metin.split(ayirac)]


def _satir_veri_satirimi(satir: str, ayirac: str) -> bool:
    alanlar = _satir_ayir(satir, ayirac)
    if len(alanlar) != BEKLENEN_ALAN_SAYISI:
        return False
    ilk = _kolon_adi_normalize(alanlar[0])
    if ilk == "ID":
        return False
    return alanlar[0].strip().isdigit()


def _satirlari_temizle(satirlar: list[str]) -> tuple[list[str], str | None]:
    """Excel metadata satırlarını atlar; varsa Sep= ayırıcını döndürür."""
    temiz: list[str] = []
    zorunlu_ayrac: str | None = None

    for satir in satirlar:
        satir = satir.strip("\r\n")
        if not satir.strip():
            continue
        ust = satir.strip().upper()
        if ust.startswith("SEP="):
            zorunlu_ayrac = satir.split("=", 1)[1].strip()
            continue
        if ust.startswith(("\ufeff",)):
            satir = satir.lstrip("\ufeff")
        temiz.append(satir)

    return temiz, zorunlu_ayrac


def _ayrac_puanla(satirlar: list[str], ayirac: str) -> tuple[int, int]:
    dogru = 0
    puan = 0

    for satir in satirlar:
        alanlar = _satir_ayir(satir, ayirac)
        alan_sayisi = len(alanlar)
        veri = _satir_veri_satirimi(satir, ayirac)

        if alan_sayisi == BEKLENEN_ALAN_SAYISI:
            dogru += 1
            puan += 30 if veri else 10
        elif veri:
            puan -= 50
        elif alan_sayisi > 1:
            puan -= abs(alan_sayisi - BEKLENEN_ALAN_SAYISI) * 2

    if ayirac == ";":
        noktali_virgul_satiri = sum(1 for s in satirlar if s.count(";") >= 7)
        puan += noktali_virgul_satiri * 15

    return puan, dogru


def _en_iyi_ayrac_bul(satirlar: list[str], zorunlu_ayrac: str | None = None) -> str:
    if zorunlu_ayrac:
        return zorunlu_ayrac

    if any(s.count(";") >= 7 for s in satirlar):
        puan_noktali, dogru_noktali = _ayrac_puanla(satirlar, ";")
        if dogru_noktali > 0 or puan_noktali > 0:
            return ";"

    en_iyi_ayrac = ";"
    en_iyi_puan = float("-inf")
    en_iyi_dogru = -1

    for ayirac in AYRAC_ADAYLARI:
        puan, dogru = _ayrac_puanla(satirlar, ayirac)
        if dogru > en_iyi_dogru or (dogru == en_iyi_dogru and puan > en_iyi_puan):
            en_iyi_ayrac = ayirac
            en_iyi_puan = puan
            en_iyi_dogru = dogru

    if en_iyi_dogru <= 0:
        if any(s.count(";") >= 7 for s in satirlar):
            return ";"
        raise DosyaOkumaHatasi(
            "Dosya okunamadı: 8 kolonlu veri satırı bulunamadı. "
            f"Beklenen format: ID;ADI;TIP;BOY;EN;BIRIM;FIYAT;MONTAJ"
        )
    return en_iyi_ayrac


def _metin_coz(ham: bytes) -> tuple[str, str]:
    son_hata: Exception | None = None
    for encoding in ENCODING_ADAYLARI:
        try:
            return ham.decode(encoding), encoding
        except UnicodeDecodeError as exc:
            son_hata = exc
    raise DosyaOkumaHatasi(
        "Dosya kodlaması okunamadı. Dosyayı UTF-8 veya Excel CSV olarak kaydedin."
    ) from son_hata


def _baslik_satirimi(alanlar: list[str]) -> bool:
    normalize = {_kolon_adi_normalize(a) for a in alanlar}
    bilinen = {_kolon_adi_normalize(k) for k in KOLONLAR}
    for adaylar in KOLON_ESLEMELERI.values():
        bilinen.update(_kolon_adi_normalize(a) for a in adaylar)
    return len(normalize & bilinen) >= 3


def _csv_satirlari_dataframe_yap(
    satirlar: list[str], ayirac: str
) -> tuple[pd.DataFrame, int, list[str]]:
    veri_satirlari: list[list[str]] = []
    atlanan = 0
    atlanan_ornekler: list[str] = []
    baslik_var = False
    kolonlar: list[str] = []

    for satir in satirlar:
        alanlar = _satir_ayir(satir, ayirac)
        if not any(a.strip() for a in alanlar):
            continue
        if len(alanlar) != BEKLENEN_ALAN_SAYISI:
            atlanan += 1
            if len(atlanan_ornekler) < 3:
                atlanan_ornekler.append(satir[:80])
            continue
        if not baslik_var and _baslik_satirimi(alanlar):
            baslik_var = True
            kolonlar = [_kolon_adi_normalize(a) for a in alanlar]
            continue
        veri_satirlari.append(alanlar)

    if not veri_satirlari:
        mesaj = (
            f"Dosya okunamadı: {BEKLENEN_ALAN_SAYISI} kolonlu geçerli satır yok. "
            f"Kullanılan ayraç: {repr(ayirac)}"
        )
        if atlanan_ornekler:
            mesaj += f". Atlanan örnek: {atlanan_ornekler[0]!r}"
        raise DosyaOkumaHatasi(mesaj)

    if baslik_var:
        df = pd.DataFrame(veri_satirlari, columns=kolonlar)
    else:
        df = pd.DataFrame(veri_satirlari, columns=KOLONLAR)

    return df, atlanan, atlanan_ornekler


def _tip_normalize(tip: str) -> str:
    ascii_tip = _kolon_adi_normalize(tip)
    if ascii_tip == "URUN":
        return "ÜRÜN"
    if ascii_tip == "AYAK":
        return "AYAK"
    return str(tip).strip().upper()


def _kolonlari_esle(df: pd.DataFrame) -> pd.DataFrame:
    ham_kolonlar = list(df.columns)
    yeni_kolonlar: dict[str, str] = {}

    for hedef in KOLONLAR:
        for ham in ham_kolonlar:
            normalize_ham = _kolon_adi_normalize(ham)
            adaylar = [_kolon_adi_normalize(a) for a in KOLON_ESLEMELERI[hedef]]
            if normalize_ham == _kolon_adi_normalize(hedef) or normalize_ham in adaylar:
                yeni_kolonlar[ham] = hedef
                break

    if len(yeni_kolonlar) < len(KOLONLAR):
        if len(df.columns) == len(KOLONLAR):
            df.columns = KOLONLAR
            return df
        eksik = [k for k in KOLONLAR if k not in yeni_kolonlar.values()]
        raise DosyaOkumaHatasi(
            "Kolon eşleşmesi yapılamadı. Eksik kolonlar: "
            + ", ".join(eksik)
            + f". Dosyadaki kolonlar: {', '.join(str(c) for c in ham_kolonlar)}"
        )

    df = df.rename(columns=yeni_kolonlar)
    return df[KOLONLAR].copy()


def _sayisal_deger_cevir(deger) -> float | int | None:
    if pd.isna(deger):
        return None
    if isinstance(deger, (int, float)):
        return deger
    metin = str(deger).strip()
    if not metin:
        return None
    metin = metin.replace(" ", "")
    if "," in metin and "." in metin:
        if metin.rfind(",") > metin.rfind("."):
            metin = metin.replace(".", "").replace(",", ".")
        else:
            metin = metin.replace(",", "")
    else:
        metin = metin.replace(",", ".")
    try:
        sayi = float(metin)
        if sayi.is_integer():
            return int(sayi)
        return sayi
    except ValueError:
        return None


def _sayisal_kolonlari_temizle(df: pd.DataFrame) -> pd.DataFrame:
    temiz = df.copy()
    for kolon in SAYISAL_KOLONLAR:
        if kolon in temiz.columns:
            temiz[kolon] = temiz[kolon].map(_sayisal_deger_cevir)
    return temiz


def _dataframe_son_isle(df: pd.DataFrame) -> pd.DataFrame:
    df = df.dropna(how="all")
    if df.empty:
        raise DosyaOkumaHatasi("Dosya boş veya okunabilir satır bulunamadı.")

    df.columns = [_kolon_adi_normalize(c) for c in df.columns]
    df = _kolonlari_esle(df)
    df = _sayisal_kolonlari_temizle(df)
    df["ADI"] = df["ADI"].astype(str).str.strip()
    df["TIP"] = df["TIP"].map(_tip_normalize)
    df["BOY"] = df["BOY"].astype(str).str.strip()
    df["BIRIM"] = df["BIRIM"].fillna("").astype(str).str.strip()

    if df["ID"].isna().any():
        df["ID"] = range(1, len(df) + 1)

    return df


def metin_oku(metin: str) -> tuple[pd.DataFrame, str]:
    """Panoya yapıştırılan metni okur."""
    satirlar = metin.splitlines()
    temiz, zorunlu_ayrac = _satirlari_temizle(satirlar)
    if not temiz:
        raise DosyaOkumaHatasi("Yapıştırılan metin boş.")

    ayirac = _en_iyi_ayrac_bul(temiz, zorunlu_ayrac)
    df, atlanan, _ = _csv_satirlari_dataframe_yap(temiz, ayirac)
    df = _dataframe_son_isle(df)

    bilgi = f"metin, ayraç={repr(ayirac)}"
    if atlanan:
        bilgi += f", {atlanan} satır atlandı"
    return df, bilgi


def _csv_oku(ham: bytes) -> tuple[pd.DataFrame, str]:
    metin, encoding = _metin_coz(ham)
    satirlar = metin.splitlines()
    temiz, zorunlu_ayrac = _satirlari_temizle(satirlar)
    if not temiz:
        raise DosyaOkumaHatasi("Dosya boş.")

    ayirac = _en_iyi_ayrac_bul(temiz, zorunlu_ayrac)
    df, atlanan, atlanan_ornekler = _csv_satirlari_dataframe_yap(temiz, ayirac)
    df = _dataframe_son_isle(df)

    ayirac_adi = {";": "noktalı virgül (;)", ",": "virgül (,)", "\t": "tab", "|": "pipe (|)"}.get(
        ayirac, ayirac
    )
    bilgi = f"kodlama={encoding}, ayraç={ayirac_adi}, okuyucu v{OKUYUCU_SURUM}"
    if atlanan:
        bilgi += f", {atlanan} satır atlandı"
        if atlanan_ornekler:
            bilgi += f" (ör: {atlanan_ornekler[0][:50]}...)"
    return df, bilgi


def _excel_oku(dosya: BinaryIO) -> pd.DataFrame:
    try:
        df = pd.read_excel(dosya, engine="openpyxl", dtype=str)
    except ImportError as exc:
        raise DosyaOkumaHatasi(
            "Excel dosyası okunamadı. openpyxl gerekli: py -m pip install openpyxl"
        ) from exc
    except Exception as exc:
        raise DosyaOkumaHatasi(f"Excel dosyası okunamadı: {exc}") from exc

    df.columns = [_kolon_adi_normalize(c) for c in df.columns]
    return df


def _dosya_turu_belirle(ham: bytes, dosya_adi: str) -> str:
    if ham[:2] == b"PK":
        return "excel"
    if ham[:4] == b"\xd0\xcf\x11\xe0":
        return "excel"
    ad = dosya_adi.lower()
    if ad.endswith((".xlsx", ".xls")):
        return "excel"
    return "csv"


def dosya_oku(dosya) -> tuple[pd.DataFrame, str]:
    """Yüklenen dosyayı DataFrame ve okuma bilgisi olarak döndürür."""
    dosya_adi = (dosya.name or "").lower()
    ham = dosya.getvalue() if hasattr(dosya, "getvalue") else dosya.read()

    tur = _dosya_turu_belirle(ham, dosya_adi)

    if tur == "excel":
        try:
            df = _excel_oku(io.BytesIO(ham))
            df = _dataframe_son_isle(df)
            return df, f"Excel, okuyucu v{OKUYUCU_SURUM}"
        except DosyaOkumaHatasi:
            pass

    return _csv_oku(ham)
