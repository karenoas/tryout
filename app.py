from flask import Flask, render_template, request, jsonify, send_from_directory
import os
import secrets
import string

app = Flask(__name__)

# Configuración del directorio para cargar archivos
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Función para generar un nombre de archivo único sin extensión
def generate_unique_filename():
    characters = string.ascii_letters + string.digits
    return ''.join(secrets.choice(characters) for _ in range(6))

# Ruta principal
@app.route('/')
def index():
    return render_template('index.html')

# Ruta para cargar archivos
@app.route('/upload', methods=['POST'])
def upload():
    print("Recibiendo solicitud POST para cargar imagen...")
    if 'image' not in request.files:
        return jsonify({'error': 'No se ha proporcionado ninguna imagen'}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'Nombre de archivo no válido'}), 400

    # Generar un nombre de archivo único sin extensión
    filename_without_extension = generate_unique_filename()
    file_extension = os.path.splitext(file.filename)[1]
    filename = filename_without_extension
    print("Nombre del archivo generado:", filename)  # Depuración
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    return jsonify({'product': filename_without_extension}), 200

# Ruta para servir imágenes cargadas
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    full_filename = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(full_filename):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    else:
        return "Archivo no encontrado", 404

# Ruta para mostrar la imagen cargada
@app.route('/imagen.html')
def show_image():
    product = request.args.get('product')
    return render_template('imagen.html', product=product)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
