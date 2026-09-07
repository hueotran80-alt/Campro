const db = require('../config/db');
const bcrypt = require('bcryptjs');

// =====================================================
// NEWS CONTROLLER
// =====================================================
const newsController = {
  index: async (req, res) => {
    try {
      const { page = 1 } = req.query;
      const limit = 9;
      const offset = (parseInt(page) - 1) * limit;
      const [news] = await db.query(
        `SELECT n.*, u.full_name AS author_name FROM news n
         LEFT JOIN users u ON n.author_id = u.id
         WHERE n.is_published = 1 ORDER BY n.created_at DESC LIMIT ? OFFSET ?`,
        [limit, offset]
      );
      const [[{ total }]] = await db.query('SELECT COUNT(*) as total FROM news WHERE is_published = 1');
      res.render('pages/news', {
        title: 'Tin tức', news,
        pagination: { total, page: parseInt(page), limit, totalPages: Math.ceil(total / limit) }
      });
    } catch (err) {
      res.status(500).render('pages/error', { title: 'Lỗi', message: err.message });
    }
  },

  detail: async (req, res) => {
    try {
      const [rows] = await db.query(
        'SELECT n.*, u.full_name AS author_name FROM news n LEFT JOIN users u ON n.author_id = u.id WHERE n.slug = ? AND n.is_published = 1',
        [req.params.slug]
      );
      if (!rows.length) return res.status(404).render('pages/404', { title: 'Không tìm thấy bài viết' });
      await db.query('UPDATE news SET views = views + 1 WHERE id = ?', [rows[0].id]);
      const [related] = await db.query(
        'SELECT * FROM news WHERE id != ? AND is_published = 1 ORDER BY created_at DESC LIMIT 3',
        [rows[0].id]
      );
      res.render('pages/news-detail', { title: rows[0].title, article: rows[0], related });
    } catch (err) {
      res.status(500).render('pages/error', { title: 'Lỗi', message: err.message });
    }
  }
};

// =====================================================
// CONTACT CONTROLLER
// =====================================================
const contactController = {
  show: (req, res) => {
    res.render('pages/contact', { title: 'Liên hệ' });
  },

  submit: async (req, res) => {
    try {
      const { full_name, email, phone, subject, message } = req.body;
      if (!full_name || !email || !message) {
        req.flash('error', 'Vui lòng điền đầy đủ thông tin bắt buộc.');
        return res.redirect('/contact');
      }
      await db.query(
        'INSERT INTO contacts (full_name, email, phone, subject, message) VALUES (?, ?, ?, ?, ?)',
        [full_name, email, phone, subject, message]
      );
      req.flash('success', 'Gửi liên hệ thành công! Chúng tôi sẽ phản hồi sớm nhất.');
      return res.redirect('/contact');
    } catch (err) {
      req.flash('error', 'Lỗi gửi liên hệ, vui lòng thử lại.');
      return res.redirect('/contact');
    }
  }
};

// =====================================================
// PROFILE CONTROLLER
// =====================================================
const profileController = {
  show: async (req, res) => {
    try {
      const [rows] = await db.query(
        'SELECT id, full_name, username, email, phone, address, role, created_at FROM users WHERE id = ?',
        [req.session.user.id]
      );
      res.render('pages/profile', { title: 'Thông tin tài khoản', profile: rows[0] });
    } catch (err) {
      req.flash('error', 'Lỗi tải thông tin.');
      res.redirect('/');
    }
  },

  update: async (req, res) => {
    try {
      const { full_name, phone, address } = req.body;
      await db.query(
        'UPDATE users SET full_name = ?, phone = ?, address = ? WHERE id = ?',
        [full_name, phone, address, req.session.user.id]
      );
      // Cập nhật session
      req.session.user.full_name = full_name;
      req.flash('success', 'Cập nhật thông tin thành công!');
      return res.redirect('/profile');
    } catch (err) {
      req.flash('error', 'Lỗi cập nhật thông tin.');
      return res.redirect('/profile');
    }
  },

  changePassword: async (req, res) => {
    try {
      const { old_password, new_password, confirm_password } = req.body;
      if (!old_password || !new_password) {
        req.flash('error', 'Vui lòng nhập đầy đủ thông tin.');
        return res.redirect('/profile');
      }
      if (new_password !== confirm_password) {
        req.flash('error', 'Mật khẩu xác nhận không khớp.');
        return res.redirect('/profile');
      }
      if (new_password.length < 6) {
        req.flash('error', 'Mật khẩu mới phải có ít nhất 6 ký tự.');
        return res.redirect('/profile');
      }
      const [rows] = await db.query('SELECT password FROM users WHERE id = ?', [req.session.user.id]);
      const match = await bcrypt.compare(old_password, rows[0].password);
      if (!match) {
        req.flash('error', 'Mật khẩu cũ không đúng.');
        return res.redirect('/profile');
      }
      const hashed = await bcrypt.hash(new_password, 10);
      await db.query('UPDATE users SET password = ? WHERE id = ?', [hashed, req.session.user.id]);
      req.flash('success', 'Đổi mật khẩu thành công!');
      return res.redirect('/profile');
    } catch (err) {
      req.flash('error', 'Lỗi đổi mật khẩu.');
      return res.redirect('/profile');
    }
  }
};

module.exports = { newsController, contactController, profileController };
