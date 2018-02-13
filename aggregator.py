import ccxt, pickle, sys, psycopg2, time, threading, json, cfscrape

try:
    conn = psycopg2.connect("dbname='exchange_db' user='postgres' host='localhost' password='PasswordGoesHere'")
except:
    print("Can't connect to DB :(")
    exit()

exchangeData = {}
assetsData   = {}
symbolsData  = {}

excludeSources = ['coinmarketcap']

for exchange in ccxt.exchanges:
    try:
        if not exchange in excludeSources:
            exchangeData[exchange] = getattr(ccxt, exchange)().load_markets()
            print("Indexed: "+exchange)
    except:
            pass

for exchangeName in list(exchangeData.keys()):
    symbolsData[exchangeName] = []

    for assetItem in exchangeData[exchangeName]:
        assetBase = exchangeData[exchangeName][assetItem]['base']
        quoteItem = exchangeData[exchangeName][assetItem]['quote']

        symbolsData[exchangeName].append(exchangeData[exchangeName][assetItem]['symbol'])

        if assetBase in assetsData:
            if exchangeName in assetsData[assetBase]:
                assetsData[assetBase][exchangeName].append(quoteItem)
            else:
                assetsData[assetBase][exchangeName] = [quoteItem]
        else:
            assetsData[assetBase] = {}
            assetsData[assetBase][exchangeName] = [quoteItem]

pickle.dump(assetsData, open("assets.p", "wb"))
pickle.dump(exchangeData, open("exchanges.p", "wb"))
pickle.dump(symbolsData, open("symbols.p", "wb"))

exchangeList = list(symbolsData.keys())

cursor = conn.cursor()

threads = []

def exchangeThread(exchange):
    try:
        exchangeObject = getattr(ccxt, exchange)({
            'timeout': 20000,
            'session': cfscrape.create_scraper(),
        })
        if exchangeObject.hasFetchTickers:
            try:
                tickers = exchangeObject.fetch_tickers()

                for symbol in list(tickers.keys()):
                    if "/" in symbol:
                        symbolSplit = symbol.split("/")
                        baseSymbol = symbolSplit[0]
                        quoteSymbol = symbolSplit[1]
                        cursor.execute("DELETE FROM ticker_prices WHERE exchange = %s AND base = %s AND quote = %s", (exchange, baseSymbol, quoteSymbol))
                        cursor.execute("INSERT INTO ticker_prices (exchange, base, quote, timestamp, bid, ask, high, low) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", (exchange, baseSymbol, quoteSymbol, int(tickers[symbol]['timestamp']), tickers[symbol]['bid'], tickers[symbol]['ask'], tickers[symbol]['high'], tickers[symbol]['low']))
                    else:
                        print("Symbol not correct format: "+symbol+" on exchange "+exchange)
                print("Exchange: "+exchange+", symbol: all")
            except Exception as e:
                print("An exception of type "+type(e).__name__+" has occurred.")
        else:
            exchangeObject.load_markets()

            for symbol in exchangeObject.symbols:
                try:
                    if "/" in symbol:
                        symbolSplit = symbol.split("/")
                        baseSymbol = symbolSplit[0]
                        quoteSymbol = symbolSplit[1]
                        ticker = exchangeObject.fetch_ticker(symbol)
                        time.sleep(exchangeObject.rateLimit/800)
                        cursor.execute("DELETE FROM ticker_prices WHERE exchange = %s AND base = %s AND quote = %s", (exchange, baseSymbol, quoteSymbol))
                        cursor.execute("INSERT INTO ticker_prices (exchange, base, quote, timestamp, bid, ask, high, low) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", (exchange, baseSymbol, quoteSymbol, int(ticker['timestamp']), ticker['bid'], ticker['ask'], ticker['high'], ticker['low']))
                        print("Exchange: "+exchange+", symbol: "+symbol)
                    else:
                        print("Symbol not correct format: "+symbol+" on exchange "+exchange)
                except Exception as e:
                    print("An exception of type "+type(e).__name__+" has occurred.")

        conn.commit()
    except Exception as e:
        print("An exception of type "+type(e).__name__+" has occurred.")

for exchange in exchangeList:
    t = threading.Thread(target=exchangeThread, args=(exchange,))
    threads.append(t)
    t.start()

while True:
    for thread in threads:
        if not thread.isAlive():
            print(thread._args[0])
            cursor.execute("SELECT MAX(timestamp) FROM ticker_prices WHERE exchange = %s", (thread._args[0],))
            latestTimestamp = cursor.fetchone()[0]

            thread.start()

            time.sleep(0.25)

            cursor.execute("DELETE FROM ticker_prices WHERE timestamp <= %s AND exchange = %s", (latestTimestamp,thread._args[0]))
            conn.commit()
    time.sleep(5)

cursor.close()
conn.close()