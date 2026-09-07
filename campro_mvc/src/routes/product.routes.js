const router = require('express').Router();
const { index, detail } = require('../controllers/product.controller');
router.get('/',      index);
router.get('/:slug', detail);
module.exports = router;
