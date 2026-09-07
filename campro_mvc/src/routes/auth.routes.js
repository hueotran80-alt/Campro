const router = require('express').Router();
const { showLogin, login, showRegister, register, logout } = require('../controllers/auth.controller');
const { guestOnly } = require('../middleware/auth.middleware');
router.get('/login',    guestOnly, showLogin);
router.post('/login',   guestOnly, login);
router.get('/register', guestOnly, showRegister);
router.post('/register',guestOnly, register);
router.get('/logout',   logout);
module.exports = router;
