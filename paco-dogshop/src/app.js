require('dotenv').config();

const express = require('express');
const path = require('path');
const helmet = require('helmet');
const morgan = require('morgan');
const session = require('express-session');

const app = express();
const PORT = process.env.PORT || 3000;

// Security middleware
app.use(helmet({ contentSecurityPolicy: false }));

// Logging
app.use(morgan('dev'));

// Body parsing
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Static files
app.use(express.static(path.join(__dirname, '..', 'public')));

// View engine
app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views', 'pages'));

// Session
app.use(session({
  secret: process.env.SESSION_SECRET || 'dev-secret-change-me',
  resave: false,
  saveUninitialized: false,
  cookie: { secure: process.env.NODE_ENV === 'production' }
}));

// Make cart available to all templates
app.use((req, res, next) => {
  res.locals.cart = req.session.cart || { items: [], total: 0 };
  res.locals.currentPath = req.path;
  next();
});

// Routes
app.use('/', require('./routes/home'));
app.use('/shop', require('./routes/shop'));
app.use('/training', require('./routes/training'));
app.use('/cart', require('./routes/cart'));
app.use('/about', require('./routes/about'));
app.use('/contact', require('./routes/contact'));
app.use('/api', require('./routes/api'));

// 404 handler
app.use((req, res) => {
  res.status(404).render('404', { title: 'Page Not Found' });
});

// Error handler
app.use((err, req, res, _next) => {
  console.error(err.stack);
  res.status(500).render('error', {
    title: 'Server Error',
    message: process.env.NODE_ENV === 'production'
      ? 'Something went wrong'
      : err.message
  });
});

if (require.main === module) {
  app.listen(PORT, () => {
    console.log(`Paco Dog Shop running at http://localhost:${PORT}`);
  });
}

module.exports = app;
