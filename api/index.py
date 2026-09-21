from flask import Flask, render_template, request, flash
import pandas as pd
import plotly.express as px
import plotly.io as pio
import os
import io

# กำหนด Path ให้ถอยออกจาก api ไปยัง templates
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
template_dir = os.path.join(base_dir, 'templates')

app = Flask(__name__, template_folder=template_dir)
app.secret_key = os.environ.get('SECRET_KEY', 'super-secret-key')

@app.route('/', methods=['GET', 'POST'])
def index():
    graphJSON = None
    
    if request.method == 'POST':
        # ดึงไฟล์จากฟอร์ม
        file = request.files.get('file')
        
        if file and file.filename != '':
            try:
                # อ่านไฟล์ด้วย pandas โดยตรง
                file_bytes = io.BytesIO(file.read())
                
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
                flash('ไม่สามารถอ่านไฟล์ได้ กรุณาตรวจสอบว่าเป็นไฟล์ CSV ที่ถูกต้อง', 'danger')
        else:
            flash('กรุณาเลือกไฟล์ก่อนกดส่งข้อมูล', 'warning')
                
    return render_template('index.html', graphJSON=graphJSON)

app = app