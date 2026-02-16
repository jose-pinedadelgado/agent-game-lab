require('dotenv').config({ path: require('path').join(__dirname, '..', '..', '.env') });

module.exports = {
  development: {
    client: 'sqlite3',
    connection: {
      filename: process.env.DB_FILENAME || './data/paco-dogshop.sqlite3'
    },
    useNullAsDefault: true,
    migrations: {
      directory: require('path').join(__dirname, '..', '..', 'data', 'migrations')
    },
    seeds: {
      directory: require('path').join(__dirname, '..', '..', 'data', 'seed')
    }
  },
  production: {
    client: process.env.DB_CLIENT || 'pg',
    connection: {
      host: process.env.DB_HOST,
      port: process.env.DB_PORT,
      database: process.env.DB_NAME,
      user: process.env.DB_USER,
      password: process.env.DB_PASSWORD
    },
    migrations: {
      directory: require('path').join(__dirname, '..', '..', 'data', 'migrations')
    },
    seeds: {
      directory: require('path').join(__dirname, '..', '..', 'data', 'seed')
    }
  }
};
