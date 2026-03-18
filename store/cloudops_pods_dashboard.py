
from store.cloudops_pods_collector import CloudopsPodsCollector
from src.models.dashboard import CellResult, TableDashboard, dashboardColumn


class CloudopsPodsDashboard(TableDashboard):

    def getCollector(self) -> Collector:
        return CloudopsPodsCollector()

    @dashboardColumn("Pod Name")
    def pod_name(self, row: dict[str, Any]) -> CellResult:
        return {
            "value": row.get("name", "—"),
            "style": "font-family: monospace; font-weight: 500;",
        }

    @dashboardColumn("Namespace")
    def namespace(self, row: dict[str, Any]) -> CellResult:
        return {
            "value": row.get("namespace", "—"),
            "style": "color: #818cf8; font-family: monospace;",
        }

    @dashboardColumn("Restart Policy")
    def region(self, row: dict[str, Any]) -> CellResult:
        return {
            "value": row.get("restartPolicy", "—"),
            "style": "color: #10b981; font-weight: 600;",
        }

    @dashboardColumn("Generate Name")
    def region(self, row: dict[str, Any]) -> CellResult:
        return {
            "value": row.get("generateName", "—"),
            "style": "color: #10b981; font-weight: 600;",
        }
