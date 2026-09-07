const db = require('../config/db');

const homeController = {
  // GET /
  index: async (req, res) => {
    try {
      // Sản phẩm nổi bật
      const [featuredProducts] = await db.query(
        `SELECT p.*, c.name AS category_name FROM products p
         LEFT JOIN categories c ON p.category_id = c.id
         WHERE p.is_active = 1 ORDER BY p.views DESC LIMIT 8`
      );

      // Sản phẩm mới
      const [newProducts] = await db.query(
        `SELECT p.*, c.name AS category_name FROM products p
         LEFT JOIN categories c ON p.category_id = c.id
         WHERE p.is_active = 1 ORDER BY p.created_at DESC LIMIT 8`
      );

      // Danh mục
      const [categories] = await db.query(
        'SELECT * FROM categories WHERE is_active = 1 ORDER BY name'
      );

      // Tin tức mới nhất
      const [latestNews] = await db.query(
        'SELECT * FROM news WHERE is_published = 1 ORDER BY created_at DESC LIMIT 3'
      );

      res.render('pages/home', {
        title: 'CAMPRO - Cửa hàng camera chuyên nghiệp',
        featuredProducts,
        newProducts,
        categories,
        latestNews
      });
    } catch (err) {
      console.error(err);
      res.status(500).render('pages/error', { title: 'Lỗi', message: err.message });
    }
  }
};

module.exports = homeController;
