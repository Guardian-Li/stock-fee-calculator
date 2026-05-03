# Stock Fee Calculator

## 中文说明

这是一个 Windows 桌面版 A 股买卖收益计算器，使用 Python Tkinter 编写，数据使用 SQLite 本地保存。

### 功能

- 计算 A 股买入、卖出后的手续费、净收益和收益率。
- 使用 SQLite 本地数据库，不依赖 MySQL。
- 支持股票代码和股票名称自动补全。
- 支持保存交易记录，并在程序中查看、刷新和删除记录。
- 自动记住上一次使用的佣金设置。
- 股票数量单位为“手”，1 手 = 100 股。
- 卖出价支持通过 `+0.01` 和 `-0.01` 按钮微调。
- 输入买入价后，卖出价会先自动填入相同价格。
- 实时显示卖出价相对买入价是上涨、下跌还是持平。
- 在价格、数量、手续费等输入框里按 `Enter` 可以直接计算。

### 从源码运行

环境要求：

- Windows
- Python 3.10+
- Tkinter、SQLite 等 Python 标准库组件

运行命令：

```powershell
python gui.py
```

从源码运行时，程序会读取和写入 `gui.py` 同目录下的文件。

### 运行打包后的程序

请把下面三个文件放在同一个目录中运行：

```text
StockFeeCalculator.exe
stock_calculator.db
settings.json
```

如果只移动单独的 exe，股票自动补全和已有交易记录可能无法正常显示。程序会在 exe 所在目录查找 `stock_calculator.db`。

### 数据文件

- `stock_calculator.db`：SQLite 本地数据库，包含股票列表和交易记录。
- `settings.json`：本地设置文件，保存佣金费率和最低佣金。

如果 `settings.json` 不存在，程序会自动创建默认配置：

```json
{
  "commission_per_ten_thousand": "3",
  "min_commission": "5"
}
```

### 手续费规则

当前内置的 A 股手续费假设：

- 印花税：卖出单边收取，`0.05%`。
- 过户费：买入和卖出双边收取，`0.001%`。
- 佣金：界面中按“万分”输入。例如填 `3` 表示 `0.03%`，也就是常说的万三。
- 最低佣金：可配置，默认 `5` 元。

### 数据库表

`stock_master` 用于保存股票代码和名称，支持自动补全。

`trade_records` 用于保存交易计算记录，包括：

- 股票代码和名称
- 买入价和卖出价
- 手数和换算后的股数
- 各项手续费
- 净收益
- 赚/亏百分比

### 打包 exe

安装 PyInstaller 后运行：

```powershell
python -m PyInstaller --onefile --windowed --name StockFeeCalculator gui.py
```

生成的 exe 会出现在 `dist/` 目录下。

## English

A Windows Tkinter desktop app for calculating A-share trading profit, fees, and saved trade records.

## Features

- Calculates A-share buy/sell profit and fees.
- Uses SQLite for local storage.
- Supports stock code/name autocomplete from a local stock database.
- Saves and lists trade records.
- Remembers commission settings in `settings.json`.
- Uses "hands" as the trading quantity unit; 1 hand equals 100 shares.
- Lets you adjust the sell price by `0.01` using the `+0.01` and `-0.01` buttons.
- Shows the sell price rise/fall percentage compared with the buy price.
- Pressing `Enter` in price/quantity/fee inputs runs the calculation.

## Run From Source

Requirements:

- Windows
- Python 3.10+
- Tkinter, SQLite, and standard library modules bundled with Python

```powershell
python gui.py
```

The app reads and writes files in the same directory as `gui.py` when run from source.

## Run The Packaged App

Use the executable in the same folder as the SQLite database:

```text
StockFeeCalculator.exe
stock_calculator.db
settings.json
```

Do not move only the executable by itself if you want stock autocomplete and existing records to work. The app expects `stock_calculator.db` to be next to the executable.

## App Data

- `stock_calculator.db`: local SQLite database.
- `settings.json`: local app settings.

`settings.json` is created automatically if it does not exist. The default settings are:

```json
{
  "commission_per_ten_thousand": "3",
  "min_commission": "5"
}
```

## Fee Rules

The current built-in A-share fee assumptions are:

- Stamp duty: sell side only, `0.05%`.
- Transfer fee: buy and sell side, `0.001%`.
- Brokerage commission: configurable in ten-thousandths. For example, entering `3` means `0.03%`, commonly called "wan san".
- Minimum brokerage commission: configurable, default `5` yuan.

## Database Tables

`stock_master` stores stock code/name data for autocomplete.

`trade_records` stores saved calculations, including:

- stock code and name
- buy and sell price
- hand count and converted share quantity
- fees
- net profit
- profit/loss percentage

## Build EXE

Install PyInstaller, then run:

```powershell
python -m PyInstaller --onefile --windowed --name StockFeeCalculator gui.py
```

The generated executable appears under `dist/`.
