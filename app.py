from flask import Flask, render_template, request, send_file, jsonify
import base64
import os
import zipfile
import uuid
from io import BytesIO

app = Flask(__name__)

# 保存先フォルダのパス
SAVE_DIR = 'static/user_cards'
os.makedirs(SAVE_DIR, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/preview', methods=['GET', 'POST'])
def preview():
    bio = ""
    image_data = None
    bg_data = None
    bar_color = '#4caf50'

    if request.method == 'POST':
        bio = request.form.get('bio', '')
        bar_color = request.form.get('bar_color', '#4caf50')

        # プロフィール画像
        photo = request.files.get('photo')
        if photo and photo.filename:
            image_data = base64.b64encode(photo.read()).decode('utf-8')

        # 背景画像
        bg = request.files.get('background')
        if bg and bg.filename:
            bg_data = base64.b64encode(bg.read()).decode('utf-8')

    return render_template(
        'preview.html',
        bio=bio.replace('\n', '<br>'),
        image_data=image_data,
        bg_data=bg_data,
        bar_color=bar_color
    )

@app.route('/download', methods=['POST'])
def download():
    profile_data = request.form['profile_data']
    bg_data = request.form['bg_data']
    description = request.form['description']

    html_content = render_template('preview_template.html',
                                   profile_data=profile_data,
                                   bg_data=bg_data,
                                   description=description)

    # HTMLをzipに保存
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'a', zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr('index.html', html_content)
    zip_buffer.seek(0)

    return send_file(
        zip_buffer,
        mimetype='application/zip',
        as_attachment=True,
        download_name='business_card.zip'
    )

# ✅ 完成ボタンでURLを発行して返す
@app.route('/generate_url', methods=['POST'])
def generate_url():
    html_data = request.form.get('html')
    if not html_data:
        return jsonify({'error': 'HTMLデータがありません'}), 400

    unique_id = str(uuid.uuid4())
    filename = f"{unique_id}.html"
    filepath = os.path.join(SAVE_DIR, filename)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html_data)

    full_url = f"/static/user_cards/{filename}"
    return jsonify({'url': full_url})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
