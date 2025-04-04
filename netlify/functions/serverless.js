const serverless = require('serverless-http');
const { spawn } = require('child_process');
const path = require('path');

// Pythonプロセスを起動
const pythonProcess = spawn('python', [path.join(__dirname, 'app.py')]);

// 標準出力と標準エラー出力をキャプチャ
pythonProcess.stdout.on('data', (data) => {
  console.log(`stdout: ${data}`);
});

pythonProcess.stderr.on('data', (data) => {
  console.error(`stderr: ${data}`);
});

// プロセスの終了を処理
pythonProcess.on('close', (code) => {
  console.log(`child process exited with code ${code}`);
});

// サーバーレスハンドラーをエクスポート
module.exports.handler = serverless(pythonProcess);
