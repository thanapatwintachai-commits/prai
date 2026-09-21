from flask import Flask, render_template, request
import pandas as pd
import plotly.express as px
import plotly.io as pio
import os
import io

# กำหนด Absolute path ให้ templates ชัวร์ที่สุดบน Serverless
template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'templates'))
app = Flask(__name__, template_folder=template_dir)

@app.route('/', methods=['GET', 'POST'])
def index():
    graphJSON = None
    if request.method == 'POST':
        file = request.files.get('file')
        if file and file.filename != '':
            try:
                file_bytes = io.BytesIO(file.read())
                df = pd.read_csv(file_bytes)
                
                # สร้างกราฟ Histogram จากคอลัมน์แรก
                fig = px.histogram(df, x=df.columns[0])
                
                # แปลงกราฟเป็น JSON string
                graphJSON = pio.to_json(fig)
            except Exception as e:
                print(f"Error processing CSV: {e}")
                
    return render_template('index.html', graphJSON=graphJSON)

# Export ตัวแปร app ให้ Vercel ดึงไปรัน
app = app