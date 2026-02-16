const express = require('express');
const router = express.Router();

router.get('/', (req, res) => {
  res.render('training', {
    title: 'Training Services - Paco Dog Shop',
    services: [],
    trainers: []
  });
});

router.get('/book/:serviceId', (req, res) => {
  res.render('booking', {
    title: 'Book a Session - Paco Dog Shop',
    serviceId: req.params.serviceId
  });
});

module.exports = router;
