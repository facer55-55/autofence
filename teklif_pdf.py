"""PDF teklif formu oluşturma."""

from __future__ import annotations

import re
import urllib.request
from datetime import date
from io import BytesIO
from pathlib import Path

from fpdf import FPDF

from hesaplama import ToplamHesapSonucu

PDF_SABLON_SURUM = "2"

FONT_DIZINI = Path(__file__).parent / "fonts"
FONT_NORMAL = FONT_DIZINI / "Arial.ttf"
FONT_KALIN = FONT_DIZINI / "Arial-Bold.ttf"
FONT_URL = (
    "https://github.com/dejavu-fonts/dejavu-fonts/raw/version_2_37/ttf/DejaVuSans.ttf"
)
FONT_KALIN_URL = (
    "https://github.com/dejavu-fonts/dejavu-fonts/raw/version_2_37/ttf/DejaVuSans-Bold.ttf"
)

SISTEM_FONT_ADAYLARI: list[tuple[Path, Path]] = [
    (FONT_NORMAL, FONT_KALIN),
    (
        Path(r"C:\Windows\Fonts\arial.ttf"),
        Path(r"C:\Windows\Fonts\arialbd.ttf"),
    ),
    (
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
    ),
    (
        Path("/usr/share/fonts/TTF/DejaVuSans.ttf"),
        Path("/usr/share/fonts/TTF/DejaVuSans-Bold.ttf"),
    ),
]


def _fontlari_hazirla() -> tuple[str, str]:
    for normal, kalin in SISTEM_FONT_ADAYLARI:
        if normal.exists() and kalin.exists():
            return str(normal), str(kalin)

    FONT_DIZINI.mkdir(parents=True, exist_ok=True)
    if not FONT_NORMAL.exists() or not FONT_KALIN.exists():
        try:
            if not FONT_NORMAL.exists():
                urllib.request.urlretrieve(FONT_URL, FONT_NORMAL)
            if not FONT_KALIN.exists():
                urllib.request.urlretrieve(FONT_KALIN_URL, FONT_KALIN)
        except OSError as exc:
            raise RuntimeError(
                "PDF font dosyası bulunamadı. fonts/ klasörüne Arial.ttf ekleyin."
            ) from exc

    return str(FONT_NORMAL), str(FONT_KALIN)


def _dosya_adi_temizle(musteri_adi: str) -> str:
    temiz = re.sub(r"[^\w\s-]", "", musteri_adi, flags=re.UNICODE).strip()
    temiz = re.sub(r"\s+", "_", temiz)
    return temiz or "musteri"


def _para_format(tutar: float) -> str:
    return f"{tutar:,.2f} TL".replace(",", "X").replace(".", ",").replace("X", ".")


class TeklifPdf(FPDF):
    def footer(self):
        self.set_y(-15)
        self.set_font("Teklif", "", 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 10, f"Sayfa {self.page_no()}", align="C")


def olustur_teklif_pdf(
    musteri_adi: str,
    uygulama_urun: str,
    uygulama_ayak: str,
    uygulama_aralik: str,
    sonuc: ToplamHesapSonucu,
) -> bytes:
    """Hesap sonuçlarından müşteri adlı PDF teklif döndürür."""
    font_normal, font_kalin = _fontlari_hazirla()
    pdf = TeklifPdf()
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()
    pdf.add_font("Teklif", "", font_normal)
    pdf.add_font("Teklif", "B", font_kalin)
    pdf.set_font("Teklif", "", 11)

    pdf.set_font("Teklif", "B", 18)
    pdf.cell(0, 12, "TEKLİF FORMU", ln=True, align="C")
    pdf.ln(4)

    pdf.set_font("Teklif", "", 11)
    pdf.cell(0, 7, f"Müşteri: {musteri_adi}", ln=True)
    pdf.cell(0, 7, f"Tarih: {date.today().strftime('%d.%m.%Y')}", ln=True)
    pdf.ln(4)

    pdf.set_font("Teklif", "B", 12)
    pdf.cell(0, 8, "Proje Bilgileri", ln=True)
    pdf.set_font("Teklif", "", 10)
    pdf.cell(0, 6, f"Ürün: {uygulama_urun}", ln=True)
    pdf.cell(0, 6, f"Ayak: {uygulama_ayak}", ln=True)
    pdf.cell(0, 6, f"Direk aralığı: {uygulama_aralik} m", ln=True)
    pdf.ln(4)

    pdf.set_font("Teklif", "B", 12)
    pdf.cell(0, 8, "Uzunluk Detayları", ln=True)
    pdf.set_font("Teklif", "B", 9)
    kolonlar = ["Sıra", "Uzunluk (m)", "Ürün (ham)", "Direk", "Direk (TL)", "İşçilik (TL)"]
    genislikler = [12, 28, 30, 18, 32, 32]
    for baslik, gen in zip(kolonlar, genislikler):
        pdf.cell(gen, 7, baslik, border=1, align="C")
    pdf.ln()

    pdf.set_font("Teklif", "", 9)
    for i, satir in enumerate(sonuc.satirlar, start=1):
        pdf.cell(12, 7, str(i), border=1, align="C")
        pdf.cell(28, 7, f"{satir.uygulama_uzunluk:,.2f}", border=1, align="R")
        pdf.cell(30, 7, f"{satir.uygulama_urun_sayisi_ham:,.4f}", border=1, align="R")
        pdf.cell(18, 7, str(satir.uygulama_direk_sayisi), border=1, align="C")
        pdf.cell(32, 7, _para_format(satir.uygulama_direk_ucreti), border=1, align="R")
        pdf.cell(32, 7, _para_format(satir.uygulama_iscilik), border=1, align="R")
        pdf.ln()

    pdf.ln(6)
    pdf.set_font("Teklif", "B", 12)
    pdf.cell(0, 8, "Genel Toplam", ln=True)
    pdf.set_font("Teklif", "", 10)

    ozet = [
        ("Ürün sayısı (yuvarlanmış)", str(sonuc.toplam_urun_sayisi)),
        ("Direk sayısı (toplam)", str(sonuc.toplam_direk_sayisi)),
        ("Ürün ücreti", _para_format(sonuc.toplam_urun_ucreti)),
        ("Direk ücreti", _para_format(sonuc.toplam_direk_ucreti)),
        ("İşçilik", _para_format(sonuc.toplam_iscilik)),
    ]
    for etiket, deger in ozet:
        pdf.cell(95, 7, etiket, border=0)
        pdf.cell(0, 7, deger, ln=True, align="R")

    pdf.ln(2)
    pdf.set_font("Teklif", "B", 13)
    pdf.cell(95, 10, "TOPLAM ÜCRET")
    pdf.cell(0, 10, _para_format(sonuc.toplam_ucret), ln=True, align="R")

    pdf.ln(8)
    pdf.set_font("Teklif", "", 9)
    pdf.set_text_color(100, 100, 100)
    pdf.multi_cell(
        0,
        5,
        "Bu teklif bilgilendirme amaçlıdır. Fiyatlar KDV hariç olabilir. "
        "Geçerlilik süresi 30 gündür.",
    )

    cikti = BytesIO()
    pdf.output(cikti)
    return cikti.getvalue()


def teklif_dosya_adi(musteri_adi: str) -> str:
    return f"teklif_{_dosya_adi_temizle(musteri_adi)}_{date.today().strftime('%Y%m%d')}.pdf"
