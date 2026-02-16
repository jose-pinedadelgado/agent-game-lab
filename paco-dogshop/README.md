# Paco Dog Shop - Dog Accessories & Training Services

A sample e-commerce and services website for a dog accessories and training business, built as an educational project for teaching students web development, business logic, and modern deployment practices.

## Live Site

**Current:** [PacoDogshop.com](https://pacodogshop.com) (hosted on AWS Lightsail)

## Project Purpose

This project serves as a hands-on teaching tool for students learning:
- Full-stack web development
- E-commerce patterns (product catalog, cart, checkout)
- Service booking systems
- Database design and management
- API development
- Cloud deployment (AWS Lightsail)
- Payment integration (Stripe test mode)
- Responsive web design

## Features

### Shop (Dog Accessories)
- Product catalog with categories (collars, leashes, toys, grooming, apparel, bowls & feeders)
- Product detail pages with images, descriptions, pricing
- Shopping cart and checkout flow
- Stripe payment integration (test/demo mode)
- Order history and tracking

### Training Services
- Service listings (group classes, private sessions, puppy programs)
- Trainer profiles
- Online booking/scheduling system
- Class calendar view

### General
- Responsive design (mobile-first)
- Contact form
- Blog / dog care tips
- About page with business story
- Admin dashboard for inventory and booking management

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Runtime | Node.js 20+ |
| Framework | Express.js |
| Templating | EJS |
| Database | SQLite (dev) / PostgreSQL (prod) |
| ORM | Knex.js |
| CSS | Tailwind CSS |
| Payments | Stripe (test mode) |
| Hosting | AWS Lightsail |
| Testing | Jest + Supertest |

## Getting Started

### Prerequisites
- Node.js 20+
- npm or yarn

### Installation

```bash
cd paco-dogshop
npm install
```

### Environment Setup

```bash
cp .env.example .env
# Edit .env with your configuration
```

### Database Setup

```bash
npm run db:migrate
npm run db:seed
```

### Development

```bash
npm run dev
```

The site will be available at `http://localhost:3000`.

### Testing

```bash
npm test
```

### Production Build

```bash
npm run build
npm start
```

## Project Structure

```
paco-dogshop/
├── public/              # Static assets
│   ├── css/             # Stylesheets
│   ├── js/              # Client-side JavaScript
│   └── images/          # Product images, logos, etc.
├── src/
│   ├── config/          # App configuration
│   ├── controllers/     # Route handlers
│   ├── middleware/       # Express middleware
│   ├── models/          # Database models
│   ├── routes/          # Route definitions
│   ├── services/        # Business logic
│   ├── utils/           # Helper utilities
│   └── views/           # EJS templates
│       ├── pages/       # Full page templates
│       └── partials/    # Reusable components
├── data/
│   └── seed/            # Seed data for products, services, etc.
├── tests/               # Test files
├── docs/                # Documentation for students
├── scripts/             # Utility scripts (migrate, seed, deploy)
└── templates/           # Email and notification templates
```

## Deployment (AWS Lightsail)

See [docs/deployment.md](docs/deployment.md) for step-by-step AWS Lightsail deployment instructions.

## License

MIT - This is an educational project.
