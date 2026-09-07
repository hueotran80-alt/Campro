const router = require('express').Router();
const { contactController } = require('../controllers/others.controller');
router.get('/',  contactController.show);
router.post('/', contactController.submit);
module.exports = router;
