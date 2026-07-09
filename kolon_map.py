"""DB kolonları (büyük harf, alt tireli) → uygulama değişkenleri (küçük harf, snake_case).

Yönetim tablosu kolonları: ID, ADI, TIP, BOY, EN, BIRIM, FIYAT, MONTAJ
Akışta kullanılan mantıksal adlar URUN_FIYAT, URUN_MONTAJ vb. ile eşlenir.
"""

# Mantıksal DB kolon adları → fiziksel tablo kolonları
URUN_FIYAT = "FIYAT"
URUN_MONTAJ = "MONTAJ"
URUN_EN = "EN"
URUN_BOY = "BOY"
AYAK_FIYAT = "FIYAT"
AYAK_EN = "EN"
AYAK_BOY = "BOY"


def urun_kaydini_map_et(kayit: dict) -> dict:
    """URUN_FIYAT → urun_fiyat, URUN_MONTAJ → montaj_fiyat, URUN_EN → urun_en, URUN_BOY → urun_boy"""
    return {
        "urun_fiyat": float(kayit.get(URUN_FIYAT) or 0),
        "montaj_fiyat": float(kayit.get(URUN_MONTAJ) or 0),
        "urun_en": float(kayit.get(URUN_EN) or 0),
        "urun_boy": str(kayit.get(URUN_BOY) or ""),
    }


def ayak_kaydini_map_et(kayit: dict) -> dict:
    """AYAK_FIYAT → ayak_fiyat, AYAK_EN → ayak_en, AYAK_BOY → ayak_boy"""
    return {
        "ayak_fiyat": float(kayit.get(AYAK_FIYAT) or 0),
        "ayak_en": float(kayit.get(AYAK_EN) or 0),
        "ayak_boy": str(kayit.get(AYAK_BOY) or ""),
    }
