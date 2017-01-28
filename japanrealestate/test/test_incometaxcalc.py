from japanrealestate.incometaxcalc import IncomeTaxCalc
from unittest import TestCase
import datetime as dt


class TestIncomeTaxCalc(TestCase):
    def test__calculate_current_date(self):
        income_tax_calc = IncomeTaxCalc()
        self.assertEquals(income_tax_calc.current_date, dt.date.today())

        some_date = dt.date(2016, 12, 24)
        income_tax_calc.current_date = some_date
        income_tax_calc._calculate_current_date()
        self.assertEquals(income_tax_calc.current_date, some_date)

    def test__calculate_total_income(self):
        income_tax_calc = IncomeTaxCalc()
        income_tax_calc.employment_income = 10000000
        income_tax_calc.other_income = 1000000

        income_tax_calc._calculate_total_income()
        self.assertEquals(income_tax_calc.total_income, 11000000)

    def test__calculate_employment_income_after_rent_program(self):
        income_tax_calc = IncomeTaxCalc()
        income_tax_calc.employment_income = 10000000
        income_tax_calc.other_income = 1000000
        income_tax_calc.rent = 150000 * 12

        income_tax_calc.is_rent_program = False
        income_tax_calc._calculate_employment_income_after_rent_program()
        self.assertEquals(income_tax_calc.employment_income_after_rent_program, income_tax_calc.employment_income)

        income_tax_calc.is_rent_program = True
        income_tax_calc._calculate_employment_income_after_rent_program()
        expected = 10000000 - 150000 * 12 * 0.95
        self.assertEquals(income_tax_calc.employment_income_after_rent_program, expected)

    def test__calculate_social_security_expense(self):
        income_tax_calc = IncomeTaxCalc(social_security_expense=200000)
        self.assertEquals(income_tax_calc.social_security_expense, 200000)

        income_tax_calc.social_security_expense = None
        income_tax_calc.employment_income_after_rent_program = 10000000
        income_tax_calc._calculate_social_security_expense()
        self.assertEquals(income_tax_calc.social_security_expense, 1195230)

    def test__calculate_employment_income_deduction(self):
        income_tax_calc = IncomeTaxCalc()
        self.assertEquals(income_tax_calc.employment_income_deduction, 0)

        income_tax_calc.employment_income_after_rent_program = 11000000
        income_tax_calc._calculate_employment_income_deduction()
        self.assertEquals(income_tax_calc.employment_income_deduction, 2150000)

        income_tax_calc.employment_income_after_rent_program = 100000000
        income_tax_calc._calculate_employment_income_deduction()
        self.assertEquals(income_tax_calc.employment_income_deduction, 2200000)

    def test__calculate_employment_income_for_tax(self):
        income_tax_calc = IncomeTaxCalc()
        income_tax_calc.employment_income_after_rent_program = 10000000
        income_tax_calc.employment_income_deduction = 1000000
        income_tax_calc._calculate_employment_income_for_tax()
        self.assertEquals(income_tax_calc.employment_income_for_tax, 9000000)

    def test__calculate_total_income_for_tax(self):
        income_tax_calc = IncomeTaxCalc()
        income_tax_calc.employment_income_for_tax = 9000000
        income_tax_calc.other_income = 1000000
        income_tax_calc._calculate_total_income_for_tax()
        self.assertEquals(income_tax_calc.total_income_for_tax, 10000000)

    def test__calculate_deduction_dependents(self):
        income_tax_calc = IncomeTaxCalc()
        income_tax_calc.number_of_dependents = 3
        income_tax_calc._calculate_deduction_dependents()
        self.assertEquals(income_tax_calc.deduction_dependents, 1140000)

    def test__calculate_deduction_total(self):
        income_tax_calc = IncomeTaxCalc()
        income_tax_calc.medical_expense = 2500000  # Above max deduction of 2000000
        income_tax_calc.social_security_expense = 1000000
        income_tax_calc.life_insurance_premium = 200000
        income_tax_calc.deduction_dependents = 1140000
        expected = 2000000 + 1000000 + 200000 + 1140000 + 380000
        income_tax_calc._calculate_deduction_total()
        self.assertEquals(income_tax_calc.deduction_total, expected)

    def test__calculate_taxable_income(self):
        income_tax_calc = IncomeTaxCalc()

        income_tax_calc.total_income_for_tax = 10000000
        income_tax_calc.deduction_total = 4000000
        income_tax_calc._calculate_taxable_income()
        self.assertEquals(income_tax_calc.taxable_income, 6000000)

        income_tax_calc.total_income_for_tax = 4000000
        income_tax_calc.deduction_total = 10000000
        income_tax_calc._calculate_taxable_income()
        self.assertEquals(income_tax_calc.taxable_income, 0)

    def test__calculate_national_income_tax_bracket(self):
        income_tax_calc = IncomeTaxCalc()

        self.assertEquals(income_tax_calc.national_income_tax_bracket, income_tax_calc._NATIONAL_INCOME_TAX_TABLE[0])

        income_tax_calc.taxable_income = 50000000
        income_tax_calc._calculate_national_income_tax_bracket()
        self.assertEquals(income_tax_calc.national_income_tax_bracket, income_tax_calc._NATIONAL_INCOME_TAX_TABLE[-1])

    def test__calculate_national_income_tax_rate(self):
        income_tax_calc = IncomeTaxCalc()
        income_tax_calc.national_income_tax_bracket = {
            'bounds': [40000000 + 1, float('inf')],
            'rate': 0.45,
            'previous_brackets_sum': 13204000
        }

        income_tax_calc._calculate_national_income_tax_rate()
        self.assertEquals(income_tax_calc.national_income_tax_rate, 0.45)

    def test__calculate_national_income_tax(self):
        income_tax_calc = IncomeTaxCalc()

        income_tax_calc.taxable_income = 50000000
        income_tax_calc.national_income_tax_bracket = {
            'bounds': [40000000 + 1, float('inf')],
            'rate': 0.45,
            'previous_brackets_sum': 13204000
        }
        income_tax_calc.national_income_tax_rate = 0.45
        income_tax_calc.current_date = dt.date(year=2040, month=12, day=25)
        income_tax_calc._calculate_national_income_tax()
        expected = int(4499999.55 + 13204000)
        self.assertEquals(income_tax_calc.national_income_tax, expected)

        income_tax_calc.current_date = dt.date(year=2016, month=12, day=25)
        income_tax_calc._calculate_national_income_tax()
        expected = int((4499999.55 + 13204000) * 1.021)
        self.assertEquals(income_tax_calc.national_income_tax, expected)

    def test__calculate_local_income_tax(self):
        income_tax_calc = IncomeTaxCalc()

        income_tax_calc.taxable_income = 10000000
        income_tax_calc.is_resident_for_tax_purposes = False
        income_tax_calc._calculate_local_income_tax()
        self.assertEquals(income_tax_calc.local_income_tax, 0)

        income_tax_calc.is_resident_for_tax_purposes = True
        income_tax_calc._calculate_local_income_tax()
        self.assertEquals(income_tax_calc.local_income_tax, 1000000)

    def test__calculate_total_income_tax(self):
        income_tax_calc = IncomeTaxCalc()
        income_tax_calc.national_income_tax = 3000000
        income_tax_calc.local_income_tax = 1000000

        income_tax_calc._calculate_total_income_tax()
        self.assertEquals(income_tax_calc.total_income_tax, 4000000)

        income_tax_calc.tax_deduction = 500000
        income_tax_calc._calculate_total_income_tax()
        self.assertEquals(income_tax_calc.total_income_tax, 3500000)

        income_tax_calc.tax_deduction = 5000000
        income_tax_calc._calculate_total_income_tax()
        self.assertEquals(income_tax_calc.total_income_tax, 0)

    def test__calculate_net_income_after_tax(self):
        income_tax_calc = IncomeTaxCalc()
        income_tax_calc.total_income = 20000000
        income_tax_calc.total_income_tax = 7000000
        income_tax_calc.social_security_expense = 3000000
        income_tax_calc._calculate_net_income_after_tax()
        self.assertEquals(income_tax_calc.net_income_after_tax, 10000000)

    def test__calculate_effective_tax_rate(self):
        income_tax_calc = IncomeTaxCalc()
        self.assertEquals(income_tax_calc.effective_tax_rate, 0)

        income_tax_calc.net_income_after_tax = 10000000
        income_tax_calc.total_income = 20000000
        income_tax_calc._calculate_effective_tax_rate()
        self.assertEquals(income_tax_calc.effective_tax_rate, 0.5)

    def test__calculate_all_fields(self):
        """A basic regression test to confirm that all required functions are called as part of calculate_all_fields"""
        income_tax_calc = IncomeTaxCalc(
            employment_income=20000000,
            rent=2400000,
            is_rent_program=True,
            other_income=1000000,
            life_insurance_premium=30000,
            medical_expense=10000,
            number_of_dependents=2,
            social_security_expense=None,
            tax_deduction=100000,
            is_resident_for_tax_purposes=True,
        )

        self.assertAlmostEqual(income_tax_calc.effective_tax_rate, 0.281, places=3)
