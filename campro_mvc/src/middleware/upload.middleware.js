const multer = require('multer');
const path = require('path');
const fs = require('fs');

// Thư mục uploads nằm cùng cấp với thư mục src (campro_mvc/uploads/)
const UPLOAD_DIR = path.join(__dirname, '../../uploads');

// Tạo thư mục nếu chưa có
if (!fs.existsSync(UPLOAD_DIR)) {
  fs.mkdirSync(UPLOAD_DIR, { recursive: true });
}

const storage = multer.diskStorage({
  destination: (req, file, cb) => cb(null, UPLOAD_DIR),
  filename: (req, file, cb) => {
    const ext = path.extname(file.originalname);
    const safeName = Date.now() + '-' + file.originalname.replace(/[^a-zA-Z0-9._-]/g, '_');
    cb(null, safeName);
  }
});

const upload = multer({
  storage,
  limits: { fileSize: 5 * 1024 * 1024 },
  fileFilter: (req, file, cb) => {
    if (file.mimetype.startsWith('image/')) cb(null, true);
    else cb(new Error('Chỉ chấp nhận file ảnh!'), false);
  }
});

module.exports = upload;
module.exports.UPLOAD_DIR = UPLOAD_DIR;
