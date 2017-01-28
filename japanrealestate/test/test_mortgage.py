from japanrealestate.mortgage import Mortgage
from unittest import TestCase
import numpy as np


class TestMortgage(TestCase):
    def test__calculate_loan_periods(self):
        loan = Mortgage()
        loan.tenor = 1
        loan._calculate_loan_periods()
        np.testing.assert_array_equal(loan.loan_periods, list(range(1, 13, 1)))

        loan.tenor = 2
        loan._calculate_loan_periods()
        np.testing.assert_array_equal(loan.loan_periods, list(range(1, 25, 1)))

    def test__calculate_interest_schedule(self):
        loan = Mortgage()
        loan.principal = 200e3
        loan.tenor = 30
        loan.loan_periods = np.arange(30 * 12) + 1

        loan.rate = 0
        loan._calculate_interest_schedule()
        expected = [0] * 30 * 12
        np.testing.assert_array_equal(loan.interest_schedule, expected)

        loan.rate = 6.5 / 100
        loan._calculate_interest_schedule()

        # Assert size, first element, last element, and sum
        self.assertEquals(len(loan.interest_schedule), 30 * 12)
        self.assertAlmostEquals(loan.interest_schedule[0], 1083.33, places=2)
        self.assertAlmostEquals(loan.interest_schedule[-1], 6.81, places=2)
        self.assertAlmostEquals(sum(loan.interest_schedule), 255088.98, places=2)

    def test__calculate_principal_schedule(self):
        loan = Mortgage()
        loan.principal = 200e3
        loan.tenor = 30
        loan.loan_periods = np.arange(30 * 12) + 1

        loan.rate = 0
        loan._calculate_principal_schedule()
        expected = [200000 / 30 / 12] * 30 * 12
        np.testing.assert_almost_equal(loan.principal_schedule, expected, decimal=2)

        loan.rate = 6.5 / 100
        loan._calculate_principal_schedule()
        # Assert size, first element, last element, and sum
        self.assertEquals(len(loan.principal_schedule), 30 * 12)
        self.assertAlmostEquals(loan.principal_schedule[0], 180.80, places=2)
        self.assertAlmostEquals(loan.principal_schedule[-1], 1257.33, places=2)
        self.assertAlmostEquals(sum(loan.principal_schedule), 200e3, places=2)

    def test__calculate_amortization_schedule(self):
        loan = Mortgage()
        loan.tenor = 1
        loan.interest_schedule = np.asarray(range(1, 13, 1))
        loan.principal_schedule = np.asarray(range(12, 0, -1))

        loan._calculate_amortization_schedule()
        expected = [13] * 12
        np.testing.assert_array_equal(loan.amortization_schedule, expected)

    def test__calculate_monthly_payment(self):
        loan = Mortgage()
        self.assertEquals(loan.monthly_payment, 0)

        loan.amortization_schedule = np.asarray([5] * 12)
        loan._calculate_monthly_payment()
        self.assertEquals(loan.monthly_payment, 5)

    def test__calculate_all_fields(self):
        """A basic regression test to confirm that all required functions are called as part of calculate_all_fields"""
        loan = Mortgage(
            principal=200e3,
            tenor=30,
            rate=0
        )
        expected = [200000 / 30 / 12] * 30 * 12
        np.testing.assert_almost_equal(loan.amortization_schedule, expected, decimal=2)
        self.assertAlmostEquals(loan.monthly_payment, 200000 / 30 / 12, places=2)

        loan = Mortgage(
            principal=200e3,
            tenor=30,
            rate=6.5 / 100
        )
        expected = [1264.14] * 30 * 12
        np.testing.assert_almost_equal(loan.amortization_schedule, expected, decimal=2)
        self.assertAlmostEquals(loan.monthly_payment, 1264.14, places=2)
