import os
import json
import shutil
import openpyxl
from collections import defaultdict
from datetime import datetime
import tkinter as tk
from tkinter import messagebox, ttk, simpledialog, filedialog, Toplevel, Label, Button

import matplotlib.pyplot as plt

DATA_DIR = "data"
CURRENCIES = {"ILS": "₪", "Dollar": "$", "Euro": "€"}

# פונקציה להצגת חלון הודעה צבעוני עם אימוג'י


def colored_popup(title, message, bg_color, emoji="ℹ️"):
    popup = Toplevel()
    popup.title(title)
    popup.configure(bg=bg_color)
    popup.geometry("320x150")
    popup.resizable(False, False)
    Label(popup, text=emoji, font=("Arial", 28),
          bg=bg_color).pack(pady=(15, 5))
    Label(popup, text=message, font=("Arial", 12),
          bg=bg_color).pack(pady=(0, 15))
    Button(popup, text="OK", command=popup.destroy,
           bg="white", relief="flat").pack(pady=5)
    popup.transient()
    popup.grab_set()
    popup.wait_window()


class PersonalFinance:
    def __init__(self, incomes_file="incomes.json", expenses_file="expenses.json"):
        os.makedirs(DATA_DIR, exist_ok=True)
        self.incomes_file = os.path.join(DATA_DIR, incomes_file)
        self.expenses_file = os.path.join(DATA_DIR, expenses_file)
        self.incomes = self.load_data(self.incomes_file)
        self.expenses = self.load_data(self.expenses_file)

    def load_data(self, filename):
        if os.path.exists(filename):
            with open(filename, "r", encoding='utf-8') as f:
                return json.load(f)
        return []

    def backup_file(self, filename):
        if os.path.exists(filename):
            shutil.copyfile(filename, filename + ".bak")

    def save_data(self, filename, data):
        self.backup_file(filename)
        with open(filename, "w", encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def add_income(self, date, amount, source):
        self.incomes.append({"date": date, "amount": amount, "source": source})
        self.save_data(self.incomes_file, self.incomes)

    def add_expense(self, date, amount, category):
        self.expenses.append(
            {"date": date, "amount": amount, "category": category})
        self.save_data(self.expenses_file, self.expenses)

    def delete_income(self, index):
        if 0 <= index < len(self.incomes):
            self.incomes.pop(index)
            self.save_data(self.incomes_file, self.incomes)

    def delete_expense(self, index):
        if 0 <= index < len(self.expenses):
            self.expenses.pop(index)
            self.save_data(self.expenses_file, self.expenses)

    def calculate_tax(self, income):
        if income <= 6000:
            return income * 0.10
        elif income <= 10000:
            return 6000 * 0.10 + (income - 6000) * 0.20
        else:
            return 6000 * 0.10 + 4000 * 0.20 + (income - 10000) * 0.30

    def filter_by_month_year(self, data_list, year, month):
        return [
            item for item in data_list
            if item.get('date') and self._match_date(item['date'], year, month)
        ]

    def _match_date(self, date_str, year, month):
        try:
            y, m, _ = date_str.split('-')
            return int(y) == year and int(m) == month
        except:
            return False

    def monthly_summary(self, year, month):
        incomes = self.filter_by_month_year(self.incomes, year, month)
        expenses = self.filter_by_month_year(self.expenses, year, month)
        total_income = sum(i['amount'] for i in incomes)
        total_expense = sum(e['amount'] for e in expenses)
        tax = self.calculate_tax(total_income)
        remaining = total_income - total_expense - tax
        return {
            'total_income': total_income,
            'total_expense': total_expense,
            'tax': tax,
            'remaining': remaining
        }

    def export_to_excel(self, year, month, file_path):
        wb = openpyxl.Workbook()
        ws_income = wb.active
        ws_income.title = "Incomes"
        ws_income.append(["Date", "Amount", "Source"])
        for i in self.filter_by_month_year(self.incomes, year, month):
            ws_income.append([i["date"], i["amount"], i["source"]])

        ws_expense = wb.create_sheet("Expenses")
        ws_expense.append(["Date", "Amount", "Category"])
        for e in self.filter_by_month_year(self.expenses, year, month):
            ws_expense.append([e["date"], e["amount"], e["category"]])

        wb.save(file_path)


class FinanceApp:
    COLORS = {
        "add_income": "#2ecc71",     # ירוק
        "add_expense": "#e74c3c",    # אדום
        "delete_income": "#3498db",  # כחול
        "delete_expense": "#e67e22",  # כתום
        "show_summary": "#9b59b6",   # סגול
        "monthly_summary": "#f1c40f",  # צהוב
        "show_chart": "#8e44ad",     # סגול כהה
        "export_excel": "#95a5a6",   # אפור
    }

    POPUP_CONFIG = {
        "add_income": {"bg": "#d4edda", "emoji": "✅"},
        "add_expense": {"bg": "#f8d7da", "emoji": "❌"},
        "delete_income": {"bg": "#d0e7f9", "emoji": "🗑️"},
        "delete_expense": {"bg": "#fdebd0", "emoji": "🗑️"},
        "show_summary": {"bg": "#e9d7f7", "emoji": "📊"},
        "monthly_summary": {"bg": "#fcf3cf", "emoji": "📅"},
        "show_chart": {"bg": "#dcd6f7", "emoji": "📈"},
        "export_excel": {"bg": "#d7dbdd", "emoji": "📤"},
    }

    def __init__(self, root):
        self.pf = PersonalFinance()
        self.root = root
        self.root.title("Personal Finance Manager - DY")
        self.root.geometry("450x680")
        self.root.configure(bg="#f0f4f8")
        self.currency = list(CURRENCIES.values())[0]
        self.create_widgets()

    def create_widgets(self):
        tk.Label(self.root, text="Personal Finance Manager - DY",
                 font=("Arial", 18, "bold"), bg="#f0f4f8", fg="#34495e").pack(pady=(20, 15))

        self.currency_box = ttk.Combobox(
            self.root, values=list(CURRENCIES.keys()), state="readonly")
        self.currency_box.set("ILS")
        self.currency_box.pack(pady=(0, 20))
        self.currency_box.bind("<<ComboboxSelected>>", self.set_currency)

        btn_frame = tk.Frame(self.root, bg="#f0f4f8")
        btn_frame.pack(pady=10)

        actions = [
            ("➕ Add Income", self.add_income,
             self.COLORS["add_income"], "add_income"),
            ("➖ Add Expense", self.add_expense,
             self.COLORS["add_expense"], "add_expense"),
            ("🗑️ Delete Income", self.delete_income_gui,
             self.COLORS["delete_income"], "delete_income"),
            ("🗑️ Delete Expense", self.delete_expense_gui,
             self.COLORS["delete_expense"], "delete_expense"),
            ("📊 Show Summary", self.show_summary,
             self.COLORS["show_summary"], "show_summary"),
            ("📅 Monthly Summary", self.show_monthly_summary,
             self.COLORS["monthly_summary"], "monthly_summary"),
            ("📈 Expense Chart", self.show_chart,
             self.COLORS["show_chart"], "show_chart"),
            ("📤 Export to Excel", self.export_excel,
             self.COLORS["export_excel"], "export_excel")
        ]

        for text, func, color, key in actions:
            btn = self.create_button(btn_frame, text, func, color, key)
            btn.pack(pady=4)

    def create_button(self, parent, text, command, bg_color, key):
        def wrapped_command():
            command(bg_color, key)
        btn = tk.Button(parent, text=text, command=wrapped_command, bg=bg_color, fg="white",
                        font=("Arial", 12, "bold"), bd=0, relief="flat",
                        activebackground=self.darken_color(bg_color), cursor="hand2", width=28, padx=10, pady=8)
        return btn

    def darken_color(self, hex_color, factor=0.8):
        # מפחית את הבהירות של צבע HEX (ל-activebackground)
        hex_color = hex_color.lstrip('#')
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        dark_rgb = tuple(max(0, int(c * factor)) for c in rgb)
        return "#" + "".join(f"{c:02x}" for c in dark_rgb)

    def set_currency(self, event):
        self.currency = CURRENCIES[self.currency_box.get()]

    def popup_msg(self, key, message):
        conf = self.POPUP_CONFIG.get(key, {"bg": "#ffffff", "emoji": "ℹ️"})
        colored_popup("Notification", message, conf["bg"], conf["emoji"])

    def prompt_date(self, msg):
        while True:
            res = simpledialog.askstring("Date", msg, parent=self.root)
            if res is None:
                return None
            try:
                datetime.strptime(res, "%Y-%m-%d")
                return res
            except ValueError:
                self.popup_msg("add_expense", "⚠️ Use YYYY-MM-DD format.")

    def prompt_float(self, msg):
        while True:
            res = simpledialog.askstring("Amount", msg, parent=self.root)
            if res is None:
                return None
            try:
                val = float(res)
                if val < 0:
                    raise ValueError
                return val
            except:
                self.popup_msg(
                    "add_expense", "⚠️ Enter a valid positive number.")

    def prompt_string(self, msg):
        res = simpledialog.askstring("Input", msg, parent=self.root)
        if res and res.strip():
            return res.strip()
        self.popup_msg("add_expense", "⚠️ This field cannot be empty.")
        return None

    def add_income(self, bg_color=None, key=None):
        d = self.prompt_date("Enter date (YYYY-MM-DD):")
        a = self.prompt_float("Enter amount:")
        s = self.prompt_string("Enter source:")
        if None not in (d, a, s):
            self.pf.add_income(d, a, s)
            self.popup_msg(key, "✅ Income added successfully.")

    def add_expense(self, bg_color=None, key=None):
        d = self.prompt_date("Enter date (YYYY-MM-DD):")
        a = self.prompt_float("Enter amount:")
        c = self.prompt_string("Enter category:")
        if None not in (d, a, c):
            self.pf.add_expense(d, a, c)
            self.popup_msg(key, "❌ Expense added successfully.")

    def delete_income_gui(self, bg_color=None, key=None):
        items = [
            f"{i['date']} | {i['amount']} | {i['source']}" for i in self.pf.incomes]
        self.select_and_delete(items, self.pf.delete_income, key)

    def delete_expense_gui(self, bg_color=None, key=None):
        items = [
            f"{e['date']} | {e['amount']} | {e['category']}" for e in self.pf.expenses]
        self.select_and_delete(items, self.pf.delete_expense, key)

    def select_and_delete(self, items, delete_func, key):
        if not items:
            self.popup_msg(key, "No entries to delete.")
            return
        sel = simpledialog.askinteger(
            "Select item to delete",
            f"Choose item (1 to {len(items)}):\n\n" +
            "\n".join(f"{i+1}. {item}" for i, item in enumerate(items)),
            parent=self.root,
            minvalue=1,
            maxvalue=len(items)
        )
        if sel:
            delete_func(sel - 1)
            self.popup_msg(key, "🗑️ Entry deleted successfully.")

    def show_summary(self, bg_color=None, key=None):
        income = sum(i['amount'] for i in self.pf.incomes)
        expense = sum(e['amount'] for e in self.pf.expenses)
        tax = self.pf.calculate_tax(income)
        msg = (f"Total Income: {self.currency}{income:.2f}\n"
               f"Total Expense: {self.currency}{expense:.2f}\n"
               f"Tax: {self.currency}{tax:.2f}\n"
               f"Remaining: {self.currency}{income - expense - tax:.2f}")
        self.popup_msg(key, msg)

    def show_monthly_summary(self, bg_color=None, key=None):
        y, m = self.prompt_year_month()
        if y is None:
            return
        s = self.pf.monthly_summary(y, m)
        msg = (f"Summary for {y}-{m:02d}\n"
               f"Income: {self.currency}{s['total_income']:.2f}\n"
               f"Expenses: {self.currency}{s['total_expense']:.2f}\n"
               f"Tax: {self.currency}{s['tax']:.2f}\n"
               f"Remaining: {self.currency}{s['remaining']:.2f}")
        self.popup_msg(key, msg)

    def show_chart(self, bg_color=None, key=None):
        y, m = self.prompt_year_month()
        if y is None:
            return
        data = self.pf.filter_by_month_year(self.pf.expenses, y, m)
        if not data:
            self.popup_msg(key, "No expenses to show.")
            return
        totals = defaultdict(float)
        for d in data:
            totals[d["category"]] += d["amount"]
        plt.pie(totals.values(), labels=totals.keys(), autopct='%1.1f%%',
                startangle=90, colors=plt.get_cmap('Pastel1').colors)
        plt.axis('equal')
        plt.title(f"Expenses {y}-{m:02d}")
        plt.show()

    def export_excel(self, bg_color=None, key=None):
        y, m = self.prompt_year_month()
        if y is None:
            return
        file_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx", filetypes=[("Excel Files", "*.xlsx")])
        if file_path:
            self.pf.export_to_excel(y, m, file_path)
            self.popup_msg(key, f"Exported to {file_path}")

    def prompt_year_month(self):
        y = simpledialog.askinteger(
            "Year", "Enter year (e.g. 2025):", parent=self.root, minvalue=1900, maxvalue=2100)
        m = simpledialog.askinteger(
            "Month", "Enter month (1-12):", parent=self.root, minvalue=1, maxvalue=12)
        return (y, m) if y and m else (None, None)

    def set_currency(self, event):
        self.currency = CURRENCIES[self.currency_box.get()]


if __name__ == "__main__":
    root = tk.Tk()
    app = FinanceApp(root)
    root.mainloop()
