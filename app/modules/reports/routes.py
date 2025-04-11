from flask import Blueprint, render_template, request, session
from datetime import datetime
from calendar import monthrange
from pymongo import MongoClient
import os
import pdfkit
from flask import make_response

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

    # תעריפי מים
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

    # דלק
    for item in db.fuel.find({"email": filter_email}):
        refuel_type = item.get("refuel_type")
        cost = float(item.get("cost", 0))
        amount = float(item.get("fuel_amount", 0))
        if refuel_type == "דלקן" and item.get("month", "").startswith(month):
            total_fuel += cost * amount
        elif refuel_type == "ידני" and match_month(item.get("refuel_date"), month):
            total_fuel += cost * amount

    # ביטוחים
    for item in db.insurance_history.find({"manager_email": filter_email}):
        if match_month(item.get("insurance_date"), month):
            total_insurance += float(item.get("insurance_cost", 0))

    # השקיה
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

    # רכישות
    for item in db.purchases.find({"email": filter_email}):
        if match_month(item.get("purchase_date"), month):
            try:
                q = float(item.get("quantity", 0))
                up = float(item.get("unit_price", 0))
                total_purchases += q * up
            except:
                pass

    # טיפולים
    for item in db.service_history.find({"manager_email": filter_email}):
        if match_month(item.get("service_date"), month):
            total_services += float(item.get("service_cost", 0))

    # טסטים
    for item in db.test_history.find({"manager_email": filter_email}):
        if match_month(item.get("test_date"), month):
            total_tests += float(item.get("test_cost", 0))

    # יבול
    for plot in db.plots.find({"manager_email": filter_email}):
        if match_month(plot.get("harvest_date"), month):
            try:
                yield_amount = float(plot.get("crop_yield", 0))
                yield_price = float(plot.get("price_yield", 0))
                total_crop_income += yield_amount * yield_price
            except:
                continue

    total_expenses = sum([total_fuel, total_insurance, total_irrigation, total_purchases, total_services, total_tests])
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

    return {
        "total_expenses": round(total_expenses, 2),
        "total_income": round(total_income, 2),
        "expenses_by_category": expenses_by_category,
        "income_by_category": income_by_category
    }
