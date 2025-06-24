from flask import Blueprint, render_template, request, session,render_template_string,redirect, url_for, jsonify, flash
from datetime import datetime, timedelta
from collections import defaultdict
from calendar import monthrange
from pymongo import MongoClient
import os
from flask import make_response
from dateutil.relativedelta import relativedelta
import json
import io
import base64
# from weasyprint import HTML
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
    return render_template("/reports/reports.html")



def get_all_relevant_emails(main_email):
    user = db.manager.find_one({"email": main_email})
    if not user:
        return [main_email]
    
    emails = [main_email]
    emails.extend(user.get("co_managers", []))
    emails.extend(user.get("workers", []))
    
    return list(set(emails))


@reports_bp.route("/monthly")
def monthly_income_expense_report():
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

    return render_template("/reports/monthly_income_expense.html",
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

        total_expenses = report_data["total_expenses"]
        total_income = report_data["total_income"]
        values = [total_expenses, total_income]
        colors = ['#E53935', '#4CAF50']

        wedges, texts, autotexts = ax.pie(
            values,
            colors=colors,
            startangle=90,
            autopct=lambda pct: f"{pct:1.2f}%",
            textprops=dict(color="black", fontsize=22, fontweight='bold')
        )

        legend_labels = ['תואצוה', 'תוסנכה']
        legend_handles = [
            plt.Line2D([0], [0], marker='o', color='w', label=legend_labels[0], markerfacecolor=colors[0], markersize=12),
            plt.Line2D([0], [0], marker='o', color='w', label=legend_labels[1], markerfacecolor=colors[1], markersize=12)
        ]
        ax.legend(handles=legend_handles, loc='lower center', bbox_to_anchor=(0.5, -0.15), ncol=2, frameon=False, fontsize=22)

        ax.axis('equal')
        return fig



    def bar_chart():
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


def get_latest_water_rate(water_prices, selected_date, water_type):
    for p in reversed(water_prices):
        try:
            water_date = datetime.strptime(p["date"], "%Y-%m-%d")
            if water_date <= selected_date and p.get("water_type") == water_type:
                return float(p.get("price", 0))
        except:
            continue
    return 0


def generate_monthly_report_data(month, filter_email):
    total_expenses = total_income = 0
    total_fuel = total_insurance = total_purchases = total_services = total_tests = 0
    total_irrigation_shafirim = total_irrigation_mushavim = 0
    total_crop_income = total_equipment_sales = 0
    equipment_sales_by_item = {}
    default_price_shafirim = default_price_mushavim = 0

    year, month_num = int(month[:4]), int(month[5:])
    last_day = monthrange(year, month_num)[1]
    month_start = datetime(year, month_num, 1)
    month_end = datetime(year, month_num, last_day)


    water_prices = sorted(
        db.water.find({"email": filter_email}),
        key=lambda x: datetime.strptime(x["date"], "%Y-%m-%d")
    )

    def match_month(date_obj, selected_month):
        try:
            if not date_obj:
                return False
            if isinstance(date_obj, str):
                if len(date_obj) == 10:
                    date_obj = datetime.strptime(date_obj, "%Y-%m-%d")
                elif len(date_obj) == 7:
                    date_obj = datetime.strptime(date_obj, "%Y-%m")
                else:
                    return False
            return date_obj.strftime("%Y-%m") == selected_month
        except:
            return False


    for item in db.irrigation.find({"email": filter_email}):
        date_str = item.get("Irrigation_date")
        if not date_str:
            continue
        try:
            irrigation_date = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        except:
            try:
                irrigation_date = datetime.strptime(date_str, "%Y-%m-%d")
            except:
                continue
        if not match_month(irrigation_date, month):
            continue
        quantity = float(item.get("quantity_irrigation", 0))
        water_type = item.get("irrigation_water_type", "")
        rate = 0
        for wp in reversed(water_prices):
            try:
                wp_date = datetime.strptime(wp["date"], "%Y-%m-%d")
                if wp_date <= irrigation_date and wp.get("water_type") == water_type:
                    rate = float(wp["price"])
                    break
            except:
                continue
        if water_type == "מים שפירים":
            total_irrigation_shafirim += quantity * rate
        elif water_type == "מים מושבים":
            total_irrigation_mushavim += quantity * rate


    relevant_emails = get_all_relevant_emails(filter_email)
    for item in db.fuel.find({"email": {"$in": relevant_emails}}):
        try:
            refuel_type = item.get("refuel_type")
            cost = float(item.get("cost", 0))
            amount = float(item.get("fuel_amount", 0))
            month_str = item.get("month", "") if refuel_type == "דלקן" else item.get("refuel_date", "")[:7]
            if month_str == month:
                total_fuel += cost * amount
        except:
            continue


    for item in db.insurance_history.find({"manager_email": filter_email}):
        if match_month(item.get("insurance_date"), month):
            total_insurance += float(item.get("insurance_cost", 0))


    relevant_emails = get_all_relevant_emails(filter_email)
    for item in db.purchases.find({"email": {"$in": relevant_emails}}):
        if match_month(item.get("purchase_date"), month):
            try:
                total_purchases += float(item.get("quantity", 0)) * float(item.get("unit_price", 0))
            except:
                continue



    for item in db.service_history.find({"manager_email": filter_email}):
        if match_month(item.get("service_date"), month):
            total_services += float(item.get("service_cost", 0))


    for item in db.test_history.find({"manager_email": filter_email}):
        if match_month(item.get("test_date"), month):
            total_tests += float(item.get("test_cost", 0))

    for plot in db.plots.find({"manager_email": filter_email}):
        if match_month(plot.get("harvest_date"), month):
            try:
                total_crop_income += float(plot.get("crop_yield", 0)) * float(plot.get("price_yield", 0))
            except:
                continue
    for plot in db.plots_yield.find({"manager_email": filter_email}):
        if match_month(plot.get("harvest_date"), month):
            try:
                total_crop_income += float(plot.get("crop_yield", 0)) * float(plot.get("price_yield", 0))
            except:
                continue


    for item in db.equipment_sales.find({"email": filter_email}):
        try:
            sale_date = item.get("sale_date")
            if isinstance(sale_date, str):
                sale_date = datetime.fromisoformat(sale_date[:10])
            if match_month(sale_date, month):
                quantity = float(item.get("quantity", 0))
                unit_price = float(item.get("unit_price", 0))
                item_total = quantity * unit_price
                total_equipment_sales += item_total
                name = item.get("name", "פריט לא ידוע")
                equipment_sales_by_item[name] = equipment_sales_by_item.get(name, 0) + item_total
        except:
            continue

 
    total_expenses = sum([
        total_fuel, total_insurance, total_irrigation_shafirim,
        total_irrigation_mushavim, total_purchases, total_services, total_tests
    ])
    total_income = total_crop_income + total_equipment_sales

    expenses_by_category = {
        "דלק": round(total_fuel, 2),
        "ביטוחים": round(total_insurance, 2),
        f"השקיית מים שפירים (תעריף {round(default_price_shafirim, 2)}₪)": round(total_irrigation_shafirim, 2),
        f"השקיית מים מושבים (תעריף {round(default_price_mushavim, 2)}₪)": round(total_irrigation_mushavim, 2),
        "רכישות": round(total_purchases, 2),
        "טיפולים רכבים": round(total_services, 2),
        "טסטים": round(total_tests, 2),
    }

    income_by_category = {
        "יבול": round(total_crop_income, 2),
        "מכירה ציוד": round(total_equipment_sales, 2)
    }

  
    start_month = datetime(year, month_num, 1) - relativedelta(months=11)
    months_list = [(start_month + relativedelta(months=i)).strftime("%Y-%m") for i in range(12)]
    yearly_data = {m: {"income": 0, "expense": 0} for m in months_list}


    for plot in db.plots.find({"manager_email": filter_email}):
        try:
            d = plot.get("harvest_date")
            if isinstance(d, str):
                d = datetime.strptime(d, "%Y-%m-%d")
            m = d.strftime("%Y-%m")
            if m in yearly_data:
                yearly_data[m]["income"] += float(plot.get("crop_yield", 0)) * float(plot.get("price_yield", 0))
        except:
            continue

    for plot in db.plots_yield.find({"manager_email": filter_email}):
        try:
            d = plot.get("harvest_date")
            if isinstance(d, str):
                d = datetime.strptime(d, "%Y-%m-%d")
            m = d.strftime("%Y-%m")
            if m in yearly_data:
                yearly_data[m]["income"] += float(plot.get("crop_yield", 0)) * float(plot.get("price_yield", 0))
        except:
            continue


    for item in db.equipment_sales.find({"email": filter_email}):
        try:
            d = item.get("sale_date")
            if isinstance(d, str):
                d = datetime.fromisoformat(d[:10])
            m = d.strftime("%Y-%m")
            if m in yearly_data:
                yearly_data[m]["income"] += float(item.get("quantity", 0)) * float(item.get("unit_price", 0))
        except:
            continue

    for m in months_list:
        y, mo = map(int, m.split("-"))
        month_start = datetime(y, mo, 1)
        last_day = monthrange(y, mo)[1]
        month_end = datetime(y, mo, last_day)

        total_monthly_expense = 0


       
        relevant = get_all_relevant_emails(filter_email)
        for item in db.fuel.find({"email": {"$in": relevant}}):
            try:
                refuel_type = item.get("refuel_type")
                cost = float(item.get("cost", 0))
                amount = float(item.get("fuel_amount", 0))
                date_str = item.get("refuel_date") if refuel_type != "דלקן" else f"{item.get('month')}-01"
                date = datetime.strptime(date_str, "%Y-%m-%d")
                if month_start <= date <= month_end:
                    total_monthly_expense += cost * amount
            except:
                continue

   
        for item in db.insurance_history.find({"manager_email": filter_email}):
            try:
                date = datetime.strptime(item.get("insurance_date", ""), "%Y-%m-%d")
                if month_start <= date <= month_end:
                    total_monthly_expense += float(item.get("insurance_cost", 0))
            except:
                continue


        relevant_emails = get_all_relevant_emails(filter_email)
        for item in db.purchases.find({"email": {"$in": relevant_emails}}):
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
                date = datetime.strptime(item.get("service_date", ""), "%Y-%m-%d")
                if month_start <= date <= month_end:
                    total_monthly_expense += float(item.get("service_cost", 0))
            except:
                continue

        
        for item in db.test_history.find({"manager_email": filter_email}):
            try:
                date = datetime.strptime(item.get("test_date", ""), "%Y-%m-%d")
                if month_start <= date <= month_end:
                    total_monthly_expense += float(item.get("test_cost", 0))
            except:
                continue

        
        for item in db.irrigation.find({"email": filter_email}):
            date_str = item.get("Irrigation_date")
            if not date_str:
                continue
            try:
                date = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
            except:
                try:
                    date = datetime.strptime(date_str, "%Y-%m-%d")
                except:
                    continue
            if not (month_start <= date <= month_end):
                continue
            quantity = float(item.get("quantity_irrigation", 0))
            water_type = item.get("irrigation_water_type", "")
            rate = get_latest_water_rate(water_prices, date, water_type)
            total_monthly_expense += quantity * rate

        yearly_data[m]["expense"] = round(total_monthly_expense, 2)
    yearly_data_json = json.dumps([
        {
            "month": datetime.strptime(m, "%Y-%m").strftime("%m-%Y"),
            "income": round(yearly_data[m]["income"], 2),
            "expense": round(yearly_data[m]["expense"], 2),
            "balance": round(yearly_data[m]["income"] - yearly_data[m]["expense"], 2)
        }
        for m in months_list
    ], ensure_ascii=False)


    return {
        "total_expenses": round(total_expenses, 2),
        "total_income": round(total_income, 2),
        "expenses_by_category": expenses_by_category,
        "income_by_category": income_by_category,
        "yearly_data_json": yearly_data_json,
        "equipment_sales_by_item": {k: round(v, 2) for k, v in equipment_sales_by_item.items()}
    }


@reports_bp.route("/yearly")
def yearly_report():
    selected_year = int(request.args.get("year", datetime.now().year))

    user_role = session.get("role")
    user_email = session.get("email")
    manager_email = session.get("manager_email")
    filter_email = user_email if user_role == "manager" else manager_email

    report_data = generate_yearly_report_data(selected_year, filter_email)

    return render_template("/reports/yearly_income_expense.html",
                        datetime=datetime,
                        **report_data)


def calculate_yearly_irrigation_cost_split(email, start_date, end_date):
    irrigation_shafirim = 0.0
    irrigation_mushavim = 0.0

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
        water_type = item.get("irrigation_water_type", "none")
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
                if water_date <= irrigation_date and p.get("water_type") == water_type:
                    applicable_price = float(p.get("price", 0))
                    break
            except:
                continue

        if water_type == "מים שפירים":
            irrigation_shafirim += quantity * applicable_price
        elif water_type == "מים מושבים":
            irrigation_mushavim += quantity * applicable_price

    return round(irrigation_shafirim, 2), round(irrigation_mushavim, 2)


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
            # table plots_yield
    for plot in db.plots_yield.find({"manager_email": filter_email}):
        try:
            harvest_date = plot.get("harvest_date")
            if isinstance(harvest_date, str):
                harvest_date = datetime.strptime(harvest_date, "%Y-%m-%d")
            if start_date <= harvest_date <= end_date:
                income = float(plot.get("crop_yield", 0)) * float(plot.get("price_yield", 0))
                income_by_category["יבול"] += income
        except:
            continue


    for item in db.equipment_sales.find({"email": filter_email}):
        try:
            sale_date = item.get("sale_date")
            if isinstance(sale_date, str):
                sale_date = datetime.fromisoformat(sale_date[:10])
            if start_date <= sale_date <= end_date:
                total = float(item.get("quantity", 0)) * float(item.get("unit_price", 0))
                income_by_category["מכירה ציוד"] += total
        except:
            continue


    relevant = get_all_relevant_emails(filter_email)
    for item in db.fuel.find({"email": {"$in": relevant}}):
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

    shafirim_total, mushavim_total = calculate_yearly_irrigation_cost_split(filter_email, start_date, end_date)

    expense_by_category[f"השקיית מים שפירים"] += shafirim_total
    expense_by_category[f"השקיית מים מושבים"] += mushavim_total

    relevant_emails = get_all_relevant_emails(filter_email)
    for item in db.purchases.find({"email": {"$in": relevant_emails}}):
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
        for plot in db.plots_yield.find({"manager_email": filter_email}):
            try:
                d = plot.get("harvest_date")
                if isinstance(d, str):
                    d = datetime.strptime(d, "%Y-%m-%d")
                if sy <= d <= ey:
                    income += float(plot.get("crop_yield", 0)) * float(plot.get("price_yield", 0))
            except:
                continue
        for item in db.equipment_sales.find({"email": filter_email}):
            try:
                sale_date = item.get("sale_date")
                if isinstance(sale_date, str):
                    sale_date = datetime.fromisoformat(sale_date[:10])
                if sy <= sale_date <= ey:
                    total = float(item.get("quantity", 0)) * float(item.get("unit_price", 0))
                    income += total
            except:
                continue

        for plot in db.plots.find({"manager_email": filter_email}):
            try:
                d = plot.get("harvest_date")
                if isinstance(d, str):
                    d = datetime.strptime(d, "%Y-%m-%d")
                if sy <= d <= ey:
                    income += float(plot.get("crop_yield", 0)) * float(plot.get("price_yield", 0))
            except:
                continue

        relevant = get_all_relevant_emails(filter_email)
        for item in db.fuel.find({"email": {"$in": relevant}}):
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

        shafirim_y, mushavim_y = calculate_yearly_irrigation_cost_split(filter_email, sy, ey)
        expense += shafirim_y + mushavim_y

        balance_data.append({
            "year": str(y),
            "income": round(income, 2),
            "expense": round(expense, 2),
            "balance": round(income - expense, 2)
        })

    yearly_pie_data = json.dumps({
        "labels": [x["category"] for x in pie_income + pie_expense],
        "data": [x["amount"] for x in pie_income + pie_expense],
        "colors": ['#4CAF50'] * len(pie_income) + ['#E53935'] * len(pie_expense)
    }, ensure_ascii=False)

    yearly_trend_data = json.dumps({
        "labels": [str(item["year"]) for item in balance_data],
        "income": [item["income"] for item in balance_data],
        "expense": [item["expense"] for item in balance_data],
        "balance": [item["balance"] for item in balance_data]
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
        fig, ax = plt.subplots(figsize=(6, 6))

        total_expenses = report_data["total_expenses"]
        total_income = report_data["total_income"]
        values = [total_expenses, total_income]
        colors = ['#E53935', '#4CAF50']

        wedges, texts, autotexts = ax.pie(
            values,
            colors=colors,
            startangle=90,
            autopct=lambda pct: f"{pct:.1f}%",
            textprops=dict(color="black", fontsize=20, fontweight='bold')
        )

        ax.legend(handles=[
            plt.Line2D([0], [0], marker='o', color='w', label='תואצוה', markerfacecolor='#E53935', markersize=12),
            plt.Line2D([0], [0], marker='o', color='w', label='תוסנכה', markerfacecolor='#4CAF50', markersize=12)
        ], loc='lower center', bbox_to_anchor=(0.5, -0.15), ncol=2, frameon=False, fontsize=22)

        ax.axis('equal')
        return fig

    def line_chart():
        data = json.loads(report_data["yearly_trend_data"])
        fig, ax = plt.subplots(figsize=(5.5, 3.2))

        ax.plot(data["labels"], data["balance"], marker='o', color='blue', linewidth=2)

        ax.set_ylabel("(₪) םירזת", fontsize=18)
        ax.set_xlabel("הנש", fontsize=18)
        ax.grid(True)
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

@reports_bp.route("/attendance_report")
def monthly_attendance_report():
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

    return render_template("/reports/attendance_report.html",
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

    start_date = datetime(year, month, 1)
    last_day = monthrange(year, month)[1]
    end_date = datetime(year, month, last_day, 23, 59, 59)

    query = { "check_in": {"$gte": start_date, "$lte": end_date} }
    if name != "all":
        first, last = name.split(" ", 1)
        query.update({"first_name": first, "last_name": last})

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
            sow_date_formatted = datetime.strptime(sow_date_str, "%d-%m-%Y").strftime("%Y-%m-%d")
        except ValueError:
            flash("פורמט תאריך שגוי", "danger")
            return render_template("/reports/plot_report.html", plot_name=plot_name, sow_date=sow_date_str)

        
        plot = db.plots.find_one({
            "plot_name": plot_name,
            "sow_date": sow_date_formatted,
            "manager_email": filter_email
        })

        if plot:
            report_data = calculate_plot_report(plot, filter_email)
        else:
            flash("החלקה לא נמצאה", "danger")

    return render_template("/reports/plot_report.html", plot_name=plot_name, sow_date=sow_date_str, **report_data)

def calculate_plot_report(plot, email):
    sow_date = datetime.strptime(plot["sow_date"], "%Y-%m-%d")
    plot_name = plot["plot_name"]

    harvest_str = plot.get("harvest_date")
    harvest_date_source = ""
    alt_yield_doc = None

    if not harvest_str:
        alt_yield_doc = db.plots_yield.find_one(
            {"manager_email": email, "plot_name": plot_name, "sow_date": plot["sow_date"]},
            sort=[("harvest_date", -1)]
        )
        if alt_yield_doc and alt_yield_doc.get("harvest_date"):
            harvest_str = alt_yield_doc["harvest_date"]
            harvest_date_source = f" (מתוך טבלת קציר: {harvest_str})"
    else:
        harvest_date_source = f" ({harvest_str})"

    if harvest_str:
        harvest_date = datetime.strptime(harvest_str, "%Y-%m-%d")
        days_diff = (harvest_date - sow_date).days

        try:
            yield_amount = float(plot.get("crop_yield") or 0)
            price_yield = float(plot.get("price_yield") or 0)
        except:
            yield_amount = price_yield = 0

        if (yield_amount == 0 or price_yield == 0) and not alt_yield_doc:
            alt_yield_doc = db.plots_yield.find_one(
                {"manager_email": email, "plot_name": plot_name, "sow_date": plot["sow_date"]},
                sort=[("harvest_date", -1)]
            )

        if alt_yield_doc:
            try:
                yield_amount = float(alt_yield_doc.get("crop_yield") or yield_amount)
                price_yield = float(alt_yield_doc.get("price_yield") or price_yield)
            except:
                pass

        total_income = yield_amount * price_yield
        yield_display = f"{yield_amount} ק״ג"
        price_yield_display = f"{price_yield} ₪"
        income_display = f"{total_income:.2f} ₪"
    else:
        days_diff = (datetime.now() - sow_date).days
        total_income = 0
        yield_display = "טרם בוצעה קצירה"
        price_yield_display = "-"
        income_display = "-"

    irrigations = db.irrigation.find({"email": email, "name": plot_name, "sow_date": plot["sow_date"]})
    water_prices = sorted(
        db.water.find({"email": email}),
        key=lambda x: datetime.strptime(x["date"], "%Y-%m-%d")
    )

    irrigation_shafirim = 0
    irrigation_mushavim = 0
    irrigation_shafirim_amount = 0
    irrigation_mushavim_amount = 0

    for irrigation in irrigations:
        irrigation_date = datetime.strptime(irrigation["Irrigation_date"], "%Y-%m-%d %H:%M:%S")
        quantity = float(irrigation.get("quantity_irrigation", 0))
        water_type = irrigation.get("irrigation_water_type", "none")
        price = 0
        for wp in reversed(water_prices):
            wp_date = datetime.strptime(wp["date"], "%Y-%m-%d")
            if wp_date <= irrigation_date and wp.get("water_type") == water_type:
                price = float(wp.get("price", 0))
                break

        if water_type == "מים שפירים":
            irrigation_shafirim += quantity * price
            irrigation_shafirim_amount += quantity
        elif water_type == "מים מושבים":
            irrigation_mushavim += quantity * price
            irrigation_mushavim_amount += quantity

    total_irrigation_cost = irrigation_shafirim + irrigation_mushavim
    total_irrigation_amount = irrigation_shafirim_amount + irrigation_mushavim_amount

    return {
        "crop": plot.get("crop"),
        "quantity_planted": plot.get("quantity_planted"),
        "crop_yield": yield_display + harvest_date_source,
        "price_yield": price_yield_display,
        "total_irrigation_amount": round(total_irrigation_amount, 2),
        "irrigation_cost_shafirim": round(irrigation_shafirim, 2),
        "irrigation_cost_mushavim": round(irrigation_mushavim, 2),
        "irrigation_cost_total": round(total_irrigation_cost, 2),
        "income_yield": income_display,
        "balance": round(total_income - total_irrigation_cost, 2),
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
        if name:
            valid_names.setdefault(name, set()).add(plot.get("sow_date"))

    return jsonify(sorted([name for name, sow_dates in valid_names.items() if len(sow_dates) > 1 or len(sow_dates) == 1]))


@reports_bp.route("/get_sow_dates")
def get_sow_dates():
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

    formatted_dates = []
    for date_str in sow_dates:
        try:
            formatted = datetime.strptime(date_str, "%Y-%m-%d").strftime("%d-%m-%Y")
            formatted_dates.append(formatted)
        except Exception:
            continue

    return jsonify(sorted(formatted_dates))


@reports_bp.route("/vehicle_expenses", methods=["GET"])
def vehicle_expenses():
    user_role = session.get("role")
    user_email = session.get("email")
    manager_email = user_email if user_role == "manager" else session.get("manager_email")

    vehicle_number = request.args.get("vehicle_number")
    selected_year = request.args.get("year")
    vehicle_info = {}
    expenses = {}
    pie_data = {}

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

        def calculate_fuel_cost(vehicle_number, manager_email, selected_year):
            start_date = datetime(int(selected_year), 1, 1)
            end_date = datetime(int(selected_year), 12, 31, 23, 59, 59)

            relevant_emails = get_all_relevant_emails(manager_email)
            total = 0

            for doc in db.fuel.find({
                "vehicle_number": vehicle_number,
                "email": {"$in": relevant_emails}
            }):
                try:
                    refuel_type = doc.get("refuel_type", "")
                    if refuel_type == "דלקן":
                        month_str = doc.get("month", "")
                        if not month_str or len(month_str) != 7:
                            continue
                        date = datetime.strptime(month_str + "-01", "%Y-%m-%d")
                    else:
                        date_str = doc.get("refuel_date", "")
                        if not date_str or len(date_str) < 10:
                            continue
                        date = datetime.strptime(date_str[:10], "%Y-%m-%d")

                    if not (start_date <= date <= end_date):
                        continue

                    amount = float(doc.get("fuel_amount", 0))
                    cost = float(doc.get("cost", 0))
                    total += amount * cost
                except Exception as e:
                    print("Fuel calc error:", e)
                    continue

            return round(total, 2)
        def total_cost(col, date_field, price_field, start_date, end_date, vehicle_number, manager_email):
            total = 0
            for doc in db[col].find({
                "vehicle_number": vehicle_number,
                "manager_email": manager_email
            }):
                try:
                    date_str = doc.get(date_field)
                    if not date_str or len(date_str) < 10:
                        continue
                    date = datetime.strptime(date_str[:10], "%Y-%m-%d")
                    if not (start_date <= date <= end_date):
                        continue
                    total += float(doc.get(price_field, 0))
                except:
                    continue
            return total

        expenses = {
            "fuel": calculate_fuel_cost(vehicle_number, manager_email, selected_year),
            "service": total_cost("service_history", "service_date", "service_cost", year_start, year_end, vehicle_number, manager_email),
            "test": total_cost("test_history", "test_date", "test_cost", year_start, year_end, vehicle_number, manager_email),
            "insurance": total_cost("insurance_history", "insurance_date", "insurance_cost", year_start, year_end, vehicle_number, manager_email),
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

    return render_template("/reports/vehicle_expenses_report.html",
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

 
    user_role = session.get("role")
    user_email = session.get("email")
    manager_email = user_email if user_role == "manager" else session.get("manager_email")

   
    vehicle_info = db.vehicles.find_one({
        "vehicle_number": vehicle_number,
        "manager_email": manager_email
    }) or {}

    
    def format_date(date_str):
        try:
            return datetime.strptime(date_str, "%Y-%m-%d").strftime("%d-%m-%Y")
        except Exception:
            return ""

    for field in ["test_date", "last_service_date", "insurance_date"]:
        if field in vehicle_info:
            vehicle_info[field] = format_date(vehicle_info[field])


    year_start = datetime(int(year), 1, 1)
    year_end = datetime(int(year), 12, 31, 23, 59, 59)
    
    def calculate_fuel_cost(vehicle_number, manager_email, selected_year):
        start_date = datetime(int(selected_year), 1, 1)
        end_date = datetime(int(selected_year), 12, 31, 23, 59, 59)

        relevant_emails = get_all_relevant_emails(manager_email)
        total = 0

        for doc in db.fuel.find({
            "vehicle_number": vehicle_number,
            "email": {"$in": relevant_emails}
        }):
            try:
                refuel_type = doc.get("refuel_type", "")
                if refuel_type == "דלקן":
                    month_str = doc.get("month", "")
                    if not month_str or len(month_str) != 7:
                        continue
                    date = datetime.strptime(month_str + "-01", "%Y-%m-%d")
                else:
                    date_str = doc.get("refuel_date", "")
                    if not date_str or len(date_str) < 10:
                        continue
                    date = datetime.strptime(date_str[:10], "%Y-%m-%d")

                if not (start_date <= date <= end_date):
                    continue

                amount = float(doc.get("fuel_amount", 0))
                cost = float(doc.get("cost", 0))
                total += amount * cost
            except Exception as e:
                print("Fuel calc error:", e)
                continue

        return round(total, 2)
    def total_cost(col, date_field, price_field, start_date, end_date, vehicle_number, manager_email):
        total = 0
        for doc in db[col].find({
            "vehicle_number": vehicle_number,
            "manager_email": manager_email
        }):
            try:
                date_str = doc.get(date_field)
                if not date_str or len(date_str) < 10:
                    continue
                date = datetime.strptime(date_str[:10], "%Y-%m-%d")
                if not (start_date <= date <= end_date):
                    continue
                total += float(doc.get(price_field, 0))
            except:
                continue
        return total

    expenses = {
    "fuel": calculate_fuel_cost(vehicle_number, manager_email, selected_year),
        "service": total_cost("service_history", "service_date", "service_cost"),
        "test": total_cost("test_history", "test_date", "test_cost"),
        "insurance": total_cost("insurance_history", "insurance_date", "insurance_cost"),
    }
    expenses["total"] = sum(expenses.values())

    pie_data = {
        "labels": ["דלק", "טיפולים", "טסט", "ביטוח"],
        "data": [expenses["fuel"], expenses["service"], expenses["test"], expenses["insurance"]],
        "colors": ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"]
    }

    fig, ax = plt.subplots(figsize=(3.5, 3.5))
    matplotlib.rcParams['font.family'] = 'DejaVu Sans'
    labels = [label[::-1] for label in pie_data["labels"]]
    ax.pie(pie_data["data"], labels=labels, colors=pie_data["colors"],
       autopct='%1.1f%%', startangle=90)
    ax.axis('equal')
    buf = io.BytesIO()
    fig.savefig(buf, format='png')
    buf.seek(0)
    pie_chart_base64 = base64.b64encode(buf.read()).decode('utf-8')
    buf.close()
    plt.close(fig)

    # PDF
    rendered = render_template("/pdf/vehicle_report_pdf.html",
                               vehicle_number=vehicle_number,
                               selected_year=year,
                               vehicle_info=vehicle_info,
                               expenses=expenses,
                               pie_chart_image=pie_chart_base64)

    pdf_file = HTML(string=rendered, base_url=request.host_url).write_pdf()
    response = make_response(pdf_file)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'inline; filename=vehicle_report_{vehicle_number}_{year}.pdf'
    return response