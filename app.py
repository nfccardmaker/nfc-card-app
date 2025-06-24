from flask import Flask, render_template, request, send_file, jsonify
import base64
import os
import zipfile
import uuid
from io import BytesIO
import requests
import subprocess  # ← ✅ 追加：Firebase CLI実行用

app = Flask(__name__)

SAVE_DIR = 'user_cards'
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
    youtube_url = ""

    if request.method == 'POST':
        bio = request.form.get('bio', '')
        bar_color = request.form.get('bar_color', '#4caf50')
        youtube_url = request.form.get('youtube_url', '')

        photo = request.files.get('photo')
        if photo and photo.filename:
            image_data = base64.b64encode(photo.read()).decode('utf-8')

        bg = request.files.get('background')
        if bg and bg.filename:
            bg_data = base64.b64encode(bg.read()).decode('utf-8')

    return render_template(
        'preview.html',
        bio=bio.replace('\n', '<br>'),
        image_data=image_data,
        bg_data=bg_data,
        bar_color=bar_color,
        youtube_url=youtube_url,
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

@app.route('/generate_url', methods=['POST'])
def generate_url():
    html_data = request.form.get('html')
    if not html_data:
        return jsonify({'error': 'HTMLデータがありません'}), 400

    unique_id = str(uuid.uuid4())
    filename = f"{unique_id}.html"
    filepath = os.path.join(SAVE_DIR, filename)

    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_data)
        print(f"✅ HTMLファイルを保存しました: {filepath}")
    except Exception as e:
        print(f"❌ 保存エラー: {e}")
        return jsonify({'error': '保存に失敗しました'}), 500

    github_token = os.getenv('GITHUB_TOKEN')
    if not github_token:
        return jsonify({'error': 'GitHubトークンが未設定です'}), 500

    repo_owner = 'nfccardmaker'
    repo_name = 'nfc-card-app'
    github_api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/user_cards/{filename}"

    with open(filepath, "rb") as f:
        content = f.read()
    encoded_content = base64.b64encode(content).decode('utf-8')

    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github+json"
    }
    data = {
        "message": f"Add {filename}",
        "content": encoded_content,
        "branch": "main"
    }

    response = requests.put(github_api_url, headers=headers, json=data)
    if response.status_code >= 400:
        print("❌ GitHub Upload Failed:", response.json())
        return jsonify({'error': 'GitHubアップロード失敗'}), 500

    # ✅ Firebase Hosting にデプロイ実行
    firebase_token = os.environ.get("FIREBASE_TOKEN")
    if firebase_token:
        try:
            subprocess.run(
                ["firebase", "deploy", "--only", "hosting", "--token", firebase_token],
                check=True
            )
            print("✅ Firebase にデプロイ完了")
        except subprocess.CalledProcessError as e:
            print("❌ Firebase デプロイ失敗:", e)
            return jsonify({'error': 'Firebaseデプロイ失敗'}), 500
    else:
        print("⚠️ 環境変数 FIREBASE_TOKEN が未設定です")

    firebase_project_id = 'nfc-card-app-79464'
    firebase_url = f"https://{firebase_project_id}.web.app/user_cards/{filename}"
    return jsonify({'url': firebase_url})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
