const express = require('express');
const router = express.Router();

router.get('/', (req, res) => {
  res.render('home', {
    title: 'Paco Dog Shop - Dog Accessories & Training Services',
    featuredProducts: [],
    featuredServices: []
  });
});

module.exports = router;
