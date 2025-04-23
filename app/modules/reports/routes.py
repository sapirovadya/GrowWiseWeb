from flask import Blueprint, render_template, request, session,render_template_string,redirect, url_for, jsonify, flash
from datetime import datetime, timedelta
from collections import defaultdict
from calendar import monthrange
from pymongo import MongoClient
import os
from flask import make_response
import json
import io
import base64
from weasyprint import HTML
import matplotlib
matplotlib.use('Agg')
matplotlib.rcParams['font.family'] = 'Arial'
import matplotlib.pyplot as plt 


reports_bp = Blueprint('reports_bp', __name__, url_prefix='/reports')
client = MongoClient(os.getenv("MONGO_KEY"))
db = client.get_database("dataGrow")



def match_month(date_obj, selected_month):
    try:
        if isinstance(date_obj, str):
            if len(date_obj) == 10:
                date_obj = datetime.strptime(date_obj, "%Y-%m-%d")
            elif len(date_obj) == 7:
                date_obj = datetime.strptime(date_obj, "%Y-%m")
            else:
                return False
        return date_obj.strftime("%Y-%m") == selected_month
    except Exception:
        return False


@reports_bp.route("/")
def reports_home():
    return render_template("reports.html")

## דו״ח הוצאות הכנסות חודשי
@reports_bp.route("/monthly")
def monthly_income_expense_report():
    # קבלת שנה וחודש בנפרד מהבקשה
    year = request.args.get("year", datetime.now().year)
    month = request.args.get("month", f"{datetime.now().month:02d}")

    try:
        selected_month = f"{year}-{month.zfill(2)}"
    except ValueError:
        return "פורמט חודש שגוי, צפי לפורמט YYYY-MM", 400

    user_role = session.get("role")
    user_email = session.get("email")
    manager_email = session.get("manager_email")
    filter_email = user_email if user_role == "manager" else manager_email

    report_data = generate_monthly_report_data(selected_month, filter_email)

    return render_template("monthly_income_expense.html",
                           selected_month=selected_month,
                           selected_year=year,
                           selected_month_num=month,
                           datetime=datetime, 
                           **report_data)


def generate_base64_chart(chart_func, *args, **kwargs):
    fig = chart_func(*args, **kwargs)

    fig.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    base64_img = base64.b64encode(buf.read()).decode('utf-8')
    buf.close()
    plt.close(fig)
    return base64_img


@reports_bp.route("/export_pdf")
def export_pdf():
    month = request.args.get("month", datetime.now().strftime("%Y-%m"))
    base_url = request.host_url.rstrip('/')

    year, month_num = month.split("-")
    user_role = session.get("role")
    user_email = session.get("email")
    manager_email = session.get("manager_email")
    filter_email = user_email if user_role == "manager" else manager_email

    report_data = generate_monthly_report_data(month, filter_email)

    def pie_chart():
        fig, ax = plt.subplots(figsize=(6, 6))
        values = list(report_data["expenses_by_category"].values()) + list(report_data["income_by_category"].values())
        colors = ['#E53935'] * len(report_data["expenses_by_category"]) + ['#4CAF50'] * len(report_data["income_by_category"])
        
        wedges, texts, autotexts = ax.pie(values, colors=colors, autopct='%1.1f%%', startangle=90)

        ax.legend(handles=[
            plt.Line2D([0], [0], marker='o', color='w', label='תואצוה', markerfacecolor='#E53935', markersize=10),
            plt.Line2D([0], [0], marker='o', color='w', label='תוסנכה', markerfacecolor='#4CAF50', markersize=10)
        ], loc='lower center', bbox_to_anchor=(0.5, -0.15), ncol=2, frameon=False)

        ax.axis('equal') 
        return fig


    def bar_chart():
        import json
        fig, ax = plt.subplots(figsize=(5, 5))
        data = json.loads(report_data["yearly_data_json"])
        labels = [item["month"] for item in data]
        income_vals = [item["income"] for item in data]
        expense_vals = [item["expense"] for item in data]
        x = range(len(labels))
        ax.bar(x, income_vals, width=0.4, label='תוסנכה', color='green', align='center')
        ax.bar(x, expense_vals, width=0.4, label='תואצוה', color='red', align='edge')
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=45)
        ax.legend()
        return fig

    pie_chart_image = generate_base64_chart(pie_chart)
    bar_chart_image = generate_base64_chart(bar_chart)

    rendered_html = render_template("/pdf/monthly_income_expense_pdf.html",
                                    selected_month=month,
                                    expenses_by_category=report_data["expenses_by_category"],
                                    income_by_category=report_data["income_by_category"],
                                    pie_chart_image=pie_chart_image,
                                    bar_chart_image=bar_chart_image)

    try:
        pdf = HTML(string=rendered_html, base_url=base_url).write_pdf()
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
        "monthly_pie_data": monthly_pie_data  
    }

## דו״ח הוצאות הכנסות שנתי
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

def generate_yearly_report_data(selected_year, filter_email):
    selected_year = int(selected_year) 

    start_date = datetime(selected_year, 1, 1)
    end_date = datetime(selected_year, 12, 31)

    income_by_category = defaultdict(float)
    expense_by_category = defaultdict(float)

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

    for item in db.insurance_history.find({"manager_email": filter_email}):
        try:
            d = datetime.strptime(item.get("insurance_date", ""), "%Y-%m-%d")
            if start_date <= d <= end_date:
                expense_by_category["ביטוחים"] += float(item.get("insurance_cost", 0))
        except:
            continue

    expense_by_category["השקיה"] += calculate_yearly_irrigation_cost(filter_email, start_date, end_date)

    for item in db.purchases.find({"email": filter_email}):
        try:
            d = datetime.strptime(item.get("purchase_date", ""), "%Y-%m-%d")
            if start_date <= d <= end_date:
                q = float(item.get("quantity", 0))
                up = float(item.get("unit_price", 0))
                expense_by_category["רכישות"] += q * up
        except:
            continue

    for item in db.service_history.find({"manager_email": filter_email}):
        try:
            d = datetime.strptime(item.get("service_date", ""), "%Y-%m-%d")
            if start_date <= d <= end_date:
                expense_by_category["טיפולים רכבים"] += float(item.get("service_cost", 0))
        except:
            continue

    for item in db.test_history.find({"manager_email": filter_email}):
        try:
            d = datetime.strptime(item.get("test_date", ""), "%Y-%m-%d")
            if start_date <= d <= end_date:
                expense_by_category["טסטים"] += float(item.get("test_cost", 0))
        except:
            continue

    total_income = sum(income_by_category.values())
    total_expenses = sum(expense_by_category.values())

    pie_income = [{"category": k, "amount": round(v, 2)} for k, v in income_by_category.items()]
    pie_expense = [{"category": k, "amount": round(v, 2)} for k, v in expense_by_category.items()]

    balance_data = []
    for y in range(selected_year - 2, selected_year + 1):
        sy = datetime(y, 1, 1)
        ey = datetime(y, 12, 31)
        income, expense = 0, 0

        for plot in db.plots.find({"manager_email": filter_email}):
            try:
                d = plot.get("harvest_date")
                if isinstance(d, str):
                    d = datetime.strptime(d, "%Y-%m-%d")
                if sy <= d <= ey:
                    income += float(plot.get("crop_yield", 0)) * float(plot.get("price_yield", 0))
            except:
                continue

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

        for item in db.insurance_history.find({"manager_email": filter_email}):
            try:
                d = datetime.strptime(item.get("insurance_date", ""), "%Y-%m-%d")
                if sy <= d <= ey:
                    expense += float(item.get("insurance_cost", 0))
            except:
                continue

        for item in db.purchases.find({"email": filter_email}):
            try:
                d = datetime.strptime(item.get("purchase_date", ""), "%Y-%m-%d")
                if sy <= d <= ey:
                    q = float(item.get("quantity", 0))
                    up = float(item.get("unit_price", 0))
                    expense += q * up
            except:
                continue

        for item in db.service_history.find({"manager_email": filter_email}):
            try:
                d = datetime.strptime(item.get("service_date", ""), "%Y-%m-%d")
                if sy <= d <= ey:
                    expense += float(item.get("service_cost", 0))
            except:
                continue

        for item in db.test_history.find({"manager_email": filter_email}):
            try:
                d = datetime.strptime(item.get("test_date", ""), "%Y-%m-%d")
                if sy <= d <= ey:
                    expense += float(item.get("test_cost", 0))
            except:
                continue

        expense += calculate_yearly_irrigation_cost(filter_email, sy, ey)

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

    return {
        "selected_year": selected_year,
        "expenses_by_category": expense_by_category,
        "income_by_category": income_by_category,
        "yearly_pie_data": yearly_pie_data,
        "yearly_trend_data": yearly_trend_data,
        "total_income": round(total_income, 2),  
        "total_expenses": round(total_expenses, 2) 
    }

@reports_bp.route("/export_yearly_pdf")
def export_yearly_pdf():
    year = request.args.get("year", datetime.now().year)
    base_url = request.host_url.rstrip('/')

    user_role = session.get("role")
    user_email = session.get("email")
    manager_email = session.get("manager_email")
    filter_email = user_email if user_role == "manager" else manager_email

    report_data = generate_yearly_report_data(year, filter_email)

    def pie_chart():
        fig, ax = plt.subplots(figsize=(4.5, 4.5))
        labels = list(report_data["expenses_by_category"].keys()) + list(report_data["income_by_category"].keys())
        values = list(report_data["expenses_by_category"].values()) + list(report_data["income_by_category"].values())
        colors = ['#E53935'] * len(report_data["expenses_by_category"]) + ['#4CAF50'] * len(report_data["income_by_category"])
        ax.pie(values, labels=None, colors=colors, autopct='%1.1f%%', startangle=90)
        ax.axis('equal')
        return fig

    def line_chart():
        import json
        data = json.loads(report_data["yearly_trend_data"])
        fig, ax = plt.subplots(figsize=(5.5, 3.2))
        ax.plot(data["labels"], data["data"], marker='o')
        ax.set_ylabel("הרתי")
        ax.set_xlabel("הנש")
        return fig

    pie_chart_image = generate_base64_chart(pie_chart)
    line_chart_image = generate_base64_chart(line_chart)

    html_content = render_template(
        "/pdf/yearly_income_expense_pdf.html",
        pie_chart_image=pie_chart_image,
        line_chart_image=line_chart_image,
        **report_data
    )

    try:
        pdf = HTML(string=html_content, base_url=base_url).write_pdf()
    except Exception as e:
        return f"שגיאה בהפקת PDF: {e}", 500

    response = make_response(pdf)
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = f"attachment; filename=yearly_report_{year}.pdf"
    return response

## דו״ח נוכחות עובדים חודשי
@reports_bp.route("/attendance_report")
def monthly_attendance_report():
    # קביעת חודש ושנה נוכחיים כברירת מחדל
    now = datetime.now()
    default_month = now.month
    default_year = now.year

    selected_month = int(request.args.get("month", default_month))
    selected_year = int(request.args.get("year", default_year))
    selected_name = request.args.get("name", "all")

    months_years_set = set()
    full_names_set = set()

    pipeline = [
        {"$project": {
            "year": {"$year": {"$toDate": "$check_in"}},
            "month": {"$month": {"$toDate": "$check_in"}},
            "first_name": 1,
            "last_name": 1
        }}
    ]
    for doc in db.attendance.aggregate(pipeline):
        months_years_set.add((doc["year"], doc["month"]))
        full_names_set.add(f"{doc.get('first_name', '')} {doc.get('last_name', '')}".strip())

    available_months_years = sorted(list(months_years_set), reverse=True)
    available_names = sorted(list(full_names_set))

    start_date = datetime(selected_year, selected_month, 1)
    last_day = monthrange(selected_year, selected_month)[1]
    end_date = datetime(selected_year, selected_month, last_day, 23, 59, 59)

    query = {
        "check_in": {"$gte": start_date, "$lte": end_date}
    }

    if selected_name != "all":
        first, last = selected_name.split(" ", 1)
        query.update({"first_name": first, "last_name": last})

    results = []
    for doc in db.attendance.find(query):
        try:
            check_in = doc["check_in"]
            if isinstance(check_in, str):
                check_in = datetime.fromisoformat(check_in.replace("Z", "+00:00"))
            check_out = doc.get("check_out")
            if isinstance(check_out, str):
                check_out = datetime.fromisoformat(check_out.replace("Z", "+00:00"))      
            total_hours = doc.get("total_hours", 0)
            results.append({
                "first_name": doc.get("first_name", ""),
                "last_name": doc.get("last_name", ""),
                "check_in_date": check_in.strftime("%d"),
                "check_in": check_in.strftime("%H:%M:%S"),
                "check_out": check_out.strftime("%H:%M:%S") if check_out else "-",
                "total_hours": round(float(total_hours), 2)
            })
        except Exception as e:
            print("Error parsing record:", e)
    results.sort(key=lambda x: x["check_in_date"])

    return render_template("attendance_report.html",
        selected_month=selected_month,
        selected_year=selected_year,
        selected_name=selected_name,
        month_options=[{"month": m, "label": f"{m:02d}"} for y, m in available_months_years if y == selected_year],
        years=sorted({y for y, m in available_months_years}, reverse=True),
        names = available_names,
        records=results)

@reports_bp.route("/export_attendance_pdf")
def export_attendance_pdf():
    year = int(request.args.get("year", datetime.now().year))
    month = int(request.args.get("month", datetime.now().month))
    name = request.args.get("name", "all")

    selected_month = month
    selected_year = year
    selected_name = name

    # חישוב טווח זמן
    start_date = datetime(year, month, 1)
    last_day = monthrange(year, month)[1]
    end_date = datetime(year, month, last_day, 23, 59, 59)

    # סינון
    query = { "check_in": {"$gte": start_date, "$lte": end_date} }
    if name != "all":
        first, last = name.split(" ", 1)
        query.update({"first_name": first, "last_name": last})

    # שליפת נתונים
    results = []
    total_hours_sum = 0
    for doc in db.attendance.find(query):
        try:
            check_in = doc["check_in"]
            if isinstance(check_in, str):
                check_in = datetime.fromisoformat(check_in.replace("Z", "+00:00"))
            check_out = doc.get("check_out")
            if isinstance(check_out, str):
                check_out = datetime.fromisoformat(check_out.replace("Z", "+00:00"))
            total_hours = float(doc.get("total_hours", 0))
            total_hours_sum += total_hours
            results.append({
                "first_name": doc.get("first_name", ""),
                "last_name": doc.get("last_name", ""),
                "check_in_date": check_in.strftime("%d"),
                "check_in": check_in.strftime("%H:%M:%S"),
                "check_out": check_out.strftime("%H:%M:%S") if check_out else "-",
                "total_hours": round(total_hours, 2)
            })
        except Exception as e:
            print("שגיאה בפרסוס רשומה:", e)

    # יצירת PDF
    html = render_template(
        "/pdf/monthly_attendance_pdf.html",
        selected_month=selected_month,
        selected_year=selected_year,
        selected_name=selected_name,
        records=results,
        total_hours_sum=round(total_hours_sum, 2),   
        base_url=request.host_url

    )

    try:
        pdf = HTML(string=html).write_pdf()
    except Exception as e:
        return f"שגיאה ביצירת PDF: {e}", 500

    response = make_response(pdf)
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = f"attachment; filename=attendance_report_{year}_{month}.pdf"
    return response


## דו״ח הוצאות הכנסות פר חלקה
@reports_bp.route("/plot_report")
def plot_report():
    plot_name = request.args.get("plot_name")
    sow_date_str = request.args.get("sow_date")

    user_role = session.get("role")
    user_email = session.get("email")
    filter_email = user_email if user_role == "manager" else session.get("manager_email")

    report_data = {}

    if plot_name and sow_date_str:
        try:
            # המרה מפורמט תצוגה dd-mm-yyyy לפורמט של Mongo yyyy-mm-dd
            sow_date_formatted = datetime.strptime(sow_date_str, "%d-%m-%Y").strftime("%Y-%m-%d")
        except ValueError:
            flash("פורמט תאריך שגוי", "danger")
            return render_template("plot_report.html", plot_name=plot_name, sow_date=sow_date_str)

        # חיפוש חלקה
        plot = db.plots.find_one({
            "plot_name": plot_name,
            "sow_date": sow_date_formatted,
            "manager_email": filter_email
        })

        if plot:
            report_data = calculate_plot_report(plot, filter_email)
        else:
            flash("החלקה לא נמצאה", "danger")

    return render_template("plot_report.html", plot_name=plot_name, sow_date=sow_date_str, **report_data)

def calculate_plot_report(plot, email):
    sow_date = datetime.strptime(plot["sow_date"], "%Y-%m-%d")
    harvest_date = datetime.strptime(plot.get("harvest_date", datetime.now().strftime("%Y-%m-%d")), "%Y-%m-%d")
    days_diff = (harvest_date - sow_date).days

    irrigations = db.irrigation.find({"email": email, "name": plot["plot_name"], "sow_date": plot["sow_date"]})
    water_prices = sorted(
        db.water.find({"email": email}),
        key=lambda x: datetime.strptime(x["date"], "%Y-%m-%d")
    )

    total_irrigation_cost = 0
    for irrigation in irrigations:
        irrigation_date = datetime.strptime(irrigation["Irrigation_date"], "%Y-%m-%d %H:%M:%S")
        quantity = float(irrigation.get("quantity_irrigation", 0))
        price = 0
        for wp in reversed(water_prices):
            wp_date = datetime.strptime(wp["date"], "%Y-%m-%d")
            if wp_date <= irrigation_date:
                price = float(wp.get("price", 0))
                break
        total_irrigation_cost += quantity * price

    yield_amount = float(plot.get("crop_yield", 0))
    price_yield = float(plot.get("price_yield", 0))
    total_income = yield_amount * price_yield

    total_expenses = total_irrigation_cost
    balance = total_income - total_expenses

    return {
        "crop": plot.get("crop"),
        "quantity_planted": plot.get("quantity_planted"),
        "crop_yield": plot.get("crop_yield"),
        "price_yield": plot.get("price_yield"),
        "total_irrigation_amount": sum(float(i.get("quantity_irrigation", 0)) for i in irrigations),
        "irrigation_cost": round(total_irrigation_cost, 2),
        "income_yield": round(total_income, 2),
        "balance": round(balance, 2),
        "days": days_diff
    }



@reports_bp.route("/get_plot_names")
def get_plot_names():
    from flask import jsonify

    user_role = session.get("role")
    user_email = session.get("email")
    manager_email = session.get("manager_email")
    filter_email = user_email if user_role == "manager" else manager_email

    plots = db.plots.find({"manager_email": filter_email})

    valid_names = {}
    for plot in plots:
        name = plot.get("plot_name")
        if plot.get("harvest_date") and name:
            valid_names.setdefault(name, set()).add(plot.get("sow_date"))

    return jsonify(sorted([name for name, sow_dates in valid_names.items() if len(sow_dates) > 1 or len(sow_dates) == 1]))


@reports_bp.route("/get_sow_dates")
def get_sow_dates():
    from datetime import datetime

    plot_name = request.args.get("plot_name")
    if not plot_name:
        return jsonify([])

    user_role = session.get("role")
    user_email = session.get("email")
    manager_email = session.get("manager_email")
    filter_email = user_email if user_role == "manager" else manager_email

    sow_dates = db.plots.distinct("sow_date", {
        "manager_email": filter_email,
        "plot_name": plot_name,
        "harvest_date": {"$ne": None, "$ne": ""}
    })

    # המרה לפורמט dd-mm-yyyy
    formatted_dates = []
    for date_str in sow_dates:
        try:
            formatted = datetime.strptime(date_str, "%Y-%m-%d").strftime("%d-%m-%Y")
            formatted_dates.append(formatted)
        except Exception:
            continue

    return jsonify(sorted(formatted_dates))

## דו״ח הוצאות רכב שנתי
@reports_bp.route("/vehicle_expenses", methods=["GET"])
def vehicle_expenses():
    from datetime import datetime

    user_role = session.get("role")
    user_email = session.get("email")
    manager_email = user_email if user_role == "manager" else session.get("manager_email")

    vehicle_number = request.args.get("vehicle_number")
    selected_year = request.args.get("year")
    vehicle_info = {}
    expenses = {}
    pie_data = {}  # ברירת מחדל ריקה למקרה שלא נבחר רכב ושנה

    current_year = datetime.now().year
    years = [str(y) for y in range(current_year, current_year - 3, -1)]
    vehicles = list(db.vehicles.find({"manager_email": manager_email}))

    def format_date(date_str):
        try:
            return datetime.strptime(date_str, "%Y-%m-%d").strftime("%d-%m-%Y")
        except Exception:
            return ""

    if vehicle_number and selected_year:
        vehicle_info = db.vehicles.find_one({
            "vehicle_number": vehicle_number,
            "manager_email": manager_email
        }) or {}

        for field in ["test_date", "last_service_date", "insurance_date"]:
            if field in vehicle_info:
                vehicle_info[field] = format_date(vehicle_info[field])

        year_start = datetime(int(selected_year), 1, 1)
        year_end = datetime(int(selected_year), 12, 31, 23, 59, 59)

        def total_cost(col, date_field, price_field):
            return sum(
                float(doc.get(price_field, 0))
                for doc in db[col].find({
                    "vehicle_number": vehicle_number,
                    "manager_email": manager_email,
                    date_field: {
                        "$gte": year_start.strftime("%Y-%m-%d"),
                        "$lte": year_end.strftime("%Y-%m-%d")
                    }
                })
            )

        expenses = {
            "fuel": total_cost("fuel", "fuel_date", "fuel_price"),
            "service": total_cost("service_history", "service_date", "service_cost"),
            "test": total_cost("test_history", "test_date", "test_cost"),
            "insurance": total_cost("insurance_history", "insurance_date", "insurance_cost"),
        }
        expenses["total"] = sum(expenses.values())

        pie_data = {
            "labels": ["דלק", "טיפולים", "טסט", "ביטוח"],
            "data": [expenses["fuel"], expenses["service"], expenses["test"], expenses["insurance"]],
            "colors": [
                "#1f77b4",  # כחול כהה
                "#ff7f0e",  # כתום
                "#2ca02c",  # ירוק
                "#d62728",  # אדום
                "#9467bd",  # סגול
                "#8c564b",  # חום
            ]       
        }

    return render_template("vehicle_expenses_report.html",
                        vehicles=vehicles,
                        years=years,
                        selected_vehicle=vehicle_number,
                        selected_year=selected_year,
                        vehicle_info=vehicle_info,
                        expenses=expenses,
                        pie_data=pie_data if vehicle_number and selected_year else None)

@reports_bp.route("/export_vehicle_pdf")
def export_vehicle_pdf():
    vehicle_number = request.args.get("vehicle_number")
    year = request.args.get("year")

    if not vehicle_number or not year:
        return "חסרים פרמטרים", 400

    # זיהוי המשתמש
    user_role = session.get("role")
    user_email = session.get("email")
    manager_email = user_email if user_role == "manager" else session.get("manager_email")

    # שאילתת פרטי רכב
    vehicle_info = db.vehicles.find_one({
        "vehicle_number": vehicle_number,
        "manager_email": manager_email
    }) or {}

    # עיצוב תאריכים
    def format_date(date_str):
        try:
            return datetime.strptime(date_str, "%Y-%m-%d").strftime("%d-%m-%Y")
        except Exception:
            return ""

    for field in ["test_date", "last_service_date", "insurance_date"]:
        if field in vehicle_info:
            vehicle_info[field] = format_date(vehicle_info[field])

    # טווח השנה הנבחרת
    year_start = datetime(int(year), 1, 1)
    year_end = datetime(int(year), 12, 31, 23, 59, 59)

    # חישוב הוצאות בפועל
    def total_cost(col, date_field, price_field):
        return sum(
            float(doc.get(price_field, 0))
            for doc in db[col].find({
                "vehicle_number": vehicle_number,
                "manager_email": manager_email,
                date_field: {
                    "$gte": year_start.strftime("%Y-%m-%d"),
                    "$lte": year_end.strftime("%Y-%m-%d")
                }
            })
        )

    expenses = {
        "fuel": total_cost("fuel", "fuel_date", "fuel_price"),
        "service": total_cost("service_history", "service_date", "service_cost"),
        "test": total_cost("test_history", "test_date", "test_cost"),
        "insurance": total_cost("insurance_history", "insurance_date", "insurance_cost"),
    }
    expenses["total"] = sum(expenses.values())

    # הגדרת נתוני גרף עוגה
    pie_data = {
        "labels": ["דלק", "טיפולים", "טסט", "ביטוח"],
        "data": [expenses["fuel"], expenses["service"], expenses["test"], expenses["insurance"]],
        "colors": ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"]
    }

    # יצירת גרף עוגה כ־base64
    fig, ax = plt.subplots(figsize=(3.5, 3.5))
    matplotlib.rcParams['font.family'] = 'DejaVu Sans'
    labels = [label[::-1] for label in pie_data["labels"]]  # הפיכת כיוון הטקסט    ax.pie(pie_data["data"], labels=pie_data["labels"], colors=pie_data["colors"], autopct='%1.1f%%', startangle=90)
    ax.pie(pie_data["data"], labels=labels, colors=pie_data["colors"],
       autopct='%1.1f%%', startangle=90)
    ax.axis('equal')
    buf = io.BytesIO()
    fig.savefig(buf, format='png')
    buf.seek(0)
    pie_chart_base64 = base64.b64encode(buf.read()).decode('utf-8')
    buf.close()
    plt.close(fig)

    # רינדור לתבנית PDF
    rendered = render_template("/pdf/vehicle_report_pdf.html",
                               vehicle_number=vehicle_number,
                               selected_year=year,
                               vehicle_info=vehicle_info,
                               expenses=expenses,
                               pie_chart_image=pie_chart_base64)

    # יצירת קובץ PDF
    pdf_file = HTML(string=rendered, base_url=request.host_url).write_pdf()
    response = make_response(pdf_file)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'inline; filename=vehicle_report_{vehicle_number}_{year}.pdf'
    return response
