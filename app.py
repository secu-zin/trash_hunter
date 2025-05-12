from flask import Flask, render_template, url_for, request, redirect, session
import os
import json
import sqlite3
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB 제한

ADMIN_PASSWORD = "admin1234"

# ------------------- DB 초기화 -------------------
def init_db():
    with sqlite3.connect('db.sqlite3') as conn:
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                date TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id INTEGER,
                filename TEXT,
                FOREIGN KEY(post_id) REFERENCES posts(id)
            )
        ''')
        conn.commit()

init_db()

# ------------------- 홈페이지 -------------------
@app.route("/")
def index():
    photo_folder = os.path.join(app.static_folder, 'photo_exhibit')
    valid_exts = ('.jpg', '.jpeg', '.png')
    try:
        photos = sorted([
            f for f in os.listdir(photo_folder)
            if f.lower().endswith(valid_exts)
        ])
    except FileNotFoundError:
        photos = []

    photo_urls = [url_for('static', filename=f'photo_exhibit/{photo}') for photo in photos]
    return render_template("index.html", photo_urls_json=json.dumps(photo_urls))

# ------------------- 게임 -------------------
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

# ------------------- 카드뉴스 -------------------
@app.route("/cardnews")
def cardnews():
    with sqlite3.connect('db.sqlite3') as conn:
        c = conn.cursor()
        c.execute('''
            SELECT posts.id, posts.title, posts.date,
                   (SELECT filename FROM images WHERE post_id = posts.id LIMIT 1) as thumbnail
            FROM posts
            ORDER BY posts.id DESC
        ''')
        posts = c.fetchall()
    return render_template('cardnews_index.html', posts=posts)

@app.route('/auth', methods=['GET', 'POST'])
def auth():
    if request.method == 'POST':
        password = request.form['password']
        if password == ADMIN_PASSWORD:
            session['admin'] = True
            return redirect(url_for('create'))
        else:
            return render_template('auth.html', error='비밀번호가 틀렸습니다.')
    return render_template('auth.html')

@app.route('/auth_edit/<int:post_id>', methods=['GET', 'POST'])
def auth_edit(post_id):
    if request.method == 'POST':
        password = request.form['password']
        if password == ADMIN_PASSWORD:
            session[f'edit_auth_{post_id}'] = True
            return redirect(url_for('edit', post_id=post_id))
        else:
            return render_template('auth.html', error='비밀번호가 틀렸습니다.')
    return render_template('auth.html')

@app.route('/auth_delete/<int:post_id>', methods=['GET', 'POST'])
def auth_delete(post_id):
    if request.method == 'POST':
        password = request.form['password']
        if password == ADMIN_PASSWORD:
            session[f'delete_auth_{post_id}'] = True
            return redirect(url_for('delete', post_id=post_id))
        else:
            return render_template('auth.html', error='비밀번호가 틀렸습니다.')
    return render_template('auth.html')

@app.route('/create', methods=['GET', 'POST'])
def create():
    if not session.get('admin'):
        return redirect(url_for('auth'))

    if request.method == 'POST':
        title = request.form['title']
        files = request.files.getlist('images')

        with sqlite3.connect('db.sqlite3') as conn:
            c = conn.cursor()
            c.execute('INSERT INTO posts (title) VALUES (?)', (title,))
            post_id = c.lastrowid

            for file in files:
                if file:
                    filename = secure_filename(file.filename)
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(filepath)
                    c.execute('INSERT INTO images (post_id, filename) VALUES (?, ?)', (post_id, filename))

            conn.commit()
        return redirect(url_for('cardnews'))

    return render_template('create.html')

@app.route('/detail/<int:post_id>')
def detail(post_id):
    with sqlite3.connect('db.sqlite3') as conn:
        c = conn.cursor()
        c.execute('SELECT title, id, date FROM posts WHERE id = ?', (post_id,))
        post = c.fetchone()

        c.execute('SELECT filename FROM images WHERE post_id = ?', (post_id,))
        images = c.fetchall()

    return render_template('detail.html', post=post, images=images, is_admin=session.get('admin', False))

@app.route('/edit/<int:post_id>', methods=['GET', 'POST'])
def edit(post_id):
    if not session.get(f'edit_auth_{post_id}'):
        return redirect(url_for('auth_edit', post_id=post_id))

    with sqlite3.connect('db.sqlite3') as conn:
        c = conn.cursor()

        if request.method == 'POST':
            new_title = request.form['title']
            files = request.files.getlist('images')

            c.execute('UPDATE posts SET title = ? WHERE id = ?', (new_title, post_id))
            c.execute('DELETE FROM images WHERE post_id = ?', (post_id,))

            for file in files:
                if file:
                    filename = secure_filename(file.filename)
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(filepath)
                    c.execute('INSERT INTO images (post_id, filename) VALUES (?, ?)', (post_id, filename))

            conn.commit()
            session.pop(f'edit_auth_{post_id}', None)
            return redirect(url_for('detail', post_id=post_id))

        c.execute('SELECT title FROM posts WHERE id = ?', (post_id,))
        title = c.fetchone()[0]
    return render_template('edit.html', post_id=post_id, title=title)

@app.route('/delete/<int:post_id>')
def delete(post_id):
    if not session.get(f'delete_auth_{post_id}'):
        return redirect(url_for('auth_delete', post_id=post_id))

    with sqlite3.connect('db.sqlite3') as conn:
        c = conn.cursor()
        c.execute('SELECT filename FROM images WHERE post_id = ?', (post_id,))
        images = c.fetchall()

        for img in images:
            img_path = os.path.join(app.config['UPLOAD_FOLDER'], img[0])
            if os.path.exists(img_path):
                os.remove(img_path)

        c.execute('DELETE FROM images WHERE post_id = ?', (post_id,))
        c.execute('DELETE FROM posts WHERE id = ?', (post_id,))
        conn.commit()

    session.pop(f'delete_auth_{post_id}', None)
    return redirect(url_for('cardnews'))

@app.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect(url_for('cardnews'))

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True)
