import io
import os

import pandas as pd
import plotly.express as px
import plotly.io as pio
from flask import Flask, jsonify, render_template, request

# templates/ อยู่นอกโฟลเดอร์ api/
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
app = Flask(__name__, template_folder=os.path.join(base_dir, 'templates'))
app.secret_key = os.environ.get('SECRET_KEY', 'dev-only-change-me')

# Vercel จำกัด request body ~4.5 MB
MAX_UPLOAD_BYTES = 4 * 1024 * 1024
app.config['MAX_CONTENT_LENGTH'] = MAX_UPLOAD_BYTES + 512 * 1024


def detect_delimiter(text: str) -> str:
    """เดาตัวคั่นจากบรรทัดหัวตาราง (tab, comma, semicolon, pipe)"""
    header = text.splitlines()[0] if text else ''
    counts = {d: header.count(d) for d in ('\t', ',', ';', '|')}
    best = max(counts, key=counts.get)
    return best if counts[best] > 0 else ','


def read_table_bytes(raw: bytes) -> pd.DataFrame:
    """อ่านไฟล์ตาราง (CSV / TSV / TXT) โดยเดา encoding และตัวคั่นอัตโนมัติ
    utf-8-sig รองรับ BOM จาก Excel"""
    last_error = None
    for enc in ('utf-8-sig', 'tis-620', 'cp874'):
        try:
            text = raw.decode(enc)
        except UnicodeDecodeError as e:
            last_error = e
            continue
        sep = detect_delimiter(text)
        df = pd.read_csv(io.StringIO(text), sep=sep, skipinitialspace=True)
        # ตัดช่องว่างหน้า-หลังข้อความ (เช่น "Production       " กับ "Production" จะได้เป็นกลุ่มเดียวกัน)
        for col in df.select_dtypes(include=['object', 'string']).columns:
            df[col] = df[col].str.strip()
        return df
    raise last_error


def pick_default_column(df: pd.DataFrame) -> str:
    """เลือกคอลัมน์เริ่มต้น: ตัวเลขตัวแรกที่ไม่ใช่รหัส (ID) ถ้าไม่มีใช้คอลัมน์แรก"""
    for col in df.select_dtypes(include='number').columns:
        is_id_name = str(col).lower().endswith('id')
        is_unique = df[col].nunique(dropna=True) == len(df)
        if not is_id_name and not is_unique:
            return col
    numeric = df.select_dtypes(include='number').columns
    return numeric[0] if len(numeric) else df.columns[0]


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


@app.route('/analyze', methods=['POST'])
def analyze():
    file = request.files.get('file')
    if not file or file.filename == '':
        return jsonify(error='กรุณาเลือกไฟล์ก่อน'), 400

    raw = file.read()
    if len(raw) > MAX_UPLOAD_BYTES:
        return jsonify(error='ไฟล์ใหญ่เกิน 4 MB กรุณาลดขนาดไฟล์แล้วลองใหม่'), 413

    try:
        df = read_table_bytes(raw)
    except Exception:
        return jsonify(error='อ่านไฟล์ไม่ได้ กรุณาตรวจสอบว่าเป็นไฟล์ตาราง (CSV, TSV หรือ TXT) ที่ถูกต้อง'), 400

    if df.empty or len(df.columns) == 0:
        return jsonify(error='ไฟล์ไม่มีข้อมูล'), 400

    df.columns = [str(c).strip() for c in df.columns]
    columns = list(df.columns)

    # ถ้าไม่ได้เลือกคอลัมน์ ให้เลือกคอลัมน์เริ่มต้นให้อัตโนมัติ
    column = request.form.get('column')
    if column not in columns:
        column = pick_default_column(df)

    fig = px.histogram(
        df,
        x=column,
        title=f'การกระจายของข้อมูล: {column}',
        template='plotly_white',
    )
    fig.update_layout(bargap=0.05, margin=dict(l=40, r=20, t=60, b=40))

    return jsonify(
        columns=columns,
        column=column,
        rows=int(len(df)),
        graph=pio.to_json(fig),
    )


@app.errorhandler(413)
def too_large(_):
    return jsonify(error='ไฟล์ใหญ่เกิน 4 MB กรุณาลดขนาดไฟล์แล้วลองใหม่'), 413