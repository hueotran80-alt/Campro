const db = require('../config/db');
const path = require('path');
const fs = require('fs');
const upload = require('../middleware/upload.middleware');
const UPLOAD_DIR = upload.UPLOAD_DIR;

const makeSlug = (name) => {
  const map = {'à':'a','á':'a','ả':'a','ã':'a','ạ':'a','ă':'a','ặ':'a','ắ':'a','ằ':'a','ẳ':'a','ẵ':'a','â':'a','ầ':'a','ấ':'a','ẩ':'a','ẫ':'a','ậ':'a','đ':'d','è':'e','é':'e','ẻ':'e','ẽ':'e','ẹ':'e','ê':'e','ề':'e','ế':'e','ể':'e','ễ':'e','ệ':'e','ì':'i','í':'i','ỉ':'i','ĩ':'i','ị':'i','ò':'o','ó':'o','ỏ':'o','õ':'o','ọ':'o','ô':'o','ồ':'o','ố':'o','ổ':'o','ỗ':'o','ộ':'o','ơ':'o','ờ':'o','ớ':'o','ở':'o','ỡ':'o','ợ':'o','ù':'u','ú':'u','ủ':'u','ũ':'u','ụ':'u','ư':'u','ừ':'u','ứ':'u','ử':'u','ữ':'u','ự':'u','ỳ':'y','ý':'y','ỷ':'y','ỹ':'y','ỵ':'y'};
  return name.toLowerCase().split('').map(c => map[c] || c).join('').replace(/[^a-z0-9 ]/g,'').trim().replace(/\s+/g,'-');
};

const adminController = {
  // ==================== DASHBOARD ====================
  dashboard: async (req, res) => {
    try {
      const [[{ total_orders }]]    = await db.query("SELECT COUNT(*) as total_orders FROM orders");
      const [[{ total_revenue }]]   = await db.query("SELECT COALESCE(SUM(total),0) as total_revenue FROM orders WHERE order_status IN ('completed','delivered')");
      const [[{ total_products }]]  = await db.query("SELECT COUNT(*) as total_products FROM products WHERE is_active = 1");
      const [[{ total_customers }]] = await db.query("SELECT COUNT(*) as total_customers FROM users WHERE role = 'customer'");
      const [[{ pending_orders }]]  = await db.query("SELECT COUNT(*) as pending_orders FROM orders WHERE order_status = 'pending'");
      const [[{ unread_contacts }]] = await db.query("SELECT COUNT(*) as unread_contacts FROM contacts WHERE status = 'unread'");
      const [recentOrders] = await db.query(
        "SELECT o.*, u.full_name FROM orders o LEFT JOIN users u ON o.user_id = u.id ORDER BY o.created_at DESC LIMIT 8"
      );
      const [topProducts] = await db.query(
        `SELECT p.id, p.name, p.image, SUM(oi.quantity) as sold FROM order_items oi
         JOIN products p ON oi.product_id = p.id JOIN orders o ON oi.order_id = o.id
         WHERE o.order_status NOT IN ('cancelled') GROUP BY p.id ORDER BY sold DESC LIMIT 5`
      );
      // 7 days revenue chart
      const [revenueChart] = await db.query(
        `SELECT DATE_FORMAT(created_at,'%d/%m') as day, COALESCE(SUM(total),0) as revenue
         FROM orders WHERE order_status IN ('completed','delivered')
         AND created_at >= DATE_SUB(CURDATE(), INTERVAL 6 DAY)
         GROUP BY DATE(created_at) ORDER BY DATE(created_at) ASC`
      );
      res.render('admin/dashboard', {
        title: 'Dashboard',
        stats: { total_orders, total_revenue: total_revenue || 0, total_products, total_customers, pending_orders, unread_contacts },
        recentOrders, topProducts, revenueChart
      });
    } catch (err) {
      res.status(500).render('pages/error', { title: 'Lỗi', message: err.message });
    }
  },

  // ==================== PRODUCTS ====================
  productList: async (req, res) => {
    try {
      const { search, page = 1 } = req.query;
      const limit = 20;
      let where = [], params = [];
      if (search) { where.push('p.name LIKE ?'); params.push(`%${search}%`); }
      const whereStr = where.length ? 'WHERE ' + where.join(' AND ') : '';
      const offset = (parseInt(page) - 1) * limit;
      const [products] = await db.query(
        `SELECT p.*, c.name AS category_name, s.name AS supplier_name FROM products p
         LEFT JOIN categories c ON p.category_id = c.id
         LEFT JOIN suppliers s ON p.supplier_id = s.id
         ${whereStr} ORDER BY p.created_at DESC LIMIT ? OFFSET ?`,
        [...params, limit, offset]
      );
      const [[{ total }]] = await db.query(`SELECT COUNT(*) as total FROM products p ${whereStr}`, params);
      res.render('admin/products', {
        title: 'Quản lý sản phẩm', products, query: req.query,
        pagination: { total, page: parseInt(page), limit, totalPages: Math.ceil(total / limit) }
      });
    } catch (err) {
      res.status(500).render('pages/error', { title: 'Lỗi', message: err.message });
    }
  },

  productBulkDelete: async (req, res) => {
    try {
      let ids = req.body['ids[]'] || req.body.ids || [];
      if (!Array.isArray(ids)) ids = [ids];
      ids = ids.map(Number).filter(Boolean);
      if (ids.length > 0) {
        const [rows] = await db.query(`SELECT image FROM products WHERE id IN (${ids.map(() => '?').join(',')})`, ids);
        rows.forEach(r => {
          if (r.image) { const p = path.join(UPLOAD_DIR, r.image); if (fs.existsSync(p)) fs.unlinkSync(p); }
        });
        await db.query(`DELETE FROM products WHERE id IN (${ids.map(() => '?').join(',')})`, ids);
        req.flash('success', `Đã xóa ${ids.length} sản phẩm!`);
      }
    } catch (err) {
      req.flash('error', 'Lỗi xóa hàng loạt: ' + err.message);
    }
    return res.redirect('/admin/products');
  },

  productCreate: async (req, res) => {
    const [categories] = await db.query('SELECT * FROM categories WHERE is_active = 1');
    const [suppliers]  = await db.query('SELECT * FROM suppliers WHERE is_active = 1');
    res.render('admin/product-form', { title: 'Thêm sản phẩm', product: null, categories, suppliers });
  },

  productStore: async (req, res) => {
    try {
      const { name, category_id, supplier_id, description, specifications, price, sale_price, stock, resolution, view_angle } = req.body;
      if (!name || !price) { req.flash('error', 'Tên và giá là bắt buộc.'); return res.redirect('/admin/products/create'); }
      const slug = makeSlug(name) + '-' + Date.now();
      const image = req.file ? req.file.filename : null;
      await db.query(
        `INSERT INTO products (name, slug, category_id, supplier_id, description, specifications, price, sale_price, stock, image, resolution, view_angle)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
        [name, slug, category_id || null, supplier_id || null, description || null, specifications || null, price, sale_price || null, stock || 0, image, resolution || null, view_angle || null]
      );
      req.flash('success', 'Thêm sản phẩm thành công!');
      return res.redirect('/admin/products');
    } catch (err) {
      req.flash('error', 'Lỗi thêm sản phẩm.');
      return res.redirect('/admin/products/create');
    }
  },

  productEdit: async (req, res) => {
    try {
      const [rows] = await db.query('SELECT * FROM products WHERE id = ?', [req.params.id]);
      if (!rows.length) return res.status(404).render('pages/404', { title: 'Không tìm thấy' });
      const [categories] = await db.query('SELECT * FROM categories');
      const [suppliers]  = await db.query('SELECT * FROM suppliers');
      res.render('admin/product-form', { title: 'Sửa sản phẩm', product: rows[0], categories, suppliers });
    } catch (err) {
      req.flash('error', 'Lỗi tải sản phẩm.'); res.redirect('/admin/products');
    }
  },

  productUpdate: async (req, res) => {
    try {
      const { name, category_id, supplier_id, description, specifications, price, sale_price, stock, resolution, view_angle, is_active } = req.body;
      const [existing] = await db.query('SELECT * FROM products WHERE id = ?', [req.params.id]);
      if (!existing.length) return res.status(404).render('pages/404', { title: 'Không tìm thấy' });
      let image = existing[0].image;
      if (req.file) {
        if (image) { const old = path.join(UPLOAD_DIR, image); if (fs.existsSync(old)) fs.unlinkSync(old); }
        image = req.file.filename;
      }
      await db.query(
        `UPDATE products SET name=?, category_id=?, supplier_id=?, description=?, specifications=?, price=?, sale_price=?, stock=?, image=?, resolution=?, view_angle=?, is_active=? WHERE id=?`,
        [name, category_id || null, supplier_id || null, description, specifications, price, sale_price || null, stock, image, resolution, view_angle, is_active ?? 1, req.params.id]
      );
      req.flash('success', 'Cập nhật sản phẩm thành công!');
      return res.redirect('/admin/products');
    } catch (err) {
      req.flash('error', 'Lỗi cập nhật.'); return res.redirect(`/admin/products/${req.params.id}/edit`);
    }
  },

  productDelete: async (req, res) => {
    try {
      const [rows] = await db.query('SELECT image FROM products WHERE id = ?', [req.params.id]);
      if (rows[0]?.image) { const p = path.join(UPLOAD_DIR, rows[0].image); if (fs.existsSync(p)) fs.unlinkSync(p); }
      await db.query('DELETE FROM products WHERE id = ?', [req.params.id]);
      req.flash('success', 'Xóa sản phẩm thành công!');
      return res.redirect('/admin/products');
    } catch (err) {
      req.flash('error', 'Lỗi xóa sản phẩm.'); return res.redirect('/admin/products');
    }
  },

  productToggle: async (req, res) => {
    try {
      const [rows] = await db.query('SELECT is_active FROM products WHERE id = ?', [req.params.id]);
      if (!rows.length) { req.flash('error', 'Không tìm thấy.'); return res.redirect('/admin/products'); }
      await db.query('UPDATE products SET is_active = ? WHERE id = ?', [rows[0].is_active ? 0 : 1, req.params.id]);
      req.flash('success', 'Đã cập nhật trạng thái.');
      return res.redirect('/admin/products');
    } catch (err) {
      req.flash('error', 'Lỗi cập nhật trạng thái.'); return res.redirect('/admin/products');
    }
  },

  // ==================== CATEGORIES ====================
  categoryList: async (req, res) => {
    const [categories] = await db.query('SELECT c.*, COUNT(p.id) AS product_count FROM categories c LEFT JOIN products p ON c.id = p.category_id GROUP BY c.id ORDER BY c.created_at DESC');
    res.render('admin/categories', { title: 'Quản lý danh mục', categories });
  },

  categoryCreate: async (req, res) => {
    const { name, description } = req.body;
    if (!name) { req.flash('error', 'Tên danh mục là bắt buộc.'); return res.redirect('/admin/categories'); }
    const slug = makeSlug(name) + '-' + Date.now();
    await db.query('INSERT INTO categories (name, slug, description) VALUES (?, ?, ?)', [name, slug, description || null]);
    req.flash('success', 'Thêm danh mục thành công!');
    return res.redirect('/admin/categories');
  },

  categoryUpdate: async (req, res) => {
    const { name, description, is_active } = req.body;
    await db.query('UPDATE categories SET name=?, description=?, is_active=? WHERE id=?', [name, description, is_active ?? 1, req.params.id]);
    req.flash('success', 'Cập nhật danh mục thành công!');
    return res.redirect('/admin/categories');
  },

  categoryDelete: async (req, res) => {
    await db.query('DELETE FROM categories WHERE id = ?', [req.params.id]);
    req.flash('success', 'Xóa danh mục thành công!');
    return res.redirect('/admin/categories');
  },

  // ==================== SUPPLIERS ====================
  supplierList: async (req, res) => {
    const [suppliers] = await db.query('SELECT s.*, COUNT(p.id) AS product_count FROM suppliers s LEFT JOIN products p ON s.id = p.supplier_id GROUP BY s.id ORDER BY s.created_at DESC');
    res.render('admin/suppliers', { title: 'Quản lý nhà cung cấp', suppliers });
  },

  supplierCreate: async (req, res) => {
    const { name, email, phone, address, website } = req.body;
    if (!name) { req.flash('error', 'Tên nhà cung cấp là bắt buộc.'); return res.redirect('/admin/suppliers'); }
    await db.query('INSERT INTO suppliers (name, email, phone, address, website) VALUES (?, ?, ?, ?, ?)', [name, email || null, phone || null, address || null, website || null]);
    req.flash('success', 'Thêm nhà cung cấp thành công!');
    return res.redirect('/admin/suppliers');
  },

  supplierUpdate: async (req, res) => {
    const { name, email, phone, address, website, is_active } = req.body;
    await db.query('UPDATE suppliers SET name=?, email=?, phone=?, address=?, website=?, is_active=? WHERE id=?', [name, email, phone, address, website, is_active ?? 1, req.params.id]);
    req.flash('success', 'Cập nhật nhà cung cấp thành công!');
    return res.redirect('/admin/suppliers');
  },

  supplierDelete: async (req, res) => {
    await db.query('DELETE FROM suppliers WHERE id = ?', [req.params.id]);
    req.flash('success', 'Xóa nhà cung cấp thành công!');
    return res.redirect('/admin/suppliers');
  },

  // ==================== ORDERS ====================
  orderList: async (req, res) => {
    try {
      const { status, search, page = 1 } = req.query;
      const limit = 20;
      let where = [], params = [];
      if (status) { where.push('o.order_status = ?'); params.push(status); }
      if (search) { where.push('(o.order_code LIKE ? OR o.full_name LIKE ? OR o.phone LIKE ?)'); params.push(`%${search}%`, `%${search}%`, `%${search}%`); }
      const whereStr = where.length ? 'WHERE ' + where.join(' AND ') : '';
      const offset = (parseInt(page) - 1) * limit;
      const [orders] = await db.query(
        `SELECT o.*, COUNT(oi.id) AS item_count FROM orders o LEFT JOIN order_items oi ON o.id = oi.order_id ${whereStr} GROUP BY o.id ORDER BY o.created_at DESC LIMIT ? OFFSET ?`,
        [...params, limit, offset]
      );
      const [[{ total }]] = await db.query(`SELECT COUNT(*) as total FROM orders o ${whereStr}`, params);
      res.render('admin/orders', {
        title: 'Quản lý đơn hàng', orders, query: req.query,
        pagination: { total, page: parseInt(page), limit, totalPages: Math.ceil(total / limit) }
      });
    } catch (err) {
      res.status(500).render('pages/error', { title: 'Lỗi', message: err.message });
    }
  },

  orderDetail: async (req, res) => {
    try {
      const [orders] = await db.query('SELECT o.*, u.email AS user_email FROM orders o LEFT JOIN users u ON o.user_id = u.id WHERE o.id = ?', [req.params.id]);
      if (!orders.length) return res.status(404).render('pages/404', { title: 'Không tìm thấy' });
      const [items] = await db.query('SELECT * FROM order_items WHERE order_id = ?', [req.params.id]);
      res.render('admin/order-detail', { title: `Đơn hàng #${orders[0].order_code}`, order: orders[0], items });
    } catch (err) {
      req.flash('error', 'Lỗi tải đơn hàng.'); res.redirect('/admin/orders');
    }
  },

  orderUpdateStatus: async (req, res) => {
    const { order_status, payment_status } = req.body;
    await db.query('UPDATE orders SET order_status=?, payment_status=? WHERE id=?', [order_status, payment_status, req.params.id]);
    req.flash('success', 'Cập nhật trạng thái thành công!');
    return res.redirect(`/admin/orders/${req.params.id}`);
  },

  // ==================== REPORT ====================
  report: async (req, res) => {
    try {
      const today = new Date().toISOString().slice(0, 10);
      const firstOfMonth = today.slice(0, 7) + '-01';
      const from = req.query.from || firstOfMonth;
      const to   = req.query.to   || today;

      const [[summary]] = await db.query(
        `SELECT
           COALESCE(SUM(CASE WHEN order_status IN ('completed','delivered') THEN total ELSE 0 END),0) AS total_revenue,
           COUNT(*) AS total_orders,
           SUM(CASE WHEN order_status IN ('completed','delivered') THEN 1 ELSE 0 END) AS completed_orders,
           SUM(CASE WHEN order_status='cancelled' THEN 1 ELSE 0 END) AS cancelled_orders
         FROM orders WHERE DATE(created_at) BETWEEN ? AND ?`,
        [from, to]
      );
      const [dailyRevenue] = await db.query(
        `SELECT DATE_FORMAT(created_at,'%d/%m/%Y') as day,
                COUNT(*) as orders,
                COALESCE(SUM(CASE WHEN order_status IN ('completed','delivered') THEN total ELSE 0 END),0) as revenue
         FROM orders WHERE DATE(created_at) BETWEEN ? AND ?
         GROUP BY DATE(created_at) ORDER BY DATE(created_at) ASC`,
        [from, to]
      );
      const [topProducts] = await db.query(
        `SELECT p.name, p.image, SUM(oi.quantity) as sold,
                SUM(oi.quantity * oi.price) as revenue
         FROM order_items oi
         JOIN products p ON oi.product_id = p.id
         JOIN orders o ON oi.order_id = o.id
         WHERE o.order_status IN ('completed','delivered') AND DATE(o.created_at) BETWEEN ? AND ?
         GROUP BY p.id ORDER BY sold DESC LIMIT 10`,
        [from, to]
      );
      res.render('admin/report', {
        title: 'Báo cáo Doanh thu',
        filter: { from, to },
        summary, dailyRevenue, topProducts
      });
    } catch (err) {
      res.status(500).render('pages/error', { title: 'Lỗi', message: err.message });
    }
  },

  // ==================== COUPONS ====================
  couponList: async (req, res) => {
    const [coupons] = await db.query('SELECT * FROM coupons ORDER BY created_at DESC');
    res.render('admin/coupons', { title: 'Quản lý mã giảm giá', coupons });
  },

  couponCreate: async (req, res) => {
    try {
      const { code, discount_type, discount_value, min_order_amount, max_discount, usage_limit, start_date, end_date } = req.body;
      if (!code || !discount_value) { req.flash('error', 'Thiếu thông tin bắt buộc.'); return res.redirect('/admin/coupons'); }
      await db.query(
        'INSERT INTO coupons (code, discount_type, discount_value, min_order_amount, max_discount, usage_limit, start_date, end_date) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
        [code.toUpperCase(), discount_type || 'percent', discount_value, min_order_amount || 0, max_discount || null, usage_limit || null, start_date || null, end_date || null]
      );
      req.flash('success', 'Thêm mã giảm giá thành công!');
    } catch (err) {
      req.flash('error', err.code === 'ER_DUP_ENTRY' ? 'Mã đã tồn tại.' : 'Lỗi server.');
    }
    return res.redirect('/admin/coupons');
  },

  couponDelete: async (req, res) => {
    await db.query('DELETE FROM coupons WHERE id = ?', [req.params.id]);
    req.flash('success', 'Xóa mã giảm giá thành công!');
    return res.redirect('/admin/coupons');
  },

  // ==================== NEWS ====================
  newsList: async (req, res) => {
    const [news] = await db.query('SELECT n.*, u.full_name AS author_name FROM news n LEFT JOIN users u ON n.author_id = u.id ORDER BY n.created_at DESC');
    res.render('admin/news', { title: 'Quản lý tin tức', news });
  },

  newsCreate: (req, res) => { res.render('admin/news-form', { title: 'Thêm bài viết', article: null }); },

  newsStore: async (req, res) => {
    try {
      const { title, content, excerpt, is_published } = req.body;
      if (!title) { req.flash('error', 'Tiêu đề là bắt buộc.'); return res.redirect('/admin/news/create'); }
      const slug = makeSlug(title) + '-' + Date.now();
      const thumbnail = req.file ? req.file.filename : null;
      await db.query('INSERT INTO news (title, slug, content, excerpt, thumbnail, author_id, is_published) VALUES (?, ?, ?, ?, ?, ?, ?)',
        [title, slug, content, excerpt, thumbnail, req.session.user.id, is_published ? 1 : 0]);
      req.flash('success', 'Thêm bài viết thành công!');
      return res.redirect('/admin/news');
    } catch (err) {
      req.flash('error', 'Lỗi thêm bài viết.'); return res.redirect('/admin/news/create');
    }
  },

  newsEdit: async (req, res) => {
    const [rows] = await db.query('SELECT * FROM news WHERE id = ?', [req.params.id]);
    if (!rows.length) return res.status(404).render('pages/404', { title: 'Không tìm thấy' });
    res.render('admin/news-form', { title: 'Sửa bài viết', article: rows[0] });
  },

  newsUpdate: async (req, res) => {
    try {
      const { title, content, excerpt, is_published } = req.body;
      let q = 'UPDATE news SET title=?, content=?, excerpt=?, is_published=?';
      let p = [title, content, excerpt, is_published ? 1 : 0];
      if (req.file) { q += ', thumbnail=?'; p.push(req.file.filename); }
      q += ' WHERE id=?'; p.push(req.params.id);
      await db.query(q, p);
      req.flash('success', 'Cập nhật thành công!');
      return res.redirect('/admin/news');
    } catch (err) {
      req.flash('error', 'Lỗi cập nhật.'); return res.redirect(`/admin/news/${req.params.id}/edit`);
    }
  },

  newsDelete: async (req, res) => {
    const [rows] = await db.query('SELECT thumbnail FROM news WHERE id = ?', [req.params.id]);
    if (rows[0]?.thumbnail) { const p = path.join(UPLOAD_DIR, rows[0].thumbnail); if (fs.existsSync(p)) fs.unlinkSync(p); }
    await db.query('DELETE FROM news WHERE id = ?', [req.params.id]);
    req.flash('success', 'Xóa bài viết thành công!');
    return res.redirect('/admin/news');
  },

  // ==================== CONTACTS ====================
  contactList: async (req, res) => {
    const { status } = req.query;
    const where = status ? 'WHERE status = ?' : '';
    const [contacts] = await db.query(`SELECT * FROM contacts ${where} ORDER BY created_at DESC`, status ? [status] : []);
    res.render('admin/contacts', { title: 'Quản lý liên hệ', contacts, query: req.query });
  },

  contactReply: async (req, res) => {
    const { admin_reply } = req.body;
    await db.query('UPDATE contacts SET status = ?, admin_reply = ? WHERE id = ?', ['replied', admin_reply, req.params.id]);
    req.flash('success', 'Đã lưu phản hồi!');
    return res.redirect('/admin/contacts');
  },

  contactDelete: async (req, res) => {
    await db.query('DELETE FROM contacts WHERE id = ?', [req.params.id]);
    req.flash('success', 'Xóa liên hệ thành công!');
    return res.redirect('/admin/contacts');
  },

  // ==================== CUSTOMERS ====================
  customerList: async (req, res) => {
    try {
      const { search, page = 1 } = req.query;
      const limit = 20;
      let where = ["role = 'customer'"], params = [];
      if (search) { where.push('(full_name LIKE ? OR email LIKE ? OR username LIKE ?)'); params.push(`%${search}%`, `%${search}%`, `%${search}%`); }
      const whereStr = 'WHERE ' + where.join(' AND ');
      const offset = (parseInt(page) - 1) * limit;
      const [customers] = await db.query(`SELECT id, full_name, username, email, phone, address, is_active, created_at FROM users ${whereStr} ORDER BY created_at DESC LIMIT ? OFFSET ?`, [...params, limit, offset]);
      const [[{ total }]] = await db.query(`SELECT COUNT(*) as total FROM users ${whereStr}`, params);
      res.render('admin/customers', {
        title: 'Quản lý khách hàng', customers, query: req.query,
        pagination: { total, page: parseInt(page), limit, totalPages: Math.ceil(total / limit) }
      });
    } catch (err) {
      res.status(500).render('pages/error', { title: 'Lỗi', message: err.message });
    }
  },

  customerUpdate: async (req, res) => {
    try {
      const { full_name, phone, address, is_active } = req.body;
      await db.query("UPDATE users SET full_name=?, phone=?, address=?, is_active=? WHERE id=? AND role='customer'",
        [full_name, phone || null, address || null, is_active ?? 1, req.params.id]);
      req.flash('success', 'Cập nhật thông tin khách hàng thành công!');
    } catch (err) {
      req.flash('error', 'Lỗi cập nhật khách hàng.');
    }
    return res.redirect('/admin/customers');
  },

  customerToggle: async (req, res) => {
    const [rows] = await db.query("SELECT is_active FROM users WHERE id = ? AND role = 'customer'", [req.params.id]);
    if (!rows.length) { req.flash('error', 'Không tìm thấy.'); return res.redirect('/admin/customers'); }
    await db.query('UPDATE users SET is_active = ? WHERE id = ?', [rows[0].is_active ? 0 : 1, req.params.id]);
    req.flash('success', 'Cập nhật trạng thái thành công.');
    return res.redirect('/admin/customers');
  },

  customerDelete: async (req, res) => {
    await db.query("DELETE FROM users WHERE id = ? AND role = 'customer'", [req.params.id]);
    req.flash('success', 'Xóa khách hàng thành công!');
    return res.redirect('/admin/customers');
  }
};

module.exports = adminController;
