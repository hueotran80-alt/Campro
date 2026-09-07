const router = require('express').Router();
const admin  = require('../controllers/admin.controller');
const { requireAdmin } = require('../middleware/auth.middleware');
const upload = require('../middleware/upload.middleware');

router.use(requireAdmin);

// Dashboard
router.get('/dashboard', admin.dashboard);

// Products
router.get('/products',                    admin.productList);
router.get('/products/create',             admin.productCreate);
router.post('/products',                   upload.single('image'), admin.productStore);
router.post('/products/bulk-delete',       admin.productBulkDelete);
router.get('/products/:id/edit',           admin.productEdit);
router.post('/products/:id',               upload.single('image'), admin.productUpdate);
router.post('/products/:id/delete',        admin.productDelete);
router.post('/products/:id/toggle',        admin.productToggle);

// Categories
router.get('/categories',                  admin.categoryList);
router.post('/categories',                 admin.categoryCreate);
router.post('/categories/:id',             admin.categoryUpdate);
router.post('/categories/:id/delete',      admin.categoryDelete);

// Suppliers
router.get('/suppliers',                   admin.supplierList);
router.post('/suppliers',                  admin.supplierCreate);
router.post('/suppliers/:id',              admin.supplierUpdate);
router.post('/suppliers/:id/delete',       admin.supplierDelete);

// Orders
router.get('/orders',                      admin.orderList);
router.get('/orders/:id',                  admin.orderDetail);
router.post('/orders/:id/status',          admin.orderUpdateStatus);

// Report
router.get('/report',                      admin.report);

// Coupons
router.get('/coupons',                     admin.couponList);
router.post('/coupons',                    admin.couponCreate);
router.post('/coupons/:id/delete',         admin.couponDelete);

// News
router.get('/news',                        admin.newsList);
router.get('/news/create',                 admin.newsCreate);
router.post('/news',                       upload.single('thumbnail'), admin.newsStore);
router.get('/news/:id/edit',               admin.newsEdit);
router.post('/news/:id',                   upload.single('thumbnail'), admin.newsUpdate);
router.post('/news/:id/delete',            admin.newsDelete);

// Contacts
router.get('/contacts',                    admin.contactList);
router.post('/contacts/:id/reply',         admin.contactReply);
router.post('/contacts/:id/delete',        admin.contactDelete);

// Customers
router.get('/customers',                   admin.customerList);
router.post('/customers/:id/update',       admin.customerUpdate);
router.post('/customers/:id/toggle',       admin.customerToggle);
router.post('/customers/:id/delete',       admin.customerDelete);

// Redirect /admin -> /admin/dashboard
router.get('/', (req, res) => res.redirect('/admin/dashboard'));

module.exports = router;
