import numpy as np


class Mortgage:
    """Class to calculate economics of a fixed-rate mortgage in Japan"""

    def __init__(
            self,
            principal=0.0,
            tenor=0,
            rate=0.0,
    ):
        """
        :param principal: Total loan principal
        :param tenor: Term of loan in years
        :param rate: Annual interest rate (in decimal, i.e. 0.008 for 0.8%)

        e.g. a 100M loan to be paid back in 35 years with a fixed rate of 0.8 %
           Loan = Mortgage( principal=100e6, tenor=35, rate=0.008 )
           Monthly Payment = Loan.monthly_payment
        """

        # Initialize class fields from arguments
        self.principal = principal
        self.tenor = tenor
        self.rate = rate

        # Derived fields that will be calculated
        self.loan_periods = None  # List where element i represents the month i
        self.interest_schedule = None  # List where element i represents the interest payment for month i
        self.principal_schedule = None  # List where element i represents the principal payment for month i
        self.amortization_schedule = None  # List where element i represents the total payment for month i
        self.monthly_payment = None  # Total monthly payment

        # Calculate!
        self.calculate_all_fields()

    def calculate_all_fields(self):
        """Calculate value for all derived fields"""
        self._calculate_loan_periods()
        self._calculate_interest_schedule()
        self._calculate_principal_schedule()
        self._calculate_amortization_schedule()
        self._calculate_monthly_payment()

    def _calculate_loan_periods(self):
        self.loan_periods = np.arange(self.tenor * 12) + 1  # Financial equations start the period count at 1

    def _calculate_interest_schedule(self):
        if self.tenor == 0:
            self.interest_schedule = []
        elif self.rate == 0:
            self.interest_schedule = self.loan_periods * 0
        else:
            self.interest_schedule = - np.ipmt(self.rate / 12,
                                               self.loan_periods,
                                               self.tenor * 12,
                                               self.principal)

    # noinspection PyTypeChecker,PyTypeChecker,PyTypeChecker
    def _calculate_principal_schedule(self):
        if self.tenor == 0:
            self.principal_schedule = []
        elif self.rate == 0:
            num_periods = len(self.loan_periods)
            self.principal_schedule = [self.principal / num_periods] * num_periods
        else:
            self.principal_schedule = - np.ppmt(self.rate / 12,
                                                self.loan_periods,
                                                self.tenor * 12,
                                                self.principal)

    def _calculate_amortization_schedule(self):
        if self.tenor == 0:
            self.amortization_schedule = []
        else:
            self.amortization_schedule = self.interest_schedule + self.principal_schedule

    def _calculate_monthly_payment(self):
        if len(self.amortization_schedule):
            self.monthly_payment = self.amortization_schedule[0]
        else:
            self.monthly_payment = 0

