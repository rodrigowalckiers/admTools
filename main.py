import ccxt

class CoinHunter:
    def __init__(self, exchange_name):
        try:
            self.exchange = getattr(ccxt, exchange_name)()
        except AttributeError:
            raise ValueError(f"Exchange {exchange_name} não suportada.")

    def fetch_markets(self):
        """Busca todos os mercados da exchange."""
        try:
            return self.exchange.fetch_tickers()
        except Exception as e:
            print(f"Erro ao buscar mercados: {e}")
            return {}

    def filter_and_sort_markets(self, markets):
        """Filtra os mercados para pares /USDT e ordena por volume."""
        filtered_markets = {k: v for k, v in markets.items() if k.endswith('/USDT')}
        sorted_markets = sorted(filtered_markets.items(), key=lambda x: (x[1]['quoteVolume'], x[1]['baseVolume']), reverse=True)
        return sorted_markets

    def print_markets(self, markets):
        """Imprime os mercados."""
        print("//Mercados")
        for market in markets:
            print(f"Mercado: {market[0]}, Volume 24h: {market[1]['baseVolume']}, Volume de Mercado: {market[1]['quoteVolume']}")

    def analyze_altcoins(self, markets):
        """Analisa altcoins, comparando o preço mais antigo com o preço atual."""
        valid_markets = []
        for market in markets:
            try:
                ohlcv = self.exchange.fetch_ohlcv(market[0], '1M')  # Busca dados históricos de preços com intervalo de 1 mês
                if len(ohlcv) > 0:  # Verifica se há dados históricos disponíveis
                    oldest_price = ohlcv[0][1]  # Preço mais antigo
                    current_price = market[1]['last']  # Preço atual
                    if current_price is not None and oldest_price is not None and current_price > oldest_price:
                        valid_markets.append(market)
                        if len(valid_markets) == 30:  # Se já temos 10 moedas válidas, interrompemos o loop
                            break
            except Exception as e:
                print(f"Erro ao analisar mercado {market[0]}: {e}")
        return valid_markets

    def generate_report(self, valid_markets):
        """Gera um relatório sobre os mercados válidos."""
        report = []
        for market in valid_markets:
            try:
                # Busca dados adicionais do mercado
                market_data = self.exchange.fetch_ticker(market[0])
                # Adiciona os dados ao relatório
                report.append({
                    'Mercado': market[0],
                    'Preço Atual': market_data['last'],
                    'Volume 24h': market_data['baseVolume'],
                    'Volume de Mercado': market_data['quoteVolume'],
                    'Variação 24h': market_data['percentage'],
                    'Maior Preço 24h': market_data['high'],
                    'Menor Preço 24h': market_data['low'],
                })
            except Exception as e:
                print(f"Erro ao gerar relatório para o mercado {market[0]}: {e}")
        return report

    def rank_coins_for_holding(self, report):
        """Classifica as moedas para holding com base em critérios específicos."""
        # Define os pesos para cada critério
        weights = {
            'Preço Atual': -0.1,  # Queremos moedas mais baratas
            'Volume 24h': 0.2,  # Queremos moedas com alto volume de negociação
            'Volume de Mercado': 0.2,  # Queremos moedas com alto volume de mercado
            'Variação 24h': 0.1,  # Queremos moedas com alta variação de preço
            'Maior Preço 24h': -0.1,  # Queremos moedas que não estão no seu pico de preço
            'Menor Preço 24h': 0.1,  # Queremos moedas que estão acima do seu preço mais baixo
        }
        # Calcula a pontuação total para cada moeda
        for coin in report:
            coin['Score'] = sum(coin[criterion] * weight for criterion, weight in weights.items())
        # Classifica as moedas por pontuação
        ranked_report = sorted(report, key=lambda x: x['Score'], reverse=True)
        # Retorna as 10 melhores moedas para holding
        return ranked_report[:30]

    def executar(self):
        """Executa o CoinHunter."""
        mercados = self.fetch_markets()
        mercados_ordenados = self.filter_and_sort_markets(mercados)
        mercados_validos = self.analyze_altcoins(mercados_ordenados)
        #self.print_markets(mercados_validos)
        ranked_coins = self.rank_coins_for_holding(self.generate_report(mercados_validos))
        print("//Rank Coins")
        for coin in ranked_coins:
            print(coin)

if __name__ == "__main__":
    coin_hunter = CoinHunter('binance')
    coin_hunter.executar()
