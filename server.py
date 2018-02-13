import ccxt, falcon, json, pickle, psycopg2, psycopg2.extras, re


conn = psycopg2.connect("dbname='exchange_db' user='postgres' host='localhost' password='PasswordGoesHere'")

cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

exchangeData = pickle.load(open("exchanges.p", "rb"))
assetData = pickle.load(open("assets.p", "rb"))

class GetExchanges:
    def on_get(self, req, resp):
        resp.media = list(exchangeData.keys())

class GetExchange:
    def on_get(self, req, resp, exchangeNameGiven):
        if exchangeNameGiven in exchangeData:
            resp.media = exchangeData[exchangeNameGiven]
        else:
            resp.status = falcon.HTTP_404
            resp.media = { 'message': 'Exchange not found.' }

class GetExchangeLastUpdated:
    def on_get(self, req, resp, exchangeNameGiven):
        if exchangeNameGiven in exchangeData:
            cursor.execute("SELECT MAX(timestamp) FROM ticker_prices WHERE exchange = %s", (exchangeNameGiven,))
            resp.media = cursor.fetchone()[0]

        else:
            resp.status = falcon.HTTP_404
            resp.media = { 'message': 'Exchange not found.' }

class GetAssets:
    def on_get(self, req, resp):
        resp.media = assetData

class GetAsset:
    def on_get(self, req, resp, symbolGiven):
        if symbolGiven.upper() in assetData:
            resp.media = assetData[symbolGiven.upper()]
        else:
            resp.status = falcon.HTTP_404
            resp.media = { 'message': 'Base asset not found.' }

class GetAssetPrice:
    def on_get(self, req, resp, baseGiven, quoteGiven):
        if len(baseGiven) < 32 and len(quoteGiven) < 32 and re.match("^[.A-Za-z0-9_-]*$", baseGiven) and re.match("^[.A-Za-z0-9_-]*$", quoteGiven):
            cursor.execute("SELECT * FROM ticker_prices WHERE base = %s AND quote = %s ORDER BY exchange DESC, timestamp DESC", (baseGiven,quoteGiven))
            returnObjects = []
            test = cursor.fetchall()

            for tItem in test:
                exchangeAlreadyExists = False
                for returnObject in returnObjects:
                    if returnObject[0] == tItem[0]:
                        exchangeAlreadyExists = True
                if not exchangeAlreadyExists:
                    returnObjects.append(tItem)

                resp.media = returnObjects
        else:
            resp.status = falcon.HTTP_404
            resp.media = { 'message': 'Symbol not available.' }

class GetAssetPrices:
    def on_get(self, req, resp, baseGiven):
        if len(baseGiven) < 32 and re.match("^[.A-Za-z0-9_-]*$", baseGiven):
            cursor.execute("SELECT * FROM ticker_prices WHERE base = %s ORDER BY exchange DESC, timestamp DESC", (baseGiven,))
            resp.media = cursor.fetchall()
        else:
            resp.status = falcon.HTTP_404
            resp.media = { 'message': 'Symbol not available.' }

class GetAssetPriceForExchange:
    def on_get(self, req, resp, baseGiven, quoteGiven, exchange):
        if len(baseGiven) < 10 and len(quoteGiven) < 32 and re.match("^[.A-Za-z0-9_-]*$", baseGiven) and re.match("^[.A-Za-z0-9_-]*$", quoteGiven) and exchange in exchangeData:
            cursor.execute("SELECT * FROM ticker_prices WHERE base = %s AND quote = %s AND exchange = %s ORDER BY exchange DESC, timestamp DESC", (baseGiven,quoteGiven,exchange))
            returnObjects = []
            test = cursor.fetchall()

            for tItem in test:
                exchangeAlreadyExists = False
                for returnObject in returnObjects:
                    if returnObject[0] == tItem[0]:
                        exchangeAlreadyExists = True
                if not exchangeAlreadyExists:
                    returnObjects.append(tItem)

                resp.media = returnObjects
        else:
            resp.status = falcon.HTTP_404
            resp.media = { 'message': 'Symbol not available.' }

api = falcon.API()
api.add_route('/exchanges', GetExchanges())
api.add_route('/exchange/{exchangeNameGiven}', GetExchange())
api.add_route('/exchange/{exchangeNameGiven}/lastUpdated', GetExchangeLastUpdated())
api.add_route('/assets', GetAssets())
api.add_route('/asset/{symbolGiven}', GetAsset())
api.add_route('/price/{baseGiven}/{quoteGiven}/{exchange}', GetAssetPriceForExchange())
api.add_route('/price/{baseGiven}/{quoteGiven}', GetAssetPrice())
api.add_route('/price/{baseGiven}', GetAssetPrices())