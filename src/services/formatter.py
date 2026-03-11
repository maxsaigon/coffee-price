"""
Compact Telegram message formatter with volatility indicators.
"""

from datetime import datetime
from typing import Dict, Any, Optional, List


def _icon(change: float) -> str:
    if change > 0:
        return "▲"
    elif change < 0:
        return "▼"
    return "–"


def _millions(value: float) -> str:
    """Format VND value (raw dong) as triệu (millions) with 1 decimal."""
    return f"{value / 1_000_000:,.1f}"


class MessageFormatter:
    """Build compact Telegram messages from scraped price data."""

    @staticmethod
    def format_full_report(
        international_data: Optional[Dict[str, Any]],
        domestic_data: Optional[Dict[str, Any]],
        gold_data: Optional[Dict[str, Any]],
    ) -> str:
        now = datetime.now().strftime("%d/%m %H:%M")
        parts: List[str] = [f"☕ *Giá* {now}"]

        # 1. Domestic coffee (Top priority)
        if domestic_data:
            parts.append("\n🇻🇳 *VN* (₫/kg)")
            order = ['Đắk Lắk', 'Lâm Đồng', 'Gia Lai', 'Đắk Nông']
            locs = sorted(
                domestic_data.keys(),
                key=lambda x: order.index(x) if x in order else 99,
            )

            prices: List[float] = []
            changes: List[float] = []
            short_map = {'Đắk Lắk': 'ĐL', 'Lâm Đồng': 'LĐ', 'Gia Lai': 'GL', 'Đắk Nông': 'ĐN'}

            for loc in locs:
                d = domestic_data[loc]
                if not d.get('success'):
                    continue
                p = d['price']
                c = d['change']
                prices.append(p)
                changes.append(c)

                short = short_map.get(loc, loc[:2].upper())
                line = f"{short} `{p/1000:g}k`"
                if c != 0:
                    line += f" {_icon(c)}`{abs(c)/1000:g}k`"
                parts.append(line)

            if prices:
                avg = sum(prices) / len(prices)
                spread = max(prices) - min(prices)
                avg_chg = sum(changes) / len(changes) if changes else 0
                parts.append(f"📊 TB `{avg/1000:g}k` {_icon(avg_chg)}`{abs(avg_chg)/1000:g}k` | Δ `{spread/1000:g}k`")
        elif domestic_data is None:
            parts.append("\n🇻🇳 ⚠️ N/A")

        # 2. International coffee
        if international_data:
            parts.append("\n🌍 *TG*")
            for name, d in international_data.items():
                if not d.get('success'):
                    continue
                p = d['price']
                c = d['change']
                unit = d.get('currency', '')
                short = name.split('(')[0].strip().replace('Coffee', '').strip()[:3].upper() # e.g. ROB, ARA
                line = f"{short} `{p:,.0f}`{unit}"
                if c != 0:
                    line += f" {_icon(c)}`{abs(c):,.0f}`"
                parts.append(line)

        # 3. Gold
        if gold_data:
            domestic_gold = {k: v for k, v in gold_data.items() if v.get('currency') == 'VND'}
            world_gold = {k: v for k, v in gold_data.items() if v.get('currency') != 'VND'}

            if domestic_gold:
                parts.append("\n🪙 *Vàng VN* (tr)")
                for name, d in domestic_gold.items():
                    if not d.get('success'):
                        continue
                    buy = d['buy']
                    sell = d['sell']
                    chg = d.get('change_sell', 0)
                    short = name.replace('Vàng', '').replace('SJC', '').strip()[:5] or 'SJC'
                    line = f"{short} M`{_millions(buy)}` B`{_millions(sell)}`"
                    if chg != 0:
                        line += f" {_icon(chg)}`{abs(chg)/1_000_000:g}`"
                    parts.append(line)

            if world_gold:
                parts.append("\n🌐 *Vàng TG*")
                for name, d in world_gold.items():
                    if not d.get('success'):
                        continue
                    p = d['price']
                    c = d.get('change', 0)
                    unit = d['currency']
                    short = name.split()[0][:2].upper()
                    line = f"{short} `{p:,.0f}`{unit}"
                    if c != 0:
                        line += f" {_icon(c)}`{abs(c):,.0f}`"
                    parts.append(line)
        elif gold_data is None:
            parts.append("\n🪙 ⚠️ N/A")

        return "\n".join(parts)
