import tkinter as tk
from decimal import Decimal
from tkinter import messagebox, ttk

from calculations import format_profit_rate
from database import delete_trade_record, load_trade_records


class RecordsPage(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, padding=(0, 12, 0, 0))
        self.app = app
        self.summary_var = tk.StringVar(value="总净收益：0.00 元")
        self.records_tree = None
        self.build()

    def build(self):
        toolbar = ttk.Frame(self)
        toolbar.pack(fill=tk.X, pady=(0, 8))
        ttk.Button(toolbar, text="刷新记录", command=self.refresh).pack(side=tk.LEFT)
        ttk.Button(toolbar, text="删除选中记录", command=self.delete_selected_record).pack(side=tk.LEFT, padx=8)
        ttk.Label(toolbar, textvariable=self.summary_var, font=("Microsoft YaHei UI", 10, "bold")).pack(side=tk.RIGHT)

        columns = (
            "id",
            "created_at",
            "stock",
            "hands",
            "quantity",
            "buy_price",
            "sell_price",
            "total_fee",
            "net_profit",
            "return_rate",
        )
        table_frame = ttk.Frame(self)
        table_frame.pack(fill=tk.BOTH, expand=True)
        self.records_tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=20)

        headings = {
            "id": "ID",
            "created_at": "保存时间",
            "stock": "股票",
            "hands": "手数",
            "quantity": "股数",
            "buy_price": "买入价",
            "sell_price": "卖出价",
            "total_fee": "手续费",
            "net_profit": "净收益",
            "return_rate": "赚/亏比例",
        }
        widths = {
            "id": 50,
            "created_at": 150,
            "stock": 160,
            "hands": 70,
            "quantity": 80,
            "buy_price": 80,
            "sell_price": 80,
            "total_fee": 90,
            "net_profit": 90,
            "return_rate": 90,
        }
        for col in columns:
            self.records_tree.heading(col, text=headings[col])
            self.records_tree.column(col, width=widths[col], anchor=tk.CENTER)

        y_scroll = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.records_tree.yview)
        x_scroll = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=self.records_tree.xview)
        self.records_tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)
        self.records_tree.grid(row=0, column=0, sticky=tk.NSEW)
        y_scroll.grid(row=0, column=1, sticky=tk.NS)
        x_scroll.grid(row=1, column=0, sticky=tk.EW)
        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)
        self.refresh()

    def refresh(self):
        if self.records_tree is None:
            return
        for item in self.records_tree.get_children():
            self.records_tree.delete(item)

        try:
            records = load_trade_records()
        except Exception as exc:
            messagebox.showerror("读取失败", f"无法读取交易记录：\n{exc}")
            return

        total_net_profit = Decimal("0")
        for record in records:
            record_net_profit = Decimal(str(record["net_profit"] or "0"))
            total_net_profit += record_net_profit
            stock = f"{record['stock_code']} {record['stock_name']}"
            self.records_tree.insert(
                "",
                tk.END,
                values=(
                    record["id"],
                    str(record["created_at"] or ""),
                    stock,
                    record["hand_count"],
                    record["quantity"],
                    record["buy_price"],
                    record["sell_price"],
                    record["total_fee"],
                    record["net_profit"],
                    format_profit_rate(record["return_rate"]),
                ),
            )
        self.summary_var.set(f"总净收益：{total_net_profit.quantize(Decimal('0.01'))} 元，共 {len(records)} 条")

    def delete_selected_record(self):
        if self.records_tree is None:
            return
        selection = self.records_tree.selection()
        if not selection:
            messagebox.showinfo("请选择记录", "请先在交易记录表里选中一条记录。")
            return

        item = selection[0]
        values = self.records_tree.item(item, "values")
        record_id = values[0]
        stock = values[2] if len(values) > 2 else ""
        if not messagebox.askyesno("确认删除", f"确定删除记录 {record_id}：{stock} 吗？"):
            return

        try:
            delete_trade_record(record_id)
        except Exception as exc:
            messagebox.showerror("删除失败", f"无法删除交易记录：\n{exc}")
            return
        self.app.refresh_records_and_positions()
