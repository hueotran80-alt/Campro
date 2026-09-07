const router = require('express').Router();
const { profileController } = require('../controllers/others.controller');
const { requireLogin } = require('../middleware/auth.middleware');
router.use(requireLogin);
router.get('/',               profileController.show);
router.post('/update',        profileController.update);
router.post('/change-password', profileController.changePassword);
module.exports = router;
