const db = require('../config/db');
const path = require('path');
const fs = require('fs');

const makeSlug = (name) => {
  const map = {'à':'a','á':'a','ả':'a','ã':'a','ạ':'a','ă':'a','ặ':'a','ắ':'a','ằ':'a','ẳ':'a','ẵ':'a','â':'a','ầ':'a','ấ':'a','ẩ':'a','ẫ':'a','ậ':'a','đ':'d','è':'e','é':'e','ẻ':'e','ẽ':'e','ẹ':'e','ê':'e','ề':'e','ế':'e','ể':'e','ễ':'e','ệ':'e','ì':'i','í':'i','ỉ':'i','ĩ':'i','ị':'i','ò':'o','ó':'o','ỏ':'o','õ':'o','ọ':'o','ô':'o','ồ':'o','ố':'o','ổ':'o','ỗ':'o','ộ':'o','ơ':'o','ờ':'o','ớ':'o','ở':'o','ỡ':'o','ợ':'o','ù':'u','ú':'u','ủ':'u','ũ':'u','ụ':'u','ư':'u','ừ':'u','ứ':'u','ử':'u','ữ':'u','ự':'u','ỳ':'y','ý':'y','ỷ':'y','ỹ':'y','ỵ':'y'};
  return name.toLowerCase().split('').map(c => map[c] || c).join('').replace(/[^a-z0-9 ]/g,'').trim().replace(/\s+/g,'-');
};

const productController = {
  // GET /products
  index: async (req, res) => {
    try {
      const { search, category_id, min_price, max_price, sort, page = 1 } = req.query;
      const limit = 12;
      let where = ['p.is_active = 1'];
      let params = [];

      if (search)      { where.push('p.name LIKE ?');                         params.push(`%${search}%`); }
      if (category_id) { where.push('p.category_id = ?');                     params.push(category_id); }
      if (min_price)   { where.push('COALESCE(p.sale_price, p.price) >= ?');  params.push(min_price); }
      if (max_price)   { where.push('COALESCE(p.sale_price, p.price) <= ?');  params.push(max_price); }

      let orderBy = 'p.created_at DESC';
      if (sort === 'price_asc')  orderBy = 'COALESCE(p.sale_price, p.price) ASC';
      if (sort === 'price_desc') orderBy = 'COALESCE(p.sale_price, p.price) DESC';
      if (sort === 'name')       orderBy = 'p.name ASC';
      if (sort === 'popular')    orderBy = 'p.views DESC';

      const offset = (parseInt(page) - 1) * limit;
      const whereStr = 'WHERE ' + where.join(' AND ');

      const [products] = await db.query(
        `SELECT p.*, c.name AS category_name FROM products p
         LEFT JOIN categories c ON p.category_id = c.id
         ${whereStr} ORDER BY ${orderBy} LIMIT ? OFFSET ?`,
        [...params, limit, offset]
      );
      const [[{ total }]] = await db.query(`SELECT COUNT(*) as total FROM products p ${whereStr}`, params);
      const [categories] = await db.query('SELECT * FROM categories WHERE is_active = 1 ORDER BY name');

      res.render('pages/products', {
        title: 'Sản phẩm',
        products,
        categories,
        query: req.query,
        pagination: { total, page: parseInt(page), limit, totalPages: Math.ceil(total / limit) }
      });
    } catch (err) {
      console.error(err);
      res.status(500).render('pages/error', { title: 'Lỗi', message: err.message });
    }
  },

  // GET /products/:slug
  detail: async (req, res) => {
    try {
      const [rows] = await db.query(
        `SELECT p.*, c.name AS category_name, s.name AS supplier_name
         FROM products p
         LEFT JOIN categories c ON p.category_id = c.id
         LEFT JOIN suppliers s ON p.supplier_id = s.id
         WHERE p.slug = ? AND p.is_active = 1`,
        [req.params.slug]
      );
      if (!rows.length) {
        return res.status(404).render('pages/404', { title: 'Không tìm thấy sản phẩm' });
      }
      await db.query('UPDATE products SET views = views + 1 WHERE id = ?', [rows[0].id]);

      // Sản phẩm liên quan
      const [related] = await db.query(
        `SELECT * FROM products WHERE category_id = ? AND id != ? AND is_active = 1 LIMIT 4`,
        [rows[0].category_id, rows[0].id]
      );

      res.render('pages/product-detail', {
        title: rows[0].name,
        product: rows[0],
        related
      });
    } catch (err) {
      console.error(err);
      res.status(500).render('pages/error', { title: 'Lỗi', message: err.message });
    }
  }
};

module.exports = productController;
