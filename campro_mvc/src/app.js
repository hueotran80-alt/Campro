const express = require('express');
const path = require('path');
const session = require('express-session');
const flash = require('connect-flash');
const morgan = require('morgan');
const methodOverride = require('method-override');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 5000;

// =====================================================
// VIEW ENGINE - EJS
// =====================================================
app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));

// =====================================================
// MIDDLEWARE
// =====================================================
app.use(morgan('dev'));
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(methodOverride('_method'));

// Static files
app.use(express.static(path.join(__dirname, 'public')));
app.use('/uploads', express.static(path.join(__dirname, '../uploads')));

// Session
app.use(session({
  secret: process.env.SESSION_SECRET || 'campro_session_2025',
  resave: false,
  saveUninitialized: false,
  cookie: { maxAge: 7 * 24 * 60 * 60 * 1000 } // 7 ngày
}));

// Flash messages
app.use(flash());

// Truyền user và flash vào tất cả views
app.use((req, res, next) => {
  res.locals.user = req.session.user || null;
  res.locals.success = req.flash('success');
  res.locals.error = req.flash('error');
  next();
});

// =====================================================
// ROUTES
// =====================================================
app.use('/',          require('./routes/home.routes'));
app.use('/auth',      require('./routes/auth.routes'));
app.use('/products',  require('./routes/product.routes'));
app.use('/cart',      require('./routes/cart.routes'));
app.use('/orders',    require('./routes/order.routes'));
app.use('/news',      require('./routes/news.routes'));
app.use('/contact',   require('./routes/contact.routes'));
app.use('/profile',   require('./routes/profile.routes'));
app.use('/admin',     require('./routes/admin.routes'));

// =====================================================
// 404 HANDLER
// =====================================================
app.use((req, res) => {
  res.status(404).render('pages/404', { title: 'Không tìm thấy trang' });
});

// =====================================================
// ERROR HANDLER
// =====================================================
app.use((err, req, res, next) => {
  console.error('❌ Server Error:', err.message);
  res.status(500).render('pages/error', { title: 'Lỗi server', message: err.message });
});

// =====================================================
// START SERVER
// =====================================================
app.listen(PORT, () => {
  console.log('╔══════════════════════════════════════╗');
  console.log('║   🎥 CAMPRO MVC Server Running       ║');
  console.log(`║   📡 Port: ${PORT}                       ║`);
  console.log(`║   🌐 http://localhost:${PORT}             ║`);
  console.log('╚══════════════════════════════════════╝');
});

module.exports = app;
