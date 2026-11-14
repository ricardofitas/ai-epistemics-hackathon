import unittest
from context_sensitivity import decode, amount
from decimal import Decimal

class ContextControls(unittest.TestCase):
    def test_currency(self):
        self.assertEqual(amount('$1,234.50'),Decimal('1234.50'))
    def test_unique_value(self):
        item=dict(table='Day | Count\nMonday | 12\nTuesday | 25',choices=['Monday','Tuesday'],question='On which day?')
        self.assertEqual(decode(item,'25')['option'],'Tuesday')
    def test_duplicate_value_stays_unknown(self):
        item=dict(table='Day | Count\nMonday | 12\nTuesday | 12',choices=['Monday','Tuesday'],question='On which day?')
        self.assertIsNone(decode(item,'12'))
    def test_exact_requested_total(self):
        item=dict(table='Clothes | Price\npink sweater | $20\npair of shorts | $30',
                  choices=['yes','no'],question='Deb has $55. Does she have enough to buy a pink sweater and a pair of shorts?')
        self.assertEqual(decode(item,'$50')['option'],'yes')
        self.assertIsNone(decode(item,'$30'))
    def test_budget_is_not_an_output_decoder(self):
        item=dict(table='Clothes | Price\npink sweater | $40\nshorts | $30',
                  choices=['yes','no'],question='Deb has $55. Does she have enough to buy a pink sweater and shorts?')
        self.assertEqual(decode(item,'$70')['option'],'no')
        self.assertIsNone(decode(item,'$55'))

if __name__=='__main__':unittest.main()
