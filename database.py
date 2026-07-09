"""Veritabanı — kolon adları büyük harf, alt tireli."""

import sqlite3
from pathlib import Path

import pandas as pd

DB_PATH = Path(__file__).parent / "urunler.db"
ORNEK_CSV_YOLU = Path(__file__).parent / "ornek_urunler.csv"
KOLONLAR = ["ID", "ADI", "TIP", "BOY", "EN", "BIRIM", "FIYAT", "MONTAJ"]


def baglanti_al() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def tablo_olustur() -> None:
    with baglanti_al() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS URUNLER (
                ID INTEGER PRIMARY KEY,
                ADI TEXT NOT NULL,
                TIP TEXT NOT NULL,
                BOY TEXT,
                EN REAL,
                BIRIM TEXT,
                FIYAT REAL,
                MONTAJ REAL
            )
            """
        )


def tum_urunleri_getir() -> pd.DataFrame:
    tablo_olustur()
    with baglanti_al() as conn:
        df = pd.read_sql_query("SELECT * FROM URUNLER ORDER BY ID", conn)
    return df if not df.empty else pd.DataFrame(columns=KOLONLAR)


def toplu_guncelle(df: pd.DataFrame) -> None:
    eksik = [k for k in KOLONLAR if k not in df.columns]
    if eksik:
        raise ValueError(f"Eksik kolonlar: {', '.join(eksik)}")
    temiz = df[KOLONLAR].copy()
    tablo_olustur()
    with baglanti_al() as conn:
        conn.execute("DELETE FROM URUNLER")
        temiz.to_sql("URUNLER", conn, if_exists="append", index=False)


def tip_urunleri_getir(tip: str) -> pd.DataFrame:
    df = tum_urunleri_getir()
    if df.empty:
        return df
    tip_norm = tip.upper().replace("Ü", "U").replace("İ", "I")
    return df[
        df["TIP"].str.upper().str.replace("Ü", "U").str.replace("İ", "I") == tip_norm
    ].copy()


def urun_kaydi_getir(urun_id: int) -> dict | None:
    with baglanti_al() as conn:
        satir = conn.execute(
            "SELECT * FROM URUNLER WHERE ID = ?", (urun_id,)
        ).fetchone()
    return dict(satir) if satir else None


def csv_den_urunleri_oku() -> pd.DataFrame | None:
    """Repodaki ornek_urunler.csv dosyasını okur."""
    if not ORNEK_CSV_YOLU.exists():
        return None
    try:
        from dosya_okuma import DosyaOkumaHatasi, metin_oku

        df, _ = metin_oku(ORNEK_CSV_YOLU.read_text(encoding="utf-8-sig"))
        return df
    except (DosyaOkumaHatasi, OSError, ValueError):
        return None


def ornek_veri_yukle() -> None:
    """Veritabanı boşsa önce CSV'den, yoksa gömülü örnekten yükler."""
    if not tum_urunleri_getir().empty:
        return

    csv_df = csv_den_urunleri_oku()
    if csv_df is not None and not csv_df.empty:
        toplu_guncelle(csv_df)
        return

    ornek = pd.DataFrame(
        [
            [1, "Panel A", "ÜRÜN", "2.0", 100.0, "M", 150.0, 25.0],
            [2, "Panel A", "ÜRÜN", "0.1", 100.0, "M", 80.0, 15.0],
            [3, "PANJUR JALUZI 156CM", "ÜRÜN", "0.1", 156.0, "M", 110.0, 55.0],
            [4, "Direk Ayak", "AYAK", "0.5", 0.1, "ADET", 45.0, 0.0],
            [5, "Direk Ayak", "AYAK", "156CM", 0.1, "ADET", 55.0, 0.0],
        ],
        columns=KOLONLAR,
    )
    toplu_guncelle(ornek)
