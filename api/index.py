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


def read_csv_bytes(raw: bytes) -> pd.DataFrame:
    """อ่าน CSV โดยลองหลาย encoding (utf-8-sig รองรับ BOM จาก Excel)"""
    last_error = None
    for enc in ('utf-8-sig', 'tis-620', 'cp874'):
        try:
            return pd.read_csv(io.BytesIO(raw), encoding=enc)
        except UnicodeDecodeError as e:
            last_error = e
    raise last_error


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


@app.route('/analyze', methods=['POST'])
def analyze():
    file = request.files.get('file')
    if not file or file.filename == '':
        return jsonify(error='กรุณาเลือกไฟล์ CSV ก่อน'), 400

    raw = file.read()
    if len(raw) > MAX_UPLOAD_BYTES:
        return jsonify(error='ไฟล์ใหญ่เกิน 4 MB กรุณาลดขนาดไฟล์แล้วลองใหม่'), 413

    try:
        df = read_csv_bytes(raw)
    except Exception:
        return jsonify(error='อ่านไฟล์ไม่ได้ กรุณาตรวจสอบว่าเป็นไฟล์ CSV ที่ถูกต้อง'), 400

    if df.empty or len(df.columns) == 0:
        return jsonify(error='ไฟล์ CSV ไม่มีข้อมูล'), 400

    df.columns = [str(c).strip() for c in df.columns]
    columns = list(df.columns)

    # ถ้าไม่ได้เลือกคอลัมน์ ให้ใช้คอลัมน์ตัวเลขตัวแรก (ถ้าไม่มีใช้คอลัมน์แรก)
    column = request.form.get('column')
    if column not in columns:
        numeric = df.select_dtypes(include='number').columns
        column = numeric[0] if len(numeric) else columns[0]

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