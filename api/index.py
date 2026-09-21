from flask import Flask, render_template, request, flash
import pandas as pd
import plotly.express as px
import plotly.io as pio
import os
import io

# กำหนด Path ให้ถอยออกจากโฟลเดอร์ api ไปยัง templates ใน Root Directory
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
template_dir = os.path.join(base_dir, 'templates')

app = Flask(__name__, template_folder=template_dir)
app.secret_key = os.environ.get('SECRET_KEY', 'super-secret-key')

@app.route('/', methods=['GET', 'POST'])
def index():
    graphJSON = None
    
    if request.method == 'POST':
        file = request.files.get('file')
        
        if file and file.filename != '':
            filename = file.filename.lower().strip()
            
            # เช็กว่าไฟล์ลงท้ายด้วย .csv หรือไม่ (รวมถึงรองรับชื่อไฟล์แปลกๆ)
            if not filename.endswith('.csv'):
                flash('กรุณาอัปโหลดไฟล์ประเภท .csv เท่านั้น', 'danger')
                return render_template('index.html', graphJSON=graphJSON)

            try:
                # อ่านไฟล์ด้วย BytesIO
                file_bytes = io.BytesIO(file.read())
                
                # อ่าน CSV โดยใช้ encoding=utf-8 หรือ latin-1 สำรองถ้ามีภาษาไทย
                try:
                    df = pd.read_csv(file_bytes, encoding='utf-8')
                except UnicodeDecodeError:
                    file_bytes.seek(0)
                    df = pd.read_csv(file_bytes, encoding='tis-620')

                if df.empty or len(df.columns) == 0:
                    flash('ไฟล์ CSV ไม่มีข้อมูลหรือไม่ถูกต้อง', 'warning')
                else:
                    first_col = df.columns[0]
                    fig = px.histogram(
                        df, 
                        x=first_col, 
                        title=f'Histogram แสดงผลข้อมูล: {first_col}',
                        template='plotly_white'
                    )
                    graphJSON = pio.to_json(fig)

            except Exception as e:
                print(f"Error processing CSV: {e}")
                flash(f'เกิดข้อผิดพลาดในการอ่านไฟล์: {str(e)}', 'danger')
        else:
            flash('กรุณาเลือกไฟล์ CSV ก่อนส่งข้อมูล', 'warning')
                
    return render_template('index.html', graphJSON=graphJSON)

app = app