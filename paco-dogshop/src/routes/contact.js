const express = require('express');
const router = express.Router();

router.get('/', (req, res) => {
  res.render('contact', {
    title: 'Contact Us - Paco Dog Shop',
    success: req.query.success === 'true'
  });
});

router.post('/', (req, res) => {
  const { name, email, subject, message } = req.body;
  // In a real app, send email or store in database
  console.log('Contact form submission:', { name, email, subject, message });
  res.redirect('/contact?success=true');
});

module.exports = router;
