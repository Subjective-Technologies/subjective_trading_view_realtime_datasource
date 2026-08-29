import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from subjective_abstract_data_source_package import SubjectiveDataSource

from trading_contracts.market import utc_now
from trading_contracts.plugin_support import icon_for


class SubjectiveTradingViewRealtimeDataSource(SubjectiveDataSource):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @classmethod
    def connection_schema(cls):
        return {"webhook_token": {"type": "password", "label": "Webhook Token"}}

    @classmethod
    def request_schema(cls):
        return {"webhook_token": {"type": "password", "label": "Webhook Token"}, "alert": {"type": "object", "label": "TradingView Alert"}, "alerts": {"type": "array", "label": "Injected Alerts"}}

    @classmethod
    def output_schema(cls):
        return {"events": {"type": "array", "label": "Signal Events"}, "error": {"type": "text", "label": "Error"}}

    @classmethod
    def icon(cls):
        return icon_for(__file__)

    def supports_streaming(self):
        return True

    @staticmethod
    def _normalize(alert):
        alert = alert if isinstance(alert, dict) else {"text": str(alert)}
        return {"kind": "signal", "source": "tradingview_webhook", "channel": str(alert.get("channel", "tradingview")), "ts": str(alert.get("ts") or utc_now()), "text": str(alert.get("text") or alert.get("message") or ""), "structured": alert.get("structured")}

    def run(self, request):
        request = request or {}
        configured_token = str(self._connection.get("webhook_token") or "")
        if configured_token and str(request.get("webhook_token") or "") != configured_token:
            return {"events": [], "error": "invalid webhook token"}
        alerts = request.get("alerts")
        if alerts is None and request.get("alert") is not None:
            alerts = [request["alert"]]
        if alerts is None:
            return {"events": [], "error": "No webhook alert supplied; public scraping is intentionally unsupported"}
        return {"events": [self._normalize(alert) for alert in alerts], "error": ""}

    def stream(self, request):
        yield self.run(request or {})
