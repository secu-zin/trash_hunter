from flask import Flask, render_template, url_for
import os
import json

app = Flask(__name__)

@app.route("/")
def index():
    photo_folder = os.path.join(app.static_folder, 'photo_exhibit')
    
    # 이미지 확장자 목록
    valid_exts = ('.jpg', '.jpeg', '.png')
    
    # 실제 파일 경로 읽기
    try:
        photos = sorted([
            f for f in os.listdir(photo_folder)
            if f.lower().endswith(valid_exts)
        ])
    except FileNotFoundError:
        print("⚠️ 'photo_exhibit' 폴더를 찾을 수 없습니다.")
        photos = []

    # URL 생성
    photo_urls = [
        url_for('static', filename=f'photo_exhibit/{photo}')
        for photo in photos
    ]

    print("📸 이미지 경로 리스트:", photo_urls)

    photo_urls_json = json.dumps(photo_urls)
    return render_template("index.html", photo_urls_json=photo_urls_json)

@app.route("/cardnews")
def cardnews():
    return render_template("cardnews.html")

@app.route("/game")
def game_menu():
    return render_template("game_menu.html")

@app.route("/game/avoid")
def game_avoid():
    return render_template("game_avoid.html")

@app.route("/game/recycle")
def game_recycle():
    return render_template("game_recycle.html")

@app.route("/game/matchcard")
def game_matchcard():
    return render_template("game_matchcard.html")

if __name__ == "__main__":
    app.run(debug=True)
