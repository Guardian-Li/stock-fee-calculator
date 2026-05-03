import tkinter as tk
from decimal import Decimal, ROUND_HALF_UP
from tkinter import messagebox, ttk

from app_config import DB_FILE
from calculations import calculate_profit, format_profit_rate, parse_decimal
from database import save_record
from settings_store import save_settings


class CalculatorPage(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, padding=(0, 12, 0, 0))
        self.app = app
        self.entries = {}
        self.result_vars = {}
        self.current_matches = []
        self.last_inputs = None
        self.last_result = None
        self.buy_price_var = tk.StringVar()
        self.sell_price_var = tk.StringVar()
        self.price_change_var = tk.StringVar(value="涨跌：-")
        self.last_auto_sell_price = ""
        self.sell_price_manually_changed = False
        self.syncing_sell_price = False
        self.build()

    def build(self):
        form = ttk.LabelFrame(self, text="交易信息", padding=12)
        form.pack(fill=tk.X)

        ttk.Label(form, text="股票代码").grid(row=0, column=0, sticky=tk.W, padx=(0, 8), pady=6)
        code_entry = ttk.Entry(form, textvariable=self.app.code_var, width=26)
        code_entry.grid(row=0, column=1, sticky=tk.EW, padx=(0, 18), pady=6)
        code_entry.bind("<KeyRelease>", self.on_code_key)
        code_entry.bind("<Return>", self.use_first_match)
        code_entry.bind("<FocusOut>", self.fill_by_code_if_exact)
        self.entries["stock_code"] = code_entry

        ttk.Label(form, text="股票名称").grid(row=0, column=2, sticky=tk.W, padx=(0, 8), pady=6)
        name_entry = ttk.Entry(form, textvariable=self.app.name_var, width=26)
        name_entry.grid(row=0, column=3, sticky=tk.EW, padx=(0, 18), pady=6)
        name_entry.bind("<KeyRelease>", self.on_name_key)
        name_entry.bind("<Return>", self.use_first_match)
        name_entry.bind("<FocusOut>", self.fill_by_name_if_exact)
        self.entries["stock_name"] = name_entry

        self.suggestion_box = tk.Listbox(form, height=5, activestyle="dotbox", exportselection=False)
        self.suggestion_box.grid(row=1, column=1, columnspan=3, sticky=tk.EW, padx=(0, 18), pady=(0, 8))
        self.suggestion_box.bind("<<ListboxSelect>>", self.on_suggestion_selected)
        self.suggestion_box.bind("<ButtonRelease-1>", self.on_suggestion_selected)

        fields = [
            ("buy_price", "买入价格", ""),
            ("sell_price", "卖出价格", ""),
            ("hands", "数量（手）", ""),
            ("commission_per_ten_thousand", "佣金费率（万分）", self.app.settings["commission_per_ten_thousand"]),
            ("min_commission", "最低佣金（元）", self.app.settings["min_commission"]),
        ]

        for index, (key, label, default) in enumerate(fields):
            row = 2 + index // 2
            col = 0 if index % 2 == 0 else 2
            ttk.Label(form, text=label).grid(row=row, column=col, sticky=tk.W, padx=(0, 8), pady=6)
            if key == "sell_price":
                sell_frame = ttk.Frame(form)
                sell_frame.grid(row=row, column=col + 1, sticky=tk.EW, padx=(0, 18), pady=6)
                entry = ttk.Entry(sell_frame, width=14, textvariable=self.sell_price_var)
                entry.insert(0, default)
                entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
                ttk.Button(sell_frame, text="-0.01", width=6, command=lambda: self.adjust_sell_price(Decimal("-0.01"))).pack(
                    side=tk.LEFT, padx=(6, 0)
                )
                ttk.Button(sell_frame, text="+0.01", width=6, command=lambda: self.adjust_sell_price(Decimal("0.01"))).pack(
                    side=tk.LEFT, padx=(4, 0)
                )
                ttk.Label(sell_frame, textvariable=self.price_change_var, width=16).pack(side=tk.LEFT, padx=(8, 0))
            else:
                textvariable = self.buy_price_var if key == "buy_price" else None
                entry = ttk.Entry(form, width=26, textvariable=textvariable)
                entry.insert(0, default)
                entry.grid(row=row, column=col + 1, sticky=tk.EW, padx=(0, 18), pady=6)
            self.entries[key] = entry

        self.buy_price_var.trace_add("write", self.on_buy_price_changed)
        self.sell_price_var.trace_add("write", self.on_sell_price_changed)

        form.columnconfigure(1, weight=1)
        form.columnconfigure(3, weight=1)

        actions = ttk.Frame(self)
        actions.pack(fill=tk.X, pady=14)
        ttk.Button(actions, text="计算", command=self.on_calculate).pack(side=tk.LEFT)
        self.save_button = ttk.Button(actions, text="保存到数据库", command=self.on_save, state=tk.DISABLED)
        self.save_button.pack(side=tk.LEFT, padx=10)
        ttk.Button(actions, text="清空结果", command=self.clear_results).pack(side=tk.LEFT)
        ttk.Label(actions, textvariable=self.app.status_var).pack(side=tk.RIGHT)

        results = ttk.LabelFrame(self, text="计算结果", padding=12)
        results.pack(fill=tk.BOTH, expand=True)
        result_fields = [
            ("quantity", "换算股数"),
            ("buy_amount", "买入成交额"),
            ("sell_amount", "卖出成交额"),
            ("buy_commission", "买入佣金"),
            ("sell_commission", "卖出佣金"),
            ("buy_transfer_fee", "买入过户费"),
            ("sell_transfer_fee", "卖出过户费"),
            ("stamp_tax", "卖出印花税"),
            ("total_fee", "总手续费"),
            ("gross_profit", "毛收益"),
            ("net_profit", "净收益"),
            ("return_rate", "收益率"),
        ]
        for index, (key, label) in enumerate(result_fields):
            ttk.Label(results, text=label).grid(row=index, column=0, sticky=tk.W, pady=4)
            var = tk.StringVar(value="-")
            ttk.Label(results, textvariable=var, font=("Microsoft YaHei UI", 10, "bold")).grid(
                row=index, column=1, sticky=tk.W, padx=12, pady=4
            )
            self.result_vars[key] = var
        results.columnconfigure(1, weight=1)

    def match_stocks(self, text):
        keyword = text.strip().lower()
        if not keyword:
            return []
        matched = []
        for row in self.app.stock_rows:
            if row["stock_code"].startswith(keyword) or keyword in row["stock_name"].lower():
                matched.append(row)
            if len(matched) >= 20:
                break
        return matched

    def update_suggestions(self, rows):
        self.current_matches = rows
        self.suggestion_box.delete(0, tk.END)
        for row in rows:
            self.suggestion_box.insert(tk.END, f"{row['stock_code']}  {row['stock_name']}  {row['market_name']}")

    def on_code_key(self, event):
        if event.keysym in {"Up", "Down", "Escape", "Tab"}:
            return
        rows = self.match_stocks(self.app.code_var.get())
        self.update_suggestions(rows)
        if len(rows) == 1 or self.app.code_var.get().strip() in self.app.stock_by_code:
            self.fill_stock(rows[0], keep_code_text=True)
        elif rows:
            self.app.name_var.set(rows[0]["stock_name"])

    def on_name_key(self, event):
        if event.keysym in {"Up", "Down", "Escape", "Tab"}:
            return
        rows = self.match_stocks(self.app.name_var.get())
        self.update_suggestions(rows)
        if len(rows) == 1 or self.app.name_var.get().strip() in self.app.stock_by_name:
            self.fill_stock(rows[0], keep_name_text=True)
        elif rows:
            self.app.code_var.set(rows[0]["stock_code"])

    def on_suggestion_selected(self, _event=None):
        selection = self.suggestion_box.curselection()
        if selection and selection[0] < len(self.current_matches):
            self.fill_stock(self.current_matches[selection[0]])

    def use_first_match(self, _event=None):
        if self.current_matches:
            self.fill_stock(self.current_matches[0])
        return "break"

    def fill_by_code_if_exact(self, _event=None):
        code = self.app.code_var.get().strip()
        if code in self.app.stock_by_code:
            self.fill_stock(self.app.stock_by_code[code])

    def fill_by_name_if_exact(self, _event=None):
        name = self.app.name_var.get().strip()
        if name in self.app.stock_by_name:
            self.fill_stock(self.app.stock_by_name[name])

    def fill_stock(self, row, keep_code_text=False, keep_name_text=False):
        if not keep_code_text:
            self.app.code_var.set(row["stock_code"])
        if not keep_name_text:
            self.app.name_var.set(row["stock_name"])

    def on_buy_price_changed(self, *_args):
        buy_text = self.buy_price_var.get().strip()
        sell_text = self.sell_price_var.get().strip()
        if buy_text and (not self.sell_price_manually_changed or not sell_text):
            self.syncing_sell_price = True
            self.sell_price_var.set(buy_text)
            self.syncing_sell_price = False
            self.last_auto_sell_price = buy_text
        self.update_price_change()

    def on_sell_price_changed(self, *_args):
        if self.syncing_sell_price:
            self.update_price_change()
            return
        sell_text = self.sell_price_var.get().strip()
        if sell_text != self.last_auto_sell_price:
            self.sell_price_manually_changed = True
        self.update_price_change()

    def adjust_sell_price(self, step):
        base_text = self.sell_price_var.get().strip() or self.buy_price_var.get().strip() or "0"
        try:
            value = parse_decimal(base_text, "卖出价格")
        except ValueError:
            value = Decimal("0")
        value = max(Decimal("0"), value + step).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        self.sell_price_manually_changed = True
        self.sell_price_var.set(str(value))

    def update_price_change(self, _event=None):
        try:
            buy_price = parse_decimal(self.buy_price_var.get(), "买入价格")
            sell_price = parse_decimal(self.sell_price_var.get(), "卖出价格")
        except ValueError:
            self.price_change_var.set("涨跌：-")
            return
        if buy_price == 0:
            self.price_change_var.set("涨跌：-")
            return
        percent = ((sell_price - buy_price) / buy_price * Decimal("100")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        if percent > 0:
            self.price_change_var.set(f"涨 {percent}%")
        elif percent < 0:
            self.price_change_var.set(f"跌 {abs(percent)}%")
        else:
            self.price_change_var.set("持平 0.00%")

    def collect_inputs(self):
        buy_price = parse_decimal(self.entries["buy_price"].get(), "买入价格")
        sell_price = parse_decimal(self.entries["sell_price"].get(), "卖出价格")
        hands = parse_decimal(self.entries["hands"].get(), "数量（手）")
        if hands <= 0:
            raise ValueError("数量（手）必须大于 0")
        commission = parse_decimal(self.entries["commission_per_ten_thousand"].get(), "佣金费率（万分）")
        min_commission = parse_decimal(self.entries["min_commission"].get(), "最低佣金")
        save_settings(commission, min_commission)

        stock_code = self.app.code_var.get().strip()
        stock_name = self.app.name_var.get().strip()
        if stock_code in self.app.stock_by_code:
            stock_name = self.app.stock_by_code[stock_code]["stock_name"]
            self.app.name_var.set(stock_name)
        return {
            "stock_code": stock_code,
            "stock_name": stock_name,
            "buy_price": buy_price,
            "sell_price": sell_price,
            "hands": hands,
            "commission_per_ten_thousand": commission,
            "min_commission": min_commission,
        }

    def on_calculate(self):
        try:
            inputs = self.collect_inputs()
            result = calculate_profit(
                inputs["buy_price"],
                inputs["sell_price"],
                inputs["hands"],
                inputs["commission_per_ten_thousand"],
                inputs["min_commission"],
            )
        except ValueError as exc:
            messagebox.showerror("输入有误", str(exc))
            return

        for key, value in result.items():
            if key not in self.result_vars:
                continue
            if key == "quantity":
                self.result_vars[key].set(f"{value} 股")
            elif key == "return_rate":
                self.result_vars[key].set(format_profit_rate(value))
            else:
                self.result_vars[key].set(f"{value} 元")
        self.last_inputs = inputs
        self.last_result = result
        self.save_button.config(state=tk.NORMAL)

    def on_save(self):
        if not self.last_inputs or not self.last_result:
            messagebox.showinfo("请先计算", "计算完成后才能保存到数据库。")
            return
        try:
            save_record(self.last_inputs, self.last_result)
        except Exception as exc:
            messagebox.showerror("保存失败", str(exc))
            return
        messagebox.showinfo("保存成功", f"已保存到 {DB_FILE.name}")
        self.save_button.config(state=tk.DISABLED)
        self.app.refresh_records_and_positions()

    def clear_results(self):
        for var in self.result_vars.values():
            var.set("-")
        self.last_inputs = None
        self.last_result = None
        self.save_button.config(state=tk.DISABLED)

    def on_enter_calculate(self, event=None):
        widget = event.widget if event else None
        if widget in (self.entries.get("stock_code"), self.entries.get("stock_name")):
            return None
        self.on_calculate()
        return "break"
