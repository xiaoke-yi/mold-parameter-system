import base64
import json
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st


APP_DIR = Path(__file__).parent
DB_PATH = APP_DIR / "molds.db"
TABLE_SCHEMAS = {
    "射出参数": (["六段", "五段", "四段", "三段", "二段", "一段"], ["位置 (mm)", "压力 (bar)", "速度 (%)"]),
    "保压参数": (["六段", "五段", "四段", "三段", "二段", "一段"], ["压力 (bar)", "速度 (%)", "时间 (s)"]),
    "开模设定": (["一段", "二段", "三段", "低压", "高压"], ["位置 (mm)", "压力 (bar)", "速度 (%)"]),
    "关模设定": (["五段", "四段", "三段", "二段", "一段"], ["位置 (mm)", "压力 (bar)", "速度 (%)"]),
    "托进设定": (["一段", "二段"], ["位置 (mm)", "压力 (bar)", "速度 (%)", "延迟 (s)"]),
    "托退设定": (["二段", "一段"], ["位置 (mm)", "压力 (bar)", "速度 (%)", "延迟 (s)"]),
}


def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """CREATE TABLE IF NOT EXISTS molds (
        id TEXT PRIMARY KEY, code TEXT UNIQUE NOT NULL, name TEXT NOT NULL,
        status TEXT, updated_at TEXT, payload TEXT NOT NULL)"""
    )
    conn.commit()
    return conn


def blank_table(columns, rows):
    return [{"参数": row, **{column: 0.0 for column in columns}} for row in rows]


def blank_mold():
    return {
        "id": str(uuid.uuid4()), "code": "", "name": "未命名模具", "status": "待验证",
        "machine": "", "product": "", "material": "", "cavities": 0, "owner": "",
        "quick_tip": "", "transfer_mode": "时间", "transfer_value": 0.0,
        "open_stroke": 0.0, "platen_position": 0.0, "thrust_position": 0.0,
        "ejector_mode": "定次", "ejector_count": 0, "ejector_position": 0.0,
        "tables": {name: blank_table(*schema) for name, schema in TABLE_SCHEMAS.items()},
        "hoses": [], "notes": "", "images": [], "updated_at": datetime.now().isoformat(timespec="seconds"),
    }


def demo_mold():
    mold = blank_mold()
    mold.update({"code": "1255D0005", "name": "示例模具", "quick_tip": "参数依据现场照片录入，首次上机请由师傅复核。",
                 "open_stroke": 260.0, "platen_position": 269.8, "thrust_position": 233.1,
                 "ejector_mode": "定次", "ejector_count": 2, "ejector_position": 0.2,
                 "transfer_mode": "时间", "transfer_value": 7.0})
    values = {
        "射出参数": [[0, 0, 0, 0, 0, 20], [0, 0, 0, 0, 60, 62], [0, 0, 0, 0, 18, 22]],
        "开模设定": [[200, 200, 35, 1.8, 0], [30, 30, 25, 8, 120], [30, 30, 25, 15, 25]],
        "关模设定": [[260, 200, 100, 40, 5], [55, 55, 80, 80, 120], [30, 30, 30, 15, 20]],
        "托进设定": [[42, 43], [85, 85], [35, 35], [0, 0]],
        "托退设定": [[1, 40], [65, 65], [50, 50], [0, 0]],
    }
    for table_name, rows in values.items():
        columns, row_names = TABLE_SCHEMAS[table_name]
        mold["tables"][table_name] = [
            {"参数": row_names[i], **dict(zip(columns, row_values))} for i, row_values in enumerate(rows)
        ]
    return mold


def list_molds():
    with connect() as conn:
        rows = conn.execute("SELECT payload FROM molds ORDER BY updated_at DESC").fetchall()
    return [json.loads(row[0]) for row in rows]


def save_mold(mold):
    mold["updated_at"] = datetime.now().isoformat(timespec="seconds")
    with connect() as conn:
        conn.execute(
            """INSERT INTO molds(id, code, name, status, updated_at, payload) VALUES(?,?,?,?,?,?)
            ON CONFLICT(id) DO UPDATE SET code=excluded.code, name=excluded.name,
            status=excluded.status, updated_at=excluded.updated_at, payload=excluded.payload""",
            (mold["id"], mold["code"], mold["name"], mold["status"], mold["updated_at"], json.dumps(mold, ensure_ascii=False)),
        )
        conn.commit()


def delete_mold(mold_id):
    with connect() as conn:
        conn.execute("DELETE FROM molds WHERE id=?", (mold_id,))
        conn.commit()


def ensure_demo():
    if not list_molds():
        save_mold(demo_mold())


def to_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def table_editor(mold, name):
    columns, rows = TABLE_SCHEMAS[name]
    source = mold.get("tables", {}).get(name) or blank_table(columns, rows)
    frame = pd.DataFrame(source).reindex(columns=["参数", *columns])
    return st.data_editor(
        frame, hide_index=True, use_container_width=True, key=f"{mold['id']}_{name}",
        disabled=["参数"], column_config={"参数": st.column_config.TextColumn(width="medium")},
    ).to_dict("records")


st.set_page_config(page_title="模具参数库", page_icon="🧰", layout="wide")
st.markdown("""
<style>
[data-testid="stAppViewContainer"]{background:#f4f7f8}.block-container{padding-top:1.5rem;max-width:1400px}
[data-testid="stSidebar"]{background:#12343b}[data-testid="stSidebar"] *{color:#fff}
.hero{background:linear-gradient(110deg,#12343b,#0c7c72);padding:24px 28px;border-radius:16px;color:white;margin-bottom:18px}
.hero h1{margin:0;font-size:30px}.hero p{margin:6px 0 0;color:#d5e8e7}.tip{background:#e4f3f1;border-left:4px solid #0c7c72;padding:12px 15px;border-radius:8px}
</style>
""", unsafe_allow_html=True)

ensure_demo()
molds = list_molds()

with st.sidebar:
    st.title("🧰 模具参数库")
    st.caption("打样中心调机参考")
    query = st.text_input("搜索", placeholder="模具编号、名称、产品…")
    filtered = [m for m in molds if query.lower() in f"{m['code']} {m['name']} {m.get('product','')}".lower()]
    options = {f"{m['code']} · {m['name']}": m["id"] for m in filtered}
    current_id = st.session_state.get("current_id")
    if current_id not in [m["id"] for m in molds]:
        current_id = molds[0]["id"] if molds else None
        st.session_state.current_id = current_id
    if options:
        labels = list(options)
        selected_index = next((i for i, label in enumerate(labels) if options[label] == current_id), 0)
        selected_label = st.radio("模具列表", labels, index=selected_index)
        selected_id = options[selected_label]
        if selected_id != current_id:
            st.session_state.current_id = selected_id
            st.rerun()
    if st.button("＋ 新建模具", use_container_width=True):
        new = blank_mold()
        new["code"] = f"NEW-{datetime.now():%m%d%H%M}"
        save_mold(new)
        st.session_state.current_id = new["id"]
        st.rerun()
    st.divider()
    backup = json.dumps({"version": 1, "molds": molds}, ensure_ascii=False, indent=2)
    st.download_button("⬇ 导出全部备份", backup, "模具参数备份.json", "application/json", use_container_width=True)
    imported = st.file_uploader("导入 JSON 备份", type="json")
    if imported and st.button("导入备份", use_container_width=True):
        try:
            imported_molds = json.load(imported).get("molds", [])
            for item in imported_molds:
                if item.get("id") and item.get("code") and item.get("name"):
                    save_mold(item)
            st.success(f"已导入 {len(imported_molds)} 条记录")
            st.rerun()
        except Exception as exc:
            st.error(f"导入失败：{exc}")

mold = next((m for m in molds if m["id"] == st.session_state.get("current_id")), molds[0])
st.markdown(f'<div class="hero"><h1>{mold["code"]} · {mold["name"]}</h1><p>最后更新：{mold.get("updated_at", "-")}　状态：{mold.get("status", "-")}</p></div>', unsafe_allow_html=True)

tab_basic, tab_injection, tab_clamp, tab_ejector, tab_hoses, tab_notes = st.tabs(
    ["基本信息", "射出参数", "模座 / 开关模", "托模参数", "油管使用", "图文备注"]
)

with tab_basic:
    left, right = st.columns(2)
    code = left.text_input("模具编号 *", mold["code"], key=f"{mold['id']}_code")
    name = right.text_input("模具名称 *", mold["name"], key=f"{mold['id']}_name")
    machine = left.text_input("适用机台", mold.get("machine", ""), key=f"{mold['id']}_machine")
    product = right.text_input("产品名称 / 料号", mold.get("product", ""), key=f"{mold['id']}_product")
    material = left.text_input("材料", mold.get("material", ""), key=f"{mold['id']}_material")
    cavities = right.number_input("型腔数", min_value=0, value=int(mold.get("cavities", 0)), key=f"{mold['id']}_cavities")
    owner = left.text_input("记录人", mold.get("owner", ""), key=f"{mold['id']}_owner")
    statuses = ["可用", "待验证", "维修中", "停用"]
    status = right.selectbox("状态", statuses, index=statuses.index(mold.get("status", "待验证")), key=f"{mold['id']}_status")
    quick_tip = st.text_area("快速提示", mold.get("quick_tip", ""), placeholder="换模时最需要先知道的事项", key=f"{mold['id']}_quick")

with tab_injection:
    st.subheader("射出阶段")
    injection = table_editor(mold, "射出参数")
    c1, c2 = st.columns(2)
    transfer_modes = ["时间", "位置", "压力"]
    transfer_mode = c1.selectbox("转保压方式", transfer_modes, index=transfer_modes.index(mold.get("transfer_mode", "时间")), key=f"{mold['id']}_transfer_mode")
    transfer_value = c2.number_input("转保压数值", value=to_float(mold.get("transfer_value")), key=f"{mold['id']}_transfer_value")
    st.subheader("保压阶段")
    holding = table_editor(mold, "保压参数")

with tab_clamp:
    c1, c2, c3 = st.columns(3)
    open_stroke = c1.number_input("开模行程 (mm)", value=to_float(mold.get("open_stroke")), key=f"{mold['id']}_open_stroke")
    platen_position = c2.number_input("模座位置 (mm)", value=to_float(mold.get("platen_position")), key=f"{mold['id']}_platen")
    thrust_position = c3.number_input("推力座位置 (mm)", value=to_float(mold.get("thrust_position")), key=f"{mold['id']}_thrust")
    st.subheader("开模设定")
    open_table = table_editor(mold, "开模设定")
    st.subheader("关模设定")
    close_table = table_editor(mold, "关模设定")

with tab_ejector:
    c1, c2, c3 = st.columns(3)
    ejector_modes = ["定次", "保持", "震动"]
    ejector_mode = c1.selectbox("托模方式", ejector_modes, index=ejector_modes.index(mold.get("ejector_mode", "定次")), key=f"{mold['id']}_eject_mode")
    ejector_count = c2.number_input("托模次数", min_value=0, value=int(mold.get("ejector_count", 0)), key=f"{mold['id']}_eject_count")
    ejector_position = c3.number_input("托模位置 (mm)", value=to_float(mold.get("ejector_position")), key=f"{mold['id']}_eject_pos")
    st.subheader("托进设定")
    eject_forward = table_editor(mold, "托进设定")
    st.subheader("托退设定")
    eject_back = table_editor(mold, "托退设定")

with tab_hoses:
    st.caption("逐条记录油管接口、用途和接法。可在表格底部直接添加新行。")
    hose_columns = ["接口 / 编号", "用途", "规格", "数量", "连接位置 / 方向", "备注"]
    hose_frame = pd.DataFrame(mold.get("hoses", []), columns=hose_columns)
    hoses = st.data_editor(hose_frame, num_rows="dynamic", hide_index=True, use_container_width=True, key=f"{mold['id']}_hoses").fillna("").to_dict("records")

with tab_notes:
    notes = st.text_area("文字备注", mold.get("notes", ""), height=180, placeholder="接管位置、异常处理、成型注意事项…", key=f"{mold['id']}_notes")
    existing_images = mold.get("images", [])
    if existing_images:
        st.caption("已保存图片")
        cols = st.columns(4)
        remove_images = []
        for i, image in enumerate(existing_images):
            cols[i % 4].image(base64.b64decode(image["data"]), caption=image.get("name", f"图片{i+1}"), use_container_width=True)
            if cols[i % 4].checkbox("保存时删除", key=f"{mold['id']}_remove_image_{i}"):
                remove_images.append(i)
    else:
        remove_images = []
    uploads = st.file_uploader("添加现场图片", type=["jpg", "jpeg", "png", "webp"], accept_multiple_files=True, key=f"{mold['id']}_uploads")

st.divider()
save_col, copy_col, delete_col, _ = st.columns([1, 1, 1, 4])
if save_col.button("💾 保存更改", type="primary", use_container_width=True):
    if not code.strip() or not name.strip():
        st.error("模具编号和名称不能为空。")
    else:
        mold.update({"code": code.strip(), "name": name.strip(), "machine": machine, "product": product,
                     "material": material, "cavities": cavities, "owner": owner, "status": status,
                     "quick_tip": quick_tip, "transfer_mode": transfer_mode, "transfer_value": transfer_value,
                     "open_stroke": open_stroke, "platen_position": platen_position, "thrust_position": thrust_position,
                     "ejector_mode": ejector_mode, "ejector_count": ejector_count, "ejector_position": ejector_position,
                     "hoses": hoses, "notes": notes})
        mold["tables"] = {"射出参数": injection, "保压参数": holding, "开模设定": open_table,
                          "关模设定": close_table, "托进设定": eject_forward, "托退设定": eject_back}
        mold["images"] = [img for i, img in enumerate(existing_images) if i not in remove_images]
        for upload in uploads:
            mold["images"].append({"name": upload.name, "type": upload.type, "data": base64.b64encode(upload.getvalue()).decode("ascii")})
        try:
            save_mold(mold)
            st.success("保存成功")
            st.rerun()
        except sqlite3.IntegrityError:
            st.error("该模具编号已存在，请使用唯一编号。")

if copy_col.button("复制为新模具", use_container_width=True):
    copied = json.loads(json.dumps(mold))
    copied["id"] = str(uuid.uuid4())
    copied["code"] = f"{mold['code']}-副本"
    copied["name"] = f"{mold['name']}（副本）"
    save_mold(copied)
    st.session_state.current_id = copied["id"]
    st.rerun()

if delete_col.button("删除模具", use_container_width=True):
    st.session_state.confirm_delete = True
if st.session_state.get("confirm_delete"):
    st.warning(f"确定删除 {mold['code']} · {mold['name']}？")
    yes, no, _ = st.columns([1, 1, 5])
    if yes.button("确认删除", type="primary"):
        delete_mold(mold["id"])
        st.session_state.confirm_delete = False
        st.session_state.current_id = None
        st.rerun()
    if no.button("取消"):
        st.session_state.confirm_delete = False
        st.rerun()
