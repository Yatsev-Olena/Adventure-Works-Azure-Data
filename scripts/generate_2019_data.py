import csv
import random
import datetime
import os

random.seed(42)

# scripts/ lives one level below the repo root; data lives in <root>/Datasets
BASE_DIR    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SALES_2017  = os.path.join(BASE_DIR, 'Datasets', 'AdventureWorks_Sales_2017.csv')
SALES_2018  = os.path.join(BASE_DIR, 'Datasets', 'AdventureWorks_Sales_2018.csv')
SALES_2019  = os.path.join(BASE_DIR, 'Datasets', 'AdventureWorks_Sales_2019.csv')
CALENDAR    = os.path.join(BASE_DIR, 'Datasets', 'AdventureWorks_Calendar.csv')

FIELDNAMES = ['OrderDate', 'StockDate', 'OrderNumber', 'ProductKey',
              'CustomerKey', 'TerritoryKey', 'OrderLineItem', 'OrderQuantity']


def fmt(d):
    return f"{d.month}/{d.day}/{d.year}"


def rdate(start, end):
    return start + datetime.timedelta(days=random.randint(0, (end - start).days))


# ── 1. Read ProductKeys dynamically from Sales_2017 (used as the template) ────
product_keys = []
seen = set()
with open(SALES_2017, newline='') as f:
    for row in csv.DictReader(f):
        pk = int(row['ProductKey'])
        if pk not in seen:
            seen.add(pk)
            product_keys.append(pk)
product_keys.sort()

# ── 2. Determine the next free OrderNumber across all existing sales files ────
#     OrderNumber is part of the composite PK (OrderNumber + OrderLineItem),
#     so the 2019 sequence must start strictly above every existing value.
max_order_num = 0
for path in (SALES_2017, SALES_2018):
    if not os.path.exists(path):
        continue
    with open(path, newline='') as f:
        for row in csv.DictReader(f):
            n = int(row['OrderNumber'].lstrip('SO'))
            if n > max_order_num:
                max_order_num = n

order_num = max_order_num + 1  # first unused OrderNumber

# ── 3. Generate 2019 sales rows ───────────────────────────────────────────────
ORDER_DATE_START = datetime.date(2019, 1, 1)
ORDER_DATE_END   = datetime.date(2019, 12, 31)
STOCK_DATE_START = datetime.date(2001, 1, 1)
STOCK_DATE_END   = datetime.date(2004, 12, 31)

rows = []
while len(rows) < 1000:
    num_items     = random.randint(1, 4)
    order_date    = rdate(ORDER_DATE_START, ORDER_DATE_END)
    customer_key  = random.randint(11001, 29480)
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

with open(SALES_2019, 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(FIELDNAMES)
    w.writerows(rows)

# ── 4. Extend Calendar with all 2019 dates (no gap: current data ends 12/31/2018) ─
existing_dates = set()
with open(CALENDAR, newline='') as f:
    for row in csv.DictReader(f):
        if row['Date'].strip():
            existing_dates.add(row['Date'].strip())

cal_dates = []
d = datetime.date(2019, 1, 1)
while d <= datetime.date(2019, 12, 31):
    ds = fmt(d)
    if ds not in existing_dates:          # PK guard: never duplicate a Date
        cal_dates.append(ds)
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

# ── 5. Summary ────────────────────────────────────────────────────────────────
order_dates = [datetime.datetime.strptime(r[0], '%m/%d/%Y').date() for r in rows]
first_order = rows[0][2]
last_order  = rows[-1][2]

print(f"Sales 2019 created : {len(rows)} rows")
print(f"OrderDate range    : {fmt(min(order_dates))} - {fmt(max(order_dates))}")
print(f"OrderNumber range  : {first_order} - {last_order} (started at {max_order_num + 1})")
print(f"Unique ProductKeys : {len(product_keys)}")
print(f"Calendar extended  : {len(cal_dates)} dates appended (1/1/2019 - 12/31/2019)")
