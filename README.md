# ccxt-falcon-prototype

A web API to fetch the prices of crypto-assets, fully written in Python.

## What comes in the box?

ccxt-falcon-prototype has been split into 2 different Python files:

  - aggregator.py
  - server.py

The aggregator is responsible for aggregating data, and the server is responsible for serving API requests from clients.

## Dependencies

 * [ccxt](https://github.com/ccxt/ccxt)
 * [falcon](https://github.com/falconry/falcon)
 * [gunicorn](https://github.com/benoitc/gunicorn)
 * [psycopg2](https://github.com/psycopg/psycopg2)

 You will also need a working PostgreSQL database to store asset data in.
 Also, please use python 3.x and not python 2.x :)

 ## How do I set this up?

This is the setup procedure I use on an Ubuntu LXC container:

```bash
apt update && apt -y upgrade
apt install ca-certificates -y
apt install build-essential git python3 python3-dev python3-setuptools

apt install postgresql libpq-dev -y
sudo -u postgres psql
ALTER USER postgres PASSWORD 'PasswordGoesHere';
CREATE DATABASE exchange_db OWNER postgres;
\c exchange_db
CREATE TABLE ticker_prices(
	exchange VARCHAR NOT NULL,
	base VARCHAR NOT NULL,
	quote VARCHAR NOT NULL,
	timestamp BIGINT NOT NULL,
	bid FLOAT,
	ask FLOAT,
	high FLOAT,
	low FLOAT
);
\q

git clone https://github.com/ccxt/ccxt.git
git clone https://github.com/falconry/falcon.git
git clone https://github.com/benoitc/gunicorn.git
git clone https://github.com/psycopg/psycopg2.git
git clone https://github.com/Anorov/cloudflare-scrape.git

# Run this for all the cloned GitHub repositories
# python3 setup.py install

/usr/local/bin/gunicorn server:api --bind 0.0.0.0:8000
```