from flask import Flask, render_template, request, send_file, jsonify
import base64
import os
import zipfile
import uuid
from io import BytesIO
import subprocess

app = Flask(__name__)

# ✅ Firebaseのpublicフォルダに合わせて保存先変更
SAVE_DIR = 'C:/Users/PC1/my-firebase-project/public/generated_cards'
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
    youtube_url = ""  # ✅ 空で初期化しておくことで未入力でもエラー防止

    if request.method == 'POST':
        bio = request.form.get('bio', '')
        bar_color = request.form.get('bar_color', '#4caf50')
        youtube_url = request.form.get('youtube_url', '')

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
        bar_color=bar_color,
        youtube_url=youtube_url,  # ✅ ここでテンプレートに渡す
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

# ✅ FirebaseのHosting公開URLで返すよう変更 + deploy自動化付き
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

    firebase_project_id = 'nfc-card-app-79464'
    firebase_url = f"https://{firebase_project_id}.web.app/generated_cards/{filename}"

    # ✅ firebase.cmd のフルパスを使用して実行
    try:
        subprocess.run(
            ["C:/Users/PC1/AppData/Roaming/npm/firebase.cmd", "deploy", "--only", "hosting"],
            cwd="C:/Users/PC1/my-firebase-project",
            check=True
        )
    except subprocess.CalledProcessError:
        return jsonify({'error': 'Firebaseへのデプロイに失敗しました'}), 500

    return jsonify({'url': firebase_url})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
