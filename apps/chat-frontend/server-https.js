const https = require('https');
const http = require('http');
const fs = require('fs');
const path = require('path');
const next = require('next');

const dev = process.env.NODE_ENV !== 'production';
const app = next({ dev, dir: __dirname });
const handle = app.getRequestHandler();

const pfxPath = path.join(__dirname, 'certificate.pfx');

let httpsOptions = null;
try {
  if (fs.existsSync(pfxPath)) {
    httpsOptions = {
      pfx: fs.readFileSync(pfxPath),
      passphrase: 'reveal2026'
    };
  }
} catch (e) {
  console.warn('HTTPS Certificate load warning:', e.message);
}

const port = parseInt(process.env.PORT, 10) || 3000;
const host = '0.0.0.0';

app.prepare().then(() => {
  // 1. Primary HTTP Server on port 3000 (Universal access without certificate errors)
  http.createServer((req, res) => {
    handle(req, res);
  }).listen(port, host, (err) => {
    if (err) throw err;
    console.log(`> 🌐 REVEAL 2.0 Web Server ready on http://localhost:${port}`);
    console.log(`> 📱 Access on Network via: http://<YOUR-IP>:${port}`);
  });

  // 2. Optional HTTPS Server on port 3443 if certificate exists
  if (httpsOptions) {
    https.createServer(httpsOptions, (req, res) => {
      handle(req, res);
    }).listen(3443, host, (err) => {
      if (!err) {
        console.log(`> 🔒 Secure HTTPS Server also ready on https://localhost:3443`);
      }
    });
  }
}).catch((err) => {
  console.error('Error starting server:', err);
  process.exit(1);
});
