import streamlit as st
import time
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from dataclasses import dataclass
from typing import List, Tuple

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(
    page_title="Greedy Diet Planner",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =========================
# CSS
# =========================
st.markdown("""
<style>
.stApp { background: #FCF8F8; }
section[data-testid="stSidebar"] { background: #FBEFEF; border-right: 1px solid #F9DFDF; }
div[data-testid="stMetric"], div[data-testid="stContainer"], div[data-testid="stVerticalBlockBorderWrapper"]{
  background:#FBEFEF; border:1px solid #F9DFDF; border-radius:16px; padding:12px;
}
hr { border:none; border-top:1px solid #F9DFDF; }
</style>
""", unsafe_allow_html=True)

# =========================
# DATA STRUCTURE
# =========================
@dataclass
class Makanan:
    nama: str
    kalori: int

# =========================
# LOAD CSV
# =========================
@st.cache_data(show_spinner=False)
def load_menu_from_csv(csv_path: str) -> List[Makanan]:
    df = pd.read_csv(csv_path)

    required_cols = {"Nama_Makanan", "Kalori_kcal"}
    if not required_cols.issubset(df.columns):
        raise ValueError(f"Kolom CSV harus ada: {required_cols}. Kolom ditemukan: {set(df.columns)}")

    return [
        Makanan(nama=str(row["Nama_Makanan"]), kalori=int(row["Kalori_kcal"]))
        for _, row in df.iterrows()
    ]

# =========================
# GREEDY ITERATIVE
# =========================
def greedy_menu(target: int, menu: List[Makanan]) -> List[Makanan]:
    sisa = target
    hasil: List[Makanan] = []

    while sisa > 0:
        idx_pilih = -1
        selisih_min = float("inf")

        for i, m in enumerate(menu):
            selisih = abs(m.kalori - sisa)
            if selisih < selisih_min:
                selisih_min = selisih
                idx_pilih = i

        if idx_pilih == -1:
            break

        hasil.append(menu[idx_pilih])
        sisa -= menu[idx_pilih].kalori

        if sisa <= 0:
            break

    return hasil

# =========================
# GREEDY RECURSIVE
# =========================
def greedy_menu_rekursif(sisa: int, menu: List[Makanan], hasil: List[Makanan]) -> None:
    if sisa <= 0:
        return

    idx_pilih = -1
    selisih_min = float("inf")

    for i, m in enumerate(menu):
        selisih = abs(m.kalori - sisa)
        if selisih < selisih_min:
            selisih_min = selisih
            idx_pilih = i

    if idx_pilih == -1:
        return

    hasil.append(menu[idx_pilih])
    greedy_menu_rekursif(sisa - menu[idx_pilih].kalori, menu, hasil)

# =========================
# TIME MEASURE
# =========================
def measure_time_iteratif(target: int, menu: List[Makanan], trials: int = 5) -> Tuple[List[Makanan], float]:
    times = []
    result: List[Makanan] = []
    for _ in range(trials):
        start = time.perf_counter()
        result = greedy_menu(target, menu)
        end = time.perf_counter()
        times.append((end - start) * 1_000_000)
    return result, sum(times) / len(times)

def measure_time_rekursif(target: int, menu: List[Makanan], trials: int = 5) -> Tuple[List[Makanan], float]:
    times = []
    result: List[Makanan] = []
    for _ in range(trials):
        start = time.perf_counter()
        result = []
        greedy_menu_rekursif(target, menu, result)
        end = time.perf_counter()
        times.append((end - start) * 1_000_000)
    return result, sum(times) / len(times)

def to_df(items: List[Makanan]) -> pd.DataFrame:
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
show_chart = st.sidebar.checkbox("Tampilkan grafik waktu", value=True)

# =========================
# LOAD DATA
# =========================
try:
    MENU_DATABASE = load_menu_from_csv(csv_file)
except Exception as e:
    st.error(f"Gagal membaca CSV: {e}")
    st.stop()

# =========================
# HEADER
# =========================
st.title("💗 Rekomendasi Menu Diet (Greedy Closest First)")
st.caption(f"Data dari CSV: **{len(MENU_DATABASE)}** menu • Target: **{target} kkal** • Trials: **{trials}**")

# =========================
# AUTO-RUN: langsung hitung saat page dibuka / target berubah
# =========================
with st.spinner("Menyusun rekomendasi menu..."):
    hasil_iter, t_iter = measure_time_iteratif(target, MENU_DATABASE, trials=trials)
    hasil_rec, t_rec = measure_time_rekursif(target, MENU_DATABASE, trials=trials)

total_iter, diff_iter, status_iter = summarize(target, hasil_iter)
total_rec, diff_rec, status_rec = summarize(target, hasil_rec)

# =========================
# SIDE-BY-SIDE RESULTS (NO SCROLL)
# =========================
colL, colR = st.columns(2, gap="large")

with colL:
    st.subheader("✅ Iteratif")
    m1, m2, m3 = st.columns(3)
    m1.metric("Total", f"{total_iter} kkal")
    m2.metric("Item", f"{len(hasil_iter)}")
    m3.metric("Waktu", f"{t_iter:.2f} µs")
    st.write(f"**Status:** {status_iter}")
    st.dataframe(to_df(hasil_iter), use_container_width=True, height=320)

with colR:
    st.subheader("🔁 Rekursif")
    m1, m2, m3 = st.columns(3)
    m1.metric("Total", f"{total_rec} kkal")
    m2.metric("Item", f"{len(hasil_rec)}")
    m3.metric("Waktu", f"{t_rec:.2f} µs")
    st.write(f"**Status:** {status_rec}")
    st.dataframe(to_df(hasil_rec), use_container_width=True, height=320)

st.markdown("---")

# =========================
# QUICK COMPARISON ROW
# =========================
c1, c2, c3 = st.columns(3)
faster = "Iteratif" if t_iter < t_rec else ("Rekursif" if t_rec < t_iter else "Seimbang")
same_total = "SAMA" if total_iter == total_rec else "BEDA"

c1.metric("Lebih cepat", faster)
c2.metric("Total hasil", same_total)
c3.metric("Selisih waktu", f"{abs(t_iter - t_rec):.2f} µs")

# =========================
# CHART (OPTIONAL, ringkas)
# =========================
if show_chart:
    st.subheader("📊 Perbandingan Waktu Eksekusi")
    fig, ax = plt.subplots()
    ax.bar(["Iteratif", "Rekursif"], [t_iter, t_rec])
    ax.set_ylabel("Waktu (µs)")
    ax.set_title(f"Target = {target} kkal")
    for i, v in enumerate([t_iter, t_rec]):
        ax.text(i, v * 1.01, f"{v:.2f}", ha="center")
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)

# =========================
# FOOTNOTE
# =========================
st.caption("Catatan: Greedy tidak menjamin solusi optimal global. Pendekatan Closest First memilih kalori terdekat terhadap sisa target.")
