"""
Compact Telegram message formatter — 2 groups: Coffee + Gold.
"""

from datetime import datetime
from typing import Dict, Any, Optional, List


def _icon(change: float) -> str:
    if change > 0:
        return "▲"
    elif change < 0:
        return "▼"
    return ""


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
        forex_data: Optional[Dict[str, Any]] = None,
    ) -> str:
        now = datetime.now().strftime("%d/%m %H:%M")
        parts: List[str] = [f"☕ {now}"]

        # --- Coffee: international ---
        if international_data:
            for name, d in international_data.items():
                if not d.get('success'):
                    continue
                p = d['price']
                c = d['change']
                pct = d['change_percent']
                # Short labels
                if 'Robusta' in name:
                    short, unit = 'Rob', '$/T'
                elif 'Arabica' in name:
                    short, unit = 'Ara', '¢/lb'
                else:
                    short = name.split('(')[0].strip()
                    unit = d.get('currency', '')
                line = f"{short} `{p:,.0f}` {unit}"
                if c != 0:
                    line += f" {_icon(c)}`{pct:+.1f}%`"
                parts.append(line)

        # --- Coffee: domestic ---
        if domestic_data:
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

                short = loc.replace('Đắk ', 'Đ.').replace('Lâm ', 'L.').replace('Gia ', 'G.')
                line = f"{short} `{p:,.0f}`"
                if c != 0:
                    pct = (c / (p - c)) * 100 if (p - c) != 0 else 0
                    line += f" {_icon(c)}`{abs(c):,.0f}` `{pct:+.1f}%`"
                parts.append(line)

            # Summary line
            if prices:
                avg = sum(prices) / len(prices)
                spread = max(prices) - min(prices)
                avg_chg = sum(changes) / len(changes) if changes else 0
                avg_pct = (avg_chg / (avg - avg_chg)) * 100 if (avg - avg_chg) != 0 else 0
                parts.append(
                    f"TB `{avg:,.0f}` {_icon(avg_chg)}`{avg_pct:+.1f}%` Δ`{spread:,.0f}`"
                )
        elif domestic_data is None and international_data is None:
            parts.append("⚠️ Cafe: N/A")

        # --- Gold + Forex ---
        if gold_data or forex_data:
            domestic_gold = {k: v for k, v in (gold_data or {}).items() if v.get('currency') == 'VND'}
            world_gold = {k: v for k, v in (gold_data or {}).items() if v.get('currency') != 'VND'}

            parts.append("")
            parts.append("🪙 *Vàng*")

            for name, d in domestic_gold.items():
                if not d.get('success'):
                    continue
                buy = d['buy']
                sell = d['sell']
                chg = d.get('change_sell', 0)
                line = f"{name} M`{_millions(buy)}`|B`{_millions(sell)}`"
                if chg != 0:
                    line += f" {_icon(chg)}`{chg / 1_000_000:+.1f}`"
                parts.append(line)

            for name, d in world_gold.items():
                if not d.get('success'):
                    continue
                p = d['price']
                c = d.get('change', 0)
                unit = d['currency']
                short = 'XAU' if 'TG' in name or 'XAU' in name else name
                u_short = unit.replace('USD/', '$/').replace('usd/', '$/')
                line = f"{short} `{p:,.0f}` {u_short}"
                if c != 0:
                    pct = (c / (p - c)) * 100 if (p - c) != 0 else 0
                    line += f" {_icon(c)}`{pct:+.1f}%`"
                parts.append(line)

            # --- USD/VND ---
            if forex_data:
                usd = forex_data.get('USD/VND')
                if usd and usd.get('success'):
                    parts.append(
                        f"💵 USD `{usd['rate']:,}` ₫"
                    )
        elif gold_data is None:
            parts.append("\n🪙 ⚠️ Vàng: N/A")

        return "\n".join(parts)
