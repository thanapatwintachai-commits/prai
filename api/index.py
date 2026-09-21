from flask import Flask, render_template, request
import pandas as pd
import plotly
import plotly.express as px
import json
import os

# กำหนด path ให้หาโฟลเดอร์ templates เจอทั้งแบบ Local และ Vercel
template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'templates'))
app = Flask(__name__, template_folder=template_dir)

@app.route('/', methods=['GET', 'POST'])
def index():
    graphJSON = None
    if request.method == 'POST':
        file = request.files.get('file')
        if file and file.filename != '':
            df = pd.read_csv(file)
            fig = px.histogram(df, x=df.columns[0])
            graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
            
    return render_template('index.html', graphJSON=graphJSON)

if __name__ == '__main__':
    app.run(debug=True)