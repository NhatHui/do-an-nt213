const express = require('express');
const multer = require('multer');
const path = require('path');
const fs = require('fs');
const crypto = require('crypto');
const sharp = require('sharp');

const app = express();
const OUTSIDE = path.join(__dirname, 'storage_outside_webroot');
fs.mkdirSync(OUTSIDE, {recursive: true});
app.set('view engine', 'ejs');
app.use(express.static(path.join(__dirname, 'public')));

const publicUpload = multer({dest: './public/uploads/'});
const traversalStorage = multer.diskStorage({
  destination: './public/uploads/',
  filename: (req, file, cb) => cb(null, file.originalname)
});
const traversalUpload = multer({
  // Deliberately unsafe: default Multer strips paths and prevents this demonstration.
  preservePath: true,
  storage: traversalStorage,
  fileFilter: (req, file, cb) => cb(null, file.mimetype === 'image/jpeg')
});
const defendedUpload = multer({storage: multer.memoryStorage(), limits: {fileSize: 2 * 1024 * 1024, files: 1}});

app.get('/', (req, res) => res.render('index'));

app.post('/vuln/public-upload', publicUpload.single('file'), (req, res) => {
  if (!req.file) return res.status(400).json({error: 'Missing file'});
  res.status(201).json({stored: true, url: `/uploads/${req.file.filename}`, original: req.file.originalname});
});

app.post('/vuln/traversal-upload', traversalUpload.single('file'), (req, res) => {
  if (!req.file) return res.status(415).json({error: 'MIME policy rejected file'});
  res.status(201).json({stored: true, path: req.file.path, original: req.file.originalname});
});

async function detectImage(buffer) {
  if (buffer.length >= 3 && buffer.subarray(0, 3).equals(Buffer.from([0xff, 0xd8, 0xff]))) return 'jpeg';
  if (buffer.length >= 8 && buffer.subarray(0, 8).equals(Buffer.from('89504e470d0a1a0a', 'hex'))) return 'png';
  return null;
}

app.post('/defended/upload', defendedUpload.single('file'), async (req, res, next) => {
  try {
    if (!req.file) return res.status(400).json({error: 'Missing file'});
    const ext = path.extname(req.file.originalname).toLowerCase();
    const kind = await detectImage(req.file.buffer);
    if (!['.jpg', '.jpeg', '.png'].includes(ext) || !kind || (ext !== '.png' && kind !== 'jpeg') || (ext === '.png' && kind !== 'png')) {
      return res.status(415).json({error: 'Extension and signature mismatch'});
    }
    const id = `${crypto.randomUUID()}.jpg`;
    const target = path.join(OUTSIDE, id);
    let output;
    try {
      output = await sharp(req.file.buffer, {limitInputPixels: 4000000, failOn: 'warning'})
        .rotate().jpeg({quality: 90}).toBuffer();
    } catch (err) {
      return res.status(415).json({error: 'Image decoder rejected file'});
    }
    await fs.promises.writeFile(target, output, {flag: 'wx', mode: 0o600});
    res.status(201).json({stored: true, id, marker_present: output.includes('B22_UFU_EXEC_SUCCESS')});
  } catch (err) { next(err); }
});

app.get('/defended/file/:name', (req, res) => {
  if (!/^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\.jpg$/.test(req.params.name)) return res.status(400).send('Invalid file ID');
  const target = path.join(OUTSIDE, req.params.name);
  if (!fs.existsSync(target)) return res.sendStatus(404);
  res.set({
    'X-Content-Type-Options': 'nosniff',
    'Content-Disposition': `attachment; filename="${req.params.name}"`,
    'Content-Security-Policy': "default-src 'none'"
  });
  res.type('image/jpeg').sendFile(target);
});

app.use((err, req, res, next) => {
  if (res.headersSent) return next(err);
  const status = err.code === 'LIMIT_FILE_SIZE' ? 413 : err instanceof multer.MulterError ? 400 : 500;
  res.status(status).json({error: status === 400 ? 'Invalid multipart upload' : 'Upload failed'});
});
app.listen(3000, '0.0.0.0', () => console.log('B22 Node lab listening on 3000'));