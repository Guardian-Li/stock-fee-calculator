import tkinter as tk
from decimal import Decimal
from tkinter import messagebox, ttk

from calculations import money, parse_decimal
from database import delete_position, load_positions, save_position


class PositionsPage(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, padding=(0, 12, 0, 0))
        self.app = app
        self.position_entries = {}
        self.positions_tree = None
        self.summary_var = tk.StringVar(value="持仓：0 条")
        self.build()

    def build(self):
        form = ttk.LabelFrame(self, text="设置持仓", padding=12)
        form.pack(fill=tk.X, pady=(0, 10))

        fields = [
            ("stock_code", "股票代码", ""),
            ("stock_name", "股票名称", ""),
            ("hands", "持仓手数", ""),
            ("cost_price", "持仓成本价", ""),
        ]
        for index, (key, label, default) in enumerate(fields):
            row = index // 2
            col = 0 if index % 2 == 0 else 2
            ttk.Label(form, text=label).grid(row=row, column=col, sticky=tk.W, padx=(0, 8), pady=6)
            entry = ttk.Entry(form, width=26)
            entry.insert(0, default)
            entry.grid(row=row, column=col + 1, sticky=tk.EW, padx=(0, 18), pady=6)
            self.position_entries[key] = entry

        form.columnconfigure(1, weight=1)
        form.columnconfigure(3, weight=1)

        actions = ttk.Frame(self)
        actions.pack(fill=tk.X, pady=(0, 8))
        ttk.Button(actions, text="使用当前股票", command=self.fill_from_current_stock).pack(side=tk.LEFT)
        ttk.Button(actions, text="保存/重设持仓", command=self.save_position).pack(side=tk.LEFT, padx=8)
        ttk.Button(actions, text="删除选中持仓", command=self.delete_selected_position).pack(side=tk.LEFT)
        ttk.Button(actions, text="刷新持仓", command=self.refresh).pack(side=tk.LEFT, padx=8)
        ttk.Label(actions, textvariable=self.summary_var, font=("Microsoft YaHei UI", 10, "bold")).pack(side=tk.RIGHT)

        columns = (
            "stock",
            "hands",
            "quantity",
            "initial_cost",
            "applied_profit",
            "adjusted_cost",
            "updated_at",
        )
        table_frame = ttk.Frame(self)
        table_frame.pack(fill=tk.BOTH, expand=True)
        self.positions_tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=16)
        headings = {
            "stock": "股票",
            "hands": "持仓手数",
            "quantity": "股数",
            "initial_cost": "原始成本价",
            "applied_profit": "已摊净收益",
            "adjusted_cost": "摊后成本价",
            "updated_at": "更新时间",
        }
        widths = {
            "stock": 160,
            "hands": 90,
            "quantity": 90,
            "initial_cost": 110,
            "applied_profit": 120,
            "adjusted_cost": 110,
            "updated_at": 150,
        }
        for col in columns:
            self.positions_tree.heading(col, text=headings[col])
            self.positions_tree.column(col, width=widths[col], anchor=tk.CENTER)

        y_scroll = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.positions_tree.yview)
        self.positions_tree.configure(yscrollcommand=y_scroll.set)
        self.positions_tree.grid(row=0, column=0, sticky=tk.NSEW)
        y_scroll.grid(row=0, column=1, sticky=tk.NS)
        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)
        self.refresh()

    def fill_from_current_stock(self):
        code = self.app.code_var.get().strip()
        name = self.app.name_var.get().strip()
        if code in self.app.stock_by_code:
            name = self.app.stock_by_code[code]["stock_name"]
        self.position_entries["stock_code"].delete(0, tk.END)
        self.position_entries["stock_code"].insert(0, code)
        self.position_entries["stock_name"].delete(0, tk.END)
        self.position_entries["stock_name"].insert(0, name)

    def save_position(self):
        try:
            stock_code = self.position_entries["stock_code"].get().strip()
            stock_name = self.position_entries["stock_name"].get().strip()
            if stock_code in self.app.stock_by_code:
                stock_name = self.app.stock_by_code[stock_code]["stock_name"]
                self.position_entries["stock_name"].delete(0, tk.END)
                self.position_entries["stock_name"].insert(0, stock_name)
            if not stock_code or not stock_name:
                raise ValueError("请填写股票代码和股票名称")
            hands = parse_decimal(self.position_entries["hands"].get(), "持仓手数")
            cost_price = parse_decimal(self.position_entries["cost_price"].get(), "持仓成本价")
            if hands <= 0:
                raise ValueError("持仓手数必须大于 0")
            save_position(stock_code, stock_name, hands, cost_price)
        except ValueError as exc:
            messagebox.showerror("持仓设置有误", str(exc))
            return
        except Exception as exc:
            messagebox.showerror("保存失败", str(exc))
            return

        messagebox.showinfo("保存成功", "持仓成本已保存。之后同股票交易的净利润会自动摊入成本。")
        self.refresh()

    def delete_selected_position(self):
        if self.positions_tree is None:
            return
        selection = self.positions_tree.selection()
        if not selection:
            messagebox.showinfo("请选择持仓", "请先选中一条持仓记录。")
            return
        values = self.positions_tree.item(selection[0], "values")
        stock_text = values[0]
        stock_code = stock_text.split(" ", 1)[0]
        if not messagebox.askyesno("确认删除", f"确定删除持仓 {stock_text} 吗？"):
            return
        try:
            delete_position(stock_code)
        except Exception as exc:
            messagebox.showerror("删除失败", str(exc))
            return
        self.refresh()

    def refresh(self):
        if self.positions_tree is None:
            return
        for item in self.positions_tree.get_children():
            self.positions_tree.delete(item)

        try:
            positions = load_positions()
        except Exception as exc:
            messagebox.showerror("读取失败", f"无法读取持仓记录：\n{exc}")
            return

        total_adjusted_cost = Decimal("0")
        for position in positions:
            quantity = Decimal(str(position["quantity"]))
            initial_cost_price = Decimal(str(position["initial_cost_price"]))
            applied_profit = Decimal(str(position["accumulated_net_profit"] or "0"))
            initial_total_cost = initial_cost_price * quantity
            adjusted_total_cost = initial_total_cost - applied_profit
            adjusted_cost = Decimal("0") if quantity == 0 else money(adjusted_total_cost / quantity)
            total_adjusted_cost += adjusted_total_cost
            stock = f"{position['stock_code']} {position['stock_name']}"
            self.positions_tree.insert(
                "",
                tk.END,
                values=(
                    stock,
                    position["hand_count"],
                    position["quantity"],
                    initial_cost_price,
                    applied_profit,
                    adjusted_cost,
                    position["updated_at"],
                ),
            )
        self.summary_var.set(f"持仓：{len(positions)} 条，摊后总成本：{money(total_adjusted_cost)} 元")
