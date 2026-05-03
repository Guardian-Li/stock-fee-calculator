import sys
from decimal import Decimal
from pathlib import Path


APP_DIR = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
DB_FILE = APP_DIR / "stock_calculator.db"
SETTINGS_FILE = APP_DIR / "settings.json"

TRADE_TABLE = "trade_records"
STOCK_TABLE = "stock_master"
POSITION_TABLE = "positions"

STAMP_TAX_RATE = Decimal("0.0005")
TRANSFER_FEE_RATE = Decimal("0.00001")
DEFAULT_COMMISSION_PER_TEN_THOUSAND = Decimal("3")
DEFAULT_MIN_COMMISSION = Decimal("5")
SHARES_PER_HAND = Decimal("100")
