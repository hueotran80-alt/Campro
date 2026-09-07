const db = require('../config/db');

const cartController = {
  // GET /cart
  index: async (req, res) => {
    try {
      const [items] = await db.query(
        `SELECT ci.id, ci.quantity, p.id AS product_id, p.name, p.image, p.price, p.sale_price, p.stock
         FROM cart_items ci JOIN products p ON ci.product_id = p.id
         WHERE ci.user_id = ? AND p.is_active = 1`,
        [req.session.user.id]
      );
      const total = items.reduce((sum, i) => sum + (i.sale_price || i.price) * i.quantity, 0);
      res.render('pages/cart', { title: 'Giỏ hàng', items, total });
    } catch (err) {
      req.flash('error', 'Lỗi tải giỏ hàng.');
      res.redirect('/');
    }
  },

  // POST /cart/add
  add: async (req, res) => {
    try {
      const { product_id, quantity = 1 } = req.body;
      const [product] = await db.query('SELECT * FROM products WHERE id = ? AND is_active = 1', [product_id]);
      if (!product.length) {
        req.flash('error', 'Sản phẩm không tồn tại.');
        return res.redirect('back');
      }
      if (product[0].stock < parseInt(quantity)) {
        req.flash('error', 'Không đủ hàng trong kho.');
        return res.redirect('back');
      }
      await db.query(
        'INSERT INTO cart_items (user_id, product_id, quantity) VALUES (?, ?, ?) ON DUPLICATE KEY UPDATE quantity = quantity + VALUES(quantity)',
        [req.session.user.id, product_id, parseInt(quantity)]
      );
      req.flash('success', 'Đã thêm sản phẩm vào giỏ hàng!');
      return res.redirect('back');
    } catch (err) {
      req.flash('error', 'Lỗi thêm vào giỏ hàng.');
      return res.redirect('back');
    }
  },

  // POST /cart/update/:id
  update: async (req, res) => {
    try {
      const { quantity } = req.body;
      if (parseInt(quantity) < 1) {
        req.flash('error', 'Số lượng không hợp lệ.');
        return res.redirect('/cart');
      }
      await db.query(
        'UPDATE cart_items SET quantity = ? WHERE id = ? AND user_id = ?',
        [parseInt(quantity), req.params.id, req.session.user.id]
      );
      return res.redirect('/cart');
    } catch (err) {
      req.flash('error', 'Lỗi cập nhật giỏ hàng.');
      return res.redirect('/cart');
    }
  },

  // POST /cart/remove/:id
  remove: async (req, res) => {
    try {
      await db.query('DELETE FROM cart_items WHERE id = ? AND user_id = ?', [req.params.id, req.session.user.id]);
      req.flash('success', 'Đã xóa sản phẩm khỏi giỏ hàng.');
      return res.redirect('/cart');
    } catch (err) {
      req.flash('error', 'Lỗi xóa sản phẩm.');
      return res.redirect('/cart');
    }
  },

  // POST /cart/clear
  clear: async (req, res) => {
    try {
      await db.query('DELETE FROM cart_items WHERE user_id = ?', [req.session.user.id]);
      req.flash('success', 'Đã xóa toàn bộ giỏ hàng.');
      return res.redirect('/cart');
    } catch (err) {
      req.flash('error', 'Lỗi xóa giỏ hàng.');
      return res.redirect('/cart');
    }
  }
};

module.exports = cartController;
