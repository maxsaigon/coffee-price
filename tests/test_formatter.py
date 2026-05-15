import unittest
from unittest.mock import patch

from src.services.formatter import MessageFormatter


class MessageFormatterTest(unittest.TestCase):
    def test_report_header_uses_runtime_not_source_time(self):
        gold_data = {
            "SJC 1L/10L": {
                "buy": 162_200_000,
                "sell": 165_200_000,
                "change_sell": -700_000,
                "currency": "VND/lượng",
                "source_time": "11/05 18:00",
                "success": True,
            }
        }

        with patch("src.services.formatter.datetime") as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "11/05 18:22"

            message = MessageFormatter.format_full_report(
                international_data=None,
                domestic_data=None,
                gold_data=gold_data,
                forex_data=None,
            )

        self.assertTrue(message.startswith("☕ 11/05 18:22"))
        self.assertIn("VN M`162.2`|B`165.2`", message)
        self.assertIn("(11/05 18:00)", message)

    def test_report_header_falls_back_to_runtime_when_no_source_time(self):
        with patch("src.services.formatter.datetime") as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "12/05 08:35"

            message = MessageFormatter.format_full_report(
                international_data=None,
                domestic_data=None,
                gold_data=None,
                forex_data=None,
            )

        self.assertTrue(message.startswith("☕ 12/05 08:35"))

    def test_domestic_gold_is_averaged_into_one_line_and_excludes_ring_gold(self):
        gold_data = {
            "SJC 1L/10L": {
                "buy": 162_000_000,
                "sell": 165_000_000,
                "change_sell": -500_000,
                "currency": "VND/lượng",
                "source_time": "12/05 08:30",
                "success": True,
            },
            "Nhẫn SJC": {
                "buy": 161_000_000,
                "sell": 164_000_000,
                "change_sell": -700_000,
                "currency": "VND/lượng",
                "source_time": "12/05 08:30",
                "success": True,
            },
            "DOJI HN": {
                "buy": 162_000_000,
                "sell": 165_000_000,
                "change_sell": -500_000,
                "currency": "VND/lượng",
                "source_time": "12/05 08:30",
                "success": True,
            },
            "DOJI HCM": {
                "buy": 164_000_000,
                "sell": 167_000_000,
                "change_sell": -900_000,
                "currency": "VND/lượng",
                "source_time": "12/05 08:30",
                "success": True,
            },
            "PNJ HN": {
                "buy": 162_200_000,
                "sell": 165_200_000,
                "change_sell": -700_000,
                "currency": "VND/lượng",
                "source_time": "12/05 08:30",
                "success": True,
            },
        }

        message = MessageFormatter.format_full_report(
            international_data=None,
            domestic_data=None,
            gold_data=gold_data,
            forex_data=None,
        )

        self.assertIn("VN M`162.6`|B`165.6`", message)
        self.assertNotIn("SJC M", message)
        self.assertNotIn("DOJI M", message)
        self.assertNotIn("PNJ M", message)
        self.assertNotIn("Nhẫn", message)

    def test_fuel_prices_are_formatted_in_one_line(self):
        fuel_data = {
            "R95": {
                "price": 24_830,
                "region": 2,
                "source_time": "14/05 14:13",
                "success": True,
            },
            "E5": {
                "price": 24_260,
                "region": 2,
                "source_time": "14/05 14:13",
                "success": True,
            },
            "DO": {
                "price": 28_030,
                "region": 2,
                "source_time": "14/05 14:13",
                "success": True,
            },
        }

        message = MessageFormatter.format_full_report(
            international_data=None,
            domestic_data=None,
            gold_data=None,
            forex_data=None,
            fuel_data=fuel_data,
        )

        self.assertIn("⛽ R95 `24.83` E5 `24.26` DO `28.03`k/L (V2, 14/05 14:13)", message)


if __name__ == "__main__":
    unittest.main()
