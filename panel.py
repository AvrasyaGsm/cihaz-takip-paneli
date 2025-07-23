import streamlit as st
import pandas as pd
import os
import base64
import io
from PIL import Image

# ---- Şifre kontrolü ----
def check_password():
    def password_entered():
        if (
            st.session_state["username"] == "admin"
            and st.session_state["password"] == "1234"
        ):
            st.session_state["password_correct"] = True
            del st.session_state["password"]
            del st.session_state["username"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("Kullanıcı Adı", key="username")
        st.text_input("Şifre", type="password", key="password")
        st.button("Giriş Yap", on_click=password_entered)
        return False
    elif not st.session_state["password_correct"]:
        st.error("❌ Hatalı kullanıcı adı veya şifre.")
        del st.session_state["password_correct"]
        return False
    else:
        return True

if check_password():
    # ---------- Şifre doğruysa uygulama başlasın ----------

    CSV_DOSYA = "siparis_kayitlari.csv"
    DOSYA_KLASOR = "faturalar"

    if os.path.exists(CSV_DOSYA):
        df = pd.read_csv(CSV_DOSYA)
    else:
        df = pd.DataFrame(columns=["Sipariş No", "Mağaza", "Ürün", "Tarih", "Fatura No", "Dosya Adı"])

    st.set_page_config(page_title="📦 Cihaz Takip Paneli", layout="wide")

    logo = Image.open("avrasya_gsm_logo.png")

    col1, col2, col3 = st.columns([1, 3, 4])

    with col1:
        st.image(logo, width=130)

    with col2:
        st.write("")
        st.write("")
        st.write("")
        st.markdown("<h1 style='text-align:center; color:#0A53BE; font-weight:bold;'>📦 Cihaz Alış Takip Paneli</h1>", unsafe_allow_html=True)

    with col3:
        st.write("")

    st.header("➕ Yeni Sipariş Ekle")
    with st.form("siparis_form"):
        col1f, col2f, col3f = st.columns(3)
        with col1f:
            siparis_no = st.text_input("Sipariş No")
            magaza = st.text_input("Mağaza")
        with col2f:
            urun = st.text_input("Ürün")
            tarih = st.date_input("Tarih")
        with col3f:
            fatura_no = st.text_input("Fatura No")
            dosya = st.file_uploader("Fatura Dosyası (PDF, JPG, PNG)", type=["pdf", "jpg", "png"])
        submitted = st.form_submit_button("📥 Kaydet")

    if submitted:
        dosya_adi = ""
        if dosya:
            dosya_adi = dosya.name
            os.makedirs(DOSYA_KLASOR, exist_ok=True)
            dosya_yolu = os.path.join(DOSYA_KLASOR, dosya_adi)
            with open(dosya_yolu, "wb") as f:
                f.write(dosya.read())
        yeni_kayit = {
            "Sipariş No": siparis_no,
            "Mağaza": magaza,
            "Ürün": urun,
            "Tarih": tarih,
            "Fatura No": fatura_no,
            "Dosya Adı": dosya_adi
        }
        df = pd.concat([df, pd.DataFrame([yeni_kayit])], ignore_index=True)
        df.to_csv(CSV_DOSYA, index=False)
        st.success("✅ Kayıt başarıyla eklendi!")

    def to_excel(df):
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Siparisler')
        return output.getvalue()

    st.header("📄 Kayıtlı Siparişler")
    excel_data = to_excel(df)
    st.download_button(
        label='📤 Excel Olarak İndir',
        data=excel_data,
        file_name='siparis_kayitlari.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

    st.subheader("🗑️ Kayıt Sil")
    secim = st.multiselect("Silmek istediğiniz Sipariş No'ları seçin:", df["Sipariş No"].tolist())
    if st.button("Sil"):
        if secim:
            df = df[~df["Sipariş No"].isin(secim)]
            df.to_csv(CSV_DOSYA, index=False)
            st.success(f"Seçilen {len(secim)} kayıt silindi.")
        else:
            st.warning("Lütfen en az bir kayıt seçin.")

    st.subheader("📁 Fatura Dosyası Görüntüle")
    secili_siparis = st.selectbox("Fatura dosyasını görmek istediğiniz Sipariş No'yu seçin:", options=df["Sipariş No"].tolist())
    if secili_siparis:
        dosya_adi = df.loc[df["Sipariş No"] == secili_siparis, "Dosya Adı"].values[0]
        if dosya_adi and os.path.exists(os.path.join(DOSYA_KLASOR, dosya_adi)):
            dosya_yolu = os.path.join(DOSYA_KLASOR, dosya_adi)
            uzanti = dosya_adi.split(".")[-1].lower()
            if uzanti == "pdf":
                with open(dosya_yolu, "rb") as f:
                    base64_pdf = base64.b64encode(f.read()).decode('utf-8')
                pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="700" height="900" type="application/pdf"></iframe>'
                st.markdown(pdf_display, unsafe_allow_html=True)
            elif uzanti in ["jpg", "jpeg", "png"]:
                st.image(dosya_yolu, caption=dosya_adi)
            else:
                st.warning("Dosya türü görüntülenemiyor.")
        else:
            st.info("Bu sipariş için fatura dosyası bulunamadı.")

    st.dataframe(df, use_container_width=True)
