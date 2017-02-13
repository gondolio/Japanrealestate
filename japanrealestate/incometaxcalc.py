from japanrealestate import taxconstants
import datetime as dt


# To do
# Find out how constants are used in Python to avoid magic numbers? Is there any point to constants only used in one
# method?
# Should I be using @property?? what is the pythonic way to do this graph stuff
# reg tests

class IncomeTaxCalc:
    """
    Class to calculate Japanese taxes and post tax income
    https://home.kpmg.com/xx/en/home/insights/2011/12/japan-income-tax.html is a very good resource to understand
    the logic.

    This class is (of course) not exhaustive. Example issues not dealt with:
    * Employment-related expenditures incurred but not reimbursed by the employer
    * Capital gains deduction
    * Occasional income deduction
    * Medical expenses rules (e.g. limits and qualifying conditions)
    * Contributions and donations
    * Earthquake insurance ("up to the value of JPY50,000 can be deducted from income for income tax purposes,
      and a half of the premiums for local inhabitant tax purposes (up to JPY25,000)").
    * Relief for foreign taxes paid
    * General tax credits
    * Spouse & children deductions
    * Retirement income
    * Any special logic applied to local taxes vs national taxes (other than excluding local taxes for non-residents,
      which is supported).
    * Any tax laws that were only applicable prior to December 2016 (when this class was written)
    """

    def __init__(
            self,
            employment_income=0,
            rent=0,
            is_rent_program=False,
            other_income=0,
            life_insurance_premium=0,
            medical_expense=0,
            number_of_dependents=0,
            social_security_expense=None,
            tax_deduction=0,
            is_resident_for_tax_purposes=True,
            current_date=None,
     ):
        """
        :param employment_income: Annual income from employment (amount prior to rent program being taken out)
        :param rent: Annual rent you are paying (actual amount paid to landlord)
        :param is_rent_program: True if your rent is deducted from your taxable income
        :param other_income: Annual net income from real estate investments etc. Can be negative (e.g. depreciation).
        :param life_insurance_premium: Annual premium paid for life insurance
        :param medical_expense: Annual medical expenses paid by you and not reimbursed
        :param number_of_dependents: Number of tax dependents you have claimed
        :param social_security_expense: Annual social security expense (see your pay stub).
               Default value of None will result in auto-calculation (not 100% accurate but pretty close)
        :param tax_deduction: Legally allowed deductions from taxes due. This is a deduction from actual taxes due,
               NOT a deduction from taxable income (which should be included under other_income). Examples include
               home loan mortgage deductions on primary residence.
        :param current_date: date for which tax is being calculated. Defaults to date.today().
        """

        # Initialize class fields from arguments
        self.employment_income = employment_income
        self.rent = rent
        self.other_income = other_income
        self.life_insurance_premium = life_insurance_premium
        self.medical_expense = medical_expense
        self.number_of_dependents = number_of_dependents
        self.is_rent_program = is_rent_program
        self.social_security_expense = social_security_expense
        self.tax_deduction = tax_deduction
        self.is_resident_for_tax_purposes = is_resident_for_tax_purposes
        self.current_date = current_date

        # Derived fields that will be calculated
        self.total_income = None  # Real cash flow income
        self.employment_income_after_rent_program = None  # After deducting amount allowed under rent program
        self.employment_income_deduction = None  # Deduction allowed for Employment Income
        self.employment_income_for_tax = None  # Employment Income amount for tax purposes after deduction
        self.total_income_for_tax = None  # Sum of all annual income
        self.deduction_dependents = None  # Income deduction due to tax dependents
        self.deduction_total = None  # Sum of all income deduction
        self.taxable_income = None  # Taxable income based on your actual income before deductions
        self.national_income_tax_bracket = None  # Entry in _NATIONAL_INCOME_TAX_TABLE matching taxable_income
        self.national_income_tax_rate = None  # Marginal tax rate based on income bracket
        self.national_income_tax = None  # Amount of national income tax that must be paid
        self.local_income_tax = None  # Amount of local income tax that must be paid (aka local inhabitants tax)
        self.total_income_tax = None  # Amount of total income tax that must be paid
        self.net_income_after_tax = None  # Annual cash flow after mandatory govt. expenses (taxes, social insurance)
        self.effective_tax_rate = None  # Earnings after tax divided by

        # Calculate!
        self.calculate_all_fields()

    def calculate_all_fields(self):
        """Calculate value for all derived fields"""
        self._calculate_current_date()
        self._calculate_total_income()
        self._calculate_employment_income_after_rent_program()
        self._calculate_social_security_expense()
        self._calculate_employment_income_for_tax()
        self._calculate_employment_income_deduction()
        self._calculate_total_income_for_tax()
        self._calculate_deduction_dependents()
        self._calculate_deduction_total()
        self._calculate_taxable_income()
        self._calculate_national_income_tax_bracket()
        self._calculate_national_income_tax_rate()
        self._calculate_national_income_tax()
        self._calculate_local_income_tax()
        self._calculate_total_income_tax()
        self._calculate_net_income_after_tax()
        self._calculate_effective_tax_rate()

    # Income tax specific constants
    _DEDUCTION_BASIC = 380000  # Basic deduction each tax individual receives
    _DEDUCTION_PER_DEPENDENT = 380000
    _LEGAL_RENT_RATE = 0.95  # The amount of rent deducted from your employment_income (pre-tax) as part of rent program

    """
    A deduction is applied to the gross revenue (収入(syunyuu)) depending upon its type and amount. For employment
    income, the net revenue (所得 (syotoku)) is calculated from the gross amount based on the following table.
    Please refer to page 9 of the following file (page 8 based on documents numbering)
    http://www.nta.go.jp/tetsuzuki/shinkoku/shotoku/tebiki2016/pdf/01.pdf
    """

    _EMPLOYMENT_INCOME_FOR_TAX_TABLE = [
        {
            'bounds': [0, 650999],
            'function': lambda x: 0
        },
        {
            'bounds': [651000, 1618999],
            'function': lambda x: x-650000
        },
        {
            'bounds': [1619000, 1619999],
            'function': lambda x: 969000
        },
        {
            'bounds': [1620000, 1621999],
            'function': lambda x: 970000
        },
        {
            'bounds': [1622000, 1623999],
            'function': lambda x: 972000
        },
        {
            'bounds': [1624000, 1627999],
            'function': lambda x: 974000
        },
        {
            'bounds': [1628000, 1799999],
            'function': lambda x: round(x/(4*1000))*1000 * 2.4
        },
        {
            'bounds': [1800000, 3599999],
            'function': lambda x: round(x / (4 * 1000)) * 1000 * 2.8 - 180000
        },
        {
            'bounds': [3600000, 6599999],
            'function': lambda x: round(x / (4 * 1000)) * 1000 * 3.2 - 540000
        },
        {
            'bounds': [6600000, 9999999],
            'function': lambda x: x*0.9 - 1200000
        },
        {
            'bounds': [10000000, 11999999],
            'function': lambda x: x*0.95 - 1700000
        },
        {
            'bounds': [12000000, 10000000000000],
            'function': lambda x: x - 2300000
        },
    ]

    _NATIONAL_INCOME_TAX_TABLE = [
        {
            'bounds': [0, 1950000],  # Income range that this bracket is applied to
            'rate': 0.05,  # Rate applied to income within bound
            'previous_brackets_sum': 0  # Sum of taxes for all previous brackets
        },
        {
            'bounds': [1950000 + 1, 3300000],
            'rate': 0.1,
            'previous_brackets_sum': 97500
        },
        {
            'bounds': [3300000 + 1, 6950000],
            'rate': 0.2,
            'previous_brackets_sum': 232500
        },
        {
            'bounds': [6950000 + 1, 9000000],
            'rate': 0.23,
            'previous_brackets_sum': 962500
        },
        {
            'bounds': [9000000 + 1, 18000000],
            'rate': 0.33,
            'previous_brackets_sum': 1434000
        },
        {
            'bounds': [18000000 + 1, 40000000],
            'rate': 0.40,
            'previous_brackets_sum': 4404000
        },
        {
            'bounds': [40000000 + 1, float('inf')],
            'rate': 0.45,
            'previous_brackets_sum': 13204000
        }
    ]

    _LOCAL_INCOME_TAX_RATE = 0.04 + 0.06  # 4 percent prefectural + 6 percent municipal
    _HEALTH_INSURANCE_RATE = 0.0996  # For Tokyo
    _SOCIAL_PENSION_RATE = 0.183  # Expected as of Sept 2017

    @staticmethod
    def __lookup_in_tax_table(lookup_value,
                              rules):
        """Helper to look up entry in rule set for employment income"""
        for rule in rules:
            bounds = rule['bounds']
            if bounds[0] <= lookup_value <= bounds[1]:
                return rule
        raise ValueError("'{}' is not a valid income".format(lookup_value))

    def _calculate_current_date(self):
        if self.current_date is None:
            self.current_date = dt.date.today()

    def _calculate_total_income(self):
        self.total_income = self.employment_income + self.other_income

    def _calculate_employment_income_after_rent_program(self):
        self.employment_income_after_rent_program = (self.employment_income -
                                                     self.is_rent_program * self.rent * self._LEGAL_RENT_RATE)

    def _calculate_social_security_expense(self):
        """
        Defaults expense of social security insurance to sensible value.

        Social security insurance consists of:
        Health Insurance
        Social Pension Insurance
        Nursing (for people 40-65 years old)
        Children Upbringing (for people with children)

        50% of the Social Insurance tax is deducted from employee salary whereas, the other 50% is paid by the employer.
        The exception is the Children Upbringing tax which is paid only by employer.

        This class only deals with Health Insurance / Social Pension Insurance.

        The exact formula is not implemented because it varies by region/age/children/etc and requires a large lookup
        table, but below approximation should be sufficient. Not sure if other income (e.g. from rental properties)
        counts towards the income used for calculating social security, but excluding it for now.

        Details:
        http://www.shigakukyosai.jp/en/about/en_about_premiumchart2016_9.pdf
        https://www.quora.com/How-is-social-insurance-calculated-in-Japan
        http://www.htm.co.jp/payroll-social-insurance-practices-japan.htm
        https://www.justlanded.jp/english/Japan/Japan-Guide/Jobs/Japanese-pension-insurance
        """
        if self.social_security_expense is None:
            health_insurance_standard_salary = min(self.employment_income_after_rent_program, 1390000 * 12)
            health_insurance_expense = health_insurance_standard_salary * self._HEALTH_INSURANCE_RATE

            social_pension_standard_salary = min(self.employment_income_after_rent_program, 635000 * 12)
            social_pension_standard_expense = social_pension_standard_salary * self._SOCIAL_PENSION_RATE

            total_expense = health_insurance_expense + social_pension_standard_expense
            self.social_security_expense = int(total_expense * 0.5)  # Half paid by employer

    def _calculate_employment_income_for_tax(self):
        """Converts an actual annual employment income into the income used for tax calculations"""
        income_for_tax_rule = self.__lookup_in_tax_table(
            self.employment_income_after_rent_program,
            self._EMPLOYMENT_INCOME_FOR_TAX_TABLE
        )

        self.employment_income_for_tax = min(
            int(
                income_for_tax_rule['function'](
                    self.employment_income_after_rent_program
                )
            ),
            self.employment_income_after_rent_program
        )

    def _calculate_employment_income_deduction(self):
        """This field is just for reference"""
        self.employment_income_deduction = self.employment_income_after_rent_program - self.employment_income_for_tax

    def _calculate_total_income_for_tax(self):
        self.total_income_for_tax = self.employment_income_for_tax + self.other_income

    def _calculate_deduction_dependents(self):
        self.deduction_dependents = self.number_of_dependents * self._DEDUCTION_PER_DEPENDENT

    def _calculate_deduction_total(self):
        self.deduction_total = (min(2000000, self.medical_expense) +
                                self.social_security_expense +
                                self.life_insurance_premium +
                                self._DEDUCTION_BASIC +
                                self.deduction_dependents)

    def _calculate_taxable_income(self):
        # taxable_income has a floor of 0 as this class does not handle tax losses or credits
        self.taxable_income = max(0, self.total_income_for_tax - self.deduction_total)

    def _calculate_national_income_tax_bracket(self):
        self.national_income_tax_bracket = self.__lookup_in_tax_table(self.taxable_income,
                                                                      self._NATIONAL_INCOME_TAX_TABLE)

    def _calculate_national_income_tax_rate(self):
        self.national_income_tax_rate = self.national_income_tax_bracket['rate']

    def _calculate_national_income_tax(self):
        marginal_income = self.taxable_income - self.national_income_tax_bracket['bounds'][0]
        marginal_rate = self.national_income_tax_rate
        marginal_tax = marginal_income * marginal_rate
        total_tax = self.national_income_tax_bracket['previous_brackets_sum'] + marginal_tax

        #  Restoration tax is multiplied on top of national income tax only (there is also a 10 year ¥1000
        #  inhabitant tax increase but this is not implemented as it is insignificant)
        #  http://www.eytax.jp/pdf/newsletter/2011/Newsletter_Dec_2011_E.pdf

        if self.current_date < taxconstants.RESTORATION_TAX_EXPIRY:
            total_tax *= (1 + taxconstants.RESTORATION_TAX)

        self.national_income_tax = int(total_tax)

    def _calculate_local_income_tax(self):
        self.local_income_tax = (self.is_resident_for_tax_purposes *
                                 self._LOCAL_INCOME_TAX_RATE *
                                 self.taxable_income)

    def _calculate_total_income_tax(self):
        total_income_tax = self.national_income_tax + self.local_income_tax - self.tax_deduction
        self.total_income_tax = max(0, total_income_tax)  # No negative taxes

    def _calculate_net_income_after_tax(self):
        self.net_income_after_tax = (self.total_income -
                                     self.total_income_tax -
                                     self.social_security_expense)

    def _calculate_effective_tax_rate(self):
        if self.total_income == 0:
            self.effective_tax_rate = 0
        else:
            self.effective_tax_rate = 1 - self.net_income_after_tax / self.total_income
