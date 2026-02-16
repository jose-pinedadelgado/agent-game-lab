const request = require('supertest');
const app = require('../src/app');

describe('Paco Dog Shop Routes', () => {
  describe('GET /', () => {
    it('should return 200 and render home page', async () => {
      const res = await request(app).get('/');
      expect(res.statusCode).toBe(200);
      expect(res.text).toContain('Paco Dog Shop');
    });
  });

  describe('GET /shop', () => {
    it('should return 200 and render shop page', async () => {
      const res = await request(app).get('/shop');
      expect(res.statusCode).toBe(200);
      expect(res.text).toContain('All Products');
    });
  });

  describe('GET /training', () => {
    it('should return 200 and render training page', async () => {
      const res = await request(app).get('/training');
      expect(res.statusCode).toBe(200);
      expect(res.text).toContain('Training Services');
    });
  });

  describe('GET /about', () => {
    it('should return 200 and render about page', async () => {
      const res = await request(app).get('/about');
      expect(res.statusCode).toBe(200);
      expect(res.text).toContain('About Paco Dog Shop');
    });
  });

  describe('GET /contact', () => {
    it('should return 200 and render contact page', async () => {
      const res = await request(app).get('/contact');
      expect(res.statusCode).toBe(200);
      expect(res.text).toContain('Contact Us');
    });
  });

  describe('GET /cart', () => {
    it('should return 200 and render cart page', async () => {
      const res = await request(app).get('/cart');
      expect(res.statusCode).toBe(200);
      expect(res.text).toContain('Shopping Cart');
    });
  });

  describe('GET /nonexistent', () => {
    it('should return 404', async () => {
      const res = await request(app).get('/nonexistent');
      expect(res.statusCode).toBe(404);
    });
  });

  describe('API endpoints', () => {
    it('GET /api/products should return JSON', async () => {
      const res = await request(app).get('/api/products');
      expect(res.statusCode).toBe(200);
      expect(res.body).toHaveProperty('products');
    });

    it('GET /api/services should return JSON', async () => {
      const res = await request(app).get('/api/services');
      expect(res.statusCode).toBe(200);
      expect(res.body).toHaveProperty('services');
    });

    it('GET /api/cart should return cart object', async () => {
      const res = await request(app).get('/api/cart');
      expect(res.statusCode).toBe(200);
      expect(res.body).toHaveProperty('items');
      expect(res.body).toHaveProperty('total');
    });
  });

  describe('POST /contact', () => {
    it('should redirect to contact page with success', async () => {
      const res = await request(app)
        .post('/contact')
        .send({ name: 'Test', email: 'test@test.com', subject: 'general', message: 'Hello' });
      expect(res.statusCode).toBe(302);
      expect(res.headers.location).toBe('/contact?success=true');
    });
  });

  describe('POST /cart/add', () => {
    it('should add item to cart and redirect', async () => {
      const res = await request(app)
        .post('/cart/add')
        .send({ productId: 'test-1', name: 'Test Product', price: '9.99', quantity: '1' });
      expect(res.statusCode).toBe(302);
      expect(res.headers.location).toBe('/cart');
    });
  });
});
