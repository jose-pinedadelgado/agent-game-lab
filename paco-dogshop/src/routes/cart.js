const express = require('express');
const router = express.Router();

router.get('/', (req, res) => {
  const cart = req.session.cart || { items: [], total: 0 };
  res.render('cart', {
    title: 'Cart - Paco Dog Shop',
    cart
  });
});

router.post('/add', (req, res) => {
  if (!req.session.cart) {
    req.session.cart = { items: [], total: 0 };
  }
  const { productId, name, price, quantity } = req.body;
  const existing = req.session.cart.items.find(i => i.productId === productId);
  if (existing) {
    existing.quantity += parseInt(quantity) || 1;
  } else {
    req.session.cart.items.push({
      productId,
      name,
      price: parseFloat(price),
      quantity: parseInt(quantity) || 1
    });
  }
  req.session.cart.total = req.session.cart.items.reduce(
    (sum, item) => sum + item.price * item.quantity, 0
  );
  res.redirect('/cart');
});

router.post('/remove', (req, res) => {
  if (req.session.cart) {
    req.session.cart.items = req.session.cart.items.filter(
      i => i.productId !== req.body.productId
    );
    req.session.cart.total = req.session.cart.items.reduce(
      (sum, item) => sum + item.price * item.quantity, 0
    );
  }
  res.redirect('/cart');
});

router.get('/checkout', (req, res) => {
  const cart = req.session.cart || { items: [], total: 0 };
  res.render('checkout', {
    title: 'Checkout - Paco Dog Shop',
    cart,
    stripeKey: process.env.STRIPE_PUBLISHABLE_KEY || ''
  });
});

module.exports = router;
