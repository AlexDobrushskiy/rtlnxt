#!/usr/bin/python3
import unittest
from datetime import datetime

from main import POSTransactionManager, ExchangeRate, POSTransaction

CURRENCY_RUB = 'RUB'
CURRENCY_USD = 'USD'
CURRENCY_CNY = 'CNY'
CURRENCY_THB = 'THB'
CURRENCY_EUR = 'EUR'


class AddExchangeRateTestCase(unittest.TestCase):
    def setUp(self):
        self.timestamp1 = datetime(2017, 3, 1, 3)
        self.exchange_rate1 = ExchangeRate(CURRENCY_USD, CURRENCY_RUB, 60., datetime(2017, 3, 1, 0),
                                           datetime(2017, 3, 2, 0))
        self.exchange_rate2 = ExchangeRate(CURRENCY_USD, CURRENCY_RUB, 60., datetime(2017, 3, 1, 1),
                                           self.timestamp1)
        self.exchange_rate3 = ExchangeRate(CURRENCY_USD, CURRENCY_RUB, 60., datetime(2017, 2, 27, 1),
                                           self.timestamp1)

    def test_add_exchange_rate_base(self):
        transaction_manager = POSTransactionManager(storage=[])
        self.assertEqual(len(transaction_manager._storage), 0)

        transaction_manager.add_exchange_rate(self.exchange_rate1)
        self.assertEqual(len(transaction_manager._storage), 1)

        rate = transaction_manager._storage[0]
        self.assertEqual(rate, self.exchange_rate1)

    def test_add_exchange_rate_between(self):
        transaction_manager = POSTransactionManager(storage=[])
        self.assertEqual(len(transaction_manager._storage), 0)

        transaction_manager.add_exchange_rate(self.exchange_rate1)
        transaction_manager.add_exchange_rate(self.exchange_rate2)
        self.assertEqual(len(transaction_manager._storage), 3)

    def test_add_exchange_rate_in_the_begining(self):
        transaction_manager = POSTransactionManager(storage=[])
        self.assertEqual(len(transaction_manager._storage), 0)

        transaction_manager.add_exchange_rate(self.exchange_rate1)
        transaction_manager.add_exchange_rate(self.exchange_rate3)
        self.assertEqual(len(transaction_manager._storage), 2)
        self.assertEqual(transaction_manager._storage[0].from_dt, self.timestamp1)


class ListExchangeRatesTestCase(unittest.TestCase):
    def setUp(self):
        self.exchange_rate1 = ExchangeRate(CURRENCY_USD, CURRENCY_RUB, 60., datetime(2017, 3, 1, 0),
                                           datetime(2017, 3, 2, 0))
        self.exchange_rate2 = ExchangeRate(CURRENCY_USD, CURRENCY_RUB, 61., datetime(2017, 3, 2, 0),
                                           datetime(2017, 3, 3, 0))
        self.exchange_rate3 = ExchangeRate(CURRENCY_USD, CURRENCY_RUB, 62., datetime(2017, 3, 3, 0),
                                           datetime(2017, 3, 4, 0))

    def test_rates_list(self):
        transaction_manager = POSTransactionManager(storage=[])
        transaction_manager.add_exchange_rate(self.exchange_rate1)
        transaction_manager.add_exchange_rate(self.exchange_rate2)
        transaction_manager.add_exchange_rate(self.exchange_rate3)
        rates_list = transaction_manager.list_exchange_rates()
        self.assertEqual(len(rates_list), 3)
        self.assertEqual(rates_list[0].rate, 60.)
        self.assertEqual(rates_list[1].rate, 61.)
        self.assertEqual(rates_list[2].rate, 62.)


class GetExchangeRateTestCase(unittest.TestCase):
    def setUp(self):
        self.exchange_rate1 = ExchangeRate(CURRENCY_USD, CURRENCY_RUB, 60., datetime(2017, 3, 1, 0),
                                           datetime(2017, 3, 2, 0))
        self.exchange_rate2 = ExchangeRate(CURRENCY_USD, CURRENCY_THB, 30., datetime(2017, 3, 1, 0),
                                           datetime(2017, 3, 2, 0))

    def test_get_exchange_rate_rub_thb(self):
        transaction_manager = POSTransactionManager(storage=[])
        transaction_manager.add_exchange_rate(self.exchange_rate1)
        transaction_manager.add_exchange_rate(self.exchange_rate2)
        rub_thb = transaction_manager.get_exchange_rate(CURRENCY_RUB, CURRENCY_THB, datetime(2017, 3, 1, 1))
        self.assertAlmostEqual(rub_thb, 0.5)

    def test_get_exchange_rate_thb_rub(self):
        transaction_manager = POSTransactionManager(storage=[])
        transaction_manager.add_exchange_rate(self.exchange_rate1)
        transaction_manager.add_exchange_rate(self.exchange_rate2)
        rub_thb = transaction_manager.get_exchange_rate(CURRENCY_THB, CURRENCY_RUB, datetime(2017, 3, 1, 1))
        self.assertAlmostEqual(rub_thb, 2)

    def test_get_exchange_rate_usd_rub(self):
        transaction_manager = POSTransactionManager(storage=[])
        transaction_manager.add_exchange_rate(self.exchange_rate1)
        transaction_manager.add_exchange_rate(self.exchange_rate2)
        usd_rub = transaction_manager.get_exchange_rate(CURRENCY_USD, CURRENCY_RUB, datetime(2017, 3, 1, 1))
        self.assertAlmostEqual(usd_rub, 60.)

    def test_get_exchange_rate_rub_usd(self):
        transaction_manager = POSTransactionManager(storage=[])
        transaction_manager.add_exchange_rate(self.exchange_rate1)
        transaction_manager.add_exchange_rate(self.exchange_rate2)
        usd_rub = transaction_manager.get_exchange_rate(CURRENCY_RUB, CURRENCY_USD, datetime(2017, 3, 1, 1))
        self.assertAlmostEqual(usd_rub, 1./60.)


class ConvertPOSTransactionTestCase(unittest.TestCase):
    def setUp(self):
        self.exchange_rate1 = ExchangeRate(CURRENCY_USD, CURRENCY_RUB, 60., datetime(2017, 3, 1, 0),
                                           datetime(2017, 3, 2, 0))
        self.exchange_rate2 = ExchangeRate(CURRENCY_USD, CURRENCY_THB, 30., datetime(2017, 3, 1, 0),
                                           datetime(2017, 3, 2, 0))
        self.pos_transaction = POSTransaction(3.62, CURRENCY_RUB, datetime(2017, 3, 1, 1))

    def test_convert_pos_transaction(self):
        transaction_manager = POSTransactionManager(storage=[])
        transaction_manager.add_exchange_rate(self.exchange_rate1)
        transaction_manager.add_exchange_rate(self.exchange_rate2)
        converted_transaction = transaction_manager.convert_pos_transaction(self.pos_transaction, CURRENCY_THB)
        self.assertEqual(converted_transaction.currency, CURRENCY_THB)
        self.assertAlmostEqual(converted_transaction.total, 3.62/2)


if __name__ == '__main__':
    unittest.main()
