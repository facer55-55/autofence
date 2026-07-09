"""Hesaplama fonksiyonları — değişkenler küçük harf, snake_case."""

import math
from dataclasses import dataclass


def aralik_sayiya_cevir(aralik: str) -> float:
    try:
        return float(str(aralik).replace(",", ".").strip())
    except ValueError:
        return 1.0


def boy_sayiya_cevir(boy: str) -> float:
    metin = str(boy).upper().replace("CM", "").replace(",", ".").strip()
    try:
        return float(metin)
    except ValueError:
        return 1.0


def hesapla_direk_sayisi(uygulama_uzunluk: float, uygulama_aralik: float) -> int:
    """uygulama_uzunluk / uygulama_aralik — küsüratlıysa yukarı yuvarla, sonra +1."""
    if uygulama_aralik <= 0:
        return 0
    sonuc = uygulama_uzunluk / uygulama_aralik
    if not math.isclose(sonuc, round(sonuc)):
        sonuc = math.ceil(sonuc)
    else:
        sonuc = int(sonuc)
    return sonuc + 1


def urun_sayisini_yuvarla(sonuc: float) -> int:
    """Toplam ürün sayısı için tek seferlik yukarı yuvarlama."""
    if not math.isclose(sonuc, round(sonuc)):
        return math.ceil(sonuc)
    return int(sonuc)


def hesapla_urun_sayisi_ham_panel(
    uygulama_uzunluk: float, urun_en: float, panjur_sayisi: float
) -> float:
    """Panel ham: (uzunluk / (en/100)) × panjur — yuvarlama yok."""
    en_bolen = urun_en / 100
    if en_bolen <= 0:
        return 0.0
    return (uygulama_uzunluk / en_bolen) * panjur_sayisi


def hesapla_urun_sayisi_ham_cim(uygulama_uzunluk: float, urun_en: float) -> float:
    """Çim ham: uzunluk / urun_en — yuvarlama yok."""
    if urun_en <= 0:
        return 0.0
    return uygulama_uzunluk / urun_en


def hesapla_panjur_sayisi(ayak_boy: str, urun_boy: str) -> float:
    """panjur_sayisi = ayak_boy / urun_boy"""
    urun_boy_sayi = boy_sayiya_cevir(urun_boy)
    if urun_boy_sayi <= 0:
        return 1.0
    return boy_sayiya_cevir(ayak_boy) / urun_boy_sayi


def panel_en_mi(urun_en: float) -> bool:
    """urun_en == 156 ise panel formülleri uygulanır."""
    return math.isclose(float(urun_en), 156.0)


def cim_en_mi(urun_en: float) -> bool:
    """urun_en < 156 ise çim formülleri uygulanır."""
    return float(urun_en) < 156.0


def hesapla_iscilik_panel(
    uygulama_uzunluk: float, ayak_boy: str, montaj_fiyat: float
) -> float:
    """Panel: (uygulama_uzunluk × montaj_fiyat) × ayak_boy"""
    return (uygulama_uzunluk * montaj_fiyat) * boy_sayiya_cevir(ayak_boy)


def hesapla_iscilik_cim(
    uygulama_uzunluk: float, urun_boy: str, montaj_fiyat: float
) -> float:
    """Çim: uygulama_uzunluk × urun_boy × montaj_fiyat"""
    return uygulama_uzunluk * boy_sayiya_cevir(urun_boy) * montaj_fiyat


def hesapla_urun_ucreti_panel(uygulama_urun_sayisi: int, urun_fiyat: float) -> float:
    """Panel: uygulama_urun_sayisi × urun_fiyat"""
    return uygulama_urun_sayisi * urun_fiyat


def hesapla_urun_ucreti_cim(
    uygulama_urun_sayisi: int, urun_boy: str, urun_en: float, urun_fiyat: float
) -> float:
    """Çim: uygulama_urun_sayisi × urun_boy × urun_en × urun_fiyat"""
    return (
        uygulama_urun_sayisi
        * boy_sayiya_cevir(urun_boy)
        * urun_en
        * urun_fiyat
    )


def hesapla_direk_ucreti(uygulama_direk_sayisi: int, ayak_fiyat: float) -> float:
    """uygulama_direk_sayisi × ayak_fiyat"""
    return uygulama_direk_sayisi * ayak_fiyat


@dataclass
class HesapSonucu:
    """Tek uzunluk satırı — ürün sayısı ham tutulur, yuvarlama toplamda yapılır."""
    uygulama_urun_sayisi_ham: float
    uygulama_uzunluk: float
    uygulama_direk_ucreti: float
    uygulama_iscilik: float
    uygulama_direk_sayisi: int
    panjur_sayisi: float


@dataclass
class ToplamHesapSonucu:
    satirlar: list[HesapSonucu]
    toplam_urun_sayisi: int
    toplam_direk_sayisi: int
    toplam_urun_ucreti: float
    toplam_direk_ucreti: float
    toplam_iscilik: float
    toplam_ucret: float
    panjur_sayisi: float
    panel_mi: bool


def hesapla_satir_maliyet(
    uygulama_uzunluk: float,
    uygulama_aralik: str,
    urun_en: float,
    urun_boy: str,
    montaj_fiyat: float,
    ayak_boy: str,
    ayak_fiyat: float,
    panjur_sayisi: float,
) -> HesapSonucu:
    """Tek uzunluk için direk ve işçilik hesaplar; ürün sayısı ham bırakılır."""
    aralik_sayi = aralik_sayiya_cevir(uygulama_aralik)
    uygulama_direk_sayisi = hesapla_direk_sayisi(uygulama_uzunluk, aralik_sayi)
    uygulama_direk_ucreti = hesapla_direk_ucreti(uygulama_direk_sayisi, ayak_fiyat)

    if panel_en_mi(urun_en):
        uygulama_urun_sayisi_ham = hesapla_urun_sayisi_ham_panel(
            uygulama_uzunluk, urun_en, panjur_sayisi
        )
        uygulama_iscilik = hesapla_iscilik_panel(
            uygulama_uzunluk, ayak_boy, montaj_fiyat
        )
    else:
        uygulama_urun_sayisi_ham = hesapla_urun_sayisi_ham_cim(
            uygulama_uzunluk, urun_en
        )
        uygulama_iscilik = hesapla_iscilik_cim(
            uygulama_uzunluk, urun_boy, montaj_fiyat
        )

    return HesapSonucu(
        uygulama_urun_sayisi_ham=uygulama_urun_sayisi_ham,
        uygulama_uzunluk=uygulama_uzunluk,
        uygulama_direk_ucreti=uygulama_direk_ucreti,
        uygulama_iscilik=uygulama_iscilik,
        uygulama_direk_sayisi=uygulama_direk_sayisi,
        panjur_sayisi=panjur_sayisi,
    )


def hesapla_toplam_maliyet(
    uygulama_uzunluk: float,
    uygulama_aralik: str,
    urun_en: float,
    urun_boy: str,
    urun_fiyat: float,
    montaj_fiyat: float,
    ayak_boy: str,
    ayak_fiyat: float,
) -> ToplamHesapSonucu:
    """Tek veya çoklu uzunluk için ana giriş noktası."""
    return hesapla_coklu_maliyet(
        uygulama_uzunluklar=[uygulama_uzunluk],
        uygulama_aralik=uygulama_aralik,
        urun_en=urun_en,
        urun_boy=urun_boy,
        urun_fiyat=urun_fiyat,
        montaj_fiyat=montaj_fiyat,
        ayak_boy=ayak_boy,
        ayak_fiyat=ayak_fiyat,
    )


def hesapla_coklu_maliyet(
    uygulama_uzunluklar: list[float],
    uygulama_aralik: str,
    urun_en: float,
    urun_boy: str,
    urun_fiyat: float,
    montaj_fiyat: float,
    ayak_boy: str,
    ayak_fiyat: float,
) -> ToplamHesapSonucu:
    """Her uzunluk ayrı hesaplanır; ürün sayısı yuvarlaması en sonda toplamda yapılır."""
    panjur_sayisi = hesapla_panjur_sayisi(ayak_boy, urun_boy)
    panel_mi = panel_en_mi(urun_en)

    satirlar: list[HesapSonucu] = []
    for uzunluk in uygulama_uzunluklar:
        if uzunluk <= 0:
            continue
        satirlar.append(
            hesapla_satir_maliyet(
                uygulama_uzunluk=uzunluk,
                uygulama_aralik=uygulama_aralik,
                urun_en=urun_en,
                urun_boy=urun_boy,
                montaj_fiyat=montaj_fiyat,
                ayak_boy=ayak_boy,
                ayak_fiyat=ayak_fiyat,
                panjur_sayisi=panjur_sayisi,
            )
        )

    if not satirlar:
        raise ValueError("En az bir geçerli uygulama_uzunluk girilmelidir.")

    ham_urun_toplami = sum(s.uygulama_urun_sayisi_ham for s in satirlar)
    toplam_urun_sayisi = urun_sayisini_yuvarla(ham_urun_toplami)

    if panel_mi:
        toplam_urun_ucreti = hesapla_urun_ucreti_panel(toplam_urun_sayisi, urun_fiyat)
    else:
        toplam_urun_ucreti = hesapla_urun_ucreti_cim(
            toplam_urun_sayisi, urun_boy, urun_en, urun_fiyat
        )

    toplam_direk_ucreti = sum(s.uygulama_direk_ucreti for s in satirlar)
    toplam_iscilik = sum(s.uygulama_iscilik for s in satirlar)
    toplam_ucret = toplam_urun_ucreti + toplam_direk_ucreti + toplam_iscilik

    return ToplamHesapSonucu(
        satirlar=satirlar,
        toplam_urun_sayisi=toplam_urun_sayisi,
        toplam_direk_sayisi=sum(s.uygulama_direk_sayisi for s in satirlar),
        toplam_urun_ucreti=toplam_urun_ucreti,
        toplam_direk_ucreti=toplam_direk_ucreti,
        toplam_iscilik=toplam_iscilik,
        toplam_ucret=toplam_ucret,
        panjur_sayisi=panjur_sayisi,
        panel_mi=panel_mi,
    )
