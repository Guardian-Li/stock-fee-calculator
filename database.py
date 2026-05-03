import sqlite3
from datetime import datetime
from decimal import Decimal

from app_config import DB_FILE, POSITION_TABLE, SHARES_PER_HAND, STOCK_TABLE, TRADE_TABLE
from calculations import money


def get_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def row_to_dict(row):
    return dict(row)


def ensure_stock_table():
    with get_connection() as conn:
        conn.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {STOCK_TABLE} (
                stock_code TEXT PRIMARY KEY,
                stock_name TEXT NOT NULL,
                market_name TEXT NOT NULL
            )
            """
        )
        conn.execute(f"CREATE INDEX IF NOT EXISTS idx_stock_name ON {STOCK_TABLE}(stock_name)")
        conn.commit()


def load_stock_master():
    ensure_stock_table()
    with get_connection() as conn:
        rows = conn.execute(
            f"""
            SELECT stock_code, stock_name, market_name
            FROM {STOCK_TABLE}
            ORDER BY stock_code
            """
        ).fetchall()
        return [row_to_dict(row) for row in rows]


def ensure_position_table():
    with get_connection() as conn:
        conn.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {POSITION_TABLE} (
                stock_code TEXT PRIMARY KEY,
                stock_name TEXT NOT NULL,
                hand_count TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                initial_cost_price TEXT NOT NULL,
                accumulated_net_profit TEXT NOT NULL DEFAULT '0',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.commit()


def load_positions():
    ensure_position_table()
    with get_connection() as conn:
        rows = conn.execute(
            f"""
            SELECT stock_code, stock_name, hand_count, quantity, initial_cost_price,
                   accumulated_net_profit, created_at, updated_at
            FROM {POSITION_TABLE}
            ORDER BY stock_code
            """
        ).fetchall()
        return [row_to_dict(row) for row in rows]


def save_position(stock_code, stock_name, hands, cost_price):
    ensure_position_table()
    quantity = int(hands * SHARES_PER_HAND)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_connection() as conn:
        conn.execute(
            f"""
            INSERT INTO {POSITION_TABLE} (
                stock_code, stock_name, hand_count, quantity, initial_cost_price,
                accumulated_net_profit, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, '0', ?, ?)
            ON CONFLICT(stock_code) DO UPDATE SET
                stock_name = excluded.stock_name,
                hand_count = excluded.hand_count,
                quantity = excluded.quantity,
                initial_cost_price = excluded.initial_cost_price,
                accumulated_net_profit = '0',
                updated_at = excluded.updated_at
            """,
            (stock_code, stock_name, str(hands), quantity, str(cost_price), now, now),
        )
        conn.commit()


def delete_position(stock_code):
    ensure_position_table()
    with get_connection() as conn:
        conn.execute(f"DELETE FROM {POSITION_TABLE} WHERE stock_code = ?", (stock_code,))
        conn.commit()


def merge_unapplied_trades_to_position(stock_code):
    ensure_trade_table()
    ensure_position_table()
    with get_connection() as conn:
        position = conn.execute(
            f"SELECT stock_code FROM {POSITION_TABLE} WHERE stock_code = ?",
            (stock_code,),
        ).fetchone()
        if not position:
            raise ValueError("请先设置该股票的持仓")

        rows = conn.execute(
            f"""
            SELECT id, net_profit
            FROM {TRADE_TABLE}
            WHERE stock_code = ? AND position_applied = '0'
            ORDER BY id
            """,
            (stock_code,),
        ).fetchall()
        if not rows:
            return 0, Decimal("0")

        total_profit = sum((Decimal(str(row["net_profit"] or "0")) for row in rows), Decimal("0"))
        applied = apply_profit_to_position(conn, stock_code, total_profit)
        if applied:
            ids = [row["id"] for row in rows]
            placeholders = ",".join("?" for _ in ids)
            conn.execute(
                f"UPDATE {TRADE_TABLE} SET position_applied = '1' WHERE id IN ({placeholders})",
                ids,
            )
        conn.commit()
        return len(rows), money(total_profit)


def apply_profit_to_position(conn, stock_code, net_profit):
    row = conn.execute(
        f"SELECT accumulated_net_profit FROM {POSITION_TABLE} WHERE stock_code = ?",
        (stock_code,),
    ).fetchone()
    if not row:
        return False

    current_profit = Decimal(str(row["accumulated_net_profit"] or "0"))
    next_profit = money(current_profit + Decimal(str(net_profit)))
    conn.execute(
        f"""
        UPDATE {POSITION_TABLE}
        SET accumulated_net_profit = ?, updated_at = ?
        WHERE stock_code = ?
        """,
        (str(next_profit), datetime.now().strftime("%Y-%m-%d %H:%M:%S"), stock_code),
    )
    return True


def ensure_trade_table():
    with get_connection() as conn:
        conn.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {TRADE_TABLE} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                stock_code TEXT,
                stock_name TEXT,
                buy_price TEXT NOT NULL,
                sell_price TEXT NOT NULL,
                hand_count TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                commission_rate TEXT NOT NULL,
                min_commission TEXT NOT NULL,
                buy_amount TEXT NOT NULL,
                sell_amount TEXT NOT NULL,
                buy_commission TEXT NOT NULL,
                sell_commission TEXT NOT NULL,
                buy_transfer_fee TEXT NOT NULL,
                sell_transfer_fee TEXT NOT NULL,
                stamp_tax TEXT NOT NULL,
                total_fee TEXT NOT NULL,
                net_profit TEXT NOT NULL,
                return_rate TEXT NOT NULL,
                position_applied TEXT NOT NULL DEFAULT '0'
            )
            """
        )
        columns = {row["name"] for row in conn.execute(f"PRAGMA table_info({TRADE_TABLE})").fetchall()}
        if "hand_count" not in columns:
            conn.execute(f"ALTER TABLE {TRADE_TABLE} ADD COLUMN hand_count TEXT NOT NULL DEFAULT '0'")
        if "position_applied" not in columns:
            conn.execute(f"ALTER TABLE {TRADE_TABLE} ADD COLUMN position_applied TEXT NOT NULL DEFAULT '0'")
        conn.commit()


def load_trade_records():
    ensure_trade_table()
    with get_connection() as conn:
        rows = conn.execute(
            f"""
            SELECT
                id, created_at, stock_code, stock_name, hand_count, quantity,
                buy_price, sell_price, total_fee, net_profit, return_rate
            FROM {TRADE_TABLE}
            ORDER BY created_at DESC, id DESC
            LIMIT 500
            """
        ).fetchall()
        return [row_to_dict(row) for row in rows]


def save_record(inputs, result):
    ensure_trade_table()
    ensure_position_table()
    with get_connection() as conn:
        cursor = conn.execute(
            f"""
            INSERT INTO {TRADE_TABLE} (
                created_at, stock_code, stock_name, buy_price, sell_price, hand_count,
                quantity, commission_rate, min_commission, buy_amount, sell_amount,
                buy_commission, sell_commission, buy_transfer_fee, sell_transfer_fee,
                stamp_tax, total_fee, net_profit, return_rate, position_applied
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                inputs["stock_code"],
                inputs["stock_name"],
                str(inputs["buy_price"]),
                str(inputs["sell_price"]),
                str(inputs["hands"]),
                int(result["quantity"]),
                str(result["commission_rate"]),
                str(inputs["min_commission"]),
                str(result["buy_amount"]),
                str(result["sell_amount"]),
                str(result["buy_commission"]),
                str(result["sell_commission"]),
                str(result["buy_transfer_fee"]),
                str(result["sell_transfer_fee"]),
                str(result["stamp_tax"]),
                str(result["total_fee"]),
                str(result["net_profit"]),
                str(result["return_rate"]),
                "0",
            ),
        )
        applied = apply_profit_to_position(conn, inputs["stock_code"], result["net_profit"])
        if applied:
            conn.execute(f"UPDATE {TRADE_TABLE} SET position_applied = '1' WHERE id = ?", (cursor.lastrowid,))
        conn.commit()


def delete_trade_record(record_id):
    ensure_trade_table()
    ensure_position_table()
    with get_connection() as conn:
        record = conn.execute(
            f"SELECT stock_code, net_profit, position_applied FROM {TRADE_TABLE} WHERE id = ?",
            (record_id,),
        ).fetchone()
        if record and str(record["position_applied"]) == "1":
            apply_profit_to_position(conn, record["stock_code"], -Decimal(str(record["net_profit"] or "0")))
        conn.execute(f"DELETE FROM {TRADE_TABLE} WHERE id = ?", (record_id,))
        conn.commit()
