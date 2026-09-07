const db = require('../config/db');

const generateOrderCode = () => 'CAM' + Date.now().toString().slice(-8);

const orderController = {
  // GET /orders
  myOrders: async (req, res) => {
    try {
      const [orders] = await db.query(
        `SELECT o.*, COUNT(oi.id) AS item_count FROM orders o
         LEFT JOIN order_items oi ON o.id = oi.order_id
         WHERE o.user_id = ? GROUP BY o.id ORDER BY o.created_at DESC`,
        [req.session.user.id]
      );
      res.render('pages/orders', { title: 'Đơn hàng của tôi', orders });
    } catch (err) {
      req.flash('error', 'Lỗi tải đơn hàng.');
      res.redirect('/');
    }
  },

  // GET /orders/:id
  detail: async (req, res) => {
    try {
      const [orders] = await db.query('SELECT * FROM orders WHERE id = ?', [req.params.id]);
      if (!orders.length) return res.status(404).render('pages/404', { title: 'Không tìm thấy' });
      if (orders[0].user_id !== req.session.user.id && req.session.user.role !== 'admin') {
        req.flash('error', 'Bạn không có quyền xem đơn hàng này.');
        return res.redirect('/orders');
      }
      const [items] = await db.query('SELECT * FROM order_items WHERE order_id = ?', [req.params.id]);
      res.render('pages/order-detail', { title: `Đơn hàng #${orders[0].order_code}`, order: orders[0], items });
    } catch (err) {
      req.flash('error', 'Lỗi tải chi tiết đơn hàng.');
      res.redirect('/orders');
    }
  },

  // GET /orders/checkout
  showCheckout: async (req, res) => {
    try {
      const [items] = await db.query(
        `SELECT ci.id, ci.quantity, p.id AS product_id, p.name, p.image, p.price, p.sale_price, p.stock
         FROM cart_items ci JOIN products p ON ci.product_id = p.id
         WHERE ci.user_id = ? AND p.is_active = 1`,
        [req.session.user.id]
      );
      if (!items.length) {
        req.flash('error', 'Giỏ hàng trống, không thể thanh toán.');
        return res.redirect('/cart');
      }
      const subtotal = items.reduce((sum, i) => sum + (i.sale_price || i.price) * i.quantity, 0);
      res.render('pages/checkout', { title: 'Thanh toán', items, subtotal, user: req.session.user });
    } catch (err) {
      req.flash('error', 'Lỗi tải trang thanh toán.');
      res.redirect('/cart');
    }
  },

  // POST /orders/coupon-check  (AJAX kiểm tra mã giảm giá)
  checkCoupon: async (req, res) => {
    try {
      const { coupon_code, subtotal } = req.body;
      if (!coupon_code) return res.json({ ok: false, message: 'Vui lòng nhập mã giảm giá.' });

      const [rows] = await db.query(
        `SELECT * FROM coupons
         WHERE code = ? AND is_active = 1
           AND (start_date IS NULL OR start_date <= CURDATE())
           AND (end_date IS NULL OR end_date >= CURDATE())
           AND (usage_limit IS NULL OR used_count < usage_limit)`,
        [coupon_code.trim().toUpperCase()]
      );

      if (!rows.length) {
        return res.json({ ok: false, message: 'Mã giảm giá không hợp lệ hoặc đã hết hạn.' });
      }

      const coupon = rows[0];
      const sub = parseFloat(subtotal) || 0;

      if (coupon.min_order_amount && sub < coupon.min_order_amount) {
        return res.json({
          ok: false,
          message: `Đơn hàng tối thiểu ${Number(coupon.min_order_amount).toLocaleString('vi-VN')}đ để dùng mã này.`
        });
      }

      let discount = 0;
      if (coupon.discount_type === 'percent') {
        discount = Math.round((sub * coupon.discount_value) / 100);
        if (coupon.max_discount) discount = Math.min(discount, coupon.max_discount);
      } else {
        discount = coupon.discount_value;
      }
      discount = Math.min(discount, sub); // không giảm quá tổng tiền

      return res.json({
        ok: true,
        message: `✅ Áp dụng thành công! Giảm ${Number(discount).toLocaleString('vi-VN')}đ`,
        discount,
        final: sub - discount,
        coupon_code: coupon.code
      });
    } catch (err) {
      return res.json({ ok: false, message: 'Lỗi kiểm tra mã giảm giá.' });
    }
  },

  // POST /orders/checkout
  placeOrder: async (req, res) => {
    const conn = await db.getConnection();
    try {
      await conn.beginTransaction();
      const { full_name, email, phone, address, note, payment_method, coupon_code } = req.body;

      if (!full_name || !phone || !address) {
        req.flash('error', 'Vui lòng điền đầy đủ thông tin giao hàng.');
        await conn.rollback(); conn.release();
        return res.redirect('/orders/checkout');
      }

      const [cartRows] = await conn.query(
        `SELECT ci.quantity, p.id as product_id, p.name, p.image, p.price, p.sale_price, p.stock
         FROM cart_items ci JOIN products p ON ci.product_id = p.id WHERE ci.user_id = ?`,
        [req.session.user.id]
      );
      if (!cartRows.length) {
        req.flash('error', 'Giỏ hàng trống.');
        await conn.rollback(); conn.release();
        return res.redirect('/cart');
      }

      // Kiểm tra tồn kho
      for (const item of cartRows) {
        if (item.stock < item.quantity) {
          req.flash('error', `Sản phẩm "${item.name}" không đủ hàng.`);
          await conn.rollback(); conn.release();
          return res.redirect('/cart');
        }
      }

      const orderItems = cartRows.map(r => ({
        product_id: r.product_id, name: r.name, image: r.image,
        price: r.sale_price || r.price, quantity: r.quantity
      }));
      const subtotal = orderItems.reduce((s, i) => s + i.price * i.quantity, 0);
      let discount = 0, coupon_id = null;

      if (coupon_code) {
        const [cp] = await conn.query(
          `SELECT * FROM coupons WHERE code = ? AND is_active = 1
           AND (end_date IS NULL OR end_date >= CURDATE())
           AND (usage_limit IS NULL OR used_count < usage_limit)`,
          [coupon_code]
        );
        if (cp.length) {
          coupon_id = cp[0].id;
          if (cp[0].discount_type === 'percent') {
            discount = Math.round((subtotal * cp[0].discount_value) / 100);
            if (cp[0].max_discount) discount = Math.min(discount, cp[0].max_discount);
          } else {
            discount = cp[0].discount_value;
          }
          await conn.query('UPDATE coupons SET used_count = used_count + 1 WHERE id = ?', [coupon_id]);
        }
      }

      const total = Math.max(0, subtotal - discount);
      const order_code = generateOrderCode();

      const [orderResult] = await conn.query(
        `INSERT INTO orders (user_id, order_code, full_name, email, phone, address, note, payment_method, subtotal, discount, total, coupon_id)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
        [req.session.user.id, order_code, full_name, email || req.session.user.email, phone, address, note || null, payment_method || 'cod', subtotal, discount, total, coupon_id]
      );

      const order_id = orderResult.insertId;
      for (const item of orderItems) {
        await conn.query(
          'INSERT INTO order_items (order_id, product_id, product_name, product_image, quantity, price, total) VALUES (?, ?, ?, ?, ?, ?, ?)',
          [order_id, item.product_id, item.name, item.image || null, item.quantity, item.price, item.price * item.quantity]
        );
        await conn.query('UPDATE products SET stock = stock - ? WHERE id = ?', [item.quantity, item.product_id]);
      }

      await conn.query('DELETE FROM cart_items WHERE user_id = ?', [req.session.user.id]);
      await conn.commit();
      conn.release();

      req.flash('success', `Đặt hàng thành công! Mã đơn: ${order_code}`);
      return res.redirect(`/orders/${order_id}`);
    } catch (err) {
      await conn.rollback(); conn.release();
      console.error(err);
      req.flash('error', 'Lỗi đặt hàng, vui lòng thử lại.');
      return res.redirect('/orders/checkout');
    }
  },

  // POST /orders/:id/cancel
  cancel: async (req, res) => {
    try {
      const [rows] = await db.query('SELECT * FROM orders WHERE id = ? AND user_id = ?', [req.params.id, req.session.user.id]);
      if (!rows.length) {
        req.flash('error', 'Không tìm thấy đơn hàng.');
        return res.redirect('/orders');
      }
      if (rows[0].order_status !== 'pending') {
        req.flash('error', 'Chỉ có thể hủy đơn hàng đang chờ xử lý.');
        return res.redirect(`/orders/${req.params.id}`);
      }
      await db.query('UPDATE orders SET order_status = ? WHERE id = ?', ['cancelled', req.params.id]);
      const [items] = await db.query('SELECT * FROM order_items WHERE order_id = ?', [req.params.id]);
      for (const item of items) {
        await db.query('UPDATE products SET stock = stock + ? WHERE id = ?', [item.quantity, item.product_id]);
      }
      req.flash('success', 'Đã hủy đơn hàng thành công.');
      return res.redirect(`/orders/${req.params.id}`);
    } catch (err) {
      req.flash('error', 'Lỗi hủy đơn hàng.');
      return res.redirect('/orders');
    }
  }
};

module.exports = orderController;
