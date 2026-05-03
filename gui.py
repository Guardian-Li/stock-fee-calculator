import tkinter as tk
from tkinter import messagebox, ttk

from database import load_stock_master
from pages.calculator_page import CalculatorPage
from pages.positions_page import PositionsPage
from pages.records_page import RecordsPage
from settings_store import load_settings


class StockFeeCalculatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("A股买卖收益计算器")
        self.root.geometry("1100x900")
        self.root.minsize(980, 820)

        self.stock_rows = []
        self.stock_by_code = {}
        self.stock_by_name = {}
        self.settings = load_settings()

        self.code_var = tk.StringVar()
        self.name_var = tk.StringVar()
        self.status_var = tk.StringVar(value="正在读取股票列表...")

        self.calculator_page = None
        self.records_page = None
        self.positions_page = None

        self.build_ui()
        self.root.bind("<Return>", self.on_enter)
        self.load_stocks_into_memory()

    def build_ui(self):
        main = ttk.Frame(self.root, padding=16)
        main.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main, text="A股买卖收益计算器", font=("Microsoft YaHei UI", 18, "bold")).pack(anchor=tk.W)
        ttk.Label(
            main,
            text="规则：数量单位为手，1手=100股；佣金费率单位为万分，万三请填3；印花税卖出单边0.05%；过户费买卖双边0.001%。",
            wraplength=730,
        ).pack(anchor=tk.W, pady=(8, 12))

        notebook = ttk.Notebook(main)
        notebook.pack(fill=tk.BOTH, expand=True)

        self.calculator_page = CalculatorPage(notebook, self)
        self.records_page = RecordsPage(notebook, self)
        self.positions_page = PositionsPage(notebook, self)

        notebook.add(self.calculator_page, text="收益计算")
        notebook.add(self.records_page, text="交易记录")
        notebook.add(self.positions_page, text="持仓成本")

    def load_stocks_into_memory(self):
        try:
            self.stock_rows = load_stock_master()
        except Exception as exc:
            self.status_var.set("股票列表读取失败")
            messagebox.showwarning("股票列表读取失败", f"无法读取股票主数据：\n{exc}")
            return

        self.stock_by_code = {row["stock_code"]: row for row in self.stock_rows}
        self.stock_by_name = {row["stock_name"]: row for row in self.stock_rows}
        self.status_var.set(f"已加载 {len(self.stock_rows)} 只股票")

    def refresh_records_and_positions(self):
        if self.records_page:
            self.records_page.refresh()
        if self.positions_page:
            self.positions_page.refresh()

    def on_enter(self, event=None):
        if self.calculator_page:
            return self.calculator_page.on_enter_calculate(event)
        return None


def main():
    root = tk.Tk()
    StockFeeCalculatorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
