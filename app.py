from flask import Flask, render_template, request, jsonify, send_from_directory, redirect, url_for, session, flash, get_flashed_messages, abort
import random
import os
import secrets
import string
import json
import sqlite3
import shutil
from flask_socketio import SocketIO, emit, join_room


app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'  
socketio = SocketIO(app)
    
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def check_authorization(f):
  def decorated_function(*args, **kwargs):
    # Verificar si el usuario está autenticado y tiene permiso para acceder a /admin
    if 'username' not in session or session['username'] not in ['Miguel N.', 'Admin']:
        # El usuario no está autorizado, redirigirlo a la página anterior
        return redirect(request.referrer or '/')
    return f(*args, **kwargs)
  return decorated_function
# Modifica la función like() para devolver el recuento actualizado de likes
# Modifica la función like() para devolver el recuento actualizado de likes
@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404
  
@app.route('/loading')
def loading():
    return render_template('loading.html')

@app.route('/like', methods=['POST'])
def like():
  data = request.json
  image_id = data.get('image_id')
  action = data.get('action', 'like')  # Por defecto, la acción es 'like'
  username = session.get(
      'username')  # Obtener el nombre de usuario de la sesión

  if username:
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    # Verificar si el usuario ya ha dado like
    c.execute("SELECT * FROM likes WHERE user_id=? AND image_id=?",
              (username, image_id))
    existing_like = c.fetchone()

    if action == 'like':
      if not existing_like:
        # Registrar el like
        c.execute("INSERT INTO likes (user_id, image_id) VALUES (?, ?)",
                  (username, image_id))
    else:  # Si la acción es 'unlike'
      if existing_like:
        # Remover el like
        c.execute("DELETE FROM likes WHERE user_id=? AND image_id=?",
                  (username, image_id))

    # Obtener el recuento actualizado de likes para la imagen
    c.execute("SELECT COUNT(*) FROM likes WHERE image_id=?", (image_id, ))
    likes_count = c.fetchone()[0]

    conn.commit()
    conn.close()

    # Devolver el recuento actualizado de likes como respuesta
    return jsonify({'likesCount': likes_count})

  return jsonify({'success': False, 'message': 'Usuario no autenticado'}), 401


@app.route('/likes', methods=['GET'])
def get_likes():
  conn = sqlite3.connect(DATABASE)
  c = conn.cursor()
  c.execute("SELECT image_id, COUNT(*) FROM likes GROUP BY image_id")
  likes = dict(c.fetchall())
  conn.close()
  return jsonify(likes)


def load_titles():
  try:
    with open('titles.json', 'r') as f:
      return json.load(f)
  except FileNotFoundError:
    return {}


titles = load_titles()


def save_titles():
  with open('titles.json', 'w') as f:
    json.dump(titles, f)


def load_descriptions():
  try:
    with open('descriptions.json', 'r') as f:
      return json.load(f)
  except FileNotFoundError:
    return {}


descriptions = load_descriptions()


def save_descriptions():
  with open('descriptions.json', 'w') as f:
    json.dump(descriptions, f)


def generate_unique_filename():
  characters = string.digits
  unique_id = 'A-' + ''.join(secrets.choice(characters) for _ in range(6))
  return unique_id


def load_users():
  try:
    with open('users.json', 'r') as f:
      return json.load(f)
  except FileNotFoundError:
    return []


def save_users(users):
  with open('users.json', 'w') as f:
    json.dump(users, f)
  


DATABASE = 'usuarios.db'


def create_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                 username TEXT, email TEXT, password TEXT)''')

    c.execute('''CREATE TABLE IF NOT EXISTS imagenes
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                 filename TEXT, username TEXT, 
                 user_profile_picture TEXT, 
                 description TEXT, 
                 likes_count INTEGER)''')

    c.execute('''CREATE TABLE IF NOT EXISTS likes (
                     id INTEGER PRIMARY KEY AUTOINCREMENT,
                     user_id INTEGER,
                     image_id INTEGER,
                     FOREIGN KEY(user_id) REFERENCES usuarios(id),
                     FOREIGN KEY(image_id) REFERENCES imagenes(id)
                 )''')

    c.execute('''CREATE TABLE IF NOT EXISTS comments (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 username TEXT,
                 comment_text TEXT,
                 user_profile_picture TEXT,
                 image_id INTEGER,
                 FOREIGN KEY(image_id) REFERENCES imagenes(id)
             )''')

    c.execute('''CREATE TABLE IF NOT EXISTS messages (
                 id INTEGER PRIMARY KEY AUTOINCREMENT, 
                 user1 TEXT,
                 user2 TEXT,
                 message TEXT, 
                 timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
             )''')

    c.execute('''CREATE TABLE IF NOT EXISTS chats (
                     id INTEGER PRIMARY KEY AUTOINCREMENT,
                     user1 TEXT,
                     user2 TEXT,
                     FOREIGN KEY(user1) REFERENCES usuarios(username),
                     FOREIGN KEY(user2) REFERENCES usuarios(username)
                 )''')

    conn.commit()
    conn.close()

create_db()



@app.route('/login')
def logpage():
  return render_template('login.html')
@app.route('/register')
def landingpage():
    return render_template('landing.html')
  
@app.route('/')
def index():
    if 'username' in session:
        # Si hay una sesión activa, redirige al usuario a la página de carga
        return redirect(url_for('loading'))
    else:
        # Si no hay una sesión activa, renderiza la plantilla de inicio de sesión
        flash_messages = get_flashed_messages(with_categories=True)
        return render_template('landing.html', flash_messages=flash_messages)

@app.route('/obtener_columnas', methods=['GET'])
def obtener_columnas():
    tabla = request.args.get('tabla')
    columnas = obtener_nombres_columnas(tabla)
    return jsonify(columnas)
  
def obtener_nombres_columnas(tabla):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute(f"PRAGMA table_info({tabla})")
    columnas = [columna[1] for columna in c.fetchall()]
    conn.close()
    return columnas

@app.route('/adminfilas')
def adminfilas():
    tablas = ['usuarios', 'imagenes', 'likes', 'comments', 'messages', 'chats']
    return render_template('adminfilas.html', tablas=tablas)

@app.route('/agregar_fila', methods=['POST'])
def agregar_fila():
    tabla = request.form['tabla']
    valores = request.form.getlist('valores[]')

    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    # Insertar fila en la tabla
    placeholders = ','.join(['?' for _ in valores])
    try:
        c.execute(f"INSERT INTO {tabla} VALUES ({placeholders})", tuple(valores))
        conn.commit()
        conn.close()
        return 'Fila agregada exitosamente'
    except sqlite3.Error as e:
        conn.rollback()
        print("Error al insertar fila:", e)
        return 'Error al agregar fila: {}'.format(e), 500


      
@app.route('/get_tables')
def get_tables():
    connection = sqlite3.connect('usuarios.db')
    cursor = connection.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    cursor.close()
    connection.close()
    table_names = [table[0] for table in tables]
    return jsonify({'tables': table_names})

@app.route('/get_data/<table_name>')
def get_data(table_name):
    connection = sqlite3.connect('usuarios.db')
    cursor = connection.cursor()
    cursor.execute(f"SELECT * FROM {table_name};")
    data = cursor.fetchall()
    cursor.close()
    connection.close()
    column_names = [description[0] for description in cursor.description]
    return jsonify({'data': data, 'columns': column_names})

@app.route('/edit_data/<table_name>/<row_id>', methods=['POST'])
def edit_data(table_name, row_id):
    data = request.get_json()

    # Convierte los valores enviados desde el frontend en una lista de tuplas (columna, valor)
    columns_values = list(zip(data['columns'], data['values']))

    # Construye la cadena SET para la actualización
    set_clause = ', '.join([f"{column} = ?" for column, _ in columns_values])

    # Construye la lista de valores
    values = [value for _, value in columns_values]

    # Agrega el row_id al final de la lista de valores
    values.append(row_id)

    # Crea la consulta SQL para actualizar los datos
    query = f"UPDATE {table_name} SET {set_clause} WHERE id = ?"

    # Ejecuta la consulta SQL
    connection = sqlite3.connect('usuarios.db')
    cursor = connection.cursor()
    cursor.execute(query, values)
    connection.commit()
    cursor.close()
    connection.close()

    return 'Data edited'

@app.route('/delete_data/<table_name>/<row_id>', methods=['POST'])
def delete_data(table_name, row_id):
    query = f"DELETE FROM {table_name} WHERE id = ?"

    connection = sqlite3.connect('usuarios.db')
    cursor = connection.cursor()
    cursor.execute(query, (row_id,))
    connection.commit()
    cursor.close()
    connection.close()

    return 'Data deleted'
  
@app.route('/admin')
@check_authorization
def admin():
    username = session['username']

    images = []
    for filename in os.listdir(app.config['UPLOAD_FOLDER']):
        if filename.startswith('A-'):
            images.append(filename)

    likes_count_dict = {}
    comments_dict = {}
    img_usernames = {}
    descriptions_dict = {}  # Crear un diccionario para almacenar las descripciones

    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    for image in images:
        c.execute("SELECT COUNT(*) FROM likes WHERE image_id=?", (image,))
        likes_count = c.fetchone()[0]
        likes_count_dict[image] = likes_count

        c.execute(
            "SELECT username, comment_text, user_profile_picture FROM comments WHERE image_id=?",
            (image,))
        comments = [{
            'username': row[0],
            'comment_text': row[1],
            'user_profile_picture': row[2]
        } for row in c.fetchall()]
        comments_dict[image] = comments

        c.execute("SELECT username, description FROM imagenes WHERE filename=?",
                  (image,))
        result = c.fetchone()
        if result:
            img_username, description = result
            img_usernames[image] = img_username
            descriptions_dict[
                image] = description  # Almacenar la descripción en el diccionario
        else:
            img_usernames[image] = ""
            descriptions_dict[
                image] = ""  # Asignar una cadena vacía si no hay descripción

        if session.get(image) == 'liked':
            likes_count_dict[image] += 1

    # Verificar si el usuario tiene una imagen de perfil
    user_profile_picture = os.path.join(PROFILE_PICS_FOLDER, f"{username}.jpg")
    if not os.path.exists(user_profile_picture):
        # Si no tiene una imagen de perfil, usar la imagen predeterminada vendetta.jpg
        vendetta_image = os.path.join(PROFILE_PICS_FOLDER, "vendetta.jpg")
        # Copiar la imagen predeterminada con el nombre del usuario
        vendetta_user_image = os.path.join(PROFILE_PICS_FOLDER, f"{username}.jpg")
        shutil.copy(vendetta_image, vendetta_user_image)
        user_profile_picture = url_for('uploaded_file', filename=f'prof_pics/{username}.jpg')

    conn.close()

    return render_template('staffpanel.html',
                           images=images,
                           titles=titles,
                           descriptions=descriptions_dict,
                           likes_count_dict=likes_count_dict,
                           comments_dict=comments_dict,
                           img_usernames=img_usernames,
                           username=username,
                           user_profile_picture=user_profile_picture)


@app.route('/upload', methods=['POST'])
def upload():
  if 'image' not in request.files:
    return jsonify({'error': 'No se ha proporcionado ninguna imagen'}), 400

  file = request.files['image']
  if file.filename == '':
    return jsonify({'error': 'Nombre de archivo no válido'}), 400

  # Capturar el nombre de usuario de la sesión
  username = session.get('username')

  # Obtener la ruta de la foto de perfil del usuario si está disponible
  if username:
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT filename FROM imagenes WHERE username=?", (username, ))
    user_profile_picture = url_for('uploaded_file',
                                   filename='prof_pics/' + username + '.jpg')
    conn.close()
  else:
    user_profile_picture = None  # o cualquier valor predeterminado que desees

  # Generar un nombre de archivo único y guardar la imagen
  filename = generate_unique_filename()
  filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
  file.save(filepath)

  # Obtener el título y la descripción de la imagen
  title = request.form.get('title')
  titles[filename] = title
  save_titles()
  description = request.form.get('description')
  descriptions[filename] = description
  save_descriptions()

  # Guardar la información de la imagen en la base de datos
  conn = sqlite3.connect(DATABASE)
  c = conn.cursor()
  c.execute(
      "INSERT INTO imagenes (filename, username, user_profile_picture, description) VALUES (?, ?, ?, ?)",
      (filename, username, user_profile_picture, description))
  conn.commit()
  conn.close()

  # Redirigir al usuario a la página de la imagen cargada
  return redirect(url_for('show_image', product=filename))


@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
  return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/get_description')
def get_description():
  image_name = request.args.get('image_name')

  # Conectarse a la base de datos
  conn = sqlite3.connect(DATABASE)
  c = conn.cursor()

  # Consultar la descripción basada en el nombre del archivo de imagen
  c.execute("SELECT description FROM imagenes WHERE filename = ?",
            (image_name, ))
  row = c.fetchone()
  description = row[
      0] if row else ""  # Si no se encuentra la descripción, se asigna una cadena vacía

  # Cerrar la conexión a la base de datos
  conn.close()

  # Devolver la descripción como una respuesta JSON
  return jsonify({"description": description})


@app.route('/aureal')
def show_image():
  product = request.args.get('product')
  title = titles.get(product)  # Obtener el título asociado al producto
  description = descriptions.get(product)
  username = session.get(
      'username')  # Obtener el nombre de usuario de la sesión

  return render_template('imagen.html',
                         product=product,
                         title=title,
                         description=description,
                         username=username)

@app.route('/chat')
def chat():
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']

    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    # Obtén todos los usuarios
    c.execute('''SELECT username FROM usuarios''')
    users = c.fetchall()

    # Obtén todos los chats del usuario de la sesión actual
    c.execute("SELECT user2 FROM chats WHERE user1=? UNION SELECT user1 FROM chats WHERE user2=?", (username, username))
    chats = c.fetchall()

    conn.close()

    # Proporcionar un valor predeterminado para other_user
    other_user = None

    return render_template('chat.html', username=username, other_user=other_user, users=users, chats=chats)

@app.route('/add_to_chats/<username>/', methods=['POST'])
def add_to_chats(username):
    # Aquí debes insertar un nuevo registro en la tabla 'chats' con los nombres de usuario correspondientes
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    # Agregar el usuario de la sesión actual a la lista de chats del usuario 'username'
    c.execute("INSERT INTO chats (user1, user2) VALUES (?, ?)", (session['username'], username))

    # Agregar el usuario 'username' a la lista de chats del usuario de la sesión actual
    c.execute("INSERT INTO chats (user1, user2) VALUES (?, ?)", (username, session['username']))

    conn.commit()
    conn.close()

    return redirect(url_for('vista_perfil', username=username))

@app.template_filter('default')
def default(value, default_value):
    return value if value is not None else default_value
  
@app.route('/chat/<other_user>')
def chat_with_user(other_user):
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']
    chat_id = hash(frozenset({username, other_user}))

    # Obtener los mensajes intercambiados entre los dos usuarios
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''SELECT * FROM messages WHERE (user1=? AND user2=?) OR (user1=? AND user2=?) ORDER BY timestamp ASC''',
              (username, other_user, other_user, username))
    messages = c.fetchall()
    conn.close()

    return render_template('chat.html', username=username, other_user=other_user, chat_id=chat_id, messages=messages)



# Emitir el evento 'new_message' a todos los clientes cuando se recibe un mensaje
@socketio.on('send_message')
def handle_message(data):
    user1 = session['username']
    user2 = data['receiver']
    message = data['message']

    print(f"Mensaje enviado de {user1} a {user2}: {message}")

    # Unir a los usuarios a una sala específica
    room_name = f"chat_{user1}_{user2}"
    join_room(room_name)

    # Guardar el mensaje en la base de datos
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''INSERT INTO messages (user1, user2, message) VALUES (?, ?, ?)''', (user1, user2, message))
    conn.commit()
    conn.close()

    # Emitir el evento 'new_message' a todos los clientes en la misma sala
    emit('new_message', {'sender': user1, 'receiver': user2, 'message': message}, room=room_name)

    print("Mensaje enviado correctamente.")

@socketio.on('typing')
def handle_typing(typing_status):
    # Emitir el evento a todos los clientes conectados
    emit('typing', typing_status, broadcast=True, include_self=False)
  
@app.route('/get_recent_messages')
def get_recent_messages():
    user1 = session['username']
    user2 = request.args.get('other_user')

    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''SELECT * FROM messages WHERE (user1=? AND user2=?) OR (user1=? AND user2=?) ORDER BY timestamp ASC''',
              (user1, user2, user2, user1))
    messages = [{'sender': row[2], 'message': row[3]} for row in c.fetchall()]
    conn.close()

    return jsonify({'messages': messages})
# Mantener un registro de qué usuarios están actualmente en qué salas de chat
active_chats = {}

@socketio.on('join_chat')
def handle_join_chat(data):
    user1 = session['username']
    user2 = data['other_user']
    room_name = f"chat_{user1}_{user2}"
    join_room(room_name)

    # Registrar que el otro usuario está activo en esta sala de chat
    active_chats[room_name] = user2

@socketio.on('leave_chat')
def handle_leave_chat(data):
    user1 = session['username']
    user2 = data['other_user']
    room_name = f"chat_{user1}_{user2}"
    leave_room(room_name)

    # Eliminar la entrada de la sala de chat cuando el otro usuario abandona el chat
    if room_name in active_chats:
        del active_chats[room_name]

# Verificar si el otro usuario está en la sala de chat antes de enviar un mensaje
def is_other_user_active(user1, user2):
    room_name = f"chat_{user1}_{user2}"
    return room_name in active_chats

@app.route('/roller')
def show_roller():
  # Verificar si el usuario ha iniciado sesión
  if 'username' not in session:
    return redirect(
        url_for('index')
    )  # Redirigir al usuario a la página de inicio de sesión si no ha iniciado sesión

  # Obtener el nombre de usuario de la sesión
  username = session['username']

  # Obtener las imágenes y los recuentos de likes
  images = []
  for filename in os.listdir(app.config['UPLOAD_FOLDER']):
    if filename.startswith('A-'):
      images.append(filename)

  likes_count_dict = {}
  comments_dict = {}
  conn = sqlite3.connect(DATABASE)
  c = conn.cursor()
  for image in images:
    # Obtener el recuento de likes para la imagen
    c.execute("SELECT COUNT(*) FROM likes WHERE image_id=?", (image, ))
    likes_count = c.fetchone()[0]
    likes_count_dict[image] = likes_count

    # Obtener los comentarios para la imagen
    c.execute(
        "SELECT username, comment_text, user_profile_picture FROM comments WHERE image_id=?",
        (image, ))
    comments = [{
        'username': row[0],
        'comment_text': row[1],
        'user_profile_picture': row[2]
    } for row in c.fetchall()]
    comments_dict[image] = comments

    # Restaurar el estado de los likes si existe en sessionStorage
    if session.get(image) == 'liked':
      likes_count_dict[image] += 1

  conn.close()

  return render_template('roller.html',
                         images=images,
                         titles=titles,
                         likes_count_dict=likes_count_dict,
                         comments_dict=comments_dict,
                         username=username)


@app.route('/profile/<username>/')
def vista_perfil(username):

  descriptions_dict = {}

  own_username = session.get('username')
  # Comprobación adicional de la existencia de un nombre de usuario
  if not username:
    return "No se ha proporcionado un nombre de usuario", 400

  conn = sqlite3.connect(DATABASE)
  c = conn.cursor()
  c.execute("SELECT filename FROM imagenes WHERE username=?", (username, ))
  user_images = [row[0] for row in c.fetchall()]
  conn.close()
  return render_template('vista.html',
                         user_images=user_images,
                         username=username,
                         titles=titles, descriptions=descriptions_dict, own=own_username)


@app.route('/profile')
def profile():
  # Verificar si el usuario ha iniciado sesión
  if 'username' not in session:
    return redirect(
        url_for('index')
    )  # Redirigir al usuario a la página de inicio de sesión si no ha iniciado sesión

  # Obtener el nombre de usuario de la sesión
  username = session['username']

  user = buscar_usuario(username)
  if not user:
    session.pop('username', None)
    flash('El nombre de usuario no está registrado')
    return redirect(url_for('index'))

  search_username = request.args.get('username')

  if search_username:
    # Obtener las imágenes subidas por el usuario especificado en la URL
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT filename FROM imagenes WHERE username=?",
              (search_username, ))
    user_images = [row[0] for row in c.fetchall()]
    conn.close()

    # Renderizar la plantilla de perfil con las imágenes del usuario buscado
    return render_template('profile.html',
                           user_images=user_images,
                           username=search_username,
                           titles=titles)
  else:
    # Obtener las imágenes subidas por el usuario actual
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT filename FROM imagenes WHERE username=?", (username, ))
    user_images = [row[0] for row in c.fetchall()]
    conn.close()

    # Renderizar la plantilla de perfil con las imágenes del usuario actual
    return render_template('profile.html',
                           user_images=user_images,
                           username=username,
                           titles=titles)


def close_user_sessions(username):
  """
            Cierra todas las sesiones de usuario correspondientes al nombre de usuario dado.
            """
  for key in list(session.keys()):
    if session[key] == username:
      session.pop(key)


@app.route('/like_count', methods=['GET'])
def get_like_count():
  image_name = request.args.get('image_name')

  if image_name:
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM likes WHERE image_id=?", (image_name, ))
    likes_count = c.fetchone()[0]

    conn.close()

    return jsonify({'likesCount': likes_count})
  else:
    return jsonify({'error': 'Image name not provided'}), 400


@app.route('/delete_account', methods=['POST'])
def delete_account():
  if 'username' not in session:
    return redirect(
        url_for('admin')
    )  # Redirigir al usuario a la página de inicio de sesión si no ha iniciado sesión

  if session['username'] == 'Miguel N.':
    username_to_delete = request.form.get('username_to_delete')
    if username_to_delete:
      conn = sqlite3.connect(DATABASE)
      c = conn.cursor()
      c.execute("DELETE FROM usuarios WHERE username=?",
                (username_to_delete, ))
      conn.commit()
      conn.close()
      close_user_sessions(
          username_to_delete
      )  # Cierra todas las sesiones correspondientes al usuario eliminado
      flash(f'La cuenta de usuario {username_to_delete} ha sido eliminada')
      return redirect(url_for('index'))
    else:
      flash('Debe proporcionar un nombre de usuario para eliminar la cuenta')
      return redirect(url_for('index'))
  else:
    flash('No tiene permisos para eliminar cuentas de usuario')
    return redirect(url_for('index'))


@app.route('/upload_profile_photo', methods=['POST'])
def upload_profile_photo():
  if 'file' not in request.files:
    flash('No se ha seleccionado ningún archivo')
    return redirect(request.url)
  file = request.files['file']
  if file.filename == '':
    flash('No se ha seleccionado ningún archivo')
    return redirect(request.url)
  if file:
    # Guardar el archivo en la carpeta prof_pics con el nombre de usuario de la sesión
    username = session.get(
        'username')  # Obtener el nombre de usuario de la sesión
    file.save(
        os.path.join(app.config['UPLOAD_FOLDER'], 'prof_pics',
                     username + '.jpg'))
    flash('Foto de perfil actualizada exitosamente')
    return redirect(
        url_for('profile'))  # Redirigir al usuario a la página de perfil

  # Si no se carga ningún archivo, redirigir al usuario a la página de perfil
  return redirect(url_for('profile'))


@app.route('/logout')
def logout():
  session.pop('username', None)  # Eliminar el nombre de usuario de la sesión
  return redirect(
      url_for('index'))  # Redirigir al usuario a la página de inicio de sesión


@app.route('/delete_image', methods=['POST'])
def delete_image():
  if request.method == 'POST':
    image_filename = request.form.get('image_filename')
    if image_filename:
      try:
        # Ruta completa de la imagen en el sistema de archivos
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)
        # Eliminar la imagen del sistema de archivos
        os.remove(image_path)

        # Eliminar la imagen de la base de datos
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute("DELETE FROM imagenes WHERE filename=?", (image_filename, ))
        conn.commit()
        conn.close()

        # Redirigir a una página de confirmación o a la página principal
        return redirect(url_for('index'))
      except Exception as e:
        print("Error al eliminar la imagen:", e)
  return redirect(
      url_for('error')
  )  # Redirigir a una página de error si la solicitud no es POST o si falta información


@app.route('/registro', methods=['POST'])
def registro():
  data = request.json
  if not data:
    return jsonify({'error':
                    'No se han proporcionado datos JSON válidos'}), 400

  username = data.get('username')
  email = data.get('email')
  password = data.get('password')

  conn = sqlite3.connect(DATABASE)
  c = conn.cursor()
  c.execute("SELECT * FROM usuarios WHERE username=?", (username, ))
  existing_user = c.fetchone()
  if existing_user:
    conn.close()
    return jsonify({'error': 'El usuario ya está registrado'}), 400

  c.execute("INSERT INTO usuarios (username, email, password) VALUES (?, ?, ?)",
            (username, email, password))
  conn.commit()
  conn.close()
  return jsonify({'message': 'Te has registrado en rollers'}), 200  
PROFILE_PICS_FOLDER = os.path.join(app.config['UPLOAD_FOLDER'], 'prof_pics')

@app.route('/home')
def newone():
    username = session['username']

    images = []
    for filename in os.listdir(app.config['UPLOAD_FOLDER']):
        if filename.startswith('A-'):
            images.append(filename)
    shuffled_images = random.sample(images, len(images))
    likes_count_dict = {}
    comments_dict = {}
    img_usernames = {}
    descriptions_dict = {}  # Crear un diccionario para almacenar las descripciones

    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    for image in images:
        c.execute("SELECT COUNT(*) FROM likes WHERE image_id=?", (image,))
        likes_count = c.fetchone()[0]
        likes_count_dict[image] = likes_count

        c.execute(
            "SELECT username, comment_text, user_profile_picture FROM comments WHERE image_id=?",
            (image,))
        comments = [{
            'username': row[0],
            'comment_text': row[1],
            'user_profile_picture': row[2]
        } for row in c.fetchall()]
        comments_dict[image] = comments

        c.execute("SELECT username, description FROM imagenes WHERE filename=?",
                  (image,))
        result = c.fetchone()
        if result:
            img_username, description = result
            img_usernames[image] = img_username
            descriptions_dict[
                image] = description  # Almacenar la descripción en el diccionario
        else:
            img_usernames[image] = ""
            descriptions_dict[
                image] = ""  # Asignar una cadena vacía si no hay descripción

        if session.get(image) == 'liked':
            likes_count_dict[image] += 1

    # Verificar si el usuario tiene una imagen de perfil
    user_profile_picture = os.path.join(PROFILE_PICS_FOLDER, f"{username}.jpg")
    if not os.path.exists(user_profile_picture):
        # Si no tiene una imagen de perfil, usar la imagen predeterminada vendetta.jpg
        vendetta_image = os.path.join(PROFILE_PICS_FOLDER, "vendetta.jpg")
        # Copiar la imagen predeterminada con el nombre del usuario
        vendetta_user_image = os.path.join(PROFILE_PICS_FOLDER, f"{username}.jpg")
        shutil.copy(vendetta_image, vendetta_user_image)
        user_profile_picture = url_for('uploaded_file', filename=f'prof_pics/{username}.jpg')

    conn.close()
    return render_template('newone.html',
                           images=shuffled_images,
                           titles=titles,
                           descriptions=descriptions_dict,
                           likes_count_dict=likes_count_dict,
                           comments_dict=comments_dict,
                           img_usernames=img_usernames,
                           username=username,
                           user_profile_picture=user_profile_picture)

@app.route('/shared/<image_id>')
def shared(image_id):
    username = session.get('username')  # Utiliza get para evitar errores si 'username' no está en la sesión
    images = []

    # Obtener todas las imágenes del directorio de subidas que coincidan con el prefijo 'A-'
    for filename in os.listdir(app.config['UPLOAD_FOLDER']):
        if filename.startswith('A-'):
            images.append(filename)

    if image_id in images:
        # Obtener la información específica de la imagen solicitada
        shuffled_images = [image_id]  # La lista de imágenes solo contendrá la imagen solicitada
        likes_count_dict = {}
        comments_dict = {}
        img_usernames = {}
        descriptions_dict = {}

        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()

        # Obtener el recuento de likes para la imagen solicitada
        c.execute("SELECT COUNT(*) FROM likes WHERE image_id=?", (image_id,))
        likes_count = c.fetchone()[0]
        likes_count_dict[image_id] = likes_count

        # Obtener los comentarios para la imagen solicitada
        c.execute(
            "SELECT username, comment_text, user_profile_picture FROM comments WHERE image_id=?",
            (image_id,))
        comments = [{
            'username': row[0],
            'comment_text': row[1],
            'user_profile_picture': row[2]
        } for row in c.fetchall()]
        comments_dict[image_id] = comments

        # Obtener el nombre de usuario y la descripción para la imagen solicitada
        c.execute("SELECT username, description FROM imagenes WHERE filename=?", (image_id,))
        result = c.fetchone()
        if result:
            img_username, description = result
            img_usernames[image_id] = img_username
            descriptions_dict[image_id] = description
        else:
            img_usernames[image_id] = ""
            descriptions_dict[image_id] = ""

        # Verificar si el usuario tiene una imagen de perfil
        user_profile_picture = os.path.join(PROFILE_PICS_FOLDER, f"{username}.jpg")
        if not os.path.exists(user_profile_picture):
            vendetta_image = os.path.join(PROFILE_PICS_FOLDER, "vendetta.jpg")
            vendetta_user_image = os.path.join(PROFILE_PICS_FOLDER, f"{username}.jpg")
            shutil.copy(vendetta_image, vendetta_user_image)
            user_profile_picture = url_for('uploaded_file', filename=f'prof_pics/{username}.jpg')

        conn.close()

        # Renderizar la plantilla compartida con la información de la imagen solicitada
        return render_template('shared.html',
                               image_id=image_id,
                               images=shuffled_images,
                               titles=titles,
                               descriptions=descriptions_dict, likes_count_dict=likes_count_dict,
                               comments_dict=comments_dict,
                               img_usernames=img_usernames,
                               username=username,
                               user_profile_picture=user_profile_picture)
    else:
        return redirect('/404.html')

@app.route('/likeds')
def likepage():
      username = session['username']

      conn = sqlite3.connect(DATABASE)
      c = conn.cursor()

      # Obtener las imágenes que tienen un registro en la tabla likes con el nombre de usuario de la sesión
      c.execute("""
          SELECT image_id
          FROM likes
          WHERE user_id = ?
      """, (username,))
      liked_images = [row[0] for row in c.fetchall()]

      # Obtener información específica de las imágenes que han sido gustadas por el usuario
      likes_count_dict = {}
      comments_dict = {}
      img_usernames = {}
      descriptions_dict = {}

      for image_id in liked_images:
          # Obtener el recuento de likes para la imagen actual
          c.execute("SELECT COUNT(*) FROM likes WHERE image_id=?", (image_id,))
          likes_count = c.fetchone()[0]
          likes_count_dict[image_id] = likes_count

          # Obtener los comentarios para la imagen actual
          c.execute(
              "SELECT username, comment_text, user_profile_picture FROM comments WHERE image_id=?",
              (image_id,))
          comments = [{
              'username': row[0],
              'comment_text': row[1],
              'user_profile_picture': row[2]
          } for row in c.fetchall()]
          comments_dict[image_id] = comments

          # Obtener el nombre de usuario y la descripción para la imagen actual
          c.execute("SELECT username, description FROM imagenes WHERE filename=?", (image_id,))
          result = c.fetchone()
          if result:
              img_username, description = result
              img_usernames[image_id] = img_username
              descriptions_dict[image_id] = description
          else:
              img_usernames[image_id] = ""
              descriptions_dict[image_id] = ""

      # Verificar si el usuario tiene una imagen de perfil
      user_profile_picture = os.path.join(PROFILE_PICS_FOLDER, f"{username}.jpg")
      if not os.path.exists(user_profile_picture):
          vendetta_image = os.path.join(PROFILE_PICS_FOLDER, "vendetta.jpg")
          vendetta_user_image = os.path.join(PROFILE_PICS_FOLDER, f"{username}.jpg")
          shutil.copy(vendetta_image, vendetta_user_image)
          user_profile_picture = url_for('uploaded_file', filename=f'prof_pics/{username}.jpg')

      conn.close()

      return render_template('likes.html',
                             images=liked_images,
                             titles=titles,
                             descriptions=descriptions_dict,
                             likes_count_dict=likes_count_dict,
                             comments_dict=comments_dict,
                             img_usernames=img_usernames,
                             username=username,
                             user_profile_picture=user_profile_picture)

  
@app.route('/post')
def render_index():
  if 'username' not in session:
    return redirect(
        url_for('index')
    )  # Redirigir al usuario a la página de inicio de sesión si no ha iniciado sesión

  username = session['username']

  return render_template('index.html', username=username)


def buscar_usuario(username):
  # Conexión a la base de datos
  conn = sqlite3.connect('usuarios.db')
  cursor = conn.cursor()

  # Consulta para buscar el usuario por nombre de usuario
  cursor.execute("SELECT * FROM usuarios WHERE username=?", (username, ))
  usuario = cursor.fetchone()

  conn.close()
  return usuario


@app.route('/login', methods=['POST'])
def login():
  data = request.json
  if not data:
    return jsonify({'error':
                    'No se han proporcionado datos JSON válidos'}), 400

  username = data.get('username')
  password = data.get('password')
  
  conn = sqlite3.connect('usuarios.db')
  c = conn.cursor()
  c.execute("SELECT * FROM usuarios WHERE username=? AND password=?",
            (username, password))
  user = c.fetchone()
  conn.close()
  
  if user:
    session[
        'username'] = username  # Almacena el nombre de usuario en la sesión
    return jsonify({
        'success': True,
        'message': 'Inicio de sesión exitoso'
    }), 200

  # En la función 'like()':
  username = session.get(
      'username')  # Obtener el nombre de usuario de la sesión

  # Dentro del bloque donde registras el like:
  c.execute("INSERT INTO likes (user_id, image_id) VALUES (?, ?)",
    (username, product_id))
  # En la función 'logout()':
  session.pop(
      'username',
      None)  # Elimina el nombre de usuario de la sesión al cerrar sesión

  # En la función 'show_roller()':
  username = session.get(
      'username')  # Obtener el nombre de usuario de la sesión
  return render_template('loading.html',
                         username=username)


@app.route('/add_comment', methods=['POST'])
def add_comment():
    data = request.json
    image_name = data.get('image_name')
    comment_text = data.get('comment_text')
    if comment_text and image_name:
        username = session.get('username')
        if username:
            conn = sqlite3.connect(DATABASE)
            c = conn.cursor()
            # Asumiendo que la columna `filename` en `imagenes` es única para cada imagen.
            c.execute("SELECT id FROM imagenes WHERE filename=?", (image_name,))
            image_id = c.fetchone()[0]

            # Obtener la ruta de la foto de perfil del usuario
            user_profile_picture = url_for('uploaded_file', filename='prof_pics/' + username + '.jpg')

            # Insertar el comentario en la base de datos
            c.execute("INSERT INTO comments (username, comment_text, user_profile_picture, image_id) VALUES (?, ?, ?, ?)", (username, comment_text, user_profile_picture, image_id))
            conn.commit()
            conn.close()

            return jsonify({'success': True}), 200
        else:
            return jsonify({'error': 'Usuario no autenticado'}), 401
    else:
        return jsonify({'error': 'No se proporcionó ningún comentario o ID de imagen'}), 400

@app.route('/comments', methods=['GET'])
def comments():
    image_name = request.args.get('image_name')
    if image_name:
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute("SELECT id FROM imagenes WHERE filename=?", (image_name,))
        image_id = c.fetchone()
        if image_id:
            image_id = image_id[0]
            c.execute("SELECT username, comment_text, user_profile_picture FROM comments WHERE image_id=?", (image_id,))
            comments = [{'username': row[0], 'comment_text': row[1], 'user_profile_picture': row[2]} for row in c.fetchall()]
            conn.close()
            return jsonify(comments)
        else:
            conn.close()
            return jsonify({'error': 'Imagen no encontrada'}), 404
    else:
        return jsonify({'error': 'No se proporcionó el nombre de la imagen'}), 400


if __name__ == '__main__':
  socketio.run(app, host='0.0.0.0', allow_unsafe_werkzeug=True)


