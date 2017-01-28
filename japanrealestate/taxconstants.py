import datetime as dt

CONSUMPTION_TAX = 0.08

# Special tax equal to 2.1 % of basic tax levied after '11 Tohoku earthquake
# http://www.eytax.jp/pdf/newsletter/2011/Newsletter_Dec_2011_E.pdf
RESTORATION_TAX = 0.021
RESTORATION_TAX_EXPIRY = dt.date(year=2038, month=1, day=1)
