from japanrealestate.incometaxcalc import IncomeTaxCalc
from japanrealestate.mortgage import Mortgage
from japanrealestate.realestatecalc import RealEstateCalc
from japanrealestate import taxconstants
from numbers import Number
from unittest import TestCase
import copy
import datetime as dt


class TestRealEstateCalc(TestCase):
    def test__calculate_purchase_date(self):
        real_estate_calc = RealEstateCalc()
        real_estate_calc.purchase_date = None
        real_estate_calc._calculate_purchase_date()
        self.assertEquals(real_estate_calc.purchase_date, dt.date.today())

        some_date = dt.date(2016, 12, 24)
        real_estate_calc.purchase_date = some_date
        real_estate_calc._calculate_purchase_date()
        self.assertEquals(real_estate_calc.purchase_date, some_date)

    def test__calculate_renewal_income_rate(self):
        real_estate_calc = RealEstateCalc()
        real_estate_calc.renewal_income_rate = None
        real_estate_calc._calculate_renewal_income_rate()
        self.assertEquals(real_estate_calc.renewal_income_rate, 1 / 24)

        real_estate_calc.renewal_income_rate = 0.05
        real_estate_calc._calculate_renewal_income_rate()
        self.assertEquals(real_estate_calc.renewal_income_rate, 0.05)

    def test__calculate_rental_management_rental_fee(self):
        real_estate_calc = RealEstateCalc()
        real_estate_calc.rental_management_renewal_fee = None
        real_estate_calc._calculate_rental_management_renewal_fee()
        self.assertEquals(real_estate_calc.rental_management_rental_fee, 0.05)

        real_estate_calc.rental_management_renewal_fee = 0.04
        real_estate_calc = RealEstateCalc(rental_management_rental_fee=0.04)
        self.assertEquals(real_estate_calc.rental_management_rental_fee, 0.04)

    def test__calculate_rental_management_renewal_fee(self):
        real_estate_calc = RealEstateCalc()
        real_estate_calc.rental_management_renewal_fee = None
        real_estate_calc._calculate_rental_management_renewal_fee()
        self.assertEquals(real_estate_calc.rental_management_renewal_fee, (1 / 24 + 0.5 / 24) / 2)

        real_estate_calc.rental_management_renewal_fee = 0.06
        real_estate_calc._calculate_rental_management_renewal_fee()
        self.assertEquals(real_estate_calc.rental_management_renewal_fee, 0.06)

    def test__calculate_purchase_price_financed(self):
        real_estate_calc = RealEstateCalc()

        real_estate_calc._calculate_purchase_price_financed()
        self.assertEquals(real_estate_calc.purchase_price_financed, 0)

        real_estate_calc.purchase_price = 10000000
        real_estate_calc._calculate_purchase_price_financed()
        self.assertEquals(real_estate_calc.purchase_price_financed, 0)

        real_estate_calc.mortgage_loan_to_value = 1
        real_estate_calc.bank_valuation_to_actual = 0.5
        real_estate_calc._calculate_purchase_price_financed()
        self.assertEquals(real_estate_calc.purchase_price_financed, 5000000)

        real_estate_calc.mortgage_loan_to_value = 0.25
        real_estate_calc.bank_valuation_to_actual = 0.5
        real_estate_calc._calculate_purchase_price_financed()
        self.assertEquals(real_estate_calc.purchase_price_financed, 1250000)

    def test__calculate_mortgage(self):
        real_estate_calc = RealEstateCalc()

        real_estate_calc._calculate_mortgage()
        self.assertEquals(real_estate_calc.mortgage, None)

        real_estate_calc.mortgage_rate = 0.01
        real_estate_calc.mortgage_tenor = 30
        real_estate_calc.purchase_price_financed = 10000000
        real_estate_calc._calculate_mortgage()
        self.assertEquals(real_estate_calc.mortgage.rate, 0.01)
        self.assertEquals(real_estate_calc.mortgage.tenor, 30)
        self.assertEquals(real_estate_calc.mortgage.principal, 10000000)

    def test__calculate_purchase_price_building(self):
        real_estate_calc = RealEstateCalc()

        real_estate_calc.building_to_land_ratio = 0.5
        real_estate_calc.purchase_price = 100000000
        real_estate_calc.age = 1
        real_estate_calc._calculate_purchase_price_building()
        self.assertEquals(real_estate_calc.purchase_price_building, 50000000)

        real_estate_calc.building_to_land_ratio = 0.5
        real_estate_calc.purchase_price = 100000000
        real_estate_calc.age = 0
        real_estate_calc._calculate_purchase_price_building()
        self.assertEquals(real_estate_calc.purchase_price_building, 50000000 * (1 + taxconstants.CONSUMPTION_TAX))

    def test__calculate_purchase_price_land(self):
        real_estate_calc = RealEstateCalc()

        real_estate_calc.purchase_price = 100000000
        real_estate_calc.purchase_price_building = 60000000
        real_estate_calc._calculate_purchase_price_land()
        self.assertEquals(real_estate_calc.purchase_price_land, 40000000)

    def test__calculate_purchase_agent_fee(self):
        real_estate_calc = RealEstateCalc()

        real_estate_calc.purchase_price = 100000000
        real_estate_calc.agent_fee_fixed = 50000
        real_estate_calc.agent_fee_variable = 0.03
        expected = (100000000 * 0.03 + 50000) * (1 + taxconstants.CONSUMPTION_TAX)

        real_estate_calc._calculate_purchase_agent_fee()
        self.assertEquals(real_estate_calc.purchase_agent_fee, expected)

    def test__calculate_purchase_other_transaction_fees(self):
        real_estate_calc = RealEstateCalc()

        real_estate_calc.purchase_price = 100000000
        real_estate_calc.other_transaction_fees = 0.02
        real_estate_calc._calculate_purchase_other_transaction_fees()
        self.assertEquals(real_estate_calc.purchase_other_transaction_fees, 100000000 * 0.02)

    def test__calculate_purchase_price_and_fees(self):
        real_estate_calc = RealEstateCalc()

        real_estate_calc.purchase_price = 100000000
        real_estate_calc.purchase_agent_fee = 3000000
        real_estate_calc.purchase_other_transaction_fees = 1000000
        real_estate_calc.mortgage_initiation_fees = 20000
        expected = 100000000 + 3000000 + 1000000 + 20000
        real_estate_calc._calculate_purchase_price_and_fees()
        self.assertEquals(real_estate_calc.purchase_price_and_fees, expected)

    def test__calculate_purchase_initial_outlay(self):
        real_estate_calc = RealEstateCalc()

        real_estate_calc.purchase_price_and_fees = 80000000
        real_estate_calc.purchase_price_financed = 70000000
        real_estate_calc._calculate_purchase_initial_outlay()
        self.assertEquals(real_estate_calc.purchase_initial_outlay, 10000000)

    def test__calculate_depreciation_years(self):
        real_estate_calc = RealEstateCalc()

        # Brand new reinforced concrete
        real_estate_calc.useful_life = 47
        real_estate_calc.age = 0
        real_estate_calc._calculate_depreciation_years()
        self.assertEquals(real_estate_calc.depreciation_years, 47)

        # 10 year old reinforced concrete
        real_estate_calc.useful_life = 47
        real_estate_calc.age = 10
        real_estate_calc._calculate_depreciation_years()
        self.assertEquals(real_estate_calc.depreciation_years, 39)

        # 40 year old wooden house
        real_estate_calc.useful_life = 20
        real_estate_calc.age = 40
        real_estate_calc._calculate_depreciation_years()
        self.assertEquals(real_estate_calc.depreciation_years, 4)

    def test__calculate_depreciation_percentage(self):
        real_estate_calc = RealEstateCalc()

        real_estate_calc.depreciation_years = 0
        real_estate_calc._calculate_depreciation_percentage()
        self.assertEquals(real_estate_calc.depreciation_percentage, 0)

        real_estate_calc.depreciation_years = 47
        real_estate_calc._calculate_depreciation_percentage()
        self.assertEquals(real_estate_calc.depreciation_percentage, 1 / 47)

    def test__calculate_depreciation_annual(self):
        real_estate_calc = RealEstateCalc()

        real_estate_calc.purchase_price_building = 10000000
        real_estate_calc.depreciation_percentage = 0.2
        real_estate_calc._calculate_depreciation_annual()
        self.assertEquals(real_estate_calc.depreciation_annual, 2000000)

    def test__calculate_rental_income(self):
        real_estate_calc = RealEstateCalc()

        real_estate_calc.purchase_price = 10000000
        real_estate_calc.gross_rental_yield = 0.05
        real_estate_calc._calculate_rental_income()
        self.assertEquals(real_estate_calc.rental_income, 500000)

    def test__calculate_renewal_income(self):
        real_estate_calc = RealEstateCalc()

        real_estate_calc.renewal_income_rate = 1 / 24
        real_estate_calc.rental_income = 500000
        real_estate_calc._calculate_renewal_income()
        self.assertEquals(real_estate_calc.renewal_income, 20833)

    def test__calculate_total_income(self):
        real_estate_calc = RealEstateCalc()

        real_estate_calc.rental_income = 500000
        real_estate_calc.renewal_income = 20833
        real_estate_calc._calculate_total_income()
        self.assertEquals(real_estate_calc.total_income, 520833)

    def test__calculate_maintenance_expense(self):
        real_estate_calc = RealEstateCalc()

        real_estate_calc.maintenance_per_m2 = 1000
        real_estate_calc.size = 50
        real_estate_calc._calculate_maintenance_expense()
        self.assertEquals(real_estate_calc.maintenance_expense, 50000)

    def test__calculate_monthly_fees_annualized(self):
        real_estate_calc = RealEstateCalc()

        real_estate_calc.monthly_fees = 20000
        real_estate_calc._calculate_monthly_fees_annualized()
        self.assertEquals(real_estate_calc.monthly_fees_annualized, 240000)

    def test__calculate_rental_management_renewal_expense(self):
        real_estate_calc = RealEstateCalc()

        real_estate_calc.rental_income = 500000
        real_estate_calc.rental_management_renewal_fee = 0.05
        real_estate_calc._calculate_rental_management_renewal_expense()
        expected = 500000 * 0.05 * (1 + taxconstants.CONSUMPTION_TAX)
        self.assertEquals(real_estate_calc.rental_management_renewal_expense, expected)

    def test__calculate_rental_management_rental_expense(self):
        real_estate_calc = RealEstateCalc()

        real_estate_calc.rental_income = 500000
        real_estate_calc.rental_management_rental_fee = 0.05
        real_estate_calc._calculate_rental_management_rental_expense()
        expected = 500000 * 0.05 * (1 + taxconstants.CONSUMPTION_TAX)
        self.assertEquals(real_estate_calc.rental_management_rental_expense, expected)

    def test__calculate_rental_management_total_expense(self):
        real_estate_calc = RealEstateCalc()

        real_estate_calc.rental_management_renewal_expense = 100000
        real_estate_calc.rental_management_rental_expense = 1000000
        real_estate_calc._calculate_rental_management_total_expense()
        self.assertEquals(real_estate_calc.rental_management_total_expense, 1100000)

    def test__calculate_property_tax_expense(self):
        real_estate_calc = RealEstateCalc()

        real_estate_calc.purchase_price = 70000000
        real_estate_calc.property_tax_rate = 0.01
        real_estate_calc._calculate_property_tax_expense()
        self.assertEquals(real_estate_calc.property_tax_expense, 700000)

    def test__calculate_total_expense(self):
        real_estate_calc = RealEstateCalc()

        real_estate_calc.maintenance_expense = 100000
        real_estate_calc.monthly_fees_annualized = 200000
        real_estate_calc.rental_management_total_expense = 300000
        real_estate_calc.property_tax_expense = 400000
        real_estate_calc._calculate_total_expense()
        self.assertEquals(real_estate_calc.total_expense, 1000000)

        # Active mortgage
        real_estate_calc.mortgage = Mortgage()  # Create a dummy mortgage and override values
        real_estate_calc.mortgage.monthly_payment = 100000
        real_estate_calc.mortgage.tenor = 10
        real_estate_calc.calc_year = 9
        real_estate_calc._calculate_total_expense()
        self.assertEquals(real_estate_calc.total_expense, 2200000)

        # Mortgage already paid off
        real_estate_calc.calc_year = 10
        real_estate_calc._calculate_total_expense()
        self.assertEquals(real_estate_calc.total_expense, 1000000)

    def test__calculate_calc_date(self):
        real_estate_calc = RealEstateCalc()

        real_estate_calc.purchase_date = dt.date(year=2017, month=1, day=1)
        real_estate_calc.calc_year = 2
        real_estate_calc._calculate_calc_date()
        expected = dt.date(year=2019, month=1, day=1)
        self.assertEquals(real_estate_calc.calc_date, expected)

    def test__calculate_net_income_before_taxes(self):
        real_estate_calc = RealEstateCalc()

        real_estate_calc.total_income = 5000000
        real_estate_calc.total_expense = 3000000
        real_estate_calc._calculate_net_income_before_taxes()
        self.assertEquals(real_estate_calc.net_income_before_taxes, 2000000)

    def test_depreciation_for_year(self):
        real_estate_calc = RealEstateCalc()

        real_estate_calc.depreciation_years = 10
        real_estate_calc.depreciation_annual = 1000000
        self.assertEquals(real_estate_calc.depreciation_for_year(9), 1000000)
        self.assertEquals(real_estate_calc.depreciation_for_year(10), 0)

    def test__calculate_depreciation(self):
        real_estate_calc = RealEstateCalc()

        real_estate_calc.depreciation_years = 10
        real_estate_calc.depreciation_annual = 1000000
        real_estate_calc.calc_year = 9
        real_estate_calc._calculate_depreciation()
        self.assertEquals(real_estate_calc.depreciation, 1000000)

        real_estate_calc.calc_year = 10
        real_estate_calc._calculate_depreciation()
        self.assertEquals(real_estate_calc.depreciation, 0)

    def test__calculate_net_income_taxable(self):
        real_estate_calc = RealEstateCalc()

        # Not primary residence, no mortgage
        real_estate_calc.is_primary_residence = False
        real_estate_calc.total_income = 1500000
        real_estate_calc.total_expense = 300000
        real_estate_calc.depreciation = 200000
        real_estate_calc.mortgage = None
        real_estate_calc._calculate_net_income_taxable()
        self.assertEquals(real_estate_calc.net_income_taxable, 1000000)

        # Mortgage but already matured
        real_estate_calc.mortgage = Mortgage(
            principal=20e6,
            tenor=10,
            rate=0.01,
        )

        real_estate_calc.calc_year = 10
        real_estate_calc._calculate_net_income_taxable()
        self.assertEquals(real_estate_calc.net_income_taxable, 1000000)

        # Mortgage and still active
        real_estate_calc.calc_year = 9
        real_estate_calc._calculate_net_income_taxable()
        self.assertEquals(real_estate_calc.net_income_taxable, 1000000 - 11344)

        # Primary residence
        real_estate_calc.is_primary_residence = True
        real_estate_calc._calculate_net_income_taxable()
        self.assertEquals(real_estate_calc.net_income_taxable, 0)

    def test__calculate_home_loan_deduction(self):
        real_estate_calc = RealEstateCalc()

        real_estate_calc.mortgage = Mortgage(
            principal=60e6,
            tenor=30,
            rate=0.01,
        )

        # Brand new and qualifying
        real_estate_calc.is_primary_residence = True
        real_estate_calc.size = 60
        real_estate_calc.calc_year = 9
        real_estate_calc.income_tax_calculator = IncomeTaxCalc()
        real_estate_calc.income_tax_calculator.taxable_income = 20000000
        real_estate_calc.age = 0
        real_estate_calc._calculate_home_loan_deduction()
        self.assertEquals(real_estate_calc.home_loan_deduction, 400000)

        # Not brand new and qualifying
        real_estate_calc.age = 1
        real_estate_calc._calculate_home_loan_deduction()
        self.assertEquals(real_estate_calc.home_loan_deduction, 200000)

        # Qualifying but mortgage loan was small
        real_estate_calc.mortgage = Mortgage(
            principal=1e6,
            tenor=11,
            rate=0.01,
        )

        real_estate_calc._calculate_home_loan_deduction()
        self.assertEquals(real_estate_calc.home_loan_deduction, 192077)

        # Test some disqualifications
        real_estate_calc.is_primary_residence = False
        real_estate_calc._calculate_home_loan_deduction()
        self.assertEquals(real_estate_calc.home_loan_deduction, 0)
        real_estate_calc.is_primary_residence = True
        real_estate_calc._calculate_home_loan_deduction()
        self.assertNotEquals(real_estate_calc.home_loan_deduction, 0)

        real_estate_calc.size = 50
        real_estate_calc._calculate_home_loan_deduction()
        self.assertEquals(real_estate_calc.home_loan_deduction, 0)
        real_estate_calc.size = 60
        real_estate_calc._calculate_home_loan_deduction()
        self.assertNotEquals(real_estate_calc.home_loan_deduction, 0)

        real_estate_calc.calc_year = 10  # Still less than mortgage tenor but can't deduct for more than 10 years
        real_estate_calc._calculate_home_loan_deduction()
        self.assertEquals(real_estate_calc.home_loan_deduction, 0)
        real_estate_calc.calc_year = 9
        real_estate_calc._calculate_home_loan_deduction()
        self.assertNotEquals(real_estate_calc.home_loan_deduction, 0)

        real_estate_calc.income_tax_calculator.taxable_income = 30000000
        real_estate_calc._calculate_home_loan_deduction()
        self.assertEquals(real_estate_calc.home_loan_deduction, 0)
        real_estate_calc.income_tax_calculator.taxable_income = 20000000
        real_estate_calc._calculate_home_loan_deduction()
        self.assertNotEquals(real_estate_calc.home_loan_deduction, 0)

        itc = real_estate_calc.income_tax_calculator
        real_estate_calc.income_tax_calculator = None
        real_estate_calc._calculate_home_loan_deduction()
        self.assertEquals(real_estate_calc.home_loan_deduction, 0)
        real_estate_calc.income_tax_calculator = itc
        real_estate_calc._calculate_home_loan_deduction()
        self.assertNotEquals(real_estate_calc.home_loan_deduction, 0)

        mortgage = real_estate_calc.mortgage
        real_estate_calc.mortgage = None
        real_estate_calc._calculate_home_loan_deduction()
        self.assertEquals(real_estate_calc.home_loan_deduction, 0)
        real_estate_calc.mortgage = mortgage
        real_estate_calc._calculate_home_loan_deduction()
        self.assertNotEquals(real_estate_calc.home_loan_deduction, 0)

    def test__calculate_income_tax(self):
        real_estate_calc = RealEstateCalc()

        real_estate_calc._calculate_income_tax()
        self.assertEquals(real_estate_calc.income_tax, 0)

        real_estate_calc.calc_date = dt.date(year=2017, month=1, day=1)
        real_estate_calc.net_income_taxable = 1000000

        # Set up tax calculator
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
            current_date=dt.date(year=2016, month=1, day=1)
        )

        income_tax_calc_before = copy.deepcopy(income_tax_calc)

        real_estate_calc.income_tax_calculator = income_tax_calc
        real_estate_calc._calculate_income_tax()
        self.assertEquals(real_estate_calc.income_tax, 4803596.6)

        # Confirm tax calc is unmodified
        self.assertEquals(income_tax_calc_before.__dict__, real_estate_calc.income_tax_calculator.__dict__)

        # Confirm deduction is used
        real_estate_calc.home_loan_deduction = 300000
        real_estate_calc._calculate_income_tax()
        self.assertEquals(real_estate_calc.income_tax, 4503596.6)

    def test__calculate_income_tax_real_estate(self):
        real_estate_calc = RealEstateCalc()

        real_estate_calc._calculate_income_tax_real_estate()
        self.assertEquals(real_estate_calc.income_tax_real_estate, 0)

        real_estate_calc.income_tax_calculator = IncomeTaxCalc()
        real_estate_calc.income_tax = 11000000
        real_estate_calc.income_tax_calculator.total_income_tax = 10000000
        real_estate_calc._calculate_income_tax_real_estate()
        self.assertEquals(real_estate_calc.income_tax_real_estate, 1000000)

    def test__calculate_net_income_after_taxes(self):
        real_estate_calc = RealEstateCalc()

        real_estate_calc.net_income_before_taxes = 1000000
        real_estate_calc.income_tax_real_estate = 200000
        real_estate_calc._calculate_net_income_after_taxes()
        self.assertEquals(real_estate_calc.net_income_after_taxes, 800000)

    def test__calculate_cumulative_net_income(self):

        # A bit tricky to test
        real_estate_calc = RealEstateCalc(
            purchase_price=10000000,
            gross_rental_yield=0.05,
            calc_year=0,
            mortgage_loan_to_value=1,
            mortgage_rate=0.01,
            mortgage_tenor=1,
            renewal_income_rate=0,
            rental_management_renewal_fee=0,
            rental_management_rental_fee=0,
        )

        # Mortgage of one year, so year_0_income will be the rental income of 500k - mortgage payment of ~10+m
        year_0_income = real_estate_calc.net_income_after_taxes
        mortgage_payment = int(real_estate_calc.mortgage.monthly_payment * 12)
        self.assertEquals(year_0_income, 500000 - mortgage_payment)

        # Cumulative income will just be first year
        self.assertEquals(real_estate_calc.cumulative_net_income, year_0_income)

        # On second year, cumulative income will be 500k rent + year 0
        real_estate_calc.calc_year = 1
        real_estate_calc.calculate_all_fields()
        year_1_income = real_estate_calc.net_income_after_taxes
        self.assertEquals(year_1_income, 500000)
        self.assertEquals(real_estate_calc.cumulative_net_income, year_0_income + year_1_income)

        # And just to prove its this function doing the job
        real_estate_calc.calc_year = 3
        real_estate_calc._calculate_cumulative_net_income()
        self.assertEquals(real_estate_calc.cumulative_net_income, year_0_income + year_1_income * 3)

    def test__calculate_sale_agent_fee(self):
        real_estate_calc = RealEstateCalc()

        real_estate_calc.sale_price = 100000000
        real_estate_calc.agent_fee_variable = 0.03
        real_estate_calc.agent_fee_fixed = 50000
        real_estate_calc._calculate_sale_agent_fee()
        expected = (100000000 * 0.03 + 50000) * (1 + taxconstants.CONSUMPTION_TAX)
        self.assertEquals(real_estate_calc.sale_agent_fee, expected)

    def test__calculate_sale_other_transaction_fees(self):
        real_estate_calc = RealEstateCalc()

        real_estate_calc.sale_price = 100000000
        real_estate_calc.other_transaction_fees = 0.01
        real_estate_calc._calculate_sale_other_transaction_fees()
        self.assertEquals(real_estate_calc.sale_other_transaction_fees, 1000000)

    def test__calculate_depreciation_cumulative(self):
        real_estate_calc = RealEstateCalc()

        real_estate_calc.depreciation_annual = 1000000
        real_estate_calc.depreciation_years = 10

        # First year
        real_estate_calc.calc_year = 0
        real_estate_calc._calculate_depreciation_cumulative()
        self.assertEquals(real_estate_calc.depreciation_cumulative, 1000000)

        # Halfway through the depreciable years
        real_estate_calc.calc_year = 4
        real_estate_calc._calculate_depreciation_cumulative()
        self.assertEquals(real_estate_calc.depreciation_cumulative, 5000000)

        # Last depreciable year
        real_estate_calc.calc_year = 9
        real_estate_calc._calculate_depreciation_cumulative()
        self.assertEquals(real_estate_calc.depreciation_cumulative, 10000000)

        # Year after, cumulative depreciation is same as last year
        real_estate_calc.calc_year = 10
        real_estate_calc._calculate_depreciation_cumulative()
        self.assertEquals(real_estate_calc.depreciation_cumulative, 10000000)

    def test__calculate_depreciated_building_value(self):
        real_estate_calc = RealEstateCalc()

        real_estate_calc.purchase_price_building = 30000000
        real_estate_calc.depreciation_cumulative = 20000000
        real_estate_calc._calculate_depreciated_building_value()
        self.assertEquals(real_estate_calc.depreciated_building_value, 10000000)

    def test__calculate_book_value(self):
        real_estate_calc = RealEstateCalc()

        real_estate_calc.purchase_price_land = 20000000
        real_estate_calc.depreciated_building_value = 10000000
        real_estate_calc._calculate_book_value()
        self.assertEquals(real_estate_calc.book_value, 30000000)

    def test__calculate_sale_price(self):
        real_estate_calc = RealEstateCalc()

        real_estate_calc.sale_price = 50000000
        real_estate_calc.book_value = 45000000
        real_estate_calc._calculate_sale_price()
        self.assertEquals(real_estate_calc.sale_price, 50000000)

        real_estate_calc.sale_price = None
        real_estate_calc._calculate_sale_price()
        self.assertEquals(real_estate_calc.sale_price, 45000000)

    def test__calculate_sale_proceeds_after_fees(self):
        real_estate_calc = RealEstateCalc()

        real_estate_calc.sale_price = 30000000
        real_estate_calc.sale_agent_fee = 1000000
        real_estate_calc.sale_other_transaction_fees = 300000
        real_estate_calc._calculate_sale_proceeds_after_fees()
        self.assertEquals(real_estate_calc.sale_proceeds_after_fees, 28700000)

    def test__calculate_acquisition_cost(self):
        real_estate_calc = RealEstateCalc()

        real_estate_calc.purchase_price = 100000000
        real_estate_calc.purchase_agent_fee = 3000000
        real_estate_calc.purchase_other_transaction_fees = 1000000
        real_estate_calc._calculate_acquisition_cost()
        self.assertEquals(real_estate_calc.acquisition_cost, 104000000)

    def test__calculate_capital_gains_tax_primary_residence_deduction(self):
        real_estate_calc = RealEstateCalc()

        real_estate_calc.is_primary_residence = 0
        real_estate_calc._calculate_capital_gains_tax_primary_residence_deduction()
        self.assertEquals(real_estate_calc.capital_gains_tax_primary_residence_deduction, 0)

        real_estate_calc.is_primary_residence = 1
        real_estate_calc._calculate_capital_gains_tax_primary_residence_deduction()
        self.assertEquals(real_estate_calc.capital_gains_tax_primary_residence_deduction, 30000000)

        real_estate_calc.is_primary_residence = 2
        real_estate_calc._calculate_capital_gains_tax_primary_residence_deduction()
        self.assertEquals(real_estate_calc.capital_gains_tax_primary_residence_deduction, 60000000)

        real_estate_calc.is_primary_residence = 3
        self.assertRaises(ValueError, real_estate_calc._calculate_capital_gains_tax_primary_residence_deduction)

    def test__calculate_capital_gains(self):
        real_estate_calc = RealEstateCalc()

        real_estate_calc.sale_proceeds_after_fees = 28000000
        real_estate_calc.acquisition_cost = 30000000
        real_estate_calc.depreciation_cumulative = 3000000

        real_estate_calc._calculate_capital_gains()
        self.assertEquals(real_estate_calc.capital_gains, 1000000)

        real_estate_calc.sale_proceeds_after_fees = 27000001
        real_estate_calc._calculate_capital_gains()
        self.assertEquals(real_estate_calc.capital_gains, 1)

        real_estate_calc.sale_proceeds_after_fees = 26000000
        real_estate_calc._calculate_capital_gains()
        self.assertEquals(real_estate_calc.capital_gains, 0)

    def test__calculate_capital_gains_tax_rate(self):
        real_estate_calc = RealEstateCalc()

        date_without_restoration = taxconstants.RESTORATION_TAX_EXPIRY
        date_with_restoration = date_without_restoration - dt.timedelta(days=1)

        date_to_multiple = [
            (date_with_restoration, 1 + taxconstants.RESTORATION_TAX),
            (date_without_restoration, 1)
        ]

        for date, multiple in date_to_multiple:
            real_estate_calc.calc_date = date

            # Short term gain
            real_estate_calc.calc_year = 4

            # For non-resident
            real_estate_calc.is_resident_for_tax_purposes = False
            real_estate_calc._calculate_capital_gains_tax_rate()
            self.assertEquals(real_estate_calc.capital_gains_tax_rate, 0.3 * multiple)

            # For resident
            real_estate_calc.is_resident_for_tax_purposes = True
            real_estate_calc._calculate_capital_gains_tax_rate()
            self.assertEquals(real_estate_calc.capital_gains_tax_rate, (0.3 + 0.09) * multiple)

            # Long term gain
            real_estate_calc.calc_year = 5

            # For non-resident
            real_estate_calc.is_resident_for_tax_purposes = False
            real_estate_calc._calculate_capital_gains_tax_rate()
            self.assertEquals(real_estate_calc.capital_gains_tax_rate, 0.15 * multiple)

            # For resident
            real_estate_calc.is_resident_for_tax_purposes = True
            real_estate_calc._calculate_capital_gains_tax_rate()
            self.assertEquals(real_estate_calc.capital_gains_tax_rate, (0.15 + 0.05) * multiple)

    def test__calculate_capital_gains_tax(self):
        real_estate_calc = RealEstateCalc()

        real_estate_calc.capital_gains = 5000000
        real_estate_calc.capital_gains_tax_rate = 0.2
        real_estate_calc._calculate_capital_gains_tax()
        self.assertEquals(real_estate_calc.capital_gains_tax, 1000000)

        real_estate_calc.capital_gains_tax_primary_residence_deduction = 600000
        real_estate_calc._calculate_capital_gains_tax()
        self.assertEquals(real_estate_calc.capital_gains_tax, 400000)

        real_estate_calc.capital_gains_tax_primary_residence_deduction = 30000000
        real_estate_calc._calculate_capital_gains_tax()
        self.assertEquals(real_estate_calc.capital_gains_tax, 0)

    def test__calculate_sale_proceeds_net(self):
        real_estate_calc = RealEstateCalc()

        real_estate_calc.sale_proceeds_after_fees = 50000000
        real_estate_calc.capital_gains_tax = 1000000
        real_estate_calc._calculate_sale_proceeds_net()
        self.assertEquals(real_estate_calc.sale_proceeds_net, 49000000)

    def test__calculate_net_income_on_realestate(self):
        real_estate_calc = RealEstateCalc()

        real_estate_calc.sale_proceeds_net = 49000000
        real_estate_calc.cumulative_net_income = 2000000
        real_estate_calc.purchase_price_and_fees = 45000000
        real_estate_calc._calculate_net_income_on_realestate()
        self.assertEquals(real_estate_calc.net_income_on_realestate, 6000000)

    def test__calculate_all_fields(self):
        """
        A regression test to confirm that all required functions are called as part of calculate_all_fields.

        This is a pretty ugly test, lazily written by setting up a sample calculator and debugging it manually to ensure
        all functions are called and then hard-coding the expected values (such that if the functions are no longer
        called the test will fail).
        """
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
            current_date=dt.date(year=2016, month=1, day=1)
        )

        real_estate_calc = RealEstateCalc(
            purchase_date=dt.date(2017, 1, 24),
            purchase_price=100000000,
            building_to_land_ratio=0.7,
            size=100,
            age=0,
            mortgage_loan_to_value=0.9,
            bank_valuation_to_actual=1,
            mortgage_tenor=30,
            mortgage_rate=0.01,
            mortgage_initiation_fees=10000,
            agent_fee_variable=0.03,
            agent_fee_fixed=20000,
            other_transaction_fees=0.01,

            # Parameters associated with ongoing concern
            monthly_fees=20000,
            property_tax_rate=0.01,
            maintenance_per_m2=1000,
            useful_life=47,
            calc_year=32,
            income_tax_calculator=income_tax_calc,

            # Parameters associated with renting out the real estate
            gross_rental_yield=0.04,
            renewal_income_rate=None,
            rental_management_rental_fee=None,
            rental_management_renewal_fee=None,

            # Parameters associated with final disposal
            is_primary_residence=0,
            is_resident_for_tax_purposes=True,
            sale_price=47000000,
        )

        expected = {
            'acquisition_cost': 104261600,
            'age': 0,
            'agent_fee_fixed': 20000,
            'agent_fee_variable': 0.03,
            'bank_valuation_to_actual': 1,
            'book_value': 46919170.0,
            'building_to_land_ratio': 0.7,
            'calc_date': dt.date(2049, 1, 24),
            'calc_year': 32,
            'capital_gains': 0,
            'capital_gains_tax': 0,
            'capital_gains_tax_primary_residence_deduction': 0,
            'capital_gains_tax_rate': 0.2,
            'cumulative_net_income': -23442448.8,
            'depreciated_building_value': 22519170.0,
            'depreciation': 1608510,
            'depreciation_annual': 1608510,
            'depreciation_cumulative': 53080830,
            'depreciation_percentage': 0.02127659574468085,
            'depreciation_years': 47,
            'gross_rental_yield': 0.04,
            'home_loan_deduction': 0,
            'income_tax': 4676082.2,
            'income_tax_calculator': income_tax_calc,
            'income_tax_real_estate': 309415.60000000056,
            'is_primary_residence': 0,
            'is_resident_for_tax_purposes': True,
            'maintenance_expense': 100000,
            'maintenance_per_m2': 1000,
            'monthly_fees': 20000,
            'monthly_fees_annualized': 240000,
            'mortgage': real_estate_calc.mortgage,
            'mortgage_initiation_fees': 10000,
            'mortgage_loan_to_value': 0.9,
            'mortgage_rate': 0.01,
            'mortgage_tenor': 30,
            'net_income_after_taxes': 2166250.3999999994,
            'net_income_before_taxes': 2475666,
            'net_income_on_realestate': -82728448.80000001,
            'net_income_taxable': 867156,
            'other_transaction_fees': 0.01,
            'property_tax_expense': 1000000,
            'property_tax_rate': 0.01,
            'purchase_agent_fee': 3261600,
            'purchase_date': dt.date(2017, 1, 24),
            'purchase_initial_outlay': 14271600,
            'purchase_other_transaction_fees': 1000000,
            'purchase_price': 100000000,
            'purchase_price_and_fees': 104271600,
            'purchase_price_building': 75600000.0,
            'purchase_price_financed': 90000000,
            'purchase_price_land': 24400000.0,
            'renewal_income': 166666,
            'renewal_income_rate': 0.041666666666666664,
            'renovation_cost': 0,
            'rental_income': 4000000,
            'rental_management_renewal_expense': 135000,
            'rental_management_renewal_fee': 0.03125,
            'rental_management_rental_expense': 216000,
            'rental_management_rental_fee': 0.05,
            'rental_management_total_expense': 351000,
            'sale_agent_fee': 1544400,
            'sale_other_transaction_fees': 470000,
            'sale_price': 47000000,
            'sale_proceeds_after_fees': 44985600,
            'sale_proceeds_net': 44985600,
            'size': 100,
            'total_expense': 1691000,
            'total_income': 4166666,
            'useful_life': 47,
        }

        expected_keys = list(expected.keys())

        actual = real_estate_calc.__dict__
        actual_keys = list(actual.keys())

        actual_keys.sort()
        expected_keys.sort()

        # Confirm same keys
        self.assertEquals(actual_keys, expected_keys)

        # Confirm mortgage is not None (i.e. it was set up)
        self.assertIsNotNone(real_estate_calc.mortgage)

        # Confirm values match expected
        for key, value in actual.items():
            expected_value = expected[key]
            if isinstance(value, Number):
                value = round(value, 5)
                expected_value = round(expected_value, 5)

            if value != expected_value:
                print("{} with value {} does not match the expected value of {}".format(key, value, expected_value))
                self.assertEquals(value, expected[key])
