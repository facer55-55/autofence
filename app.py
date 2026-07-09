"""Streamlit — Yönetim ve Kullanıcı panelleri."""

import importlib
from pathlib import Path

import pandas as pd
import streamlit as st

import hesaplama
import teklif_pdf
importlib.reload(hesaplama)
importlib.reload(teklif_pdf)
from hesaplama import hesapla_coklu_maliyet
from kolon_map import ayak_kaydini_map_et, urun_kaydini_map_et
from database import KOLONLAR, ornek_veri_yukle, tip_urunleri_getir, toplu_guncelle, tum_urunleri_getir, urun_kaydi_getir
from dosya_okuma import DosyaOkumaHatasi, dosya_oku, metin_oku
from teklif_pdf import PDF_SABLON_SURUM, olustur_teklif_pdf, teklif_dosya_adi

UYGULAMA_SURUM = "19.0"
DIREK_ARALIKLARI = ["1.00", "1.5", "1.56", "2.00", "2.5", "3.00"]

OTURUM_ANAHTARLARI = (
    "hesap_sonuc",
    "pdf_bytes",
    "pdf_musteri",
    "pdf_sablon_surum",
    "onizleme_df",
    "onizleme_bilgi",
)


def oturum_gecmisini_temizle() -> None:
    """Hesap, PDF ve yönetim önizleme geçmişini siler."""
    for anahtar in OTURUM_ANAHTARLARI:
        st.session_state.pop(anahtar, None)


def surum_kontrolu_yap() -> None:
    """Sürüm değiştiyse tüm oturum geçmişini sıfırlar."""
    if st.session_state.get("app_surum") == UYGULAMA_SURUM:
        return
    oturum_gecmisini_temizle()
    st.session_state["app_surum"] = UYGULAMA_SURUM


def pdf_onbellek_temizle() -> None:
    """Eski PDF şablonu önbelleğini siler."""
    if st.session_state.get("pdf_sablon_surum") == PDF_SABLON_SURUM:
        return
    st.session_state.pop("pdf_bytes", None)
    st.session_state.pop("pdf_musteri", None)
    st.session_state["pdf_sablon_surum"] = PDF_SABLON_SURUM


def urun_etiketi_olustur(kayit: dict) -> str:
    return f"{kayit['ADI']} — {kayit['BOY']}"


def urun_secimi_yap(tip: str, etiket: str) -> tuple[str, dict] | tuple[None, None]:
    urunler = tip_urunleri_getir(tip)
    if urunler.empty:
        st.warning(f"{tip} tipinde kayıt yok. Yönetim panelinden liste ekleyin.")
        return None, None

    adlar = sorted(urunler["ADI"].unique())
    secilen_ad = st.selectbox(f"{etiket} — Ürün adı", adlar, key=f"ad_{tip}")

    boylar = urunler[urunler["ADI"] == secilen_ad]
    boy_secenekleri = {
        f"{row['BOY']} (ID:{row['ID']})": int(row["ID"]) for _, row in boylar.iterrows()
    }
    secilen_boy = st.selectbox(
        f"{etiket} — Boy", list(boy_secenekleri.keys()), key=f"boy_{tip}"
    )
    kayit = urun_kaydi_getir(boy_secenekleri[secilen_boy])
    return urun_etiketi_olustur(kayit), kayit


def yonetim_sayfasi() -> None:
    st.header("Yönetim Paneli")
    st.caption(
        "Ürün listesi repodaki `ornek_urunler.csv` dosyasından da otomatik yüklenir "
        "(veritabanı boşsa). CSV'yi güncelleyip GitHub'a push ederseniz Cloud yeniden "
        "başlayınca yeni liste gelir."
    )

    df = tum_urunleri_getir()
    st.subheader("Mevcut Liste")
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.subheader("Toplu Güncelleme")
    st.markdown("Kolonlar: " + ", ".join(f"`{k}`" for k in KOLONLAR))
    st.caption("Örnek: `1;PANJUR JALUZI 156CM;ÜRÜN;0,10;156,00;ADET;110,00;55`")

    yuklenen = st.file_uploader("Dosya (CSV / Excel)", type=["csv", "xlsx", "xls", "txt"])
    if yuklenen is not None:
        try:
            yeni_df, bilgi = dosya_oku(yuklenen)
            st.session_state["onizleme_df"] = yeni_df
            st.session_state["onizleme_bilgi"] = bilgi
        except DosyaOkumaHatasi as exc:
            st.error(str(exc))

    with st.expander("Metin yapıştır", expanded=False):
        yapistir = st.text_area("Ürün listesi", height=140, key="metin_yapistir")
        if st.button("Metni oku", key="metin_oku"):
            try:
                yeni_df, bilgi = metin_oku(yapistir)
                st.session_state["onizleme_df"] = yeni_df
                st.session_state["onizleme_bilgi"] = bilgi
            except DosyaOkumaHatasi as exc:
                st.error(str(exc))

    if "onizleme_df" in st.session_state:
        onizleme = st.session_state["onizleme_df"]
        bilgi = st.session_state.get("onizleme_bilgi", "")
        st.success(f"{len(onizleme)} satır okundu ({bilgi}).")
        st.dataframe(onizleme, use_container_width=True, hide_index=True)
        if st.button("Listeyi Güncelle", type="primary"):
            toplu_guncelle(onizleme)
            del st.session_state["onizleme_df"]
            del st.session_state["onizleme_bilgi"]
            st.success("Kaydedildi.")
            st.rerun()

    st.subheader("Manuel Düzenleme")
    duzenlenen = st.data_editor(
        df if not df.empty else pd.DataFrame(columns=KOLONLAR),
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "TIP": st.column_config.SelectboxColumn("TIP", options=["ÜRÜN", "AYAK"]),
        },
    )
    if st.button("Tabloyu Kaydet"):
        toplu_guncelle(duzenlenen.dropna(how="all"))
        st.success("Kaydedildi.")
        st.rerun()

    ornek_yol = Path(__file__).parent / "ornek_urunler.csv"
    if ornek_yol.exists():
        st.download_button(
            "Örnek CSV indir",
            ornek_yol.read_text(encoding="utf-8-sig"),
            "ornek_urunler.csv",
            "text/csv",
        )


def kullanici_sayfasi() -> None:
    st.header("Malzeme Hesaplama")

    st.subheader("1. Ürün Seçimi")
    uygulama_urun, urun_kayit = urun_secimi_yap("ÜRÜN", "Ürün")
    if urun_kayit is None:
        return
    urun_map = urun_kaydini_map_et(urun_kayit)

    st.subheader("2. Ayak Seçimi")
    uygulama_ayak, ayak_kayit = urun_secimi_yap("AYAK", "Ayak")
    if ayak_kayit is None:
        return
    ayak_map = ayak_kaydini_map_et(ayak_kayit)

    st.subheader("3. Direk Aralığı")
    uygulama_aralik = st.selectbox("uygulama_aralik", DIREK_ARALIKLARI, index=3)

    st.subheader("4. Uzunluklar")
    st.caption("Birden fazla uzunluk girebilirsiniz. Her satır ayrı hesaplanır.")
    varsayilan = float(uygulama_aralik.replace(",", "."))
    uzunluk_df = st.data_editor(
        pd.DataFrame({"uygulama_uzunluk (m)": [varsayilan]}),
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "uygulama_uzunluk (m)": st.column_config.NumberColumn(
                "uygulama_uzunluk (m)", min_value=0.1, step=0.1, format="%.2f"
            ),
        },
        key="uzunluk_editor",
    )

    hesapla_tiklandi = st.button("Hesapla", type="primary")

    uygulama_uzunluklar = [
        float(v)
        for v in uzunluk_df["uygulama_uzunluk (m)"].dropna().tolist()
        if float(v) > 0
    ]

    if hesapla_tiklandi:
        if not uygulama_uzunluklar:
            st.error("En az bir geçerli uygulama_uzunluk girin.")
            return
        try:
            sonuc = hesapla_coklu_maliyet(
                uygulama_uzunluklar=uygulama_uzunluklar,
                uygulama_aralik=uygulama_aralik,
                urun_en=urun_map["urun_en"],
                urun_boy=urun_map["urun_boy"],
                urun_fiyat=urun_map["urun_fiyat"],
                montaj_fiyat=urun_map["montaj_fiyat"],
                ayak_boy=ayak_map["ayak_boy"],
                ayak_fiyat=ayak_map["ayak_fiyat"],
            )
            st.session_state["hesap_sonuc"] = {
                "sonuc": sonuc,
                "uygulama_urun": uygulama_urun,
                "uygulama_ayak": uygulama_ayak,
                "uygulama_aralik": uygulama_aralik,
            }
            st.session_state.pop("pdf_bytes", None)
            st.session_state.pop("pdf_musteri", None)
        except ValueError as exc:
            st.error(str(exc))
            return

    if "hesap_sonuc" not in st.session_state:
        return

    kayitli = st.session_state["hesap_sonuc"]
    sonuc = kayitli["sonuc"]
    uygulama_urun = kayitli["uygulama_urun"]
    uygulama_ayak = kayitli["uygulama_ayak"]
    uygulama_aralik = kayitli["uygulama_aralik"]

    st.subheader("Hesap Sonuçları")
    st.caption(f"uygulama_urun: {uygulama_urun} · uygulama_ayak: {uygulama_ayak}")

    satir_tablosu = pd.DataFrame(
        [
            {
                "Sıra": i + 1,
                "uygulama_uzunluk (m)": s.uygulama_uzunluk,
                "uygulama_urun_sayisi (ham)": round(s.uygulama_urun_sayisi_ham, 4),
                "uygulama_direk_ücreti (₺)": s.uygulama_direk_ucreti,
                "uygulama_işcilik (₺)": s.uygulama_iscilik,
                "uygulama_direk_sayisi": s.uygulama_direk_sayisi,
            }
            for i, s in enumerate(sonuc.satirlar)
        ]
    )
    st.dataframe(satir_tablosu, use_container_width=True, hide_index=True)

    st.subheader("Genel Toplam")
    g1, g2 = st.columns(2)
    g1.metric(
        "uygulama_urun_sayisi (toplam, yuvarlanmış)",
        sonuc.toplam_urun_sayisi,
    )
    g2.metric("uygulama_direk_sayisi (toplam)", sonuc.toplam_direk_sayisi)

    t1, t2, t3 = st.columns(3)
    t1.metric("uygulama_ürün_ücreti (₺)", f"{sonuc.toplam_urun_ucreti:,.2f}")
    t2.metric("uygulama_direk_ücreti (₺)", f"{sonuc.toplam_direk_ucreti:,.2f}")
    t3.metric("uygulama_işcilik (₺)", f"{sonuc.toplam_iscilik:,.2f}")

    st.metric("Toplam Ücret (₺)", f"{sonuc.toplam_ucret:,.2f}")

    st.subheader("5. PDF Teklif Formu")
    musteri_adi = st.text_input(
        "Müşteri adı",
        placeholder="Firma veya kişi adını girin",
        key="musteri_adi",
    )
    pdf_olustur = st.button("PDF Teklif Oluştur", type="secondary", key="pdf_olustur")
    if pdf_olustur:
        if not musteri_adi.strip():
            st.error("Lütfen müşteri adını girin.")
        else:
            try:
                pdf_bytes = olustur_teklif_pdf(
                    musteri_adi=musteri_adi.strip(),
                    uygulama_urun=uygulama_urun,
                    uygulama_ayak=uygulama_ayak,
                    uygulama_aralik=uygulama_aralik,
                    sonuc=sonuc,
                )
                st.session_state["pdf_bytes"] = pdf_bytes
                st.session_state["pdf_musteri"] = musteri_adi.strip()
                st.session_state["pdf_sablon_surum"] = PDF_SABLON_SURUM
            except Exception as exc:
                st.error(f"PDF oluşturulamadı: {exc}")

    if "pdf_bytes" in st.session_state and st.session_state.get(
        "pdf_sablon_surum"
    ) == PDF_SABLON_SURUM:
        st.success(f"Teklif hazır: {st.session_state.get('pdf_musteri', '')}")
        st.download_button(
            label="Teklifi İndir (PDF)",
            data=st.session_state["pdf_bytes"],
            file_name=teklif_dosya_adi(st.session_state.get("pdf_musteri", "musteri")),
            mime="application/pdf",
            type="primary",
            key="pdf_indir",
        )


def main() -> None:
    st.set_page_config(page_title="Malzeme Hesaplama", page_icon="📐", layout="wide")
    surum_kontrolu_yap()
    pdf_onbellek_temizle()
    ornek_veri_yukle()

    st.sidebar.markdown(f"### Sürüm **{UYGULAMA_SURUM}**")
    if st.sidebar.button("Geçmişi Temizle", use_container_width=True):
        oturum_gecmisini_temizle()
        st.sidebar.success("Geçmiş silindi.")
        st.rerun()
    sayfa = st.sidebar.radio("Menü", ["Kullanıcı", "Yönetim"])

    st.title("Malzeme Hesaplama Uygulaması")
    if sayfa == "Yönetim":
        yonetim_sayfasi()
    else:
        kullanici_sayfasi()


if __name__ == "__main__":
    main()
