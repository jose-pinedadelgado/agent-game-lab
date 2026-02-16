const express = require('express');
const router = express.Router();

// API endpoints for AJAX / frontend integration

router.get('/products', (req, res) => {
  // Placeholder - will query database
  res.json({ products: [], total: 0 });
});

router.get('/products/:id', (req, res) => {
  res.json({ product: null });
});

router.get('/services', (req, res) => {
  res.json({ services: [], total: 0 });
});

router.get('/cart', (req, res) => {
  const cart = req.session.cart || { items: [], total: 0 };
  res.json(cart);
});

module.exports = router;
