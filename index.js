const express = require('express');
const app = express();
const port = 3000;
const http = require('http').Server(app);
const socketIO = require('socket.io')(http);
const { spawn } = require('child_process');

let messages = [];
let users = [];
let directChats = [];



// Funciones para cargar y guardar mensajes
function loadMessages() {
    try {
        const data = fs.readFileSync('messages.json');
        messages = JSON.parse(data);
    } catch (error) {
        console.error("Error al cargar mensajes:", error);
        messages = [];
    }
}

function saveMessages() {
    fs.writeFileSync('messages.json', JSON.stringify(messages));
}

// Funciones para cargar y guardar usuarios
function loadUsers() {
    try {
        const data = fs.readFileSync('users.json');
        users = JSON.parse(data);
    } catch (error) {
        console.error("Error al cargar usuarios:", error);
        users = [];
    }
}

function saveUsers() {
    fs.writeFileSync('users.json', JSON.stringify(users));
}

// Funciones para cargar y guardar chats directos
function loadDirectChats() {
    try {
        const data = fs.readFileSync('directChats.json');
        directChats = JSON.parse(data);
    } catch (error) {
        console.error("Error al cargar chats directos:", error);
        directChats = [];
    }
}

function saveDirectChats() {
    fs.writeFileSync('directChats.json', JSON.stringify(directChats));
}

app.use(express.static('templates')); // Sirve archivos estáticos desde la carpeta 'templates'
app.use(express.json()); // Middleware para procesar datos JSON

app.get("/", function (request, response) {
    response.sendFile(__dirname + '/templates/login.html');
});

// Manejar el registro de usuarios

// Manejar la autenticación del usuario
app.post('/login', (req, res) => {
    const { username, password } = req.body;

    const user = users.find(user => user.username === username && user.password === password);

    if (user) {
        res.status(200).json({ success: true, message: 'Inicio de sesión exitoso' });
    } else {
        res.status(401).json({ success: false, message: 'Usuario o contraseña incorrectos' });
    }
});

socketIO.on('connection', (socket) => {
    console.log('Usuario conectado');
    socket.emit('cargarMensajes', { messages });

    socket.on('mensaje', (data) => {
        data.socketId = socket.id;
        messages.push(data);
        saveMessages();

        // Verificar si es un chat directo
        if (data.destino) {
            const chatExists = directChats.find(chat => (
                (chat.user1 === data.usuario && chat.user2 === data.destino) ||
                (chat.user1 === data.destino && chat.user2 === data.usuario)
            ));

            if (!chatExists) {
                // Guardar el nuevo chat directo
                directChats.push({ user1: data.usuario, user2: data.destino });
                saveDirectChats();
            }
        }

        socketIO.emit('nuevoMensaje', data);
    });

    socket.on('eliminarTodosLosMensajes', () => {
        messages = [];
        socketIO.emit('eliminarTodosLosMensajes');
    });

    socket.on('disconnect', () => {
        console.log('Usuario desconectado');
    });
});

http.listen(port, () => {
    console.log(`App is listening on port ${port}`);

    // Ejecutar app.py
    const pythonProcess = spawn('python', ['app.py']);

    pythonProcess.stdout.on('data', (data) => {
        console.log(`stdout: ${data}`);
    });

    pythonProcess.stderr.on('data', (data) => {
        console.error(`stderr: ${data}`);
    });

    pythonProcess.on('close', (code) => {
        console.log(`Proceso Python se cerró con código ${code}`);
    });
});

// Función para alternar la visibilidad del chat emergente
function toggleChat() {
    var chatPopup = document.getElementById('chatPopup');
    chatPopup.style.display = chatPopup.style.display === 'none' ? 'block' : 'none';
}