from flask import Flask, render_template, request
import pandas as pd
import plotly
import plotly.express as px
import json
import os
import io

template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'templates'))
app = Flask(__name__, template_folder=template_dir)

@app.route('/', methods=['GET', 'POST'])
def index():
    graphJSON = None
    if request.method == 'POST':
        file = request.files.get('file')
        if file and file.filename != '':
            try:
                # อ่านไฟล์จาก Memory โดยตรงเพื่อรองรับระบบ Read-Only ของ Vercel
                file_bytes = io.BytesIO(file.read())
                df = pd.read_csv(file_bytes)
                
                # สร้างกราฟ Histogram จากคอลัมน์แรก
                fig = px.histogram(df, x=df.columns[0])
                graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
            except Exception as e:
                print(f"Error processing CSV: {e}")
                
    return render_template('index.html', graphJSON=graphJSON)

if __name__ == '__main__':
    app.run(debug=True)