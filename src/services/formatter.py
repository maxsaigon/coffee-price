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
        parts: List[str] = [f"☕ *CAFE* | {now}"]

        # International coffee
        if international_data:
            lines = ["", "🌍 *Quốc tế*"]
            for name, d in international_data.items():
                if not d.get('success'):
                    continue
                p = d['price']
                c = d['change']
                pct = d['change_percent']
                unit = d.get('currency', '')
                # Short name
                short = name.split('(')[0].strip()
                line = f"{short} `{p:,.2f}` {unit}"
                if c != 0:
                    line += f" {_icon(c)}`{pct:+.1f}%`"
                lines.append(line)
            parts.extend(lines)

        # ----- Gold prices -----
        if gold_data:
            # Separate domestic gold from world gold
            domestic_gold = {k: v for k, v in gold_data.items() if v.get('currency') == 'VND'}
            world_gold = {k: v for k, v in gold_data.items() if v.get('currency') != 'VND'}

            if domestic_gold:
                lines = ["", "🪙 *Vàng trong nước* (triệu ₫)"]
                for name, d in domestic_gold.items():
                    if not d.get('success'):
                        continue
                    buy = d['buy']
                    sell = d['sell']
                    chg = d.get('change_sell', 0)
                    line = f"{name}  M `{_millions(buy)}` | B `{_millions(sell)}`"
                    if chg != 0:
                        line += f" {_icon(chg)}`{chg / 1_000_000:+.1f}`"
                    lines.append(line)
                parts.extend(lines)

            if world_gold:
                lines = ["", "🌐 *Vàng thế giới*"]
                for name, d in world_gold.items():
                    if not d.get('success'):
                        continue
                    p = d['price']
                    c = d.get('change', 0)
                    unit = d['currency']
                    line = f"{name} `{p:,.2f}` {unit}"
                    if c != 0:
                        pct = (c / (p - c)) * 100 if (p - c) != 0 else 0
                        line += f" {_icon(c)}`{pct:+.1f}%`"
                    lines.append(line)
                parts.extend(lines)
        elif gold_data is None:
            parts.append("\n🪙 ⚠️ Vàng: N/A")

        # Domestic coffee
        if domestic_data:
            parts.append("")
            parts.append("🇻🇳 *Việt Nam* ₫/kg")
            order = ['Đắk Lắk', 'Lâm Đồng', 'Gia Lai', 'Đắk Nông']
            locs = sorted(
                domestic_data.keys(),
                key=lambda x: order.index(x) if x in order else 99,
            )

            prices: List[float] = []
            changes: List[float] = []

            for loc in locs:
                d = domestic_data[loc]
                if not d.get('success'):
                    continue
                p = d['price']
                c = d['change']
                prices.append(p)
                changes.append(c)

                # Abbreviated province name for compactness
                short = loc.replace('Đắk ', 'Đ.').replace('Lâm ', 'L.').replace('Gia ', 'G.').replace('Đắk ', 'Đ.')
                line = f"{short} `{p:,.0f}`"
                if c != 0:
                    pct = (c / (p - c)) * 100 if (p - c) != 0 else 0
                    line += f" {_icon(c)}`{abs(c):,.0f}` (`{pct:+.1f}%`)"
                parts.append(line)

            # Volatility summary
            if prices:
                avg = sum(prices) / len(prices)
                spread = max(prices) - min(prices)
                avg_chg = sum(changes) / len(changes) if changes else 0
                avg_pct = (avg_chg / (avg - avg_chg)) * 100 if (avg - avg_chg) != 0 else 0

                parts.append(
                    f"📊 TB `{avg:,.0f}` {_icon(avg_chg)}`{avg_pct:+.1f}%` | "
                    f"Chênh `{spread:,.0f}`"
                )
        elif domestic_data is None:
            parts.append("\n🇻🇳 ⚠️ N/A")

        return "\n".join(parts)
