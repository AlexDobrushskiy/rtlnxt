#!/usr/bin/python3
from collections import defaultdict
from datetime import datetime

BASE_CURRENCY = 'USD'
PLUS_INFINITY = datetime(9999, 12, 31, 23, 59, 59)


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
        if to_dt and to_dt <= from_dt:
            from ipdb import set_trace; set_trace()
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

    def __init__(self):
        """
        storage - dict with the following structure:
         {'RUB': {'latest': <ExchangeRate object>, rates: [<list of ExchangeRate objects>]},
         ...
         }
        """
        def dict_factory():
            return {'latest': None, 'rates': []}

        self._storage = defaultdict(dict_factory)

    def add_exchange_rate(self, exchange_rate):
        """
        Adds exchange rate record to storage.
        Implements logic of splitting record, or cutting record if
        new record intersects with existing one by time range when they have common currency pair.
        """
        start = exchange_rate.from_dt
        end = exchange_rate.to_dt
        start_rate = self._get_base_exchange_rate(exchange_rate.to_cur, start)
        end_rate = self._get_base_exchange_rate(exchange_rate.to_cur, end)

        if start_rate and start_rate == end_rate:
            # we're going to insert range in the middle of existing range
            # ^===========^++++++++++++++++++^============^
            #   start_rate  exchange_rate        new_rate
            new_rate = ExchangeRate(from_cur=start_rate.from_cur, to_cur=start_rate.to_cur, rate=start_rate.rate,
                                    from_dt=exchange_rate.to_dt,
                                    to_dt=start_rate.to_dt)
            self._storage[start_rate.to_cur]['rates'].append(new_rate)
            if self._storage[start_rate.to_cur]['latest'] == start_rate:
                self._storage[start_rate.to_cur]['latest'] = new_rate

            start_rate.to_dt = exchange_rate.from_dt
        elif start_rate and not end_rate:
            # cut start_rate
            start_rate.to_dt = exchange_rate.from_dt
        elif not start_rate and end_rate:
            # cut end_rate
            end_rate.from_dt = exchange_rate.to_dt

        # Find all rates X where exchange_rate.from_dt <= x.from_dt <= x.to_dt <= exchange_rate.to_dt, and remove them.
        rates_to_delete = self._get_base_exchange_rates_within_range(exchange_rate.to_cur, exchange_rate.from_dt,
                                                                     exchange_rate.to_dt)
        for rate_to_delete in rates_to_delete:
            self._storage[exchange_rate.to_cur]['rates'].remove(rate_to_delete)

        self._storage[exchange_rate.to_cur]['rates'].append(exchange_rate)
        if not self._storage[exchange_rate.to_cur]['latest'] or exchange_rate.from_dt > self._storage[exchange_rate.to_cur]['latest'].from_dt:
            self._storage[exchange_rate.to_cur]['latest'] = exchange_rate

        # To guarantee that latest record's 'to_dt' points to +inf
        self._storage[exchange_rate.to_cur]['latest'].to_dt = PLUS_INFINITY

    def list_exchange_rates(self):
        """
        Returns list of all exchange rates from storage.
        """
        result = []
        for key in self._storage.keys():
            result += self._storage[key]['rates']
        return result

    def _get_base_exchange_rate(self, cur, timestamp):
        """
        Comlexity is linear (of number records in storage).
        In real life database should be used instead of variable
        """
        if cur in self._storage:
            if timestamp > self._storage[cur]['latest'].from_dt:
                return self._storage[cur]['latest']
            for rate in self._storage[cur]['rates']:
                if rate.from_dt <= timestamp < rate.to_dt:
                    return rate
        return None

    def _get_base_exchange_rates_within_range(self, cur, range_from, range_to):
        """
        Linear complexity of storage length
        """
        result = []
        if cur in self._storage:
            for rate in self._storage[cur]['rates']:
                if range_from <= rate.from_dt <= rate.to_dt <= range_to:
                    result.append(rate)
        return result

    def get_exchange_rate(self, from_cur, to_cur, timestamp):
        """
        Tries to find exchange rate between two currencies in a give timestamp.
        """
        if from_cur == to_cur:
            return 1.

        base_from = self._get_base_exchange_rate(from_cur, timestamp)
        base_to = self._get_base_exchange_rate(to_cur, timestamp)
        if not base_from and from_cur != BASE_CURRENCY:
            raise NoExchangeRateException('Currency: {}, timestamp {}'.format(from_cur, timestamp))
        if not base_to and to_cur != BASE_CURRENCY:
            raise NoExchangeRateException('Currency: {}, timestamp {}'.format(to_cur, timestamp))

        if from_cur == BASE_CURRENCY:
            return base_to.rate
        if to_cur == BASE_CURRENCY:
            return 1. / base_from.rate

        return base_to.rate / base_from.rate

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
