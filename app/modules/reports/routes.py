from flask import Blueprint, render_template, request, session
from datetime import datetime, timedelta
from collections import defaultdict
from calendar import monthrange
from pymongo import MongoClient
import os
import pdfkit
from flask import make_response
import json

reports_bp = Blueprint('reports_bp', __name__, url_prefix='/reports')
client = MongoClient(os.getenv("MONGO_KEY"))
db = client.get_database("dataGrow")



def match_month(date_obj, selected_month):
    try:
        if isinstance(date_obj, str):
            date_obj = datetime.strptime(date_obj, "%Y-%m-%d")
        return date_obj.strftime("%Y-%m") == selected_month
    except Exception:
        return False

@reports_bp.route("/")
def reports_home():
    return render_template("reports.html")

@reports_bp.route("/monthly")
def monthly_income_expense_report():
    # קבלת השנה והחודש מהמשתמש
    year = request.args.get("year", datetime.now().year)
    month_num = request.args.get("month", datetime.now().strftime("%m"))
    selected_month = f"{year}-{month_num}"

    user_role = session.get("role")
    user_email = session.get("email")
    manager_email = session.get("manager_email")
    filter_email = user_email if user_role == "manager" else manager_email

    report_data = generate_monthly_report_data(selected_month, filter_email)

    return render_template("monthly_income_expense.html",
                           selected_month=selected_month,
                           selected_year=year,
                           selected_month_num=month_num,
                           datetime=datetime, 
                           **report_data)

@reports_bp.route("/export_pdf")
def export_pdf():
    month = request.args.get("month", datetime.now().strftime("%Y-%m"))

    base_url = request.host_url.rstrip('/')
    report_url = f"{base_url}/reports/monthly?month={month}"

    options = {
        'enable-local-file-access': '',
        'encoding': 'UTF-8'
    }

    try:
        pdf = pdfkit.from_url(report_url, False, options=options)
    except Exception as e:
        return f"שגיאה בהמרת PDF: {e}", 500

    response = make_response(pdf)
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = "attachment; filename=monthly_report.pdf"
    return response



def generate_monthly_report_data(month, filter_email):
    from calendar import monthrange

    total_expenses = total_income = 0
    total_fuel = total_insurance = total_irrigation = 0
    total_purchases = total_services = total_tests = 0
    total_crop_income = 0
    default_price_for_month = 0
    price_used_in_irrigation = None

    year, month_num = int(month[:4]), int(month[5:])
    last_day = monthrange(year, month_num)[1]
    month_start_date = datetime.strptime(f"{month}-01", "%Y-%m-%d")
    month_end_date = datetime.strptime(f"{month}-{last_day}", "%Y-%m-%d")

    water_prices = sorted(
        db.water.find({"email": filter_email}),
        key=lambda x: datetime.strptime(x.get("date", ""), "%Y-%m-%d")
    )
    for p in reversed(water_prices):
        try:
            water_date = datetime.strptime(p["date"], "%Y-%m-%d")
            if water_date <= month_end_date:
                default_price_for_month = float(p.get("price", 0))
                break
        except:
            continue

    # דוח חודשי
    for item in db.fuel.find({"email": filter_email}):
        refuel_type = item.get("refuel_type")
        cost = float(item.get("cost", 0))
        amount = float(item.get("fuel_amount", 0))
        if refuel_type == "דלקן" and item.get("month", "").startswith(month):
            total_fuel += cost * amount
        elif refuel_type == "ידני" and match_month(item.get("refuel_date"), month):
            total_fuel += cost * amount

    for item in db.insurance_history.find({"manager_email": filter_email}):
        if match_month(item.get("insurance_date"), month):
            total_insurance += float(item.get("insurance_cost", 0))

    for item in db.irrigation.find({"email": filter_email}):
        irrigation_date = item.get("Irrigation_date")
        if not irrigation_date:
            continue
        try:
            if isinstance(irrigation_date, str):
                irrigation_date = datetime.strptime(irrigation_date, "%Y-%m-%d %H:%M:%S")
        except:
            continue
        if match_month(irrigation_date, month):
            quantity = float(item.get("quantity_irrigation", 0))
            irrigation_price = 0
            for p in reversed(water_prices):
                try:
                    water_date = datetime.strptime(p["date"], "%Y-%m-%d")
                    if water_date <= irrigation_date:
                        irrigation_price = float(p.get("price", 0))
                        break
                except:
                    continue
            total_irrigation += quantity * irrigation_price
            price_used_in_irrigation = irrigation_price

    for item in db.purchases.find({"email": filter_email}):
        if match_month(item.get("purchase_date"), month):
            try:
                q = float(item.get("quantity", 0))
                up = float(item.get("unit_price", 0))
                total_purchases += q * up
            except:
                pass

    for item in db.service_history.find({"manager_email": filter_email}):
        if match_month(item.get("service_date"), month):
            total_services += float(item.get("service_cost", 0))

    for item in db.test_history.find({"manager_email": filter_email}):
        if match_month(item.get("test_date"), month):
            total_tests += float(item.get("test_cost", 0))

    for plot in db.plots.find({"manager_email": filter_email}):
        if match_month(plot.get("harvest_date"), month):
            try:
                yield_amount = float(plot.get("crop_yield", 0))
                yield_price = float(plot.get("price_yield", 0))
                total_crop_income += yield_amount * yield_price
            except:
                continue

    total_expenses = sum([
        total_fuel, total_insurance, total_irrigation,
        total_purchases, total_services, total_tests
    ])
    total_income = total_crop_income
    final_water_price_display = price_used_in_irrigation if price_used_in_irrigation is not None else default_price_for_month

    expenses_by_category = {
        'דלק': round(total_fuel, 2),
        'ביטוחים': round(total_insurance, 2),
        f'השקייה (תעריף {round(final_water_price_display, 2)}₪)': round(total_irrigation, 2),
        'רכישות': round(total_purchases, 2),
        'טיפולים רכבים': round(total_services, 2),
        'טסטים': round(total_tests, 2),
    }
    income_by_category = {
        'יבול': round(total_crop_income, 2)
    }

    # דוח שנתי לגרף
    today = datetime.today().replace(day=1)
    months_list = [(today - timedelta(days=30 * i)).strftime("%Y-%m") for i in reversed(range(12))]
    yearly_data = {m: {"income": 0, "expense": 0} for m in months_list}

    for plot in db.plots.find({"manager_email": filter_email}):
        harvest_date = plot.get("harvest_date")
        try:
            if harvest_date:
                if isinstance(harvest_date, str):
                    harvest_date = datetime.strptime(harvest_date, "%Y-%m-%d")
                key = harvest_date.strftime("%Y-%m")
                if key in yearly_data:
                    yield_amount = float(plot.get("crop_yield", 0))
                    yield_price = float(plot.get("price_yield", 0))
                    yearly_data[key]["income"] += yield_amount * yield_price
        except:
            continue

    for item in db.fuel.find({"email": filter_email}):
        try:
            refuel_type = item.get("refuel_type")
            cost = float(item.get("cost", 0))
            amount = float(item.get("fuel_amount", 0))
            month_str = item.get("month", "") if refuel_type == "דלקן" else item.get("refuel_date", "")[:7]
            if month_str in yearly_data:
                yearly_data[month_str]["expense"] += cost * amount
        except:
            continue

    for item in db.insurance_history.find({"manager_email": filter_email}):
        try:
            d = datetime.strptime(item.get("insurance_date", ""), "%Y-%m-%d")
            key = d.strftime("%Y-%m")
            if key in yearly_data:
                yearly_data[key]["expense"] += float(item.get("insurance_cost", 0))
        except:
            continue

    for item in db.irrigation.find({"email": filter_email}):
        try:
            irrigation_date = datetime.strptime(item.get("Irrigation_date", ""), "%Y-%m-%d %H:%M:%S")
            key = irrigation_date.strftime("%Y-%m")
            if key in yearly_data:
                quantity = float(item.get("quantity_irrigation", 0))
                irrigation_price = 0
                for p in reversed(water_prices):
                    try:
                        water_date = datetime.strptime(p["date"], "%Y-%m-%d")
                        if water_date <= irrigation_date:
                            irrigation_price = float(p.get("price", 0))
                            break
                    except:
                        continue
                yearly_data[key]["expense"] += quantity * irrigation_price
        except:
            continue

    for item in db.purchases.find({"email": filter_email}):
        try:
            d = datetime.strptime(item.get("purchase_date", ""), "%Y-%m-%d")
            key = d.strftime("%Y-%m")
            if key in yearly_data:
                q = float(item.get("quantity", 0))
                up = float(item.get("unit_price", 0))
                yearly_data[key]["expense"] += q * up
        except:
            continue

    for item in db.service_history.find({"manager_email": filter_email}):
        try:
            d = datetime.strptime(item.get("service_date", ""), "%Y-%m-%d")
            key = d.strftime("%Y-%m")
            if key in yearly_data:
                yearly_data[key]["expense"] += float(item.get("service_cost", 0))
        except:
            continue

    for item in db.test_history.find({"manager_email": filter_email}):
        try:
            d = datetime.strptime(item.get("test_date", ""), "%Y-%m-%d")
            key = d.strftime("%Y-%m")
            if key in yearly_data:
                yearly_data[key]["expense"] += float(item.get("test_cost", 0))
        except:
            continue

    yearly_data_json = json.dumps([
        {
            "month": m,
            "income": round(yearly_data[m]["income"], 2),
            "expense": round(yearly_data[m]["expense"], 2)
        }
        for m in months_list
    ])
    # גרף עוגה משולב להכנסות והוצאות, ממוין
    combined_pie_data = [
        {"category": k, "amount": v, "type": "income"} for k, v in income_by_category.items()
    ] + [
        {"category": k, "amount": v, "type": "expense"} for k, v in expenses_by_category.items()
    ]

    combined_pie_data_sorted = sorted(combined_pie_data, key=lambda x: x["amount"], reverse=True)

    monthly_pie_data = json.dumps({
        "labels": [item["category"] for item in combined_pie_data_sorted],
        "data": [item["amount"] for item in combined_pie_data_sorted],
        "colors": ['#4CAF50' if item["type"] == "income" else '#E53935' for item in combined_pie_data_sorted]
    }, ensure_ascii=False)

    return {
        "total_expenses": round(total_expenses, 2),
        "total_income": round(total_income, 2),
        "expenses_by_category": expenses_by_category,
        "income_by_category": income_by_category,
        "yearly_data_json": yearly_data_json,
        "monthly_pie_data": monthly_pie_data  # זה החדש לגרף העוגה
    }


@reports_bp.route("/yearly")
def yearly_report():
    selected_year = int(request.args.get("year", datetime.now().year))

    user_role = session.get("role")
    user_email = session.get("email")
    manager_email = session.get("manager_email")
    filter_email = user_email if user_role == "manager" else manager_email

    start_date = datetime(selected_year, 1, 1)
    end_date = datetime(selected_year, 12, 31)

    income_by_category = defaultdict(float)
    expense_by_category = defaultdict(float)

    # יבול כהכנסה
    for plot in db.plots.find({"manager_email": filter_email}):
        try:
            harvest_date = plot.get("harvest_date")
            if isinstance(harvest_date, str):
                harvest_date = datetime.strptime(harvest_date, "%Y-%m-%d")
            if start_date <= harvest_date <= end_date:
                income = float(plot.get("crop_yield", 0)) * float(plot.get("price_yield", 0))
                income_by_category["יבול"] += income
        except:
            continue

    # דלק
    for item in db.fuel.find({"email": filter_email}):
        try:
            refuel_date_str = item.get("refuel_date")
            refuel_type = item.get("refuel_type")
            if refuel_type == "דלקן":
                refuel_date_str = f"{item.get('month', '')}-01"
            refuel_date = datetime.strptime(refuel_date_str, "%Y-%m-%d")
            if start_date <= refuel_date <= end_date:
                cost = float(item.get("cost", 0)) * float(item.get("fuel_amount", 0))
                expense_by_category["דלק"] += cost
        except:
            continue

    # ביטוחים
    for item in db.insurance_history.find({"manager_email": filter_email}):
        try:
            d = datetime.strptime(item.get("insurance_date", ""), "%Y-%m-%d")
            if start_date <= d <= end_date:
                expense_by_category["ביטוחים"] += float(item.get("insurance_cost", 0))
        except:
            continue

    # השקיה לפי תעריף מים
    expense_by_category["השקיה"] += calculate_yearly_irrigation_cost(filter_email, start_date, end_date)

    # רכישות
    for item in db.purchases.find({"email": filter_email}):
        try:
            d = datetime.strptime(item.get("purchase_date", ""), "%Y-%m-%d")
            if start_date <= d <= end_date:
                q = float(item.get("quantity", 0))
                up = float(item.get("unit_price", 0))
                expense_by_category["רכישות"] += q * up
        except:
            continue

    # טיפולים
    for item in db.service_history.find({"manager_email": filter_email}):
        try:
            d = datetime.strptime(item.get("service_date", ""), "%Y-%m-%d")
            if start_date <= d <= end_date:
                expense_by_category["טיפולים רכבים"] += float(item.get("service_cost", 0))
        except:
            continue

    # טסטים
    for item in db.test_history.find({"manager_email": filter_email}):
        try:
            d = datetime.strptime(item.get("test_date", ""), "%Y-%m-%d")
            if start_date <= d <= end_date:
                expense_by_category["טסטים"] += float(item.get("test_cost", 0))
        except:
            continue

    total_income = sum(income_by_category.values())
    total_expenses = sum(expense_by_category.values())

    # הכנת גרף עוגה
    pie_income = [{"category": k, "amount": round(v, 2)} for k, v in income_by_category.items()]
    pie_expense = [{"category": k, "amount": round(v, 2)} for k, v in expense_by_category.items()]

    # גרף עקומה של שלוש השנים האחרונות
    balance_data = []
    for y in range(selected_year - 2, selected_year + 1):
        sy = datetime(y, 1, 1)
        ey = datetime(y, 12, 31)
        income, expense = 0, 0

        # הכנסות מיבול
        for plot in db.plots.find({"manager_email": filter_email}):
            try:
                d = plot.get("harvest_date")
                if isinstance(d, str):
                    d = datetime.strptime(d, "%Y-%m-%d")
                if sy <= d <= ey:
                    income += float(plot.get("crop_yield", 0)) * float(plot.get("price_yield", 0))
            except:
                continue

        # הוצאות - דלק
        for item in db.fuel.find({"email": filter_email}):
            try:
                refuel_date_str = item.get("refuel_date")
                refuel_type = item.get("refuel_type")
                if refuel_type == "דלקן":
                    refuel_date_str = f"{item.get('month', '')}-01"
                d = datetime.strptime(refuel_date_str, "%Y-%m-%d")
                if sy <= d <= ey:
                    expense += float(item.get("cost", 0)) * float(item.get("fuel_amount", 0))
            except:
                continue

        # הוצאות - ביטוחים
        for item in db.insurance_history.find({"manager_email": filter_email}):
            try:
                d = datetime.strptime(item.get("insurance_date", ""), "%Y-%m-%d")
                if sy <= d <= ey:
                    expense += float(item.get("insurance_cost", 0))
            except:
                continue

        # הוצאות - רכישות
        for item in db.purchases.find({"email": filter_email}):
            try:
                d = datetime.strptime(item.get("purchase_date", ""), "%Y-%m-%d")
                if sy <= d <= ey:
                    q = float(item.get("quantity", 0))
                    up = float(item.get("unit_price", 0))
                    expense += q * up
            except:
                continue

        # הוצאות - שירותים
        for item in db.service_history.find({"manager_email": filter_email}):
            try:
                d = datetime.strptime(item.get("service_date", ""), "%Y-%m-%d")
                if sy <= d <= ey:
                    expense += float(item.get("service_cost", 0))
            except:
                continue

        # הוצאות - טסטים
        for item in db.test_history.find({"manager_email": filter_email}):
            try:
                d = datetime.strptime(item.get("test_date", ""), "%Y-%m-%d")
                if sy <= d <= ey:
                    expense += float(item.get("test_cost", 0))
            except:
                continue

        # הוצאות - השקיה
        expense += calculate_yearly_irrigation_cost(filter_email, sy, ey)

        # תזרים: הכנסות פחות הוצאות
        balance_data.append({"year": str(y), "balance": round(income - expense, 2)})

    yearly_pie_data = json.dumps({
        "labels": [x["category"] for x in pie_income + pie_expense],
        "data": [x["amount"] for x in pie_income + pie_expense],
        "colors": ['#4CAF50'] * len(pie_income) + ['#E53935'] * len(pie_expense)
    }, ensure_ascii=False)
    
    yearly_trend_data = json.dumps({
        "labels": [str(item["year"]) for item in balance_data],
        "data": [item["balance"] for item in balance_data]
    }, ensure_ascii=False)

    return render_template("yearly_income_expense.html",
                        datetime=datetime,
                        selected_year=selected_year,
                        pie_income=pie_income,
                        pie_expense=pie_expense,
                        total_income=round(total_income, 2),
                        total_expenses=round(total_expenses, 2),
                        expenses_by_category=expense_by_category,
                        income_by_category=income_by_category,
                        balance_data=json.dumps(balance_data, ensure_ascii=False),
                        yearly_pie_data=yearly_pie_data,
                        yearly_trend_data=yearly_trend_data)





def calculate_yearly_irrigation_cost(email, start_date, end_date):
    irrigation_total = 0.0
    irrigations = db.irrigation.find({
        "email": email,
        "Irrigation_date": {"$gte": start_date.strftime("%Y-%m-%d"), "$lte": end_date.strftime("%Y-%m-%d")}
    })

    water_prices = sorted(
        db.water.find({"email": email}),
        key=lambda x: datetime.strptime(x.get("date", "1970-01-01"), "%Y-%m-%d")
    )

    for item in irrigations:
        irrigation_date_str = item.get("Irrigation_date")
        quantity = float(item.get("quantity_irrigation", 0))

        if not irrigation_date_str:
            continue

        try:
            irrigation_date = datetime.strptime(irrigation_date_str, "%Y-%m-%d %H:%M:%S")
        except:
            try:
                irrigation_date = datetime.strptime(irrigation_date_str, "%Y-%m-%d")
            except:
                continue

        applicable_price = 0
        for p in reversed(water_prices):
            try:
                water_date = datetime.strptime(p["date"], "%Y-%m-%d")
                if water_date <= irrigation_date:
                    applicable_price = float(p.get("price", 0))
                    break
            except:
                continue

        irrigation_total += quantity * applicable_price

    return round(irrigation_total, 2)


@reports_bp.route("/export_yearly_pdf")
def export_yearly_pdf():
    year = request.args.get("year", datetime.now().year)

    base_url = request.host_url.rstrip('/')
    report_url = f"{base_url}/reports/yearly?year={year}"

    options = {
        'enable-local-file-access': '',
        'encoding': 'UTF-8'
    }

    try:
        pdf = pdfkit.from_url(report_url, False, options=options)
    except Exception as e:
        return f"שגיאה בהמרת PDF: {e}", 500

    response = make_response(pdf)
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = f"attachment; filename=yearly_report_{year}.pdf"
    return response