import streamlit as st #dựng toàn bộ giao diện web
import pandas as pd #Xử lý dữ liệu dạng bảng
from streamlit_option_menu import option_menu #Vẽ menu bên trái đẹp hơn, có icon
import plotly.express as px #Vẽ biểu đồ tương tác
import duckdb  # dùng để chạy câu lệnh SQL thẳng trên dữ liệu đang có trong bộ nhớ
import os #Đọc biến môi trường của hệ điều hành — dùng để lấy thông tin trong file .env
import pymysql #Kết nối và chạy câu lệnh SQL thật tới MySQL
from dotenv import load_dotenv #Đọc file .env để lấy thông tin kết nối bí mật (host, mật khẩu...) mà không phải gõ thẳng vào code

load_dotenv()

MYSQL_HOST = os.environ["MYSQL_HOST"]
MYSQL_PORT = int(os.environ.get("MYSQL_PORT", 3306))
MYSQL_USER = os.environ["MYSQL_USER"]
MYSQL_PASSWORD = os.environ["MYSQL_PASSWORD"]
MYSQL_DB = os.environ["MYSQL_DB"]



# Hàm dùng chung: mở kết nối tới MySQL — mọi hàm bên dưới đều gọi
def ket_noi_mysql():
    return pymysql.connect(
        host=MYSQL_HOST, port=MYSQL_PORT, user=MYSQL_USER,
        password=MYSQL_PASSWORD, database=MYSQL_DB,
    )


def load_sach():
    conn = ket_noi_mysql()
    return pd.read_sql("SELECT * FROM books", conn)


def them_sach(ten, thuong_hieu, gia_ban):
    conn = ket_noi_mysql()
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO books (ten_sach, thuong_hieu, tinh_trang, gia_ban, gia_goc, link, nguon) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (ten, thuong_hieu if thuong_hieu else None, None, gia_ban, gia_ban, "", "Thu cong"),
        )
    conn.commit()
    conn.close()
    st.session_state.df_tam = load_sach()


def sua_sach(id_chon, ten_moi, thuong_hieu_moi, gia_ban_moi):
    conn = ket_noi_mysql()
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE books SET ten_sach=%s, thuong_hieu=%s, gia_ban=%s WHERE id=%s",
            (ten_moi, thuong_hieu_moi if thuong_hieu_moi else None, gia_ban_moi, id_chon),
        )
    conn.commit()
    conn.close()
    st.session_state.df_tam = load_sach()


def xoa_sach(id_chon):
    conn = ket_noi_mysql()
    with conn.cursor() as cur:
        cur.execute("DELETE FROM books WHERE id=%s", (id_chon,))
    conn.commit()
    conn.close()
    st.session_state.df_tam = load_sach()


def phuc_hoi_vao_mysql(df_khoiphuc):
    conn = ket_noi_mysql()
    cot = ["id", "ten_sach", "thuong_hieu", "tinh_trang", "gia_ban", "gia_goc", "link", "nguon"]
    # chuyển csv thành giá trị mà MySQL đọc được
    gia_tri = [
        tuple(None if pd.isna(row[c]) else row[c] for c in cot)
        for _, row in df_khoiphuc.iterrows()
    ]
    with conn.cursor() as cur:
        cur.execute("DELETE FROM books")
        cur.executemany(
            "INSERT INTO books (id, ten_sach, thuong_hieu, tinh_trang, gia_ban, gia_goc, link, nguon) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
            gia_tri,
        )
    conn.commit()
    conn.close()
    st.session_state.df_tam = load_sach()

def doc_bang(ten_bang):
    conn = ket_noi_mysql()
    try:
        return pd.read_sql(f"SELECT * FROM {ten_bang}", conn)
    finally:
        conn.close()

TEN_COT_DEP = {
    "id": "ID",
    "ten_sach": "Tên sách",
    "thuong_hieu": "Nhà xuất bản",
    "tinh_trang": "Tình trạng",
    "gia_ban": "Giá bán",
    "gia_goc": "Giá gốc",
    "link": "Đường dẫn",
    "nguon": "Nguồn",
    "chi_so": "Chỉ số",
    "gia_tri": "Giá trị",
    "ty_le_giam": "Tỉ lệ giảm (%)",
    "so_tien_giam": "Số tiền giảm",
}

def doi_ten_cot(df):
    return df.rename(columns=TEN_COT_DEP)

# Cấu hình trang + màu giao diện (màu thật lấy từ .streamlit/config.toml)
st.set_page_config(page_title="So sánh giá sách", layout="wide")


# MỤC 5: Menu bên trái — 6 tab
with st.sidebar:
    chon = option_menu(
        "Phân tích dữ liệu sách",
        ["Tổng quan", "Biểu đồ", "Dữ liệu & CRUD", "Truy vấn", "Kết quả MapReduce", "Sao lưu / Phục hồi"],
        icons=["house", "bar-chart", "pencil-square", "search", "cpu", "arrow-repeat"],
        default_index=0,
        styles={
            "nav-link": {"font-family": "Arial, sans-serif", "font-size": "16px"},
            "nav-link-selected": {
                "font-family": "Arial, sans-serif",
                "font-weight": "600",
                "background-color": "#2563eb",
            },
        },
    )

# Nạp dữ liệu vào bộ nhớ tạm 1 lần duy nhất mỗi phiên
if "df_tam" not in st.session_state:
    st.session_state.df_tam = load_sach()


# TAB "TỔNG QUAN"
if chon == "Tổng quan":
    st.title("Tổng quan thị trường sách")

    try:
        tong_quan = doc_bang("stat_overview")
        so_lieu = dict(zip(tong_quan["chi_so"], tong_quan["gia_tri"]))

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Số sách", f"{int(so_lieu.get('so_sach', 0)):,}")
        c2.metric("Giá bán trung bình", f"{float(so_lieu.get('gia_ban_trung_binh', 0)):,.0f} đ")
        c3.metric("Số nhà xuất bản", int(so_lieu.get('so_nha_xuat_ban', 0)))
        c4.metric("Số nguồn", int(so_lieu.get('so_nguon', 0)))

        st.caption("Nguồn dữ liệu: bảng stat_overview (kết quả MapReduce)")
    except Exception as loi:
        st.warning(f"Không đọc được bảng stat_overview: {loi}")

    st.subheader("Toàn bộ dữ liệu sách")
    st.write(doi_ten_cot(load_sach()))
    


# TAB "BIỂU ĐỒ"
elif chon == "Biểu đồ":
    st.title("Biểu đồ")

    # Biểu đồ 1: cột — giá bán trung bình theo nhà xuất bản
    try:
        d1 = doc_bang("stat_avg_price_by_publisher")
        fig1 = px.bar(d1, x=d1.columns[0], y=d1.columns[1], title="Giá bán trung bình theo nhà xuất bản")
        st.plotly_chart(fig1, use_container_width=True)
    except Exception as loi:
        st.warning(f"Không đọc được bảng stat_avg_price_by_publisher: {loi}")

    # Biểu đồ 2: tròn — tỉ lệ số sách theo nguồn
    try:
        d2 = doc_bang("stat_books_by_source")
        fig2 = px.pie(d2, names=d2.columns[0], values=d2.columns[1], title="Tỉ lệ số sách theo nguồn")
        st.plotly_chart(fig2, use_container_width=True)
    except Exception as loi:
        st.warning(f"Không đọc được bảng stat_books_by_source: {loi}")

    # Biểu đồ 3: phân tán — giá bán theo nguồn (thang log)
    try:
        d3 = doc_bang("price_by_source_scatter")
        fig3 = px.strip(
            d3, x=d3.columns[0], y=d3.columns[1], color=d3.columns[0],
            log_y=True,
            title="Phân tán giá bán theo nguồn (trục giá theo thang log)",
        )
        st.plotly_chart(fig3, use_container_width=True)
    except Exception as loi:
        st.warning(f"Không đọc được bảng price_by_source_scatter: {loi}")

    # Biểu đồ 4: cột — số sách theo tình trạng kho
    try:
        d4 = doc_bang("stat_books_by_status")
        fig4 = px.bar(d4, x=d4.columns[0], y=d4.columns[1], title="Số sách theo tình trạng kho")
        st.plotly_chart(fig4, use_container_width=True)
    except Exception as loi:
        st.warning(f"Không đọc được bảng stat_books_by_status: {loi}")

    # Biểu đồ 5: cột — phân bố khoảng giá bán
    try:
        d5 = doc_bang("price_range_distribution")
        fig5 = px.bar(d5, x=d5.columns[0], y=d5.columns[1], title="Phân bố khoảng giá bán")
        st.plotly_chart(fig5, use_container_width=True)
    except Exception as loi:
        st.warning(f"Không đọc được bảng price_range_distribution: {loi}")


# TAB "DỮ LIỆU & CRUD"
elif chon == "Dữ liệu & CRUD":
    st.title("Dữ liệu và thao tác")

    st.subheader("Thêm sách")
    with st.form("form_them"):
        ten = st.text_input("Tên sách")
        thuong_hieu = st.text_input("Nhà xuất bản (để trống nếu không rõ)")
        gia_ban = st.number_input("Giá bán", min_value=0, step=1000)
        gui = st.form_submit_button("Thêm")

        if gui:
            if not ten:
                st.error("Nhập tên sách trước khi thêm")
            else:
                them_sach(ten, thuong_hieu, gia_ban)
                st.toast("Đã thêm sách vào MySQL", icon="✅")
                st.rerun()

    st.subheader("Sửa / Xóa sách")
    danh_sach_id = st.session_state.df_tam["id"].tolist()
    if danh_sach_id:
        id_chon = st.selectbox("Chọn id sách", danh_sach_id)
        dong_dang_chon = st.session_state.df_tam[st.session_state.df_tam["id"] == id_chon].iloc[0]

        with st.form("form_sua"):
            ten_moi = st.text_input("Tên sách", value=dong_dang_chon["ten_sach"])
            thuong_hieu_moi = st.text_input(
                "Nhà xuất bản",
                value="" if pd.isna(dong_dang_chon["thuong_hieu"]) else dong_dang_chon["thuong_hieu"],
            )
            gia_ban_moi = st.number_input(
                "Giá bán", min_value=0, step=1000, value=int(dong_dang_chon["gia_ban"])
            )
            c1, c2 = st.columns(2)
            luu = c1.form_submit_button("Sửa")
            xoa = c2.form_submit_button("Xóa")

            if luu:
                if not ten_moi:
                    st.error("Nhập tên sách trước khi sửa")
                else:
                    sua_sach(id_chon, ten_moi, thuong_hieu_moi, gia_ban_moi)
                    st.toast(f"Đã sửa sách id {id_chon} trong MySQL", icon="✏️")
                    st.rerun()

            if xoa:
                xoa_sach(id_chon)
                st.toast(f"Đã xóa sách id {id_chon} khỏi MySQL", icon="🗑️")
                st.rerun()
    else:
        st.info("Chưa có sách nào để sửa/xóa")

    st.subheader("Tìm kiếm")
    tu_khoa = st.text_input("Tìm theo tên sách")
    df_hien = st.session_state.df_tam
    if tu_khoa:
        #giữ dòng có tên sách chứa đoạn chữ vừa gõ, case=False bỏ qua hoa thường, na=False coi ô trống là không khớp
        df_hien = df_hien[df_hien["ten_sach"].str.contains(tu_khoa, case=False, na=False)]

    st.dataframe(doi_ten_cot(df_hien), use_container_width=True)


# TAB "TRUY VẤN"
elif chon == "Truy vấn":
    st.title("Truy vấn dữ liệu")
    sach = st.session_state.df_tam

    st.subheader("Lọc theo điều kiện")
    c1, c2, c3 = st.columns(3)

    danh_sach_nxb = ["Tất cả"] + sorted(sach["thuong_hieu"].dropna().unique().tolist())
    nxb_chon = c1.selectbox("Nhà xuất bản", danh_sach_nxb)

    danh_sach_nguon = ["Tất cả"] + sorted(sach["nguon"].dropna().unique().tolist())
    nguon_chon = c2.selectbox("Nguồn", danh_sach_nguon)

    gia_min, gia_max = c3.slider(
        "Khoảng giá bán",
        min_value=0,
        max_value=int(sach["gia_ban"].max()),
        value=(0, int(sach["gia_ban"].max())),
    )

    ket_qua_loc = sach
    if nxb_chon != "Tất cả":
        ket_qua_loc = ket_qua_loc[ket_qua_loc["thuong_hieu"] == nxb_chon]
    if nguon_chon != "Tất cả":
        ket_qua_loc = ket_qua_loc[ket_qua_loc["nguon"] == nguon_chon]
    ket_qua_loc = ket_qua_loc[(ket_qua_loc["gia_ban"] >= gia_min) & (ket_qua_loc["gia_ban"] <= gia_max)]

    st.write(f"Kết quả: {len(ket_qua_loc)} sách")
    st.dataframe(doi_ten_cot(ket_qua_loc), use_container_width=True)

    st.subheader("Truy vấn SQL")
    cau_sql = st.text_area(
        "Nhập câu SQL (chỉ cho phép SELECT)",
        value="SELECT thuong_hieu, AVG(gia_ban) AS gia_tb FROM sach WHERE thuong_hieu IS NOT NULL GROUP BY thuong_hieu",
    )
    if st.button("Thực thi truy vấn"):
        if not cau_sql.strip().lower().startswith("select"):
            st.error("Chỉ cho phép câu SELECT, không cho phép sửa/xóa dữ liệu qua ô này")
        else:
            try:
                ket_qua_sql = duckdb.sql(cau_sql).df()
                st.dataframe(doi_ten_cot(ket_qua_sql), use_container_width=True)
            except Exception as loi:
                st.error(f"Câu SQL bị lỗi: {loi}")

# TAB "KẾT QUẢ MAPREDUCE"
elif chon == "Kết quả MapReduce":
    st.title("Kết quả MapReduce")

    cac_bang = {
        "Giá cao nhất theo nguồn": "max_price_by_source",
        "Sách giảm giá nhiều nhất theo nguồn": "top_discount_by_source",
    }

    ten_hien_thi = st.selectbox("Chọn kết quả để xem", list(cac_bang.keys()))
    ten_bang = cac_bang[ten_hien_thi]

    try:
        ket_qua = doc_bang(ten_bang)
        st.dataframe(doi_ten_cot(ket_qua), use_container_width=True)

        if len(ket_qua.columns) == 2 and pd.api.types.is_numeric_dtype(ket_qua.iloc[:, 1]):
            fig = px.bar(ket_qua, x=ket_qua.columns[0], y=ket_qua.columns[1], title=ten_bang)
            st.plotly_chart(fig, use_container_width=True)
    except Exception as loi:
        st.warning(f"Không đọc được bảng '{ten_bang}': {loi}")

# TAB "SAO LƯU / PHỤC HỒI"
elif chon == "Sao lưu / Phục hồi":
    st.title("Sao lưu / Phục hồi")

    if st.button("Tạo bản sao lưu"):
        ten_file = f"backup_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv"
        st.session_state.df_tam.to_csv(ten_file, index=False, encoding="utf-8-sig")
        st.success(f"Đã lưu: {ten_file}")

    st.subheader("Phục hồi từ file backup")
    file_phuchoi = st.file_uploader("Chọn file backup để phục hồi", type="csv")
    if file_phuchoi is not None:
        df_khoiphuc = pd.read_csv(file_phuchoi, encoding="utf-8-sig")
        st.write(f"File có {len(df_khoiphuc)} dòng. Xem trước:")
        st.dataframe(doi_ten_cot(df_khoiphuc), use_container_width=True)

        xac_nhan = st.checkbox(
            "Tôi hiểu: thao tác này sẽ XÓA TOÀN BỘ dữ liệu hiện có trong bảng `books` "
            "và thay bằng đúng nội dung file này."
        )

        if st.button("Phục hồi vào MySQL"):
            if not xac_nhan:
                st.error("Cần tick vào ô xác nhận phía trên trước khi phục hồi")
            else:
                with st.spinner("Đang phục hồi vào MySQL..."):
                    phuc_hoi_vao_mysql(df_khoiphuc)
                st.toast("Đã phục hồi dữ liệu vào MySQL", icon="🔄")
                st.rerun()
