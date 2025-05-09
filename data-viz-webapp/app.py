from flask import Flask, render_template, request, redirect, send_file
import os
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from fpdf import FPDF

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
STATIC_FOLDER = 'static'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['STATIC_FOLDER'] = STATIC_FOLDER

# Ensure folders exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(STATIC_FOLDER, exist_ok=True)

@app.route('/')
def index():
    files = os.listdir(UPLOAD_FOLDER)
    return render_template('index.html', files=files)

@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files['file']
    if file and file.filename.endswith('.csv'):
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)
    return redirect('/')

@app.route('/view/<filename>')
def view_file(filename):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    df = pd.read_csv(filepath)

    # Remove duplicates
    df = df.drop_duplicates()

    # Summary stats
    summary = df.describe(include='all').to_html(classes='table table-striped')

    numeric_cols = df.select_dtypes(include='number').columns
    plot_paths = []

    if not numeric_cols.empty:
        # Histogram
        plt.figure(figsize=(6, 4))
        col = numeric_cols[0]
        plt.hist(df[col].dropna(), bins=min(10, len(np.unique(df[col]))), color='skyblue', edgecolor='black')
        plt.title(f'Histogram of {col}')
        plt.xlabel(col)
        plt.ylabel('Frequency')
        plt.tight_layout()
        hist_path = os.path.join(STATIC_FOLDER, f"{filename}_hist.png")
        plt.savefig(hist_path)
        plt.close()
        plot_paths.append(hist_path)

        # Boxplot
        plt.figure(figsize=(6, 4))
        sns.boxplot(data=df[numeric_cols])
        plt.title('Boxplot of Numeric Columns')
        plt.tight_layout()
        box_path = os.path.join(STATIC_FOLDER, f"{filename}_box.png")
        plt.savefig(box_path)
        plt.close()
        plot_paths.append(box_path)

        # Correlation heatmap
        plt.figure(figsize=(6, 5))
        corr = df[numeric_cols].corr()
        sns.heatmap(corr, annot=True, cmap='coolwarm', fmt='.2f')
        plt.title('Correlation Heatmap')
        plt.tight_layout()
        heatmap_path = os.path.join(STATIC_FOLDER, f"{filename}_heatmap.png")
        plt.savefig(heatmap_path)
        plt.close()
        plot_paths.append(heatmap_path)

    return render_template('view.html',
                           filename=filename,
                           summary=summary,
                           plot_paths=[os.path.relpath(p, '.') for p in plot_paths])

@app.route('/download_pdf/<filename>')
def download_pdf(filename):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    df = pd.read_csv(filepath)
    df = df.drop_duplicates()

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Data Summary for {filename}", ln=True, align='C')

    # Summary table
    summary = df.describe(include='all').round(2)
    for col in summary.columns:
        pdf.set_font("Arial", size=10)
        pdf.cell(200, 10, f"\nColumn: {col}", ln=True)
        for stat in summary.index:
            value = summary.at[stat, col]
            pdf.cell(200, 8, f"{stat}: {value}", ln=True)

    # Add plots
    for plot_type in ['hist', 'box', 'heatmap']:
        plot_path = os.path.join(STATIC_FOLDER, f"{filename}_{plot_type}.png")
        if os.path.exists(plot_path):
            pdf.add_page()
            pdf.image(plot_path, w=180)

    pdf_path = os.path.join(STATIC_FOLDER, f"{filename}_report.pdf")
    pdf.output(pdf_path)

    return send_file(pdf_path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)

