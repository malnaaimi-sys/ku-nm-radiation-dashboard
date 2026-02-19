import streamlit as st
import pandas as pd
import numpy as np
import datetime as dt
import matplotlib.pyplot as plt
from PIL import Image
import streamlit as st
import hmac

# ----------------------------
# LOGIN / PASSWORD GATE
# ----------------------------
def check_password():
    """Returns True if the user had the correct username/password."""
    # Secrets are preferred (Streamlit Cloud or local .streamlit/secrets.toml)
    users = st.secrets.get("users", {})  # dict: {"username":"password"}

    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if st.session_state["authenticated"]:
        return True

    st.title("🔐 KU NM Radiation Safety Dashboard")
    st.subheader("Login")

    with st.form("login_form", clear_on_submit=False):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Sign in")

    if submitted:
        # Compare securely
        if username in users and hmac.compare_digest(password, str(users[username])):
            st.session_state["authenticated"] = True
            st.success("✅ Login successful")
            st.rerun()
        else:
            st.error("❌ Incorrect username or password")
            st.stop()

    st.info("Authorized users only.")
    st.stop()

check_password()
with st.sidebar:
    if st.button("🚪 Logout"):
        st.session_state["authenticated"] = False
        st.rerun()

st.set_page_config(page_title="Radiation Safety Dashboard", page_icon="🛡️", layout="wide")

# ----------------------------
# Simple helpers
# ----------------------------
def avail(file_obj):
    return "🟢 Available" if file_obj is not None else "⚪ Not added"

def try_read_table(uploaded_file):
    if uploaded_file is None:
        return None
    name = uploaded_file.name.lower()
    try:
        if name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
            df.columns = [c.strip() for c in df.columns]
            return df
        if name.endswith(".xlsx") or name.endswith(".xls"):
            df = pd.read_excel(uploaded_file)
            df.columns = [c.strip() for c in df.columns]
            return df
    except Exception as e:
        st.warning(f"Could not read {uploaded_file.name}: {e}")
    return None

def safe_to_datetime(s):
    return pd.to_datetime(s, errors="coerce")

def get_last_date(df, col):
    if df is None or col not in df.columns:
        return None
    d = safe_to_datetime(df[col])
    if d.notna().sum() == 0:
        return None
    return d.max()

def find_col(df, candidates):
    if df is None:
        return None
    cols = {c.lower(): c for c in df.columns}
    for cand in candidates:
        for k, real in cols.items():
            if cand in k:
                return real
    return None

def icon_card(title, status_text, kpi_label, kpi_value, icon="📌"):
    with st.container(border=True):
        st.markdown(f"### {icon} {title}")
        st.write(f"**Status:** {status_text}")
        st.metric(kpi_label, kpi_value)

def bar_by_radionuclide(df, title):
    rn_col = find_col(df, ["radionuclide", "isotope", "radioisotope", "nuclide"])
    if df is None or rn_col is None or df.empty:
        st.info("Upload CSV/XLSX with a Radionuclide/Isotope column to generate this chart.")
        return
    vc = df[rn_col].astype(str).str.strip().value_counts().head(8)
    fig = plt.figure()
    plt.bar(vc.index.tolist(), vc.values.tolist())
    plt.title(title)
    plt.xlabel("Radionuclide")
    plt.ylabel("Count")
    st.pyplot(fig)

# ----------------------------
# Fixed “manual” facts (from your text)
# ----------------------------
DOC_NO = "HSC-NM-RSM-001"
VERSION = "2026 – Rev. 1"
REG_AUTH = "RPD LICENSE \n NUM.1/2007"
RPD_LICENSE_NO = "1/2007"
LICENSE_VALID_UNTIL = "05 June 2027"
RESPONSIBLE_PERSON = "Dr. Mohammad Saker"

# Headline
st.title("🛡️ Radiation Safety Dashboard")

# Executive strip
a, b, c, d = st.columns(4)
with a:
    st.metric("Document", DOC_NO)
with b:
    st.metric("Version", VERSION)
with c:
    st.metric("Regulatory Authority",REG_AUTH)
with d:
    st.metric("License Valid Until", LICENSE_VALID_UNTIL)

e, f = st.columns(2)
with e:
    st.write(f"**Responsible Person (Radiation Protection):** {RESPONSIBLE_PERSON}")
with f:
    st.write(f"**Updated:** {dt.datetime.now().strftime('%Y-%m-%d %H:%M')}")

st.divider()

# ----------------------------
# Uploads (simple)
# ----------------------------
st.subheader("Upload evidence files (optional)")
u1, u2, u3 = st.columns(3)
with u1:
    floorplan_receipt = st.file_uploader("🧭 Receiving route floor plan (PNG/JPG)", type=["png","jpg","jpeg"])
    route_overlay = st.file_uploader("Optional route overlay (PNG)", type=["png"])
with u2:
    zoning_plan = st.file_uploader("🗺️ Radiation zoning plan (PNG/JPG)", type=["png","jpg","jpeg"])
with u3:
    qc_reports = st.file_uploader("🧪 QC reports (PDF/CSV/XLSX)", type=["pdf","csv","xlsx"])

u4, u5, u6 = st.columns(3)
with u4:
    receipt_log = st.file_uploader("📦 Radionuclide receipt / use log (CSV/XLSX)", type=["csv","xlsx"])
with u5:
    sealed_source_log = st.file_uploader("🔐 Sealed source inventory log (CSV/XLSX)", type=["csv","xlsx"])
with u6:
    invivo_log = st.file_uploader("🐭 In vivo administration log (CSV/XLSX)", type=["csv","xlsx"])

u7, u8 = st.columns(2)
with u7:
    animals_log = st.file_uploader("🐾 Radioactive animals log (CSV/XLSX)", type=["csv","xlsx"])
with u8:
    tld_log = st.file_uploader("📟 TLD dose record (CSV/XLSX) — optional", type=["csv","xlsx"])

# Read tables
df_receipt = try_read_table(receipt_log)
df_sealed = try_read_table(sealed_source_log)
df_invivo = try_read_table(invivo_log)
df_animals = try_read_table(animals_log)
df_tld = try_read_table(tld_log)

st.divider()

# ----------------------------
# Facility visuals (keep simple)
# ----------------------------
st.subheader("Facility visuals")
img1, img2 = st.columns(2)
with img1:
    with st.container(border=True):
        st.markdown("### 🧭 Receiving & Receipt Route")
        st.write("Status:", avail(floorplan_receipt))
        if floorplan_receipt is not None:
            base_img = Image.open(floorplan_receipt).convert("RGBA")
            if route_overlay is not None:
                overlay = Image.open(route_overlay).convert("RGBA").resize(base_img.size)
                combined = Image.alpha_composite(base_img, overlay)
                st.image(combined, use_container_width=True)
            else:
                st.image(base_img, use_container_width=True)
with img2:
    with st.container(border=True):
        st.markdown("### 🗺️ Radiation Zoning Plan")
        st.write("Status:", avail(zoning_plan))
        if zoning_plan is not None:
            st.image(Image.open(zoning_plan), use_container_width=True)

st.divider()

# ----------------------------
# KPI per pillar (very simple)
# Uses your log columns: Date, Form, Purpose (In vivo / In vitro / QC)
# ----------------------------
st.subheader("Competency snapshot (5 pillars)")

date_col = find_col(df_receipt, ["date"])
form_col = find_col(df_receipt, ["form"])
purpose_col = find_col(df_receipt, ["purpose"])
last_receipt = get_last_date(df_receipt, date_col)
last_receipt_str = last_receipt.strftime("%Y-%m-%d") if last_receipt is not None else "—"

# sealed sources KPI: number of sealed sources from sealed inventory log if present,
# else infer from receipt log where Form contains "sealed"
sealed_count = "—"
if df_sealed is not None and not df_sealed.empty:
    sealed_count = str(len(df_sealed))
elif df_receipt is not None and form_col in (df_receipt.columns if df_receipt is not None else []):
    sealed_count = str((df_receipt[form_col].astype(str).str.contains("sealed", case=False, na=False)).sum())

# QC KPI: last QC date from receipt log where Purpose contains "QC" OR from QC log if provided as CSV/XLSX
last_qc_str = "—"
if df_receipt is not None and date_col and purpose_col:
    qc_rows = df_receipt[purpose_col].astype(str).str.contains("qc", case=False, na=False)
    if qc_rows.any():
        last_qc = safe_to_datetime(df_receipt.loc[qc_rows, date_col]).max()
        if pd.notna(last_qc):
            last_qc_str = last_qc.strftime("%Y-%m-%d")

# In vivo KPI: count from invivo log if provided, else from receipt log where Purpose contains "In vivo"
invivo_count = "—"
if df_invivo is not None and not df_invivo.empty:
    invivo_count = str(len(df_invivo))
elif df_receipt is not None and purpose_col:
    invivo_count = str((df_receipt[purpose_col].astype(str).str.contains("in vivo", case=False, na=False)).sum())

# Animals KPI: count unique animals if AnimalID exists, else rows
animals_count = "—"
if df_animals is not None and not df_animals.empty:
    animal_id_col = find_col(df_animals, ["animal", "animalid", "id"])
    if animal_id_col:
        animals_count = f"{df_animals[animal_id_col].nunique()} animals"
    else:
        animals_count = f"{len(df_animals)} records"

c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    icon_card("Source Security", avail(sealed_source_log), "Sealed sources", sealed_count, icon="🔐")
with c2:
    icon_card("Safe Receiving", avail(receipt_log), "Last receipt date", last_receipt_str, icon="📦")
with c3:
    icon_card("Quality Control", avail(qc_reports), "Last QC date", last_qc_str, icon="🧪")
with c4:
    icon_card("Safe Administration", avail(invivo_log) if invivo_log else avail(receipt_log), "In vivo count", invivo_count, icon="🐭")
with c5:
    icon_card("Animal Management", avail(animals_log), "Animals (or records)", animals_count, icon="🐾")

st.divider()

# ----------------------------
# Simple infographics (optional, non-technical)
# ----------------------------
st.subheader("Simple infographics")
g1, g2, g3 = st.columns(3)
with g1:
    with st.container(border=True):
        st.markdown("#### 📦 Receiving by radionuclide")
        bar_by_radionuclide(df_receipt, "Receiving by radionuclide")
with g2:
    with st.container(border=True):
        st.markdown("#### 🔐 Sealed sources by radionuclide")
        bar_by_radionuclide(df_sealed, "Sealed sources by radionuclide")
with g3:
    with st.container(border=True):
        st.markdown("#### 🐭 In vivo by radionuclide")
        bar_by_radionuclide(df_invivo, "In vivo administrations by radionuclide")

st.divider()

# ----------------------------
# Dose performance (TLD) — default embedded list if no upload
# ----------------------------
st.subheader("Occupational dose performance (MOH/RPD TLD)")

default_tld = pd.DataFrame([
    [778,"DR ESSA LOUTFI",7134,0.124,0.139,""],
    [1137,"MR AHMED MAHMOUD MPHAMED",7145,0.132,0.139,""],
    [1342,"MR MOHAMED ABDUL MONEM S.",7153,0.123,0.122,""],
    [1398,"DR B KUMARI VASANTHY",7274,0.122,0.125,""],
    [1411,"DR FATIMA AL-SAIDEE",7346,0.129,0.133,""],
    [1686,"MISS HEBA MOHAMED HAMED",7348,0.126,0.124,""],
    [1728,"MRS JEHAN AL SHAMMARI",7393,0.133,0.131,""],
    [3265,"MS ASEEL AHMED AL KANDARI",7396,0.123,0.124,""],
    [3285,"DR SAUD A H. AL-ENEZI",7595,0.123,0.132,""],
    [5078,"DR MOHAMMAD ZAFARYAB",7755,0.105,0.106,""],
    [5217,"DR F.X. ELIZABETH JAYANTHI",7747,0.106,0.112,""],
    [5218,"MRS FATIMA SEQUEIRA",7739,0.129,0.135,""],
    [5513,"DR SHOROUK FALEH DANNOON",7738,0.157,0.169,""],
    [6091,"MR WALEED SAMIR ALI",7737,0.137,0.144,"NEW"],
    [8220,"DR MARIAM YOUSSEF HUSSAIN",7724,0.159,0.159,""],
    [8916,"MRS JEHAN ESSAM GHONEIM",7722,0.107,0.114,""],
    [9352,"MR MOHAMMED JASEEM PATTILLATH",7721,0.134,0.130,"NEW"],
    [9698,"DR SELMA SAAD ALKAFEEF",6639,0.135,0.131,"NEW"],
    [9699,"MRS ABIRAMI SELLAPANDIAN",7241,0.159,0.163,"NEW"],
    [9700,"MR YOUSEF RAED YOUSEF",6205,0.120,0.123,"NEW"],
], columns=["Code","Name","Card","Hp10_mSv","Hp07_mSv","Remarks"])

tld = df_tld if (df_tld is not None and not df_tld.empty) else default_tld

# Ensure numeric
tld["Hp10_mSv"] = pd.to_numeric(tld["Hp10_mSv"], errors="coerce")
tld["Hp07_mSv"] = pd.to_numeric(tld["Hp07_mSv"], errors="coerce")

monitored = int(tld["Hp10_mSv"].notna().sum())
hp10_min = float(tld["Hp10_mSv"].min())
hp10_max = float(tld["Hp10_mSv"].max())
hp10_mean = float(tld["Hp10_mSv"].mean())
annual_proj = hp10_mean * 4

k1, k2, k3, k4 = st.columns(4)
with k1: st.metric("Monitored staff", monitored)
with k2: st.metric("Hp(10) range (mSv)", f"{hp10_min:.3f} – {hp10_max:.3f}")
with k3: st.metric("Average Hp(10) (mSv)", f"{hp10_mean:.3f}")
with k4: st.metric("Projected annual (mSv/yr)", f"{annual_proj:.2f}")

search = st.text_input("Search staff name")
view = tld.copy()
if search.strip():
    view = view[view["Name"].str.contains(search, case=False, na=False)]
st.dataframe(view.sort_values("Hp10_mSv", ascending=False), use_container_width=True)

# Optional: keep previews hidden
with st.expander("Optional: preview receipt log (first 30 rows)"):
    if df_receipt is None:
        st.info("Upload receipt log CSV/XLSX to preview here.")
    else:
        st.dataframe(df_receipt.head(30), use_container_width=True)








