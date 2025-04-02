from flask import Flask, render_template, url_for
import os, json

app = Flask(__name__)

@app.route("/")
def index():
    photo_folder = os.path.join(app.static_folder, 'photo_exhibit')
    photos = sorted([f for f in os.listdir(photo_folder) if f.endswith('.jpg')])
    photo_urls = [url_for('static', filename=f'photo_exhibit/{p}') for p in photos]
    photo_urls_json = json.dumps(photo_urls)
    return render_template("index.html", photo_urls_json=photo_urls_json)

@app.route("/cardnews")
def cardnews():
    # 카드뉴스 예시 (나중에 DB 연결 가능)
    posts = [
        {"title": "분리배출 잘하는 법", "image": "card1.jpg", "date": "2025.04.01"},
        {"title": "헷갈리는 재활용", "image": "card2.jpg", "date": "2025.04.01"}
    ]
    return render_template("cardnews.html", posts=posts)

@app.route("/game")
def game():
    return render_template("game.html")

if __name__ == "__main__":
    app.run(debug=True)
