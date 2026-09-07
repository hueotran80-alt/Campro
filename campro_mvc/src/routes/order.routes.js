const router = require('express').Router();
const { myOrders, detail, showCheckout, placeOrder, cancel, checkCoupon } = require('../controllers/order.controller');
const { requireLogin } = require('../middleware/auth.middleware');
router.use(requireLogin);
router.get('/',              myOrders);
router.get('/checkout',      showCheckout);
router.post('/checkout',     placeOrder);
router.post('/coupon-check', checkCoupon);   // AJAX kiểm tra mã giảm giá
router.get('/:id',           detail);
router.post('/:id/cancel',   cancel);
module.exports = router;
