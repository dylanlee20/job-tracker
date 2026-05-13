"""Compat shim — the local scrapers were retired in favor of the WhaleStreet
job-scraper CSV. This module preserves the old `ScraperService` class name
and method signatures so existing routes / scheduler code keeps working
without rewrites. All work delegates to `CSVImportService`.
"""

from __future__ import annotations

import logging
from typing import Dict, List

from services.csv_import_service import CSVImportService

logger = logging.getLogger(__name__)


class ScraperService:
    """Thin compat layer over CSVImportService. Keeps the old API surface."""

    @classmethod
    def get_progress(cls) -> Dict:
        return CSVImportService.get_progress()

    @classmethod
    def is_running(cls) -> bool:
        return CSVImportService.is_running()

    @classmethod
    def run_all_scrapers(cls, with_progress: bool = False) -> Dict:
        return CSVImportService.import_all(with_progress=with_progress)

    @classmethod
    def run_all_scrapers_async(cls, app=None) -> bool:
        started = CSVImportService.run_async(app=app)
        if started and app is not None:
            import threading
            import time

            def excel_after():
                with app.app_context():
                    while CSVImportService.is_running():
                        time.sleep(0.5)
                    try:
                        from services.excel_service import ExcelService
                        ExcelService.auto_sync_excel()
                        logger.info("Excel auto-sync completed after CSV import")
                    except Exception as exc:
                        logger.warning(f"Excel auto-sync failed: {exc}")

            threading.Thread(target=excel_after, daemon=True, name="excel-sync").start()
        return started

    @staticmethod
    def run_single_scraper(company_name: str) -> Dict:
        return CSVImportService.import_single_company(company_name)

    @staticmethod
    def get_available_companies() -> List[str]:
        return CSVImportService.get_available_companies()
