from flask import Flask, render_template, request, redirect, session, url_for
from pathlib import Path
import sqlite3

#Création de la clés secrète Flask qui protège des attaques CSRF entre autre
app = Flask(__name__)
app.secret_key = 'ClesSecretePostIt'
    
#Fonction qui récupère la connexion à la base de données créée par "connect_db"
def get_db():
    return sqlite3.connect("instance/db.sqlite")
if not Path ("instance/db.sqlite").exists():
    db = get_db()
    sql = Path("db.sqlite").read_text()
    db.executescript(sql)

#On vérifie la session 
def checkSession():
    if 'username' not in session:
        return None
    else:
        return session['username']

@app.route('/')
def index():
    if 'username' in session:
        conn = sqlite3.connect('instance/db.sqlite')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        user_id = session.get("user_id")

        query = 'SELECT id, title, content FROM post WHERE user_id = ?'
        print("Query:", query, "Params:", [user_id])

        cursor.execute(query, [user_id])
        posts = cursor.fetchall()

        conn.close()
    else:
        posts = []

    username = checkSession()
    print(posts)

    return render_template('index.html', username=username, posts=posts or [])

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        #On récupère les données du formulaire
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']

        #On vérifie si l'utilisateur a déjà un compte dans la base de données
        conn = sqlite3.connect('instance/db.sqlite')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM user WHERE username = ?', (username,))
        user = cursor.fetchone()
        if user:
            error = 'Vous avez déjà un compte !'
            #Si oui, on renvoi l'utilisateur à la page register
            return render_template('register.html', error=error)
        
        #Si non, on insert les données dans la base de données
        cursor.execute('INSERT INTO user (username, password, email) VALUES (?, ?, ?)', (username, password, email))
        conn.commit()
        conn.close()

        #Si l'enregistrement en db est bon, on redirige l'utilisateur vers la page de connexion
        return redirect(url_for('login'))

    #Sinon, on le renvoi à la page d'enregistrement
    return render_template('register.html')

#Définition de la route de la fonction de connection
@app.route('/login', methods=['GET', 'POST'])
#Fonction de connection 
def login():
    error = None
    #Utilisation de la méthode "POST" pour récupérer le nom d'utilisateur et le mot de passe du formulaire
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect('instance/db.sqlite')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user WHERE username = ? AND password = ?", (username, password))
        user = cursor.fetchone()
        #Si la connection est réussie, on renvoie l'utilisateur à la page d'accueil
        if user:
            session['username'] = username
            session['user_id'] = user[0]
            conn.close()

            return redirect(url_for('index'))
        else:
            #Si la connection a échouée, on envoie un message d'erreur
            error = 'Nom d\'utilisateur ou mot de passe invalide'
            conn.close()
            return render_template('login.html', error=error)
    
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))


@app.route('/create_post', methods=['GET', 'POST'])
def create_post():
    if 'username' not in session:
        return redirect(url_for('register'))
        
    if request.method == 'POST':

        #On réfupère les données du formulaire de création de post
        title = request.form['title']
        content = request.form['content']

        #On récupère l'id de l'utilisateur à partir de la session
        conn = sqlite3.connect('instance/db.sqlite')
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM user WHERE username = ?', (session['username'],))
        user_id = cursor.fetchone()[0]

        #On insert les données dans la base de données
        cursor.execute('INSERT INTO post (title, content, user_id) VALUES (?, ?, ?)', (title, content, user_id))
        conn.commit()
        conn.close()

        #On redirige l'utilisateur vers la page d'accueil
        return redirect(url_for('index'))

    # Affichage du formulaire de création de post
    return render_template('create_post.html')

@app.route('/delete_post/<int:post_id>', methods=['GET', 'POST'])
def delete_post(post_id):

    conn = sqlite3.connect('instance/db.sqlite')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM post WHERE id = ?', (post_id,))
    post = cursor.fetchone()

    #On supprime le post
    if request.method == 'POST':
        cursor.execute('DELETE FROM post WHERE id = ?', (post_id,))
        conn.commit()
        conn.close()

        #On redirige vers la page d'accueil
        return redirect(url_for('index'))

    #On affiche une page pour confirmer que le post n'existe plus
    return render_template('success.html', post=post)