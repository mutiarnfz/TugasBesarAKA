import streamlit as st
import time
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from dataclasses import dataclass
from typing import List, Tuple

# =========================
# PAGE CONFIG (HARUS PALING ATAS)
# =========================
st.set_page_config(
    page_title="Greedy Diet Planner",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =========================
# THEME (OPSIONAL - pastel)
# =========================
st.markdown("""
<style>
.stApp { background: #FCF8F8; }
section[data-testid="stSidebar"] { background: #FBEFEF; border-right: 1px solid #F9DFDF; }
div[data-testid="stMetric"], div[data-testid="stVerticalBlockBorderWrapper"], div[data-testid="stContainer"]{
  background:#FBEFEF; border:1px solid #F9DFDF; border-radius:16px; padding:12px;
}
hr { border:none; border-top:1px solid #F9DFDF; }
div.stButton > button {
  background:#F5AFAF !important; color:white !important; border:0 !important;
  border-radius:14px !important; padding:10px 16px !important; font-weight:700 !important;
  box-shadow:0 6px 18px rgba(245,175,175,0.35) !important;
}
div.stButton > button:hover { background:#f39e9e !important; transform: translateY(-1px); }
</style>
""", unsafe_allow_html=True)

# =========================
# DATA MODEL
# =========================
@dataclass(frozen=True)
class Makanan:
    nama: str
    kalori: int

# =========================
# DATA LOADING
# =========================
@st.cache_data(show_spinner=False)
def load_menu_from_csv(csv_path: str) -> List[Makanan]:
    df = pd.read_csv(csv_path)

    required_cols = {"Nama_Makanan", "Kalori_kcal"}
    if not required_cols.issubset(df.columns):
        raise ValueError(f"Kolom CSV harus ada: {required_cols}. Kolom ditemukan: {set(df.columns)}")

    df["Kalori_kcal"] = pd.to_numeric(df["Kalori_kcal"], errors="coerce")
    df = df.dropna(subset=["Kalori_kcal", "Nama_Makanan"])

    menu = [Makanan(str(r["Nama_Makanan"]), int(r["Kalori_kcal"])) for _, r in df.iterrows()]
    if not menu:
        raise ValueError("Data menu kosong setelah validasi. Cek isi CSV kamu.")
    return menu

# =========================
# GREEDY: CLOSEST FIRST
# =========================
def greedy_iteratif(target: int, menu: List[Makanan]) -> List[Makanan]:
    hasil = []
    sisa = target

    while sisa > 0:
        pilih = min(menu, key=lambda m: abs(m.kalori - sisa))
        hasil.append(pilih)
        sisa -= pilih.kalori

    return hasil

def greedy_rekursif(sisa: int, menu: List[Makanan], hasil: List[Makanan]) -> None:
    if sisa <= 0:
        return

    pilih = min(menu, key=lambda m: abs(m.kalori - sisa))
    hasil.append(pilih)
    greedy_rekursif(sisa - pilih.kalori, menu, hasil)

# =========================
# TIMING UTILITIES
# =========================
def measure_time_iteratif(target: int, menu: List[Makanan], trials: int = 5) -> Tuple[List[Makanan], float]:
    times = []
    result = []

    for _ in range(trials):
        start = time.perf_counter()
        result = greedy_iteratif(target, menu)
        end = time.perf_counter()
        times.append((end - start) * 1_000_000)  # µs

    return result, sum(times) / len(times)

def measure_time_rekursif(target: int, menu: List[Makanan], trials: int = 5) -> Tuple[List[Makanan], float]:
    times = []
    result = []

    for _ in range(trials):
        start = time.perf_counter()
        result = []
        greedy_rekursif(target, menu, result)
        end = time.perf_counter()
        times.append((end - start) * 1_000_000)  # µs

    return result, sum(times) / len(times)

def hasil_to_df(items: List[Makanan]) -> pd.DataFrame:
    return pd.DataFrame([{"Menu": m.nama, "Kalori (kkal)": m.kalori} for m in items])

def summarize(target: int, items: List[Makanan]) -> Tuple[int, int, str]:
    total = sum(m.kalori for m in items)
    diff = total - target
    if diff == 0:
        status = "Tepat"
    elif diff > 0:
        status = f"Terlampaui (+{diff})"
    else:
        status = f"Kurang ({diff})"
    return total, diff, status

# =========================
# SIDEBAR CONTROLS
# =========================
st.sidebar.title("⚙️ Pengaturan")
csv_file = st.sidebar.text_input("File CSV", value="1000_data_makanan_kalori.csv")
target = st.sidebar.slider("Target Kalori (kkal)", 50, 3000, 650, 50)
trials = st.sidebar.slider("Trials (rata-rata waktu)", 1, 30, 5, 1)
show_preview = st.sidebar.checkbox("Preview 10 baris CSV", value=False)
show_chart = st.sidebar.checkbox("Tampilkan grafik waktu", value=True)

# =========================
# LOAD DATA
# =========================
try:
    MENU = load_menu_from_csv(csv_file)
except Exception as e:
    st.error(f"Gagal membaca CSV: {e}")
    st.stop()

# =========================
# HEADER
# =========================
st.title("💗 Greedy Diet Planner (Closest First)")
st.caption(f"Dataset: **{len(MENU)}** menu • Target: **{target} kkal** • Trials: **{trials}**")

if show_preview:
    st.subheader("🧾 Preview Data CSV (10 baris)")
    st.dataframe(pd.read_csv(csv_file).head(10), width="stretch", height=280)

st.markdown("---")

# =========================
# AUTO-RUN RESULTS (MINIM SCROLL)
# =========================
with st.spinner("Menyusun rekomendasi menu..."):
    hasil_iter, t_iter = measure_time_iteratif(target, MENU, trials=trials)
    hasil_rec, t_rec = measure_time_rekursif(target, MENU, trials=trials)

total_i, diff_i, status_i = summarize(target, hasil_iter)
total_r, diff_r, status_r = summarize(target, hasil_rec)

colL, colR = st.columns(2, gap="large")

with colL:
    st.subheader("✅ Iteratif")
    a, b, c = st.columns(3)
    a.metric("Total", f"{total_i} kkal")
    b.metric("Item", f"{len(hasil_iter)}")
    c.metric("Waktu", f"{t_iter:.2f} µs")
    st.write(f"**Status:** {status_i}")
    st.dataframe(hasil_to_df(hasil_iter), width="stretch", height=320, hide_index=True)

with colR:
    st.subheader("🔁 Rekursif")
    a, b, c = st.columns(3)
    a.metric("Total", f"{total_r} kkal")
    b.metric("Item", f"{len(hasil_rec)}")
    c.metric("Waktu", f"{t_rec:.2f} µs")
    st.write(f"**Status:** {status_r}")
    st.dataframe(hasil_to_df(hasil_rec), width="stretch", height=320, hide_index=True)

st.markdown("---")

c1, c2, c3 = st.columns(3)
faster = "Iteratif" if t_iter < t_rec else ("Rekursif" if t_rec < t_iter else "Seimbang")
same_total = "SAMA" if total_i == total_r else "BEDA"
c1.metric("Lebih cepat", faster)
c2.metric("Total hasil", same_total)
c3.metric("Selisih waktu", f"{abs(t_iter - t_rec):.2f} µs")

if show_chart:
    st.subheader("📊 Perbandingan Waktu Eksekusi")
    fig, ax = plt.subplots()
    ax.bar(["Iteratif", "Rekursif"], [t_iter, t_rec])
    ax.set_ylabel("Waktu (µs)")
    ax.set_title(f"Target = {target} kkal")
    for i, v in enumerate([t_iter, t_rec]):
        ax.text(i, v * 1.01, f"{v:.2f}", ha="center")
    st.pyplot(fig, width="stretch")
    plt.close(fig)

st.caption("Catatan: Greedy tidak menjamin solusi optimal global. Closest First memilih menu dengan kalori terdekat terhadap sisa target.")
