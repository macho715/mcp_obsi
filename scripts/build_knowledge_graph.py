"""Legacy graph builder.

The canonical export path for shipment-centric TTL exports is
`scripts/build_dashboard_graph_data.py`.
"""

import sys
from pathlib import Path

try:
    from scripts.build_dashboard_graph_data import export_dashboard_graph_data
except ModuleNotFoundError:  # pragma: no cover - CLI fallback for direct script execution
    repo_root = Path(__file__).resolve().parents[1]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    from scripts.build_dashboard_graph_data import export_dashboard_graph_data

DEPRECATED_ENTRYPOINT_MESSAGE = (
    "Deprecated entrypoint: use scripts/build_dashboard_graph_data.py "
    "for shipment-centric TTL exports."
)


def build_graph() -> None:
    export_dashboard_graph_data()


def main() -> None:
    print(DEPRECATED_ENTRYPOINT_MESSAGE)
    build_graph()


if __name__ == "__main__":
    main()
