const express = require('express');
const router = express.Router();

const CATEGORIES = [
  { slug: 'collars', name: 'Collars & Harnesses' },
  { slug: 'leashes', name: 'Leashes & Leads' },
  { slug: 'toys', name: 'Toys & Enrichment' },
  { slug: 'grooming', name: 'Grooming Supplies' },
  { slug: 'apparel', name: 'Dog Apparel' },
  { slug: 'bowls', name: 'Bowls & Feeders' },
  { slug: 'beds', name: 'Beds & Crates' },
  { slug: 'treats', name: 'Treats & Chews' }
];

router.get('/', (req, res) => {
  res.render('shop', {
    title: 'Shop - Paco Dog Shop',
    categories: CATEGORIES,
    products: [],
    filters: req.query
  });
});

router.get('/category/:slug', (req, res) => {
  const category = CATEGORIES.find(c => c.slug === req.params.slug);
  if (!category) return res.status(404).render('404', { title: 'Category Not Found' });

  res.render('shop', {
    title: `${category.name} - Paco Dog Shop`,
    categories: CATEGORIES,
    currentCategory: category,
    products: [],
    filters: req.query
  });
});

router.get('/product/:id', (req, res) => {
  res.render('product', {
    title: 'Product - Paco Dog Shop',
    product: null
  });
});

module.exports = router;
