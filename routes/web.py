from flask import Blueprint, render_template, abort
from flask_login import login_required
from services.job_service import JobService
from services.snapshot_service import SnapshotService
import logging

logger = logging.getLogger(__name__)

# Create Web Blueprint
web_bp = Blueprint('web', __name__)


@web_bp.route('/')
@login_required
def index():
    """Homepage - Job listings"""
    try:
        # Get statistics
        stats = JobService.get_statistics()

        # Get all companies, locations and categories (for filters)
        companies = JobService.get_all_companies()
        locations = JobService.get_all_locations()
        categories = JobService.get_all_categories()

        return render_template(
            'index.html',
            stats=stats,
            companies=companies,
            locations=locations,
            categories=categories
        )

    except Exception as e:
        logger.error(f"Error rendering index page: {e}")
        return str(e), 500


@web_bp.route('/job/<int:job_id>')
@login_required
def job_detail(job_id):
    """Job detail page"""
    try:
        job = JobService.get_job_by_id(job_id)

        if job:
            return render_template('job_detail.html', job=job)
        else:
            abort(404, description="Job not found")

    except Exception as e:
        logger.error(f"Error rendering job detail page: {e}")
        return str(e), 500


@web_bp.route('/settings')
@login_required
def settings():
    """Settings page"""
    try:
        from config import Config

        # Get current configuration
        config_info = {
            'schedule_hour': Config.SCHEDULE_HOUR,
            'schedule_minute': Config.SCHEDULE_MINUTE,
            'excel_path': Config.EXCEL_EXPORT_PATH,
            'headless_mode': Config.HEADLESS_MODE,
            'new_job_days': Config.NEW_JOB_DAYS,
            'scraper_delay_min': Config.SCRAPER_DELAY_MIN,
            'scraper_delay_max': Config.SCRAPER_DELAY_MAX
        }

        return render_template('settings.html', config=config_info)

    except Exception as e:
        logger.error(f"Error rendering settings page: {e}")
        return str(e), 500


@web_bp.route('/trends')
@login_required
def trends():
    """Historical trends and year-over-year analysis page"""
    try:
        # Get all snapshots
        snapshots = SnapshotService.get_all_snapshots()
        
        # Get year-over-year comparison
        yoy_comparison = SnapshotService.get_year_over_year_comparison()
        
        # Get recent trend data (last 12 weeks)
        trend_data = SnapshotService.get_trend_data(weeks=12)
        
        # Get available categories and companies for filtering
        categories = JobService.get_all_categories()
        companies = JobService.get_all_companies()
        
        return render_template(
            'trends.html',
            snapshots=snapshots,
            yoy_comparison=yoy_comparison,
            trend_data=trend_data,
            categories=categories,
            companies=companies
        )
        
    except Exception as e:
        logger.error(f"Error rendering trends page: {e}")
        return str(e), 500


@web_bp.route('/release-radar')
@login_required
def release_radar():
    """SA / Summer Intern release radar — two tabs feeding the 公众号 pipeline.

    Query params:
      tab: 'fresh' (default) | 'wave'
      region: 'US' | 'UK' | 'HK' | 'ALL' (default)
      sector: 'Finance' | 'Consulting' | 'Tech' | 'ALL' (default)
      days_fresh: int (default 3) — fresh-window in days
      min_days_wave: int (default 10) — wave lower bound in days
      max_days_wave: int (default 60) — wave upper bound in days
    """
    from flask import request
    from services.release_radar_service import (
        get_freshly_opened,
        get_interview_wave,
        group_by_sector_then_region,
    )

    tab = request.args.get('tab', 'fresh')
    region = request.args.get('region', 'ALL')
    sector = request.args.get('sector', 'ALL')
    days_fresh = int(request.args.get('days_fresh', 3))
    min_days_wave = int(request.args.get('min_days_wave', 10))
    max_days_wave = int(request.args.get('max_days_wave', 60))

    try:
        fresh = get_freshly_opened(days=days_fresh, region=region, sector=sector)
        wave = get_interview_wave(
            min_days=min_days_wave,
            max_days=max_days_wave,
            region=region,
            sector=sector,
        )
    except Exception as e:
        logger.error(f"Error loading release radar data: {e}")
        import traceback
        traceback.print_exc()
        return str(e), 500

    return render_template(
        'release_radar.html',
        tab=tab,
        region=region,
        sector=sector,
        days_fresh=days_fresh,
        min_days_wave=min_days_wave,
        max_days_wave=max_days_wave,
        fresh_events=fresh,
        fresh_grouped=group_by_sector_then_region(fresh),
        wave_events=wave,
        wave_grouped=group_by_sector_then_region(wave),
        fresh_count=len(fresh),
        wave_count=len(wave),
    )
