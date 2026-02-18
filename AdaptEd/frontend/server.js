const express = require('express');
const path = require('path');
const app = express();

// Обслуживаем статические файлы из папки build
const buildPath = path.join(__dirname, 'build');
app.use(express.static(buildPath, {
  maxAge: '1y',
  etag: true,
  lastModified: true
}));

// Все остальные запросы отправляем на index.html (для React Router)
app.get('*', (req, res) => {
  res.sendFile(path.join(buildPath, 'index.html'));
});

const port = process.env.PORT || 3000;
app.listen(port, '0.0.0.0', () => {
  console.log(`Server running on port ${port}`);
  console.log(`Serving files from: ${buildPath}`);
  console.log(`Build directory exists: ${require('fs').existsSync(buildPath)}`);
});

