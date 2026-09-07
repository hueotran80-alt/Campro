// =====================================================
// Kiểm tra đăng nhập (session-based)
// =====================================================
const requireLogin = (req, res, next) => {
  if (!req.session.user) {
    req.flash('error', 'Vui lòng đăng nhập để tiếp tục.');
    return res.redirect('/auth/login');
  }
  next();
};

// =====================================================
// Kiểm tra quyền Admin
// =====================================================
const requireAdmin = (req, res, next) => {
  if (!req.session.user) {
    req.flash('error', 'Vui lòng đăng nhập.');
    return res.redirect('/auth/login');
  }
  if (req.session.user.role !== 'admin') {
    req.flash('error', 'Bạn không có quyền truy cập trang này.');
    return res.redirect('/');
  }
  next();
};

// =====================================================
// Middleware chặn trang login/register nếu đã đăng nhập
// =====================================================
const guestOnly = (req, res, next) => {
  if (req.session.user) {
    return res.redirect('/');
  }
  next();
};

module.exports = { requireLogin, requireAdmin, guestOnly };
