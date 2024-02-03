#### working code copy

import xlsxwriter
import datetime
import calendar
from collections import defaultdict
import pandas as pd
from odoo import models, fields
import numpy as np
from .item import ITEM_TYPE_LIST
import pytz 


df = workbook.add_format({'num_format': 'dd/mm/yy'})
nf = workbook.add_format({'num_format': '0'})
nfi = workbook.add_format({'num_format': '0'})
bold2 = workbook.add_format({'bold': True, 'bg_color': 'black','color': 'white', 'num_format': '0'})
bold3 = workbook.add_format({'num_format': '0', 'bold': True, 'bg_color': 'white', 'color': 'green', 'font_size': 25, 'align': 'center', 'valign': 'vcenter'})
bold4 = workbook.add_format({'num_format': '0','bold': True, 'bg_color': 'green','color': 'black'})
nft = workbook.add_format({'num_format': '0', 'bg_color': 'green'})
purchase_report_format = workbook.add_format({'color': 'blue', 'bold': True})  # Format for Purchase Report
sheet = workbook.add_worksheet( "Purchase Report" )
sheet.merge_range('H1:M1', "Jia Industries Report", bold3)
sheet.merge_range('A2:B2', "Purchase Report", purchase_report_format)

# Write Start and End dates
sheet.write(2, 0, "Start:", bold)
sheet.write(2, 1, o.fromdate, df)
sheet.write(2, 2, "to:", bold)
sheet.write(2, 3, o.todate, df)

# Get the current date and time
download_time = datetime.datetime.now(pytz.timezone('Asia/Kolkata')).strftime("%Y-%m-%d  %I:%M:%S %p")

# Write Download Time and set the column width
sheet.write(4, 0, "Downloaded on:", bold)
sheet.write(4, 1, download_time, df)

# Set the width of the first column to accommodate the date and time
sheet.set_column(0, 0, len("Downloaded on:") + 2)  # Adjust the value as needed

# print("ITEM_TYPE_LIST:", ITEM_TYPE_LIST)
item_type_mapping = dict(ITEM_TYPE_LIST)
selected_date = o.fromdate
financial_year_start = datetime.datetime(selected_date.year - (selected_date.month < 4), 4, 1).date()
financial_year_end = financial_year_start + pd.DateOffset(years=1) - pd.DateOffset(days=1)
financial_year_end = financial_year_end.strftime('%Y-%m-%d')
all_months = pd.date_range(financial_year_start, financial_year_end, freq='MS').strftime('%b%y').tolist()
# print(all_months)

inv = self.env['simrp.purchase'].search([('pdate', '>=', financial_year_start),('pdate', '<=', financial_year_end)])
# print("inv",inv)
sorted_inv = sorted(inv, key=lambda x: x.pdate)# Sort the results based on 'pdate'
adj1= 0 
# inv = self.env['simrp.purchase'].search([('pdate', '>=', financial_year_start),('pdate', '<=', financial_year_end)])

p_reports_data = []
processed_item_types = set()
for p_report in sorted_inv:
    purchase_order = p_report.name
    purchase_date = p_report.pdate   
    
    for record_type, records in [('GRN Record', p_report.grn_s), ('ADV_GRN Record', p_report.advancegrn_s)]:
        if not records:
            continue

        for record in records:
            item_type = record.item_.category.type
            # item_type = item_type_mapping.get(item_type, item_type)  # Map item_type using the dictionary
            item_category = record.item_.category.name
            purchase_amount = record.basicamount if record_type == 'GRN Record' else record.amount
        
            if item_type not in processed_item_types:
                processed_item_types.add(item_type)

            item_name = record.item_.name

            p_reports_data.append({
                'Purchase Order': purchase_order,
                'Purchase Amount': purchase_amount,
                'Purchase Date': purchase_date,
                'Record Type': record_type,
                'Item Type': item_type,
                'Item Name': item_name,
                'Item Category': item_category,
            })
                    

    p_reports_data.append({
                        'Purchase Order': purchase_order,
                        'Purchase Date': purchase_date,
                        'Adj1 Value': p_report.basicamountadj,
                    })


df1 = pd.DataFrame(p_reports_data)

data = [{'Purchase Date': p_report.pdate, 'Expense Account Name': expense.expenseaccount_.name, 'Amount': expense.amount}
        for p_report in sorted_inv for expense in p_report.directpurchase_s]


df = pd.DataFrame(data)

df['Purchase Date'] = pd.to_datetime(df['Purchase Date'])
df['Month Name'] = df['Purchase Date'].dt.strftime('%b')  # Short month names
df['Year'] = df['Purchase Date'].dt.strftime('%y')  # Last two digits of the year
df['Month'] = df['Month Name'] + df['Year']  # Month first and then year
grouped_df = df.groupby(['Expense Account Name', 'Month'])['Amount'].sum().reset_index()
grouped_df['Month'] = pd.Categorical(grouped_df['Month'], categories=sorted(grouped_df['Month'].unique()), ordered=True)
pivot_df = grouped_df.pivot_table(index='Expense Account Name', columns='Month', values='Amount', aggfunc='sum', fill_value=0)
pivot_df['Total'] = pivot_df.sum(axis=1)

# Sort the DataFrame by the 'Total' column in descending order
pivot_df = pivot_df.sort_values(by='Total', ascending=False)

pivot_df.loc['Column Total'] = pivot_df.sum()

pivot_df = pivot_df[sorted(pivot_df.columns[:-1], key=lambda x: datetime.datetime.strptime(x, '%b%y')) + ['Total']]


pivot_df = pivot_df.round(0).astype(int)
pivot_df.replace(0, '', inplace=True)

print(pivot_df.head(10))

start_col = 1

# Write headers
sheet.write(8, 0, 'Expense Account',bold)
for col_num, value in enumerate(pivot_df.columns, start_col):
    sheet.write(8, col_num, value,bold)

# Write data from pivot_df to the sheet starting from column 2
for row_num, (index, row) in enumerate(pivot_df.iterrows(), start=9):
    sheet.write(row_num, 0, index[:18], None)  # Write Expense Account Name in the first column
    for col_num, value in enumerate(row, start_col):
        sheet.write(row_num, col_num, value)
        if index == 'Column Total':
            for col_num, value in enumerate(row, start_col):
                if not pd.isna(value):  # Check if the cell is not empty
                    sheet.write(row_num, col_num, value, bold)



























































