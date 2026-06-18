import csv
import random
import datetime
import os

random.seed(42)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SALES_2017 = os.path.join(BASE_DIR, 'Datasets', 'AdventureWorks_Sales_2017.csv')
SALES_2018 = os.path.join(BASE_DIR, 'Datasets', 'AdventureWorks_Sales_2018.csv')
CALENDAR   = os.path.join(BASE_DIR, 'Datasets', 'AdventureWorks_Calendar.csv')

FIELDNAMES = ['OrderDate', 'StockDate', 'OrderNumber', 'ProductKey',
              'CustomerKey', 'TerritoryKey', 'OrderLineItem', 'OrderQuantity']


def fmt(d):
    return f"{d.month}/{d.day}/{d.year}"


def rdate(start, end):
    return start + datetime.timedelta(days=random.randint(0, (end - start).days))


# ── 1. Read ProductKeys dynamically from Sales_2017 ──────────────────────────
product_keys = []
seen = set()
with open(SALES_2017, newline='') as f:
    for row in csv.DictReader(f):
        pk = int(row['ProductKey'])
        if pk not in seen:
            seen.add(pk)
            product_keys.append(pk)
product_keys.sort()

# ── 2. Generate 2018 sales rows ───────────────────────────────────────────────
ORDER_DATE_START = datetime.date(2018, 1, 1)
ORDER_DATE_END   = datetime.date(2018, 12, 31)
STOCK_DATE_START = datetime.date(2001, 1, 1)
STOCK_DATE_END   = datetime.date(2004, 12, 31)

rows = []
order_num = 74148

while len(rows) < 1000:
    num_items    = random.randint(1, 4)
    order_date   = rdate(ORDER_DATE_START, ORDER_DATE_END)
    customer_key = random.randint(11001, 29480)
    territory_key = random.randint(1, 10)
    order_number  = f"SO{order_num}"

    for line_item in range(1, num_items + 1):
        rows.append([
            fmt(order_date),
            fmt(rdate(STOCK_DATE_START, STOCK_DATE_END)),
            order_number,
            random.choice(product_keys),
            customer_key,
            territory_key,
            line_item,
            random.choice([1, 2, 3]),
        ])

    order_num += 1

with open(SALES_2018, 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(FIELDNAMES)
    w.writerows(rows)

# ── 3. Extend Calendar with all 2018 dates ────────────────────────────────────
cal_dates = []
d = datetime.date(2018, 1, 1)
while d <= datetime.date(2018, 12, 31):
    cal_dates.append(fmt(d))
    d += datetime.timedelta(days=1)

# Ensure the existing file ends with a newline before appending
with open(CALENDAR, 'rb') as f:
    f.seek(-1, 2)
    needs_newline = f.read(1) not in (b'\n', b'\r')

with open(CALENDAR, 'a', newline='') as f:
    if needs_newline:
        f.write('\n')
    w = csv.writer(f)
    for ds in cal_dates:
        w.writerow([ds])

# ── 4. Summary ────────────────────────────────────────────────────────────────
order_dates  = [datetime.datetime.strptime(r[0], '%m/%d/%Y').date() for r in rows]
first_order  = rows[0][2]
last_order   = rows[-1][2]

print(f"Sales 2018 created : {len(rows)} rows")
print(f"OrderDate range    : {fmt(min(order_dates))} – {fmt(max(order_dates))}")
print(f"OrderNumber range  : {first_order} – {last_order}")
print(f"Unique ProductKeys : {len(product_keys)}")
print(f"Calendar extended  : {len(cal_dates)} dates appended (1/1/2018 – 12/31/2018)")
