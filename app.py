import streamlit as st
import pandas as pd

st.title("Payroll Calculator")

# Define states list
states = ['Alabama', 'Alaska', 'Arizona', 'Arkansas', 'California', 'Colorado', 'Connecticut', 
          'Delaware', 'Florida', 'Georgia', 'Hawaii', 'Idaho', 'Illinois', 'Indiana', 'Iowa', 
          'Kansas', 'Kentucky', 'Louisiana', 'Maine', 'Maryland', 'Massachusetts', 'Michigan', 
          'Minnesota', 'Mississippi', 'Missouri', 'Montana', 'Nebraska', 'Nevada', 'New Hampshire', 
          'New Jersey', 'New Mexico', 'New York', 'North Carolina', 'North Dakota', 'Ohio', 
          'Oklahoma', 'Oregon', 'Pennsylvania', 'Rhode Island', 'South Carolina', 'South Dakota', 
          'Tennessee', 'Texas', 'Utah', 'Vermont', 'Virginia', 'Washington', 'West Virginia', 
          'Wisconsin', 'Wyoming']

# Input fields
annual_salary = st.number_input('Annual Salary ($)', min_value=80000, step=1000)
annual_401k_contribution = st.number_input('401k Contribution ($)', min_value=0, step=100, value=16000)
annual_roth_ira_contribution = st.number_input('Roth IRA Contribution ($)', min_value=0, max_value=7000, step=100)
annual_living_expenses = st.number_input('Living Expenses ($)', min_value=0, step=100, value=54000)
state = st.selectbox('State', states, index=states.index('Texas'))

# FICA checkbox
include_fica = st.checkbox('Include FICA Tax', value=True)

# Federal income tax brackets for 2025 (single filer)
federal_tax_brackets = [
    (11925, 0.10),
    (48475 - 11925, 0.12),
    (103350 - 48475, 0.22),
    (197300 - 103350, 0.24),
    (250525 - 197300, 0.32),
    (626351 - 250525, 0.35),
    (float('inf'), 0.37)
]

# Standard deduction for a single filer
standard_deduction = 15000

# FICA tax rates
fica_social_security_rate = 0.062  # up to $176,100
fica_medicare_rate = 0.0145        # all income
fica_add_medicare_rate = 0.009     # over $200,000

# State tax assumption (for now, only Texas = 0%)
if state == 'Texas':
    state_tax_percent = 0
else:
    state_tax_percent = 0.05  # Placeholder for other states

# Calculate taxable income
taxable_income = max(0, annual_salary - annual_401k_contribution - standard_deduction)

# Calculate federal income tax
federal_income_tax = 0
remaining_income = taxable_income
for bracket, rate in federal_tax_brackets:
    if remaining_income <= 0:
        break
    income_in_bracket = min(remaining_income, bracket)
    federal_income_tax += income_in_bracket * rate
    remaining_income -= income_in_bracket

# FICA taxes
fica_social_security_tax = min(annual_salary, 176100) * fica_social_security_rate
fica_medicare_tax = annual_salary * fica_medicare_rate
fica_add_medicare_tax = max(0, annual_salary - 200000) * fica_add_medicare_rate
fica_tax = fica_social_security_tax + fica_medicare_tax + fica_add_medicare_tax

# State tax
state_tax = taxable_income * state_tax_percent

# Total taxes
if include_fica:
    annual_total_taxes = federal_income_tax + fica_tax + state_tax
else:
    annual_total_taxes = federal_income_tax + state_tax

# Bi-weekly numbers
biweekly_gross_pay = annual_salary / 26
biweekly_401k_contribution = annual_401k_contribution / 26
biweekly_total_taxes = annual_total_taxes / 26
biweekly_net_pay = biweekly_gross_pay - biweekly_401k_contribution - biweekly_total_taxes

# Adjusting pay schedule
new_pay_dates = [
    "Feb 14", "Feb 28", "Mar 14", "Mar 28", "Apr 11", "Apr 25", "May 9", "May 23",
    "Jun 6", "Jun 20", "Jul 4", "Jul 18", "Aug 1", "Aug 15", "Aug 29", "Sep 12",
    "Sep 26", "Oct 10", "Oct 24", "Nov 7", "Nov 21", "Dec 5", "Dec 19"
]

first_pay_gross = (4 / 10) * biweekly_gross_pay
first_pay_401k = (4 / 10) * biweekly_401k_contribution
first_pay_taxes = (4 / 10) * biweekly_total_taxes
first_pay_net = first_pay_gross - first_pay_401k - first_pay_taxes

# Pay schedule dataframe
adjusted_pay_schedule = pd.DataFrame({
    "Pay Date": new_pay_dates,
    "Gross Pay ($)": [first_pay_gross] + [biweekly_gross_pay] * (len(new_pay_dates) - 1),
    "401(k) Contribution ($)": [-first_pay_401k] + [-biweekly_401k_contribution] * (len(new_pay_dates) - 1),
    "Federal Tax ($)": [-first_pay_taxes] + [-biweekly_total_taxes] * (len(new_pay_dates) - 1),
    "Net Pay ($)": [first_pay_net] + [biweekly_net_pay] * (len(new_pay_dates) - 1)
})

st.write("### Adjusted Pay Schedule")
st.dataframe(adjusted_pay_schedule)

# Annual Remaining Income
annual_remaining_income = (
    annual_salary - annual_401k_contribution - annual_roth_ira_contribution - annual_total_taxes - annual_living_expenses
)

# Bi-weekly and Monthly summaries
def calculate_period_values(periods):
    return {
        "Gross Income": annual_salary / periods,
        "401(k) Contribution": annual_401k_contribution / periods,
        "Roth IRA Contribution": annual_roth_ira_contribution / periods,
        "Taxes": annual_total_taxes / periods,
        "Living Expenses": annual_living_expenses / periods,
        "Remaining Income": annual_remaining_income / periods
    }

monthly_values = calculate_period_values(12)
biweekly_values = calculate_period_values(26)

breakdown_df = pd.DataFrame({
    "Category": list(monthly_values.keys()),
    "Annual ($)": [
        annual_salary,
        annual_401k_contribution,
        annual_roth_ira_contribution,
        annual_total_taxes,
        annual_living_expenses,
        annual_remaining_income
    ],
    "Monthly ($)": list(monthly_values.values()),
    "Bi-Weekly ($)": list(biweekly_values.values())
})

st.write("### Breakdown of Income")
st.dataframe(breakdown_df)

# Optional summary
st.markdown("**Summary:**")
st.markdown(f"- Estimated Annual Take-Home Pay: `${annual_salary - annual_total_taxes - annual_401k_contribution:.2f}`")
st.markdown(f"- Remaining Annual Income After Expenses: `${annual_remaining_income:.2f}`")
