EXCHANGE_RATE_TBL = []

BASE_CURRENCY = 'USD'


class NoExchangeRateException(Exception):
    pass


class ExchangeRate:
    """
    Assumption/limitation: 'from_cur' is always = BASE_CURRENCY. 'to_cur' may vary.
    """

    def __init__(self, from_cur, to_cur, rate, from_dt, to_dt):
        if from_cur != BASE_CURRENCY:
            raise ValueError('from_cur parameter is expected to be base currency: {}'.format(BASE_CURRENCY))
        if to_dt <= from_dt:
            raise ValueError('from_dt timestamp should be < to_dt')

        self.from_cur = from_cur
        self.to_cur = to_cur
        self.rate = rate
        self.from_dt = from_dt
        self.to_dt = to_dt

    def to_dict(self):
        return {
            'from_cur': self.from_cur,
            'to_cur': self.to_cur,
            'rate': self.rate,
            'from_dt': self.from_dt,
            'to_dt': self.to_dt,
        }


class POSTransaction:
    def __init__(self, total, currency, dateTime):
        self.total = total
        self.currency = currency
        self.dateTime = dateTime


class POSTransactionManager:
    def add_exchange_rate(self, exchange_rate):
        start = exchange_rate.from_dt
        end = exchange_rate.to_dt
        try:
            start_rate = self._get_base_exchange_rate(exchange_rate.to_cur, start)
        except NoExchangeRateException:
            start_rate = None

        try:
            end_rate = self._get_base_exchange_rate(exchange_rate.to_cur, end)
        except NoExchangeRateException:
            end_rate = None
        if start_rate and start_rate == end_rate:
            # we're going to insert range in the middle of existing range
            # ^===========^++++++++++++++++++^============^
            #   start_rate  exchange_rate        new_rate
            new_rate = ExchangeRate(from_cur=start_rate.from_cur, to_cur=start_rate.to_cur, rate=start_rate.rate, from_dt=exchange_rate.to_dt,
                                    to_dt=start_rate.to_dt)
            EXCHANGE_RATE_TBL.append(new_rate)
            start_rate.to_dt = exchange_rate.from_dt
        elif start_rate and not end_rate:
            # cut start_rate
            start_rate.to_dt = exchange_rate.from_dt
        elif not start_rate and end_rate:
            # cut end_rate
            end_rate.from_dt = exchange_rate.to_dt
        EXCHANGE_RATE_TBL.append(exchange_rate)

    def list_exchange_rates(self):
        return [ExchangeRate(**x) for x in EXCHANGE_RATE_TBL]

    def _get_base_exchange_rate(self, cur, timestamp):
        # Poor implementation in assumption that we shouldn't use DB.
        # In real live we should user database to store and fetch data instead of global variable.
        for rate in EXCHANGE_RATE_TBL:
            if rate['to_cur'] == cur:
                if rate['from_dt'] >= timestamp > rate['to_dt']:
                    return rate
        raise NoExchangeRateException('Currency: {}, timestamp {}'.format(cur, timestamp))

    def get_exchange_rate(self, from_cur, to_cur, timestamp):
        base_from = self._get_base_exchange_rate(from_cur, timestamp).rate
        base_to = self._get_base_exchange_rate(to_cur, timestamp).rate
        return base_to / base_from

    def convert_pos_transaction(self, pos_transaction, convert_to):
        """
        Creates new POSTransaction object with required currency.
        However doesn't touch existing POSTransaction object - it's caller's responsibility
        to remove it properly if needed.
        """
        exchange_rate = self.get_exchange_rate(pos_transaction.currency, convert_to, pos_transaction.dateTime)
        new_transaction = POSTransaction(total=pos_transaction.total * exchange_rate, currency=convert_to,
                                         dateTime=pos_transaction.dateTime)
        return new_transaction
