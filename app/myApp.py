import streamlit as st
import pandas as pd
import numpy as np
import numpy_financial as fin

st.set_page_config(page_title = "Rent vs Buy", page_icon="🏠", layout="wide")

st.title("🏠 Should you rent or buy?")

## Create two columns, one for tabular inputs and results and another for charts and visualizations
inputs, outputs = st.columns(2)

with inputs:
    ## INPUTS SECTION
    st.subheader("Inputs")
    with st.expander("Inputs", expanded=True): ## This expander section is for inputs
        purchasescenario, taxes, rent, sale = st.tabs(["Purchase Details",
                                                    "Taxes & Maintanence",
                                                    "Rent Details",
                                                    "Sale & Performance Details"])
        
        ###This entire section is for inputs
        with purchasescenario:
            purchase_price = st.number_input("Purchase Price ($)", min_value=0, value=800000, format='%i', step=1, help="Total home price in dollars")
            loan_term = st.number_input("Loan Term (years)", min_value=1, max_value=60, step=1, value=15, help="Loan term in years")
            loan_rate = st.number_input("Loan Rate (%)", min_value=0., max_value=1., step=0.005, value = 0.055, format="%.3f", help="Loan rate (decimal between 0 - 1)")
            down_paid = st.number_input("Down Paid (% of purchase price)", min_value=0., max_value=0.99, step=0.01, value=0.2, format="%.2f", help="Down paid in percent")
            assets_pledged = st.number_input("Assets Pledged (% of purchase price)", min_value=0., max_value=0.99, value=0., step=0.01, format="%.2f", help="Assets pledged in percent")
        with taxes:
            property_tax = st.number_input("Property Tax (%)", min_value=0., max_value=1., value=0.01, step=0.01, format="%.2f", help="Property tax rate in percent")
            maintanence = st.number_input("Maintance (%)", min_value=0., max_value=1., value=0.01, step=0.005, format="%.3f", help="Expected annual maintanence cost as a percentage of home price")
            insurance = st.number_input("Annual Home Insurance ($)", min_value=0, max_value=50000, value = 900, step=1, format="%i", help="Expected annual home insurance cost")
            annual_expense = purchase_price*(property_tax+maintanence) + insurance
            st.write("Estimated annual expense of " + '${:,.2f}'.format(annual_expense))
        with rent:
            monthly_rent = st.number_input("Monthly Rent ($)", min_value=0, max_value=20000, step=1, value=4000, format="%i", help="Monthly rent paid")
            rent_growth = st.number_input("Annual Rent Hike (%)", min_value=0., max_value=1., step=0.001, value=0.015, format="%.3f", help="Expected annual rent increase in percent")
        with sale:
            sell_after = st.number_input("Sell after (years)", min_value=1, max_value=40, step=1, value=10, format="%i", help="After how many years do you expect to sell?")
            home_appreciation = st.number_input('Annual Home Appreciation (%)', min_value=0., max_value=1., step=0.001, value=0.035, format="%.3f", help="Expected annual home appreciation")
            asset_appreciation = st.number_input('Annual Asset Appreciation (%)', min_value=0., max_value=1., step=0.001, value=0.05, format="%.3f", help="Expected annual asset appreciation")
            st.write("Expected home value appreciation of " + '${:,.2f}'.format(-fin.fv(home_appreciation,sell_after,0,purchase_price,0)-purchase_price))

with outputs:
    
    ## RESULTS SECTION
    st.subheader("Results")


    ## Calculations for mortgage information & Final results
    mortgage_life = min(sell_after, loan_term) ## If selling house after length of mortgage ensure no extra payments
    mortgage_data = {"Monthly Payments": fin.pmt(loan_rate/12,loan_term*12,-(purchase_price*(1-down_paid))),
                     "Interest Paid": fin.ipmt(loan_rate/12, np.arange(mortgage_life*12)+1, loan_term*12,-(purchase_price*(1-down_paid))).sum(),
                     "Principle Paid": fin.ppmt(loan_rate/12, np.arange(mortgage_life*12)+1, loan_term*12,-(purchase_price*(1-down_paid))).sum(),
                     "Total Payments": fin.pmt(loan_rate/12,loan_term*12,-(purchase_price*(1-down_paid)))*mortgage_life*12,
                     "Principle Owed": purchase_price*(1-down_paid) - fin.ppmt(loan_rate/12, np.arange(mortgage_life*12)+1, loan_term*12,-(purchase_price*(1-down_paid))).sum()}
    
    performance_data = {"Rent not Spent": -fin.fv(rent_growth,sell_after,monthly_rent*12,0,0),
                        "Taxes and Maintanence": annual_expense*sell_after,
                        "Operating Cash Flow B/(w)": -fin.fv(rent_growth,sell_after,monthly_rent*12,0,0) - annual_expense*sell_after,
                        "Home Value at Sale": -fin.fv(home_appreciation,sell_after,0,purchase_price,0)}
    
    performance_data["Cash Proceeds after Repayment"] = performance_data["Home Value at Sale"] - mortgage_data["Principle Owed"]
    performance_data["Total Cash Contributed"] = mortgage_data["Total Payments"]+purchase_price*(down_paid)
    performance_data["Cash on Cash Return"] = performance_data["Cash Proceeds after Repayment"] - performance_data["Total Cash Contributed"]
    performance_data["Return on Assets"] = -fin.fv(asset_appreciation,sell_after,0,purchase_price*(assets_pledged),0)-purchase_price*(assets_pledged)
    performance_data["Change in Net Worth"] = performance_data["Operating Cash Flow B/(w)"] + performance_data["Cash on Cash Return"] + performance_data["Return on Assets"]
    
    mortgage_df = pd.DataFrame([mortgage_data]).T
    mortgage_df.columns = ["Values"]
    mortgage_df = mortgage_df.style.format('$ {0:,.2f}')

    performance_df = pd.DataFrame([performance_data]).T
    performance_df.columns = ["Values"]
    performance_df = performance_df.style.format('$ {0:,.0f}')
    

    ## Display results
    with st.expander("Summary", expanded=True):
        performance_summary, mortgage_summary = st.tabs(["Performance Summary",
                                                         "Mortgage Summary"])
        
        with mortgage_summary: ## Basic mortgage calculator functions
            st.table(mortgage_df)

        ## Summarized outputs with conditionals
        with performance_summary:
            if performance_data["Change in Net Worth"] > 0:
                message = "You would be " + '${:,.0f}'.format(performance_data["Change in Net Worth"]) + " wealthier buying than if you rented!"
                st.success(message, icon="🏠")
                if (performance_data["Operating Cash Flow B/(w)"] > 0):
                    if (performance_data["Cash on Cash Return"] > 0):
                        st.write("You are " + '\${:,.0f}'.format(performance_data["Change in Net Worth"]) + " wealthier because you saved " + '\${:,.0f}'.format(performance_data["Operating Cash Flow B/(w)"]) + " in rent and made " + '\${:,.0f}'.format(performance_data["Cash on Cash Return"]) + " on sale of the house")
                    else:
                        st.write("You are " + '\${:,.0f}'.format(performance_data["Change in Net Worth"]) + " wealthier because while you lost " + '\${:,.0f}'.format(-performance_data["Cash on Cash Return"]) + " on sale of the house" + " you saved " + '\${:,.0f}'.format(performance_data["Operating Cash Flow B/(w)"]) + " in rent")
                else:
                    if (performance_data["Cash on Cash Return"] > 0):
                        st.write("You are " + '\${:,.0f}'.format(performance_data["Change in Net Worth"]) + " wealthier because while you lost " + '\${:,.0f}'.format(-performance_data["Operating Cash Flow B/(w)"]) + " on expenses" + " you made " + '\${:,.0f}'.format(performance_data["Cash on Cash Return"]) + " on sale of the house")                    
                st.divider()
            else:
                st.warning("You would be " + '\${:,.0f}'.format(-performance_data["Change in Net Worth"]) + " wealthier renting.")

            st.write("You saved " + '\${:,.0f}'.format(performance_data["Rent not Spent"]) + " in rent not spent but paid " + '\${:,.0f}'.format(performance_data["Taxes and Maintanence"]) + " in taxes, maintanence, insurance")
            if performance_data["Operating Cash Flow B/(w)"] > 0:
                st.write("Which means " + '\${:,.0f}'.format(performance_data["Operating Cash Flow B/(w)"]) + " more in your pocket")
            else:
                st.write("Which means you spent " + '\${:,.0f}'.format(-performance_data["Operating Cash Flow B/(w)"]) + " more than renting")
            
            st.divider()

            if performance_data["Cash on Cash Return"] > 0:
                st.write("You sold your house for " + '\${:,.0f}'.format(performance_data["Home Value at Sale"]) + " but had to pay off principle of " + '\${:,.0f}'.format(mortgage_data["Principle Owed"]))
                st.write("That means you have " + '\${:,.0f}'.format(performance_data["Cash Proceeds after Repayment"]) + " in your pocket" + " and you paid " + '\${:,.0f}'.format(performance_data["Total Cash Contributed"]) + " on your mortgage")
                st.write("Which means you made " + '\${:,.0f}'.format(performance_data["Cash on Cash Return"]) + " on sale of the house")
                st.divider()
                
            else:
                st.write("You sold your house for " + '\${:,.0f}'.format(performance_data["Home Value at Sale"]) + " but had to pay off principle of " + '\${:,.0f}'.format(mortgage_data["Principle Owed"]))
                st.write("That means you have " + '\${:,.0f}'.format(performance_data["Cash Proceeds after Repayment"]) + " in your pocket" + " but you you paid " + '\${:,.0f}'.format(performance_data["Total Cash Contributed"]) + " on your mortgage")
                st.write("Which means you lost " + '\${:,.0f}'.format(-performance_data["Cash on Cash Return"]) + " on the sale of your house")
                st.divider()
                
            st.table(performance_df)