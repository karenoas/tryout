const { spawn } = require('child_process');

// Ejecuta app.py
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
