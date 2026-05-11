import unittest
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from src.config import Config
from src.providers.financial_provider import GoldPriceProvider


class StubGoldProvider(GoldPriceProvider):
    def __init__(self, raw, backup=None):
        self.raw = raw
        self.backup = backup

    def _fetch_api(self):
        return self.raw

    def _fetch_backup_xau(self):
        return self.backup


def make_payload(timestamp):
    return {
        "success": True,
        "timestamp": timestamp,
        "time": "09:30",
        "date": "2026-05-11",
        "prices": {
            "SJL1L10": {
                "name": "SJC 9999",
                "buy": 163_400_000,
                "sell": 166_400_000,
                "change_buy": -1_100_000,
                "change_sell": -1_100_000,
                "currency": "VND",
            },
            "DOJINHTV": {
                "name": "DOJI Jewelry",
                "buy": 160_000_000,
                "sell": 165_000_000,
                "change_buy": -600_000,
                "change_sell": -600_000,
                "currency": "VND",
            },
            "DOHNL": {
                "name": "DOJI Hanoi",
                "buy": 163_400_000,
                "sell": 166_400_000,
                "change_buy": -600_000,
                "change_sell": 400_000,
                "currency": "VND",
            },
            "XAUUSD": {
                "name": "World Gold (XAU/USD)",
                "buy": 4687.2,
                "sell": 0,
                "change_buy": 1.1,
                "change_sell": 0,
                "currency": "USD",
            },
        },
    }


class GoldPriceProviderTest(unittest.TestCase):
    def test_uses_region_specific_doji_ticker_not_jewelry_ticker(self):
        now = int(datetime.now(ZoneInfo(Config.TIMEZONE)).timestamp())
        data = StubGoldProvider(make_payload(now), {"source": "gold-api.com", "price": 4688}).get_prices()

        self.assertIn("DOJI HN", data)
        self.assertNotIn("DOJI", data)
        self.assertEqual(data["DOJI HN"]["ticker"], "DOHNL")
        self.assertEqual(data["SJC 1L/10L"]["currency"], "VND/lượng")

    def test_marks_stale_gold_data(self):
        old = int(
            (datetime.now(ZoneInfo(Config.TIMEZONE)) - timedelta(minutes=90)).timestamp()
        )
        data = StubGoldProvider(make_payload(old), {"source": "gold-api.com", "price": 4688}).get_prices()

        self.assertTrue(data["SJC 1L/10L"]["stale"])
        self.assertTrue(data["Vàng TG"]["stale"])

    def test_marks_xau_unverified_when_backup_quote_differs_too_much(self):
        now = int(datetime.now(ZoneInfo(Config.TIMEZONE)).timestamp())
        data = StubGoldProvider(
            make_payload(now),
            {"source": "gold-api.com", "price": 4900},
        ).get_prices()

        self.assertFalse(data["Vàng TG"]["verified"])
        self.assertGreater(data["Vàng TG"]["source_diff_percent"], 1.0)


if __name__ == "__main__":
    unittest.main()
