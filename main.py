#!/usr/bin/python3
BASE_CURRENCY = 'USD'


class NoExchangeRateException(Exception):
    pass


class ExchangeRate:
    """
    Exchange rate entity represents exchange rate between two currencies
    in a given time range.
    For simplifying purposes we assume that first currency ('from_cur' constructor parameter)
    should be always equal to BASE_CURRENCY.
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
    """
    Interface which implements user-visible methods:
    """
    def __init__(self, storage):
        self._storage = storage

    def add_exchange_rate(self, exchange_rate):
        """
        Adds exchange rate record to storage.
        Implements logic of splitting record, or cutting record if
        new record intersects with existing one by time range when they have common currency pair.
        """
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
            self._storage.append(new_rate)
            start_rate.to_dt = exchange_rate.from_dt
        elif start_rate and not end_rate:
            # cut start_rate
            start_rate.to_dt = exchange_rate.from_dt
        elif not start_rate and end_rate:
            # cut end_rate
            end_rate.from_dt = exchange_rate.to_dt
        self._storage.append(exchange_rate)

    def list_exchange_rates(self):
        """
        Returns list of all exchange rates from storage.
        """
        return self._storage

    def _get_base_exchange_rate(self, cur, timestamp):
        """
        Comlexity is linear (of number records in storage).
        In real life database should be used instead of variable
        """
        for rate in self._storage:
            if rate.to_cur == cur:
                if rate.from_dt <= timestamp < rate.to_dt:
                    return rate
        raise NoExchangeRateException('Currency: {}, timestamp {}'.format(cur, timestamp))

    def get_exchange_rate(self, from_cur, to_cur, timestamp):
        """
        Tries to find exchange rate between two currencies in a give timestamp.
        If no conversion rate found -
        """
        if from_cur == BASE_CURRENCY:
            base_to = self._get_base_exchange_rate(to_cur, timestamp).rate
            return base_to
        if to_cur == BASE_CURRENCY:
            base_from = self._get_base_exchange_rate(from_cur, timestamp).rate
            return 1./base_from

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
