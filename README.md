# POS Transaction Manager interface 
Impelents the following methods:
 - `add_exchange_rate(exchange_rate)`
 - - Adds exchange rate record to storage
 - `list_exchange_rates()`
 - - Returns list of all exchange rates from storage
 - `get_exchange_rate(from_currency, to_currency, timestamp)`
 - - Tries to fetch/calculate exchange rate for a given pair in a given timestamp from storage
 - `convert_pos_transaction(pos_transaction, convert_to_currency)`
 - - Creates a new POSTransaction object generated from initial `pos_transaction` converted to a given currency.
 
# Tests
 - `python3 tests.py` will run the test suite. No additional libraries needed.
