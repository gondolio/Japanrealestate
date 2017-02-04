from dateutil.relativedelta import relativedelta
from japanrealestate import taxconstants
from japanrealestate.mortgage import Mortgage
import copy
import datetime as dt


class RealEstateCalc:
    """
    Class to calculate economics of owning real estate in Japan as an individual (not a corporation)

        Excluded in this class:
            * Timings of cash flows (e.g. tax payments) and tax withholding are not considered.
            * Entrepreneurial Tax is not considered in this class. See for details:
              http://www.akasakarealestate.com/wiki/index.php/Taxes#Entrepreneurial_Tax
            * Corporate contracts, commercial real estate
            * Mid-year purchases and sales (there are rules about how various costs/taxes and how they are split, as
              well as depreciation complexities)
            * Corporate considerations (i.e. if you are a corporate rather than individual)
            * Exclusion of property tax for low value land and housing
            * Methods of calculating acquisition cost for capital gains (other than the actual acquisition cost) such
              as the approximate method etc (see http://investment-japan.jp/japantaxonproperty/2994.html for details)
            * Owning more than one non-investment property. In other words, this class assumes that if it is not
              your primary residence then it is an investment property (rather than a holiday home etc)
            * Tax for income made from primary residence (e.g. AirBnB).
            * Any tax laws that were only applicable prior to December 2016 (when this class was written)
            * Joint financing with another person (thus allowing you twice the home loan deduction), although joint
              ownership for capital gains tax reduction on primary residence is supported.
            * Any modeling of real estate yield changes over time (it assumes constant yield)

    Some useful links:
    http://www.akasakarealestate.com/wiki/index.php
    http://japantax.org/?p=3882
    http://japanpropertycentral.com/real-estate-faq/capital-gains-tax/
    http://investment-japan.jp/japantaxonproperty/2994.html
    http://www.asteriskrealty.jp/2009/07/27/average-maintenance-cost-of-residential-building-in-
    japanaverage-maintenance-cost-of-residential-building-in-japan/
    http://www.tax.metro.tokyo.jp/book/guidebookgaigo/guidebook2014e.pdf
    """

    def __init__(
            self,
            # Parameters associated with initial purchase
            purchase_date=None,
            purchase_price=0,
            building_to_land_ratio=0.7,
            size=0,
            age=0,
            mortgage_loan_to_value=0,
            bank_valuation_to_actual=1,
            mortgage_tenor=0,
            mortgage_rate=0,
            mortgage_initiation_fees=0,
            renovation_cost=0,

            # Parameters associated with initial purchase but also applied to final sale
            agent_fee_variable=0,
            agent_fee_fixed=0,
            other_transaction_fees=0,


            # Parameters associated with ongoing concern
            monthly_fees=0,
            property_tax_rate=0,
            maintenance_per_m2=1000,
            useful_life=47,
            calc_year=0,
            income_tax_calculator=None,

            # Parameters associated with renting out the real estate
            gross_rental_yield=0,
            renewal_income_rate=None,
            rental_management_rental_fee=None,
            rental_management_renewal_fee=None,

            # Parameters associated with final disposal
            is_primary_residence=0,
            is_resident_for_tax_purposes=False,
            sale_price=0,
    ):
        """
        Parameters associated with initial purchase:
        :param purchase_date: date when property was purchased. Defaults to date.today().
        :param purchase_price: Market value of property
        :param building_to_land_ratio: This breakdown is normally present in the real-estate contract or can be
               calculated from the "consumption tax" included in the price (as consumption tax doesn't apply on land).
               Default value is based on few examples found on the internet. Specify in decimal (i.e. 0.5 for 50%).
        :param size: Property size in square metres
        :param age: Property age in years.
               If zero, assumes property is new (i.e. not second hand).
        :param mortgage_loan_to_value: What % of the property value (as assessed by the bank) will be financed
               If zero, an all cash purchase is assumed. Specify in decimal (i.e. 0.8 for 80%).
        :param bank_valuation_to_actual: Bank assessed property value / actual market value. Specify in decimal.
        :param mortgage_tenor: Term of loan in years
        :param mortgage_rate: Annual interest rate. Specify in decimal (i.e. 0.01 for 1%).
        :param mortgage_initiation_fees: Sum of all fees paid for initiating mortgage
        :param agent_fee_variable: % of property market value paid to real estate agent. Specify in decimal.
        :param agent_fee_fixed: Other fees paid to agent on top of variable fees
        :param other_transaction_fees: Other fees paid to acquire/dispose real estate, in percentage of market value.
               Stamp duty, acquisition tax, judicial scrivener fee (incl. registration tax). Specify in decimal.

        Parameters associated with ongoing concern:
        :param monthly_fees: Monthly fees paid for management and sinking fund
        :param property_tax_rate: Annual taxes due on real estate, as % of purchase price. This is hard to estimate
               and should be obtained from agent. Specify in decimal (i.e. 0.01 for 1%).

               From http://www.akasakarealestate.com/wiki/index.php/Taxes#Possession_Tax:
               Normally about 0.3% to 0.5% of the market value each year, (peaks as high as 1.2%).

               This class could be expanded by taking in assessed value of property and calculating the tax but since
               the assessed value of property is obtained from a 3rd party (usually the agent?) that also would know
               the property_tax_rate, it is perhaps needlessly complicated. If we did want to do this, this link has
               the breakdown in the 'Holding' section: http://sumitomo-rd.com.sg/report03.php

        :param maintenance_per_m2: Amount paid annually per square metre.

               Default value of ¥1000 taken from:
               http://www.asteriskrealty.jp/2009/07/27/average-maintenance-cost-of-residential-building-in-
               japanaverage-maintenance-cost-of-residential-building-in-japan/

        :param useful_life: Number of years it takes for a property's building book value to legally depreciate to zero
               from time of construction.

               Default value of 47 is for reinforced concrete, which is the norm for new properties.

               For more details, see:
               http://www.akasakarealestate.com/wiki/index.php/Taxes#Depreciation_Deduction_for_Income_Tax.

        :param income_tax_calculator: Instance of IncomeTaxCalc() class, instantiated based on user's tax profile.
               income_tax_calculator should be instantiated *excluding* the real estate income calculated in this class,
               since this class is used to calculate that income.

        :param calc_year: The year used when calculating net income and capital gains.
               A value of 0 means the net income and capital gains will be calculated for the same year as
               the purchase. A value of 1 means the following year, etc.

               Properties are bought at beginning of year and sold at end of year.
               So for example, calc_year=1 will simulate buying property and getting two years of rental income and
               then selling it.

               As with other fields, calculate_all_fields() should be called after this is changed.

        Parameters associated with renting out the real estate
        :param gross_rental_yield: Rental yield as % of purchase price, before any fees.
               If non-zero, the real estate will not necessarily be treated as investment property since yield is still
               achievable for primary residence (e.g. AirBnB). Note that AirBnB income for primary residence will be
               excluded from tax in this class.

        :param renewal_income_rate: If renting out the real estate, the % of annual rent the tenant pays when renewing
               or initiating contract. This can include key money. Specify in decimal.

               If None, defaults by assuming lease renewed every 2 years and one month rent is paid.

        :param rental_management_rental_fee: If renting out the real estate, the % of annual rent that the agent
               receives. Specify in decimal. Do not include consumption tax, this is handled later.

               If None, uses some sensible default.

        :param rental_management_renewal_fee: If renting out the real estate, the % of annual rent that the agent
               receives whenever a new tenant is found. Specify in decimal. Do not include consumption tax.

               If None, defaults by assuming lease renewed every 2 years with 50% of the time being a new tenant.

        Parameters associated with final disposal
        :param is_primary_residence: 0 if not, 1 if yes, 2 if jointly owned with spouse.
               If zero, will be treated as investment property for tax purposes.
        :param is_resident_for_tax_purposes: True if you are a resident of Japan for tax purposes, false otherwise.
        :param sale_price: Price of property sold. If None, will be estimated using depreciation model.
        """
        # Initialize class fields from arguments
        self.purchase_date = purchase_date
        self.purchase_price = purchase_price
        self.building_to_land_ratio = building_to_land_ratio
        self.size = size
        self.age = age
        self.mortgage_loan_to_value = mortgage_loan_to_value
        self.bank_valuation_to_actual = bank_valuation_to_actual
        self.mortgage_tenor = mortgage_tenor
        self.mortgage_rate = mortgage_rate
        self.mortgage_initiation_fees = mortgage_initiation_fees
        self.renovation_cost = renovation_cost

        self.agent_fee_variable = agent_fee_variable
        self.agent_fee_fixed = agent_fee_fixed
        self.other_transaction_fees = other_transaction_fees

        self.monthly_fees = monthly_fees
        self.property_tax_rate = property_tax_rate
        self.maintenance_per_m2 = maintenance_per_m2
        self.useful_life = useful_life
        self.calc_year = calc_year
        self.income_tax_calculator = income_tax_calculator

        self.gross_rental_yield = gross_rental_yield
        self.renewal_income_rate = renewal_income_rate
        self.rental_management_rental_fee = rental_management_rental_fee
        self.rental_management_renewal_fee = rental_management_renewal_fee

        self.is_primary_residence = is_primary_residence
        self.is_resident_for_tax_purposes = is_resident_for_tax_purposes
        self.sale_price = sale_price

        # Derived fields that will be calculated

        # Acquisition derived fields
        self.purchase_price_financed = None  # Amount of purchase price loaned by bank
        self.mortgage = None  # Mortgage() object
        self.purchase_price_building = None  # Purchase price allocated to building
        self.purchase_price_land = None  # Purchase price allocated to land
        self.purchase_agent_fee = None  # Total amount paid to agent when buying
        self.purchase_other_transaction_fees = None  # Total non-agent amount paid when acquiring real estate
        self.purchase_price_and_fees = None  # Total expense for purchase including all fees, taxes etc
        self.purchase_initial_outlay = None  # Total amount paid upfront (i.e. not financed) for purchase incl. fees/tax

        # Ongoing derived fields
        self.depreciation_years = None  # Number of years that building value can be depreciated to zero
        self.depreciation_percentage = None  # Annual % (in decimal) of building value depreciated (straight line)
        self.depreciation_annual = None  # Annual depreciation amount for building value
        self.rental_income = None  # Annual income from tenant rental
        self.renewal_income = None  # Annual income from tenant renewing lease
        self.total_income = None  # Annual total income from tenant
        self.maintenance_expense = None  # Annual expense for maintenance
        self.monthly_fees_annualized = None  # Annual expense for monthly fees
        self.rental_management_renewal_expense = None  # Annual expense for rental management renewal component
        self.rental_management_rental_expense = None  # Annual expense for rental management rental component
        self.rental_management_total_expense = None  # Annual total expense for rental management
        self.property_tax_expense = None  # Annual expense for possession tax (logic to change yearly not implemented)
        """
        Below fields field vary by year (calc_year) because mortgage payments (and interest component), depreciation
        (and cumulative depreciation) vary by year.

        To see their value on any year, change calc_year and call calculate_all_fields.
        """
        self.calc_date = None  # Date corresponding to calc_year
        self.total_expense = None  # Annual total expenses. Excludes purchase_initial_outlay as it is not recurring.
        self.net_income_before_taxes = None  # Annual income after expenses/mortgage payment, see note above.
        self.depreciation = None  # Depreciation for calc_year
        self.net_income_taxable = None  # Annual income after expenses/depreciation/interest, see note above.
        self.home_loan_deduction = None  # Tax relief provided by loan financed primary residences provide
        self.income_tax = None  # Total annual tax on income (real estate + whatever income_tax_calculator includes)
        self.income_tax_real_estate = None  # Total annual tax on real estate income only
        self.net_income_after_taxes = None  # Annual income after expenses/depreciation/interest/tax, see note above.
        self.cumulative_net_income = None  # Sum of net_income_after_taxes from first year until calc_year

        # Disposal derived fields
        self.depreciation_cumulative = None  # Sum of depreciation since purchase until calc_year, see note above.
        self.sale_agent_fee = None  # Total amount paid to agent when selling
        self.sale_other_transaction_fees = None  # Total non-agent amount paid when selling real estate
        self.depreciated_building_value = None  # Book value of building when sold (based on depreciation)
        self.book_value = None  # Book value of entire property at calc_year. Used to estimate sale_price.
        self.sale_proceeds_after_fees = None  # Sale price after fees deducted
        self.acquisition_cost = None  # Part of base used for capital gains tax calculation when selling
        self.capital_gains_tax_primary_residence_deduction = None
        self.capital_gains = None  # Capital gains that will be taxed
        self.capital_gains_tax_rate = None  # CGT rate used to calculate CGT
        self.capital_gains_tax = None  # CGT
        self.sale_proceeds_net = None  # Sale proceeds after fees and taxes
        self.net_income_on_realestate = None  # Sale proceeds after fees/taxes + net rental income - purchase price

        # Calculate!
        self.calculate_all_fields()

    def calculate_all_fields(self):
        # Default inputs
        self._calculate_purchase_date()
        self._calculate_renewal_income_rate()
        self._calculate_rental_management_rental_fee()
        self._calculate_rental_management_renewal_fee()

        # Acquisition derived fields
        self._calculate_purchase_price_financed()
        self._calculate_mortgage()
        self._calculate_purchase_price_building()
        self._calculate_purchase_price_land()
        self._calculate_purchase_agent_fee()
        self._calculate_purchase_other_transaction_fees()
        self._calculate_purchase_price_and_fees()
        self._calculate_purchase_initial_outlay()

        # Ongoing derived fields
        self._calculate_depreciation_years()
        self._calculate_depreciation_percentage()
        self._calculate_depreciation_annual()
        self._calculate_rental_income()
        self._calculate_renewal_income()
        self._calculate_total_income()
        self._calculate_maintenance_expense()
        self._calculate_monthly_fees_annualized()
        self._calculate_rental_management_renewal_expense()
        self._calculate_rental_management_rental_expense()
        self._calculate_rental_management_total_expense()
        self._calculate_property_tax_expense()
        self._calculate_total_expense()
        self._calculate_depreciation()
        self._calculate_calc_date()
        self._calculate_net_income_before_taxes()
        self._calculate_net_income_taxable()
        self._calculate_home_loan_deduction()
        self._calculate_income_tax()
        self._calculate_income_tax_real_estate()
        self._calculate_net_income_after_taxes()
        self._calculate_cumulative_net_income()

        # Disposal derived fields
        self._calculate_depreciation_cumulative()
        self._calculate_sale_agent_fee()
        self._calculate_sale_other_transaction_fees()
        self._calculate_depreciated_building_value()
        self._calculate_book_value()
        self._calculate_sale_proceeds_after_fees()
        self._calculate_acquisition_cost()
        self._calculate_capital_gains_tax_primary_residence_deduction()
        self._calculate_capital_gains()
        self._calculate_capital_gains_tax_rate()
        self._calculate_capital_gains_tax()
        self._calculate_sale_proceeds_net()
        self._calculate_net_income_on_realestate()

    # Real estate specific constants
    _RENEWAL_INCOME_RATE_DEFAULT = 1 / 24  # Lease renewed every 2 years and one month rent is paid by tenant
    _RENTAL_MANAGEMENT_FEE_DEFAULT = 0.05  # 5% seems normal in Tokyo
    """
    Rental management renewal fee defaulting:
    If new tenant, agent takes one month.
    If existing tenant, agent takes half a month.
    Contract renews every two years, and assuming 50 % of time with a new tenant
    """
    _RENTAL_MANAGEMENT_RENEWAL_DEFAULT = (1 / 24 + 0.5 / 24) / 2
    _DEPRECIATION_AGE_FACTOR_IF_SECOND_HAND = 0.8

    # Real Estate Capital Gains Tax details from following sources:
    # http://japanpropertycentral.com/real-estate-faq/capital-gains-tax/
    # http://www.akasakarealestate.com/wiki/index.php/Taxes#Capital_Gains
    # http://investment-japan.jp/japantaxonproperty/2994.html
    _CAPITAL_GAINS_TAX_SHORT_NATIONAL = 0.30
    _CAPITAL_GAINS_TAX_SHORT_MUNICIPAL = 0.09
    _CAPITAL_GAINS_TAX_LONG_NATIONAL = 0.15
    _CAPITAL_GAINS_TAX_LONG_MUNICIPAL = 0.05
    _CAPITAL_GAINS_TAX_PRIMARY_RESIDENCE_DEDUCTION = 30000000

    def _calculate_purchase_date(self):
        if self.purchase_date is None:
            self.purchase_date = dt.date.today()

    def _calculate_renewal_income_rate(self):
        if self.renewal_income_rate is None:
            self.renewal_income_rate = self._RENEWAL_INCOME_RATE_DEFAULT

    def _calculate_rental_management_rental_fee(self):
        if self.rental_management_rental_fee is None:
            self.rental_management_rental_fee = self._RENTAL_MANAGEMENT_FEE_DEFAULT

    def _calculate_rental_management_renewal_fee(self):
        if self.rental_management_renewal_fee is None:
            self.rental_management_renewal_fee = self._RENTAL_MANAGEMENT_RENEWAL_DEFAULT

    def _calculate_purchase_price_financed(self):
        self.purchase_price_financed = int(
            self.purchase_price *
            self.bank_valuation_to_actual *
            self.mortgage_loan_to_value
        )

    def _calculate_mortgage(self):
        if self.purchase_price_financed > 0:
            self.mortgage = Mortgage(
                principal=self.purchase_price_financed,
                tenor=self.mortgage_tenor,
                rate=self.mortgage_rate
            )

    def _calculate_purchase_price_building(self):
        self.purchase_price_building = int(self.purchase_price * self.building_to_land_ratio)
        """
        New properties are bought from developers and therefore incur a consumption tax.
        From http://www.realestate-tokyo.com/news/consumption-tax-for-property/
        "Consumption tax is often not imposed when purchasing an existing property.
        Since consumption tax arises when a business operator offers services or goods,
        it does not apply to any business between individual persons,
        except for the cases when individual person conducts a real estate business"
        """
        if self.age == 0:
            self.purchase_price_building *= (1 + taxconstants.CONSUMPTION_TAX)

    def _calculate_purchase_price_land(self):
        self.purchase_price_land = self.purchase_price - self.purchase_price_building

    def _calculate_purchase_agent_fee(self):
        self.purchase_agent_fee = int(
            (self.purchase_price * self.agent_fee_variable + self.agent_fee_fixed) *
            (1 + taxconstants.CONSUMPTION_TAX)
        )

    def _calculate_purchase_other_transaction_fees(self):
        self.purchase_other_transaction_fees = int(self.purchase_price * self.other_transaction_fees)

    def _calculate_purchase_price_and_fees(self):
        self.purchase_price_and_fees = int(
            self.purchase_price +
            self.purchase_agent_fee +
            self.purchase_other_transaction_fees +
            self.mortgage_initiation_fees +
            self.renovation_cost
        )

    def _calculate_purchase_initial_outlay(self):
        """This field is not included in net income (since an aspect of financing rather than investment economics)"""
        self.purchase_initial_outlay = self.purchase_price_and_fees - self.purchase_price_financed

    def _calculate_depreciation_years(self):
        """
        From http://www.akasakarealestate.com/wiki/index.php/Taxes#Depreciation_Deduction_for_Income_Tax:
        * For second hand properties you can deduct 80 percent of the age
        * When calculating the amount of years the results are truncated down
        * It is not possible to depreciate a building more than its useful life
        """
        if self.age == 0:
            self.depreciation_years = self.useful_life
        else:
            age_for_depreciation = min(self.useful_life, self.age) * self._DEPRECIATION_AGE_FACTOR_IF_SECOND_HAND
            self.depreciation_years = int(self.useful_life - age_for_depreciation)

    def _calculate_depreciation_percentage(self):
        if self.depreciation_years == 0:
            self.depreciation_percentage = 0
        else:
            self.depreciation_percentage = 1 / self.depreciation_years

    def _calculate_depreciation_annual(self):
        self.depreciation_annual = int(self.purchase_price_building * self.depreciation_percentage)

    def _calculate_rental_income(self):
        self.rental_income = int(self.purchase_price * self.gross_rental_yield)

    def _calculate_renewal_income(self):
        self.renewal_income = int(self.renewal_income_rate * self.rental_income)

    def _calculate_total_income(self):
        self.total_income = int(self.rental_income + self.renewal_income)

    def _calculate_maintenance_expense(self):
        self.maintenance_expense = int(self.maintenance_per_m2 * self.size)

    def _calculate_monthly_fees_annualized(self):
        self.monthly_fees_annualized = self.monthly_fees * 12

    def _calculate_rental_management_renewal_expense(self):
        self.rental_management_renewal_expense = int(
            self.rental_income *
            self.rental_management_renewal_fee *
            (1 + taxconstants.CONSUMPTION_TAX)
        )

    def _calculate_rental_management_rental_expense(self):
        self.rental_management_rental_expense = int(
            self.rental_income *
            self.rental_management_rental_fee *
            (1 + taxconstants.CONSUMPTION_TAX)
        )

    def _calculate_rental_management_total_expense(self):
        self.rental_management_total_expense = int(
            self.rental_management_renewal_expense +
            self.rental_management_rental_expense
        )

    def _calculate_property_tax_expense(self):
        self.property_tax_expense = int(self.purchase_price * self.property_tax_rate)

    def _calculate_calc_date(self):
        self.calc_date = self.purchase_date + relativedelta(years=self.calc_year)

    def _calculate_total_expense(self):
        self.total_expense = int(
            self.maintenance_expense +
            self.monthly_fees_annualized +
            self.rental_management_total_expense +
            self.property_tax_expense
        )

        if self.mortgage is not None and self.calc_year < self.mortgage.tenor:
            self.total_expense += int(self.mortgage.monthly_payment * 12)  # Assume tenor is whole number of years

    def _calculate_net_income_before_taxes(self):
        """ The income at input year after expenses and mortgage payment. This is the actual cash flow income """
        self.net_income_before_taxes = self.total_income - self.total_expense

    def depreciation_for_year(self, year):
        """Returns the depreciation amount for input year"""
        if year < self.depreciation_years:
            return self.depreciation_annual
        else:
            return 0

    def _calculate_depreciation(self):
        """
        Depreciation amount for calc_year.
        Unlike the other _calculate_* methods, logic is delegated to a helper function since the logic is re-used for
        _calculate_depreciation_cumulative.
        """
        self.depreciation = self.depreciation_for_year(year=self.calc_year)

    def _calculate_net_income_taxable(self):
        """
        The income at calc_year after expenses, depreciation & interest payments (principal is not tax expense).
        This is the income used for calculating taxes. It is only non-zero for investment properties.
        It differs from actual cash flow income (net_income_before_taxes) in the following ways:
        * Depreciation is not an actual cash flow expense but is recognized as an expense for tax purposes for
          investment properties
        * Only the interest portion of a mortgage is considered an expense for tax purposes (and only for investment
          properties) whereas both the interest and principal portions of a mortgage are real cash flow expense.
        """
        if self.is_primary_residence:
            # Residence means you cannot claim income, or consider interest/depreciation as expense, for tax purposes
            self.net_income_taxable = 0
        else:
            self.net_income_taxable = self.total_income - self.total_expense - self.depreciation
            if self.mortgage is not None and self.calc_year < self.mortgage.tenor:
                month = self.calc_year * 12  # Assume tenor is whole number of years
                interest_payments = self.mortgage.interest_schedule[month:][:12]  # First 12 months starting at year
                interest_payment_for_year = int(sum(interest_payments))
                self.net_income_taxable -= interest_payment_for_year

    def _calculate_home_loan_deduction(self):
        """
        The home loan tax deduction (住宅ローン減税) allows you to deduct 1% of your remaining home loan from your
        income tax each year for 10 years as long as the apartment is bigger than 50m^2 and your taxable income is less
        than 30M a year.

        If brand new apartment (technically, if home purchase included consumption tax), then 400k a year for 10 years.
        If second hand, then 200k a year for 10 years. There are also other conditions for second hand apartments such
        as age or certification, which we ignore.

        Based on:
        http://japanpropertycentral.com/real-estate-faq/home-loan-tax-deduction/
        http://resources.realestate.co.jp/buy/calculate-mortgage-loan-deduction-japan/
        http://lawyerjapanese.com/how-to-conduct-housing-loan-deduction-jutaku-loan-kojo-in-japan/
        """
        self.home_loan_deduction = 0
        is_qualified_for_deduction = (self.is_primary_residence and
                                      self.calc_year < 10 and
                                      self.size > 50 and
                                      self.mortgage is not None and
                                      self.calc_year < self.mortgage.tenor and
                                      self.income_tax_calculator is not None and
                                      self.income_tax_calculator.taxable_income < 30000000)

        if is_qualified_for_deduction:
            if self.age == 0:
                self.home_loan_deduction = 400000
            else:
                self.home_loan_deduction = 200000

            month = self.calc_year * 12  # Assume tenor is whole number of years
            remaining_loan_balance = sum(self.mortgage.amortization_schedule[month:])
            self.home_loan_deduction = int(min(self.home_loan_deduction, remaining_loan_balance))

    def _calculate_income_tax(self):
        """
        The total amount of income tax owed, taking into account rental income at calc_year based on net_income_taxable.
        This is useful as an end-result by itself to understand how your total annual taxes change by owning real estate
        even if it is a primary residence and you have no taxable income on it (because of home loan deduction that
        offsets your other income).
        """
        self.income_tax = 0  # Set 0 tax if calculator is not provided
        if self.income_tax_calculator is not None:
            # Get tax before and after real estate income, as the difference is tax liability due to real estate

            # Use a copy of income tax calculator so we don't touch the original one
            copied_calc = copy.deepcopy(self.income_tax_calculator)

            # Override fields for calculation
            copied_calc.current_date = self.calc_date
            copied_calc.other_income += self.net_income_taxable
            copied_calc.tax_deduction += self.home_loan_deduction
            copied_calc.calculate_all_fields()

            # Calculate tax
            self.income_tax = copied_calc.total_income_tax

    def _calculate_income_tax_real_estate(self):
        """The amount of tax owed for rental income at calc_year based on net_income_taxable."""
        self.income_tax_real_estate = 0  # Set 0 tax if calculator is not provided
        if self.income_tax_calculator is not None:
            self.income_tax_real_estate = max(0, self.income_tax - self.income_tax_calculator.total_income_tax)

    def _calculate_net_income_after_taxes(self):
        """The income at calc_year after expenses, mortgage and taxes"""
        self.net_income_after_taxes = self.net_income_before_taxes - self.income_tax_real_estate

    def _calculate_cumulative_net_income(self):
        """Recursively use this class to sum up all income from 0 to calc_year"""
        if self.calc_year < 0:
            self.cumulative_net_income = 0
        else:
            self.cumulative_net_income = self.net_income_after_taxes
            copy_of_self = copy.deepcopy(self)  # Not sure this is the best way to do this recursion...?
            copy_of_self.calc_year -= 1
            copy_of_self.calculate_all_fields()
            self.cumulative_net_income += copy_of_self.cumulative_net_income

    def _calculate_depreciation_cumulative(self):
        years_until_calc_year = range(0, self.calc_year + 1)
        depreciation_per_year = [self.depreciation_for_year(year=x) for x in years_until_calc_year]
        self.depreciation_cumulative = sum(depreciation_per_year)

    def _calculate_depreciated_building_value(self):
        self.depreciated_building_value = self.purchase_price_building - self.depreciation_cumulative

    def _calculate_book_value(self):
        """
        This field is just for reference - it is the land value + depreciated building value assuming no capital gains
        """
        self.book_value = self.purchase_price_land + self.depreciated_building_value

    def _calculate_sale_price(self):
        if self.sale_price is None:
            self.sale_price = self.book_value

    def _calculate_sale_agent_fee(self):
        self.sale_agent_fee = int(
            (self.sale_price * self.agent_fee_variable + self.agent_fee_fixed) *
            (1 + taxconstants.CONSUMPTION_TAX)
        )

    def _calculate_sale_other_transaction_fees(self):
        self.sale_other_transaction_fees = int(self.sale_price * self.other_transaction_fees)

    def _calculate_sale_proceeds_after_fees(self):
        self.sale_proceeds_after_fees = self.sale_price - self.sale_agent_fee - self.sale_other_transaction_fees

    def _calculate_acquisition_cost(self):
        """Differs from purchase_price_and_fees because mortgage fees are probably not relevant for capital gains tax"""
        self.acquisition_cost = self.purchase_price + self.purchase_agent_fee + self.purchase_other_transaction_fees

    def _calculate_capital_gains_tax_primary_residence_deduction(self):
        """From # http://www.akasakarealestate.com/wiki/index.php/Taxes#Capital_Gains"""
        if self.is_primary_residence in [0, 1, 2]:
            self.capital_gains_tax_primary_residence_deduction = (self._CAPITAL_GAINS_TAX_PRIMARY_RESIDENCE_DEDUCTION *
                                                                  self.is_primary_residence)
        else:
            raise ValueError("{} is not a valid value for is_primary_residence".format(self.is_primary_residence))

    def _calculate_capital_gains(self):
        self.capital_gains = max(
            0,
            self.sale_proceeds_after_fees - (self.acquisition_cost - self.depreciation_cumulative)
        )

    def _calculate_capital_gains_tax_rate(self):
        """
        This is not an exhaustive enumeration of all possible tax scenarios (e.g. it does not include
        the divided tax rate for primary residence held more than 10 years) but should be a fairly
        realistic approximation most of the time. Obviously consult a tax lawyer/accountant etc.
        """
        if self.calc_year < 5:
            self.capital_gains_tax_rate = self._CAPITAL_GAINS_TAX_SHORT_NATIONAL
            if self.is_resident_for_tax_purposes:
                self.capital_gains_tax_rate += self._CAPITAL_GAINS_TAX_SHORT_MUNICIPAL
        else:
            self.capital_gains_tax_rate = self._CAPITAL_GAINS_TAX_LONG_NATIONAL
            if self.is_resident_for_tax_purposes:
                self.capital_gains_tax_rate += self._CAPITAL_GAINS_TAX_LONG_MUNICIPAL

        if self.calc_date < taxconstants.RESTORATION_TAX_EXPIRY:
            self.capital_gains_tax_rate *= (1 + taxconstants.RESTORATION_TAX)

    def _calculate_capital_gains_tax(self):
        # http://investment-japan.jp/japantaxonproperty/2994.html
        self.capital_gains_tax = max(
            0,
            int(self.capital_gains * self.capital_gains_tax_rate - self.capital_gains_tax_primary_residence_deduction)
        )

    def _calculate_sale_proceeds_net(self):
        self.sale_proceeds_net = self.sale_proceeds_after_fees - self.capital_gains_tax

    def _calculate_net_income_on_realestate(self):
        self.net_income_on_realestate = (self.sale_proceeds_net +
                                         self.cumulative_net_income -
                                         self.purchase_price_and_fees)
