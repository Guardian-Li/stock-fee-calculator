from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from app_config import SHARES_PER_HAND, STAMP_TAX_RATE, TRANSFER_FEE_RATE


def money(value):
    return Decimal(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def parse_decimal(value, field_name):
    try:
        result = Decimal(str(value).strip())
    except (InvalidOperation, ValueError):
        raise ValueError(f"{field_name} 必须是数字")
    if result < 0:
        raise ValueError(f"{field_name} 不能小于 0")
    return result


def calculate_profit(buy_price, sell_price, hands, commission_per_ten_thousand, min_commission):
    quantity = hands * SHARES_PER_HAND
    commission_rate = commission_per_ten_thousand / Decimal("10000")

    buy_amount = money(buy_price * quantity)
    sell_amount = money(sell_price * quantity)
    buy_commission = max(money(buy_amount * commission_rate), min_commission)
    sell_commission = max(money(sell_amount * commission_rate), min_commission)
    buy_transfer_fee = money(buy_amount * TRANSFER_FEE_RATE)
    sell_transfer_fee = money(sell_amount * TRANSFER_FEE_RATE)
    stamp_tax = money(sell_amount * STAMP_TAX_RATE)

    total_buy_cost = money(buy_amount + buy_commission + buy_transfer_fee)
    total_sell_fee = money(sell_commission + sell_transfer_fee + stamp_tax)
    total_sell_income = money(sell_amount - total_sell_fee)
    total_fee = money(buy_commission + sell_commission + buy_transfer_fee + sell_transfer_fee + stamp_tax)
    gross_profit = money(sell_amount - buy_amount)
    net_profit = money(total_sell_income - total_buy_cost)
    return_rate = Decimal("0") if total_buy_cost == 0 else (net_profit / total_buy_cost * Decimal("100")).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )

    return {
        "hands": hands,
        "quantity": int(quantity),
        "commission_rate": commission_rate,
        "buy_amount": buy_amount,
        "sell_amount": sell_amount,
        "buy_commission": buy_commission,
        "sell_commission": sell_commission,
        "buy_transfer_fee": buy_transfer_fee,
        "sell_transfer_fee": sell_transfer_fee,
        "stamp_tax": stamp_tax,
        "total_buy_cost": total_buy_cost,
        "total_sell_income": total_sell_income,
        "total_fee": total_fee,
        "gross_profit": gross_profit,
        "net_profit": net_profit,
        "return_rate": return_rate,
    }


def format_profit_rate(value):
    value = Decimal(str(value))
    if value > 0:
        return f"赚 {value}%"
    if value < 0:
        return f"亏 {abs(value)}%"
    return "不赚不亏 0.00%"
