#!/usr/bin/env python

import json
import pprint as pp
from japanrealestate.incometaxcalc import IncomeTaxCalc
from japanrealestate.realestatecalc import RealEstateCalc

with open('config1.json') as config_file:
    config = json.load(config_file)

itc_params = config['income_tax_calc_params']
income_tax_calc = IncomeTaxCalc(
    employment_income=itc_params['employment_income'],
    rent=itc_params['rent'],
    is_rent_program=itc_params['is_rent_program'],
    other_income=itc_params['other_income'],
    life_insurance_premium=itc_params['life_insurance_premium'],
    medical_expense=itc_params['medical_expense'],
    number_of_dependents=itc_params['number_of_dependents'],
    social_security_expense=itc_params['social_security_expense'],
    tax_deduction=itc_params['tax_deduction'],
    is_resident_for_tax_purposes=itc_params['is_resident_for_tax_purposes'])

print('*************** Income Tax Calculation ***************** ')

pp.pprint(income_tax_calc.__dict__)

rc_params = config['real_estate_calc_params']

real_estate_calc = RealEstateCalc(
    purchase_date=rc_params['purchase_date'],
    purchase_price=rc_params['purchase_price'],
    building_to_land_ratio=rc_params['building_to_land_ratio'],
    size=rc_params['size'],
    age=rc_params['age'],
    mortgage_loan_to_value=rc_params['mortgage_loan_to_value'],
    bank_valuation_to_actual=rc_params['bank_valuation_to_actual'],
    mortgage_tenor=rc_params['mortgage_tenor'],
    mortgage_rate=rc_params['mortgage_rate'],
    mortgage_initiation_fees=rc_params['mortgage_initiation_fees'],
    agent_fee_variable=rc_params['agent_fee_variable'],
    agent_fee_fixed=rc_params['agent_fee_fixed'],
    other_transaction_fees=rc_params['other_transaction_fees'],

    # Parameters associated with ongoing concern
    monthly_fees=rc_params['monthly_fees'],
    property_tax_rate=rc_params['property_tax_rate'],
    maintenance_per_m2=rc_params['maintenance_per_m2'],
    useful_life=rc_params['useful_life'],
    calc_year=rc_params['calc_year'],
    income_tax_calculator=income_tax_calc,

    # Parameters associated with renting out the real estate
    gross_rental_yield=rc_params['gross_rental_yield'],
    renewal_income_rate=rc_params['renewal_income_rate'],
    rental_management_rental_fee=rc_params['rental_management_rental_fee'],
    rental_management_renewal_fee=rc_params['rental_management_renewal_fee'],

    # Parameters associated with final disposal
    is_primary_residence=rc_params['is_primary_residence'],
    is_resident_for_tax_purposes=rc_params['is_resident_for_tax_purposes'],
    sale_price=rc_params['sale_price']
)

print('*************** Real Estate Calculation ***************** ')

pp.pprint(real_estate_calc.__dict__)
