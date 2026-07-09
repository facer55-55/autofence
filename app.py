import math
from pathlib import Path

import pandas as pd
import streamlit as st

# ---------------------------------------------------------------------------
# Sabitler
# ---------------------------------------------------------------------------
VERI_DOSYASI = Path(__file__).parent / "data" / "urunler.csv"
KOLONLAR = ["ID", "ADI", "TIP", "BOY", "EN", "BIRIM", "FIYAT", "MONTAJ"]
DIREK_ARALIK_SECENEKLERI = [1.00, 1.5, 2.00, 2.5, 3.00]


# ---------------------------------------------------------------------------
# Veri katmanı
# ---------------------------------------------------------------------------
def urunleri_yukle() -> pd.DataFrame:
    if VERI_DOSYASI.exists():
        df = pd.read_csv(VERI_DOSYASI)
        for kolon in KOLONLAR:
            if kolon not in df.columns:
                df[kolon] = None
        return df[KOLONLAR]
    return pd.DataFrame(columns=KOLONLAR)


def urunleri_kaydet(df: pd.DataFrame) -> None:
    VERI_DOSYASI.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(VERI_DOSYASI, index=False)


def toplu_liste_ayristir(ham_metin: str) -> pd.DataFrame:
    """Virgül veya sekme ile ayrılmış toplu listeyi DataFrame'e çevirir."""
    satirlar = [s.strip() for s in ham_metin.strip().splitlines() if s.strip()]
    if not satirlar:
        return pd.DataFrame(columns=KOLONLAR)

    kayitlar = []
    for satir in satirlar:
        if "\t" in satir:
            parcalar = satir.split("\t")
        else:
            parcalar = [p.strip() for p in satir.split(",")]

        if len(parcalar) < len(KOLONLAR):
            continue

        kayitlar.append(dict(zip(KOLONLAR, parcalar[: len(KOLONLAR)])))

    df = pd.DataFrame(kayitlar)
    for kolon in ["ID", "BOY", "EN", "FIYAT", "MONTAJ"]:
        if kolon in df.columns:
            df[kolon] = pd.to_numeric(df[kolon], errors="coerce")
    return df


# ---------------------------------------------------------------------------
# Hesaplama fonksiyonları
# ---------------------------------------------------------------------------
def hesapla_panjur_sayisi(ayak_boy: float, urun_boy: float) -> float:
    if urun_boy == 0:
        return 0.0
    return ayak_boy / urun_boy


def hesapla_direk_sayisi(uygulama_uzunluk: float, uygulama_aralik: float) -> int:
    if uygulama_aralik == 0:
        return 0
    sonuc = uygulama_uzunluk / uygulama_aralik
    if not sonuc.is_integer():
        return math.ceil(sonuc) + 1
    return int(sonuc)


def hesapla_urun_sayisi(
    uygulama_uzunluk: float,
    urun_en: float,
    urun_adi: str,
    panjur_sayisi: float,
) -> int:
    if urun_en == 0:
        return 0
    uygulama_urun_sayisi = math.ceil(uygulama_uzunluk / urun_en)

    panjur_urunu = (
        urun_adi == "PANJUR JALUZI 156CM" or "156CM" in urun_adi.upper()
    )
    if panjur_urunu:
        uygulama_urun_sayisi = int(uygulama_urun_sayisi * panjur_sayisi)

    return uygulama_urun_sayisi


def hesapla_iscilik(
    uygulama_uzunluk: float, urun_boy: float, montaj_fiyat: float
) -> float:
    return uygulama_uzunluk * urun_boy * montaj_fiyat


def hesapla_malzeme_ucreti(
    uygulama_urun_sayisi: int,
    urun_boy: float,
    urun_en: float,
    urun_fiyat: float,
    uygulama_direk_sayisi: int,
    ayak_fiyat: float,
) -> float:
    urun_tutari = uygulama_urun_sayisi * urun_boy * urun_en * urun_fiyat
    ayak_tutari = uygulama_direk_sayisi * ayak_fiyat
    return urun_tutari + ayak_tutari


def urun_satirindan_map_et(satir: pd.Series) -> dict:
    """DB kolonlarını (URUN_*) Python değişkenlerine map eder."""
    return {
        "urun_fiyat": float(satir["FIYAT"]),      # URUN_FIYAT
        "montaj_fiyat": float(satir["MONTAJ"]),  # URUN_MONTAJ
        "urun_en": float(satir["EN"]),           # URUN_EN
        "urun_boy": float(satir["BOY"]),         # URUN_BOY
        "urun_adi": str(satir["ADI"]),
    }


def ayak_satirindan_map_et(satir: pd.Series) -> dict:
    """DB kolonlarını (AYAK_*) Python değişkenlerine map eder."""
    return {
        "ayak_fiyat": float(satir["FIYAT"]),  # AYAK_FIYAT
        "ayak_en": float(satir["EN"]),        # AYAK_EN
        "ayak_boy": float(satir["BOY"]),      # AYAK_BOY
        "ayak_adi": str(satir["ADI"]),
    }


# ---------------------------------------------------------------------------
# Yönetim paneli
# ---------------------------------------------------------------------------
def yonetim_paneli() -> None:
    st.header("Yönetim Paneli")
    st.caption("Ürün listesini tablo üzerinden veya toplu liste ile güncelleyebilirsiniz.")

    if "urun_df" not in st.session_state:
        st.session_state.urun_df = urunleri_yukle()

    sekme_tablo, sekme_toplu = st.tabs(["Tablo Düzenle", "Toplu Liste Güncelle"])

    with sekme_tablo:
        duzenlenen = st.data_editor(
            st.session_state.urun_df,
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                "ID": st.column_config.NumberColumn("ID", min_value=1, step=1),
                "ADI": st.column_config.TextColumn("ADI"),
                "TIP": st.column_config.SelectboxColumn(
                    "TIP", options=["ÜRÜN", "AYAK"]
                ),
                "BOY": st.column_config.NumberColumn("BOY", format="%.2f"),
                "EN": st.column_config.NumberColumn("EN", format="%.2f"),
                "BIRIM": st.column_config.TextColumn("BIRIM"),
                "FIYAT": st.column_config.NumberColumn("FIYAT", format="%.2f"),
                "MONTAJ": st.column_config.NumberColumn("MONTAJ", format="%.2f"),
            },
        )
        if st.button("Tabloyu Kaydet", type="primary", key="tablo_kaydet"):
            st.session_state.urun_df = duzenlenen
            urunleri_kaydet(duzenlenen)
            st.success("Tablo kaydedildi.")

    with sekme_toplu:
        st.markdown(
            "Her satır: `ID, ADI, TIP, BOY, EN, BIRIM, FIYAT, MONTAJ` "
            "(virgül veya sekme ile ayrılmış)"
        )
        ornek = (
            "1,PANJUR JALUZI 156CM,ÜRÜN,1.56,0.15,M2,450.00,85.00\n"
            "4,DİREK AYAK 2M,AYAK,2.00,0.10,ADET,120.00,0.00"
        )
        ham_metin = st.text_area("Toplu Liste", height=200, value=ornek)
        if st.button("Toplu Listeyi Uygula", type="primary", key="toplu_kaydet"):
            yeni_df = toplu_liste_ayristir(ham_metin)
            if yeni_df.empty:
                st.error("Geçerli satır bulunamadı.")
            else:
                st.session_state.urun_df = yeni_df
                urunleri_kaydet(yeni_df)
                st.success(f"{len(yeni_df)} kayıt güncellendi.")
                st.dataframe(yeni_df, use_container_width=True)


# ---------------------------------------------------------------------------
# Kullanıcı paneli
# ---------------------------------------------------------------------------
def kullanici_paneli() -> None:
    st.header("Hesaplama Paneli")

    if "urun_df" not in st.session_state:
        st.session_state.urun_df = urunleri_yukle()

    df = st.session_state.urun_df
    if df.empty:
        st.warning("Henüz ürün tanımlanmamış. Yönetim panelinden liste ekleyin.")
        return

    urun_df = df[df["TIP"] == "ÜRÜN"]
    ayak_df = df[df["TIP"] == "AYAK"]

    if urun_df.empty or ayak_df.empty:
        st.warning("Hem ÜRÜN hem AYAK tipinde kayıt bulunmalıdır.")
        return

    # --- Ürün seçimi ---
    st.subheader("1. Ürün Seçimi")
    urun_adlari = urun_df["ADI"].unique().tolist()
    secilen_urun_adi = st.selectbox("Ürün (URUN_TIP = ÜRÜN)", urun_adlari)

    urun_boy_secenekleri = urun_df[urun_df["ADI"] == secilen_urun_adi]["BOY"].tolist()
    secilen_urun_boy = st.selectbox("Boy", urun_boy_secenekleri)

    uygulama_urun = urun_df[
        (urun_df["ADI"] == secilen_urun_adi) & (urun_df["BOY"] == secilen_urun_boy)
    ].iloc[0]

    urun_map = urun_satirindan_map_et(uygulama_urun)
    urun_fiyat = urun_map["urun_fiyat"]
    montaj_fiyat = urun_map["montaj_fiyat"]
    urun_en = urun_map["urun_en"]
    urun_boy = urun_map["urun_boy"]

    with st.expander("Seçilen ürün detayı"):
        st.write(f"**urun_fiyat** (URUN_FIYAT): {urun_fiyat:.2f}")
        st.write(f"**montaj_fiyat** (URUN_MONTAJ): {montaj_fiyat:.2f}")
        st.write(f"**urun_en** (URUN_EN): {urun_en:.2f}")
        st.write(f"**urun_boy** (URUN_BOY): {urun_boy:.2f}")

    # --- Ayak seçimi ---
    st.subheader("2. Ayak Seçimi")
    ayak_adlari = ayak_df["ADI"].unique().tolist()
    secilen_ayak_adi = st.selectbox("Ayak (URUN_TIP = AYAK)", ayak_adlari)

    ayak_boy_secenekleri = ayak_df[ayak_df["ADI"] == secilen_ayak_adi]["BOY"].tolist()
    secilen_ayak_boy = st.selectbox("Ayak Boy", ayak_boy_secenekleri)

    uygulama_ayak = ayak_df[
        (ayak_df["ADI"] == secilen_ayak_adi) & (ayak_df["BOY"] == secilen_ayak_boy)
    ].iloc[0]

    ayak_map = ayak_satirindan_map_et(uygulama_ayak)
    ayak_fiyat = ayak_map["ayak_fiyat"]
    ayak_en = ayak_map["ayak_en"]
    ayak_boy = ayak_map["ayak_boy"]

    panjur_sayisi = hesapla_panjur_sayisi(ayak_boy, urun_boy)

    with st.expander("Seçilen ayak detayı"):
        st.write(f"**ayak_fiyat** (AYAK_FIYAT): {ayak_fiyat:.2f}")
        st.write(f"**ayak_en** (AYAK_EN): {ayak_en:.2f}")
        st.write(f"**ayak_boy** (AYAK_BOY): {ayak_boy:.2f}")
        st.write(f"**panjur_sayisi** (AYAK_BOY / URUN_BOY): {panjur_sayisi:.2f}")

    # --- Direk aralığı ve uzunluk ---
    st.subheader("3. Uygulama Bilgileri")
    uygulama_aralik = st.selectbox(
        "Direk Aralığı (uygulama_aralik)",
        DIREK_ARALIK_SECENEKLERI,
        format_func=lambda x: f"{x:.2f} m",
    )
    uygulama_uzunluk = st.number_input(
        "Uygulama Uzunluğu (uygulama_uzunluk)",
        min_value=0.01,
        value=10.0,
        step=0.1,
        format="%.2f",
    )

    # --- Hesaplamalar ---
    uygulama_direk_sayisi = hesapla_direk_sayisi(uygulama_uzunluk, uygulama_aralik)
    uygulama_urun_sayisi = hesapla_urun_sayisi(
        uygulama_uzunluk, urun_en, urun_map["urun_adi"], panjur_sayisi
    )
    uygulama_iscilik = hesapla_iscilik(uygulama_uzunluk, urun_boy, montaj_fiyat)
    uygulama_malzeme_ucreti = hesapla_malzeme_ucreti(
        uygulama_urun_sayisi,
        urun_boy,
        urun_en,
        urun_fiyat,
        uygulama_direk_sayisi,
        ayak_fiyat,
    )

    # --- Sonuçlar ---
    st.subheader("4. Sonuçlar")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("uygulama_urun_sayisi", uygulama_urun_sayisi)
        st.metric("uygulama_uzunluk", f"{uygulama_uzunluk:.2f} m")
    with col2:
        st.metric("uygulama_malzeme_ucreti", f"{uygulama_malzeme_ucreti:,.2f} ₺")
        st.metric("uygulama_iscilik", f"{uygulama_iscilik:,.2f} ₺")
    with col3:
        st.metric("uygulama_direk_sayisi", uygulama_direk_sayisi)
        st.metric("panjur_sayisi", f"{panjur_sayisi:.2f}")

    with st.expander("Hesaplama detayları"):
        st.markdown(
            f"""
            | Değişken | Formül | Sonuç |
            |----------|--------|-------|
            | uygulama_direk_sayisi | uzunluk / aralık (küsüratlıysa ceil + 1) | {uygulama_direk_sayisi} |
            | uygulama_urun_sayisi | ceil(uzunluk / URUN_EN) × panjur (156CM ise) | {uygulama_urun_sayisi} |
            | uygulama_iscilik | uzunluk × URUN_BOY × montaj_fiyat | {uygulama_iscilik:,.2f} |
            | uygulama_malzeme_ucreti | (ürün_sayısı × boy × en × fiyat) + (direk × ayak_fiyat) | {uygulama_malzeme_ucreti:,.2f} |
            """
        )


# ---------------------------------------------------------------------------
# Ana uygulama
# ---------------------------------------------------------------------------
def main() -> None:
    st.set_page_config(
        page_title="Panjur Hesaplama",
        page_icon="📐",
        layout="wide",
    )
    st.title("Panjur / Direk Hesaplama Uygulaması")

    sayfa = st.sidebar.radio(
        "Sayfa",
        ["Kullanıcı", "Yönetim"],
        index=0,
    )

    if sayfa == "Yönetim":
        yonetim_paneli()
    else:
        kullanici_paneli()


if __name__ == "__main__":
    main()
