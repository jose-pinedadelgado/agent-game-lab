# Student Guide: Paco Dog Shop Project

## Overview
This project is a sample dog accessories and training services website built for educational purposes. It covers key web development concepts that you'll encounter in real-world projects.

## What You'll Learn

### 1. Server-Side Rendering with Express + EJS
- How Express.js handles HTTP requests and responses
- Route definition and organization
- Template rendering with EJS (Embedded JavaScript)
- Middleware concepts (sessions, security, logging)

### 2. Database Design
- Relational schema design for products, orders, services, and bookings
- Migrations: versioned database schema changes
- Seed data: pre-populating the database for development

### 3. E-Commerce Patterns
- Product catalog with categories and filtering
- Shopping cart using server-side sessions
- Checkout flow with form validation
- Payment integration concepts (Stripe test mode)

### 4. Service Booking System
- Service listings with scheduling
- Booking form submission and validation
- Trainer profiles and availability

### 5. CSS & Responsive Design
- CSS custom properties (variables) for theming
- CSS Grid and Flexbox for layouts
- Mobile-first responsive design with media queries
- Component-based styling approach

### 6. Deployment
- AWS Lightsail instance setup
- Nginx reverse proxy configuration
- SSL/TLS with Let's Encrypt
- Process management with PM2

## Exercises

### Beginner
1. Add a new product category (e.g., "Health & Wellness")
2. Change the color scheme using CSS variables
3. Add a new page (e.g., FAQ or Testimonials)

### Intermediate
4. Connect the shop to a SQLite database instead of seed JSON files
5. Implement product search functionality
6. Add user registration and login
7. Build an admin page to add/edit products

### Advanced
8. Implement Stripe checkout in test mode
9. Add email notifications for bookings (using Nodemailer)
10. Build a REST API for the product catalog
11. Add image upload for products using Multer
12. Implement order tracking

## Running the Project Locally

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Run tests
npm test
```

## Project Architecture

```
Request → Express Router → Controller → Model/Service → Database
                                ↓
                           EJS Template → HTML Response
```

Each route file in `src/routes/` maps URLs to handler functions. Views in `src/views/` contain the HTML templates. Static files (CSS, JS, images) are served from `public/`.
