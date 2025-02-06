# app.py
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import database
from werkzeug.security import generate_password_hash, check_password_hash

# Initialize the database
database.init_db()

# Initialize session state for authentication
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'username' not in st.session_state:
    st.session_state.username = None

st.set_page_config(
    page_title="FinanceFlow | Personal Finance Manager",
    page_icon="💰",
    layout="wide"
)

# Authentication section
if not st.session_state.user_id:
    st.title("Welcome to FinanceFlow")
    st.subheader("Your Personal Finance Command Center")
    
    tab1, tab2, tab3 = st.tabs(["Login", "Register", "Guest Access"])
    
    with tab1:
        with st.form("login_form"):
            login_username = st.text_input("Username")
            login_password = st.text_input("Password", type="password")
            login_submitted = st.form_submit_button("Login")
            
            if login_submitted:
                user_id = database.verify_user(login_username, login_password)
                if user_id:
                    st.session_state.user_id = user_id
                    st.session_state.username = login_username
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Invalid username or password")
    
    with tab2:
        with st.form("register_form"):
            reg_username = st.text_input("Choose Username")
            reg_password = st.text_input("Choose Password", type="password")
            reg_password_confirm = st.text_input("Confirm Password", type="password")
            register_submitted = st.form_submit_button("Register")
            
            if register_submitted:
                if reg_password != reg_password_confirm:
                    st.error("Passwords do not match")
                elif len(reg_password) < 6:
                    st.error("Password must be at least 6 characters long")
                else:
                    if database.register_user(reg_username, reg_password):
                        st.success("Registration successful! Please login.")
                    else:
                        st.error("Username already exists")
    
    with tab3:
        st.warning("In guest mode, your data won't be saved between sessions.")
        if st.button("Continue as Guest"):
            st.session_state.user_id = -1  # Use -1 to indicate guest user
            st.session_state.username = "Guest"
            st.rerun()

    # Add some information about the app
    st.write("---")
    st.write("### About This App")
    st.write("""
    The Payroll & Expense Tracker helps you:
    - Calculate your take-home pay after taxes and deductions
    - Track your monthly expenses by category
    - Visualize your spending patterns
    - Plan your budget effectively
    
    Please login or register to access all features.
    """)

else:
    # Show logout button in sidebar
    if st.sidebar.button("Logout"):
        st.session_state.user_id = None
        st.session_state.username = None
        st.session_state.expenses = {}  # Clear expenses on logout
        st.rerun()
    
    st.sidebar.write(f"Logged in as: {st.session_state.username}")
    if st.session_state.user_id == -1:  # Guest user
        st.sidebar.warning("Guest Mode: Data won't be saved!")
    
    # Main app tabs
    tab1, tab2 = st.tabs(["Payroll Calculator", "Expense Tracker"])
    
    with tab1:
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

        # FICA number input with checkbox and calculation
        include_fica = st.checkbox('Include FICA Tax', value=True)

        # Federal income tax brackets for 2025 (single filer)
        federal_tax_brackets = [
            (11925, 0.10),  # 10% on income up to $11,925
            (48475 - 11925, 0.12),  # 12% on income from $11,926 to $48,475
            (103350 - 48475, 0.22),  # 22% on income from $48,476 to $103,350
            (197300 - 103350, 0.24),  # 24% on income from $103,351 to $197,300
            (250525 - 197300, 0.32),  # 32% on income from $197,301 to $250,525
            (626351 - 250525, 0.35),  # 35% on income from $250,526 to $626,350
            (float('inf'), 0.37)  # 37% on income above $626,351
        ]

        # Standard deduction for a single filer
        standard_deduction = 15000

        # FICA taxes (if needed)
        fica_social_security_rate = 0.062 # 6.2% on income up to $176,100
        fica_medicare_rate = 0.0145 # 1.45% on all wages
        fica_medicare_rate = 0.009 # 0.9% (0.9% on wages over $200,000 for single filers.)

        if state == 'Texas':
            state_tax_percent = 0
        else:
            pass

        # Calculate taxable income after 401(k) contributions and standard deduction
        taxable_income = annual_salary - annual_401k_contribution - standard_deduction

        # Calculate estimated federal tax
        federal_income_tax = 0
        remaining_income = taxable_income

        for bracket, rate in federal_tax_brackets:
            if remaining_income <= 0:
                break
            income_in_bracket = min(remaining_income, bracket)
            tax_amount = income_in_bracket * rate
            federal_income_tax += tax_amount
            remaining_income -= income_in_bracket

        # Calculate FICA taxes 
        # Calculated based on your gross salary before 401(k) contributions
        fica_social_security_tax = min(annual_salary, 176100) * fica_social_security_rate  # Cap at $176,100
        fica_medicare_tax = annual_salary * fica_medicare_rate
        fica_add_medicare_tax = (annual_salary - 200000) * fica_medicare_rate
        fica_tax = fica_social_security_tax + fica_medicare_tax + fica_add_medicare_tax

        state_tax = taxable_income * state_tax_percent


        if include_fica == 1:
            annual_total_taxes = federal_income_tax + fica_tax + state_tax
        else:
            annual_total_taxes = federal_income_tax + state_tax


        biweekly_gross_pay = annual_salary / 26  # Bi-weekly salary
        biweekly_401k_contribution = annual_401k_contribution / 26  # Bi-weekly 401(k) deduction
        biweekly_total_taxes = annual_total_taxes / 26 # # Bi-weekly total tax

        # Calculate bi-weekly net pay
        biweekly_net_pay = biweekly_gross_pay - biweekly_401k_contribution - biweekly_total_taxes 

        # Adjusting pay schedule for new start date of February 10, 2025
        new_pay_dates = [
            "Feb 14", "Feb 28", "Mar 14", "Mar 28", "Apr 11", "Apr 25", "May 9", "May 23",
            "Jun 6", "Jun 20", "Jul 4", "Jul 18", "Aug 1", "Aug 15", "Aug 29", "Sep 12",
            "Sep 26", "Oct 10", "Oct 24", "Nov 7", "Nov 21", "Dec 5", "Dec 19"
        ]

        # Adjust first paycheck for a partial period (Feb 10 start date, working ~4 out of 10 days in that pay period)
        first_pay_gross = (4 / 10) * biweekly_gross_pay
        first_pay_401k = (4 / 10) * biweekly_401k_contribution
        first_pay_federal_tax = (4 / 10) * biweekly_total_taxes
        first_pay_net = first_pay_gross - first_pay_401k - first_pay_federal_tax 

        # Create adjusted pay schedule DataFrame
        adjusted_pay_schedule = pd.DataFrame({
            "Pay Date": new_pay_dates,
            "Gross Pay ($)": [first_pay_gross] + [biweekly_gross_pay] * (len(new_pay_dates) - 1),
            "401(k) Contribution ($)": [-first_pay_401k] + [-biweekly_401k_contribution] * (len(new_pay_dates) - 1),
            "Federal Tax ($)": [-first_pay_federal_tax] + [-biweekly_total_taxes] * (len(new_pay_dates) - 1),
            "Net Pay ($)": [first_pay_net] + [biweekly_net_pay] * (len(new_pay_dates) - 1)
        })

        # Display the adjusted pay schedule
        st.write("Adjusted Pay Schedule")
        st.dataframe(adjusted_pay_schedule)


        annual_remaining_income = annual_salary - annual_401k_contribution - annual_roth_ira_contribution - annual_total_taxes -annual_living_expenses

        biweekly_gross_income = annual_salary / 26
        biweekly_401k_contribution = annual_401k_contribution / 26
        biweekly_roth_ira_contribution = annual_roth_ira_contribution / 26
        biweekly_total_taxes = annual_total_taxes / 26
        biweekly_living_expenses = annual_living_expenses / 26
        biweekly_remaining_income = annual_remaining_income / 26

        monthly_gross_income = annual_salary / 12
        monthly_401k_contribution = annual_401k_contribution / 12
        monthly_roth_ira_contribution = annual_roth_ira_contribution / 12
        monthly_total_taxes = annual_total_taxes / 12
        monthly_living_expenses = annual_living_expenses / 12
        monthly_remaining_income =  annual_remaining_income / 12

        breakdown_df = pd.DataFrame({
            "Category": [
                "Gross Income",
                "401(k) Contribution",
                "Roth IRA Contribution",
                "Taxes",
                "Living Expenses",
                "Remaining Income"
            ],
            "Annual ($)": [
                annual_salary,
                annual_401k_contribution,
                annual_roth_ira_contribution,
                annual_total_taxes,
                annual_living_expenses,
                annual_remaining_income
            ],
            "Monthly ($)": [
                monthly_gross_income,
                monthly_401k_contribution,
                monthly_roth_ira_contribution,
                monthly_total_taxes,
                monthly_living_expenses,
                monthly_remaining_income
            ],
            "Bi-Weekly ($)": [
                biweekly_gross_income,
                biweekly_401k_contribution,
                biweekly_roth_ira_contribution,
                biweekly_total_taxes,
                biweekly_living_expenses,
                biweekly_remaining_income
            ]
        })

        st.write("Breakdown of Income")
        st.dataframe(breakdown_df)

    with tab2:
        st.title("Expense Tracker")
        
        # Initialize or load expenses
        if 'expenses' not in st.session_state:
            if st.session_state.user_id and st.session_state.user_id > 0:  # Real user
                st.session_state.expenses = database.load_expenses(st.session_state.user_id)
            else:  # Guest user or None
                st.session_state.expenses = {}
        
        # Create expense categories
        expense_categories = {
            "Housing": ["Rent/Mortgage", "Utilities", "Insurance", "Maintenance"],
            "Transportation": ["Car Payment", "Gas", "Insurance", "Maintenance", "Public Transit"],
            "Food": ["Groceries", "Dining Out", "Delivery"],
            "Healthcare": ["Insurance", "Medications", "Doctor Visits"],
            "Entertainment": ["Streaming Services", "Hobbies", "Events"],
            "Personal": ["Clothing", "Personal Care", "Gym"],
            "Debt": ["Credit Cards", "Student Loans", "Personal Loans"],
            "Savings": ["Emergency Fund", "Investment", "Other Savings"],
            "Other": ["Gifts", "Miscellaneous"]
        }
        
        # Create expandable sections for each category
        total_expenses = 0
        for category, items in expense_categories.items():
            with st.expander(f"{category} Expenses"):
                for item in items:
                    key = f"{category}_{item}"
                    amount = st.number_input(
                        item,
                        min_value=0.0,
                        value=st.session_state.expenses.get(key, 0.0),
                        step=10.0,
                        key=key
                    )
                    st.session_state.expenses[key] = amount
                    total_expenses += amount
        
        # Display total expenses
        st.header("Summary")
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Total Monthly Expenses", f"${total_expenses:,.2f}")
            st.metric("Total Annual Expenses", f"${total_expenses * 12:,.2f}")
        
        # Create and display expense breakdown chart
        with col2:
            category_totals = {}
            for category in expense_categories:
                category_total = sum(st.session_state.expenses.get(f"{category}_{item}", 0)
                                   for item in expense_categories[category])
                if category_total > 0:
                    category_totals[category] = category_total
            
            if category_totals:
                fig, ax = plt.subplots(figsize=(8, 8))
                ax.pie(category_totals.values(),
                      labels=category_totals.keys(),
                      autopct='%1.1f%%')
                ax.axis('equal')
                st.pyplot(fig)

        # Save expenses only for real users
        if st.session_state.expenses and st.session_state.user_id and st.session_state.user_id > 0:
            database.save_expenses(st.session_state.user_id, st.session_state.expenses)
