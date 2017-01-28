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

1. Optionally create a Mortgage object (if you are modeling a loan financed real estate investment)
2. Create an IncomeTaxCalc object
3. Create a RealEstateCalc object, supplying the Mortgage and IncomeTaxCalc created from the previous steps
4. Inspect attributes of RealEstateCalc to learn what you want about the investment
  

## Note on IncomeTaxCalc
This is required for real estate analysis because income from real estate in Japan is taxed as regular income. This
means that any rental income from leasing apartments is pooled together with any other regular income (like salary)
prior to calculating taxes owed. So strangely enough, the profitability of a property is not just a function of the
property but of its owner.

