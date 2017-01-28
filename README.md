# Japanrealestate

Analytics for real estate investment in Japan

This project contains three classes that aim to help analyze real estate investments in Japan:
* Mortgage - a simple model of a fixed rate and fixed payment mortgage
* IncomeTaxCalc - a "calculator" of income taxes in Japan. This may be useful in its own right to better understand
your income tax situation.
* RealEstateCalc - a "calculator" of the economics of real estate ownership in Japan

## Usage
All three classes follow a design whereby (almost) every intermediary calculation is stored as a class attribute.
This allows for easy inspection of every detail of the calculation as well as allowing overrides of certain portions of
the calculations to see how it impacts the output (sort of like overriding cells in an Excel model).
This design does mean that any changes to attributes will not automatically be propagated unless calculate_all_fields()
(or one of the other \_calculate_*** functions) is called.

The "output" of these classes are the values of the calculated attributes. For example, after creating a RealEstateCalc
object, one can inspect the 'net_income_after_taxes' attribute to understand how much net income one can expect to get
from the real estate investment (after deducting all the various fees and using depreciation as a tax shield etc).

The suggested usage is as follows:

1. Create an IncomeTaxCalc object
2. Create a RealEstateCalc object, supplying the IncomeTaxCalc created from the previous steps
3. Inspect attributes of RealEstateCalc to learn what you want about the investment
  

## Note on IncomeTaxCalc
This is required for real estate analysis because income from real estate in Japan is taxed as regular income. This
means that any rental income from leasing apartments is pooled together with any other regular income (like salary)
prior to calculating taxes owed. So strangely enough, the profitability of a property is not just a function of the
property but of its owner.

## Sample Usage

```python
        # Sample income tax calculator 
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

        # Buying a brand new 100m property with a 30 year 1% mortgage, and selling it 32 years later
        real_estate_calc = RealEstateCalc(
            purchase_date=None,
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
        
        print(real_estate_calc.__dict__)
```