from japanrealestate.incometaxcalc import IncomeTaxCalc
from japanrealestate.realestatecalc import RealEstateCalc
import csv

"""
This is an example of using the calculators to do due diligence on some property.
The calculator is run over several years and output is printed to CSV files.
"""

# Let's do the due diligence assuming a salary of 20m and also assuming no salary
# This lets us see how the property behaves if we earn a decent income and also if we are unemployed

decent_income_tax_calc = IncomeTaxCalc(
    employment_income=20000000,
    is_resident_for_tax_purposes=True,
)

zero_income_tax_calc = IncomeTaxCalc()

output_file_name_to_income_tax_calc = {
    'example_csv_output_20m_salary.csv': decent_income_tax_calc,
    'example_csv_output_0_salary.csv': zero_income_tax_calc,
}

# The property details come from the agent
# We do not specify a sales price so the model will resort to book value, which is a conservative estimate assuming
# no capital gains and that the property depreciates to zero value over its useful life
real_estate_calc = RealEstateCalc(
    purchase_price=68000000,
    building_to_land_ratio=0.3,
    size=62.06,
    age=18,
    mortgage_loan_to_value=0.882352941,  # Loan of 60m
    bank_valuation_to_actual=1,
    mortgage_tenor=35,
    mortgage_rate=0.01,  # Rate more likely to be 0.825% but let's be conservative
    mortgage_initiation_fees=0,  # Putting it under other_transaction_fees as agent did not provide breakdown
    agent_fee_variable=0.03,
    agent_fee_fixed=60000,
    renovation_cost=6000000,  # Agent estimated at 5m, let's be conservative and increase by 20%
    other_transaction_fees=0.010735294,  # 73k/68m (note: I will eventually change code to take this param in JPY)

    # Parameters associated with ongoing concern
    monthly_fees=44810,
    property_tax_rate=0.00263,  # 178,645 JPY/year
    maintenance_per_m2=1000,  # This is a conservative estimate
    useful_life=47,
    calc_year=0,
    income_tax_calculator=decent_income_tax_calc,

    # Parameters associated with renting out the real estate
    gross_rental_yield=0.0467,  # (265k * 12)/68M - agent's estimate, seems reasonable
    renewal_income_rate=0,  # Be conservative, assume no key money or renewal fee from tenant

    # Tenant management fee is 5% of rent and 1 month rent when we find the tenant, assume change every 2.5 years.
    rental_management_rental_fee=0.05,
    rental_management_renewal_fee=0.03333,

    # Parameters associated with final disposal
    is_primary_residence=0,
    is_resident_for_tax_purposes=True,
)

header = [
    'Year',
    'Income',
    'Property Value',
    'Cumulative Income',
    'Equity',
    'Net PNL If Sold (incl cum income + tax shield)'
]

for output_file_name, inc_calc in output_file_name_to_income_tax_calc.items():
    output = [header]
    real_estate_calc.income_tax_calculator = inc_calc

    for calc_year in range(0, 40):
        real_estate_calc.calc_year = calc_year
        real_estate_calc.calculate_all_fields()
        row = [
            real_estate_calc.purchase_date.year + calc_year,
            real_estate_calc.net_income_after_taxes,
            real_estate_calc.book_value,
            real_estate_calc.cumulative_net_income,
            real_estate_calc.equity_value,
            real_estate_calc.net_profit_on_realestate
        ]
        output.append(row)

    with open(output_file_name, 'w', newline='') as csv_file:
        csv_writer = csv.writer(
            csv_file,
            delimiter=',',
        )

        for row in output:
            csv_writer.writerow(row)

    with open(output_file_name, 'r', newline='') as csv_file:
        print(csv_file.read())
