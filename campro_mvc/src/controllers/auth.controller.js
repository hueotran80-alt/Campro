const db = require('../config/db');
const bcrypt = require('bcryptjs');
require('dotenv').config();

const authController = {
  // GET /auth/login
  showLogin: (req, res) => {
    res.render('pages/login', { title: 'Đăng nhập' });
  },

  // POST /auth/login
  login: async (req, res) => {
    try {
      const { username, password } = req.body;
      if (!username || !password) {
        req.flash('error', 'Vui lòng nhập tên đăng nhập và mật khẩu.');
        return res.redirect('/auth/login');
      }

      const [rows] = await db.query(
        'SELECT * FROM users WHERE (username = ? OR email = ?) AND is_active = 1',
        [username, username]
      );

      if (!rows.length) {
        req.flash('error', 'Tên đăng nhập hoặc mật khẩu không đúng.');
        return res.redirect('/auth/login');
      }

      const user = rows[0];
      const match = await bcrypt.compare(password, user.password);
      if (!match) {
        req.flash('error', 'Tên đăng nhập hoặc mật khẩu không đúng.');
        return res.redirect('/auth/login');
      }

      // Lưu user vào session (bỏ password)
      const { password: _, ...userData } = user;
      req.session.user = userData;

      req.flash('success', `Chào mừng trở lại, ${user.full_name}!`);
      if (user.role === 'admin') return res.redirect('/admin/dashboard');
      return res.redirect('/');
    } catch (err) {
      console.error(err);
      req.flash('error', 'Lỗi server, vui lòng thử lại.');
      return res.redirect('/auth/login');
    }
  },

  // GET /auth/register
  showRegister: (req, res) => {
    res.render('pages/register', { title: 'Đăng ký tài khoản' });
  },

  // POST /auth/register
  register: async (req, res) => {
    try {
      const { full_name, username, email, password, phone, address } = req.body;

      if (!full_name || !username || !email || !password) {
        req.flash('error', 'Vui lòng điền đầy đủ thông tin.');
        return res.redirect('/auth/register');
      }
      if (password.length < 6) {
        req.flash('error', 'Mật khẩu phải có ít nhất 6 ký tự.');
        return res.redirect('/auth/register');
      }

      const [existing] = await db.query(
        'SELECT id FROM users WHERE email = ? OR username = ?',
        [email, username]
      );
      if (existing.length > 0) {
        req.flash('error', 'Email hoặc tên đăng nhập đã tồn tại.');
        return res.redirect('/auth/register');
      }

      const hashed = await bcrypt.hash(password, 10);
      await db.query(
        'INSERT INTO users (full_name, username, email, password, phone, address, role) VALUES (?, ?, ?, ?, ?, ?, ?)',
        [full_name, username, email, hashed, phone || null, address || null, 'customer']
      );

      req.flash('success', 'Đăng ký thành công! Vui lòng đăng nhập.');
      return res.redirect('/auth/login');
    } catch (err) {
      console.error(err);
      req.flash('error', 'Lỗi server, vui lòng thử lại.');
      return res.redirect('/auth/register');
    }
  },

  // GET /auth/logout
  logout: (req, res) => {
    req.session.destroy(() => {
      res.redirect('/auth/login');
    });
  }
};

module.exports = authController;
