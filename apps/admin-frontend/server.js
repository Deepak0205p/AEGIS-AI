const http = require('http');
const next = require('next');

const dev = process.env.NODE_ENV !== 'production';
const app = next({ dev, dir: __dirname });
const handle = app.getRequestHandler();

const port = parseInt(process.env.PORT, 10) || 3001;
const host = '0.0.0.0';

app.prepare().then(() => {
  http.createServer((req, res) => {
    handle(req, res);
  }).listen(port, host, (err) => {
    if (err) throw err;
    console.log(`> 🌐 Admin Observatory ready on http://localhost:${port}`);
  });
}).catch((err) => {
  console.error('Error starting server:', err);
  process.exit(1);
});
