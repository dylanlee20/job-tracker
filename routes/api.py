from flask import Blueprint, request, jsonify, send_file, current_app
from services.job_service import JobService
from services.scraper_service import ScraperService
from services.excel_service import ExcelService
from services.snapshot_service import SnapshotService
from config import Config
import logging
import os

logger = logging.getLogger(__name__)

# 创建 API Blueprint
api_bp = Blueprint('api', __name__, url_prefix='/api')


@api_bp.route('/jobs', methods=['GET'])
def get_jobs():
    """
    获取职位列表（带筛选和分页）

    查询参数：
        - company: 公司名称
        - location: 地点
        - category: 职位类别
        - keyword: 关键词搜索
        - is_important: 是否只显示重点职位 (true/false)
        - time_range: 时间范围 (this_week/this_month/all)
        - status: 状态 (active/inactive)
        - page: 页码 (默认 1)
        - per_page: 每页数量 (默认 50)
    """
    try:
        # 获取查询参数
        filters = {}

        if request.args.get('company'):
            filters['company'] = request.args.get('company')

        if request.args.get('location'):
            filters['location'] = request.args.get('location')

        if request.args.get('category'):
            filters['category'] = request.args.get('category')

        if request.args.get('keyword'):
            filters['keyword'] = request.args.get('keyword')

        if request.args.get('is_important') == 'true':
            filters['is_important'] = True

        if request.args.get('time_range'):
            filters['time_range'] = request.args.get('time_range')

        if request.args.get('status'):
            filters['status'] = request.args.get('status')

        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))

        # 获取职位列表
        result = JobService.get_jobs(filters=filters, page=page, per_page=per_page)

        return jsonify({
            'success': True,
            'data': result
        })

    except Exception as e:
        logger.error(f"Error in get_jobs: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/jobs/<int:job_id>', methods=['GET'])
def get_job(job_id):
    """获取单个职位详情"""
    try:
        job = JobService.get_job_by_id(job_id)

        if job:
            return jsonify({
                'success': True,
                'data': job
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Job not found'
            }), 404

    except Exception as e:
        logger.error(f"Error in get_job: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/jobs/<int:job_id>/important', methods=['PUT'])
def mark_important(job_id):
    """标记/取消标记重点职位"""
    try:
        data = request.get_json()
        is_important = data.get('is_important', False)

        success = JobService.mark_job_important(job_id, is_important)

        if success:
            return jsonify({
                'success': True,
                'message': 'Job importance updated'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Job not found'
            }), 404

    except Exception as e:
        logger.error(f"Error in mark_important: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/jobs/<int:job_id>/notes', methods=['PUT'])
def add_note(job_id):
    """添加/更新用户备注"""
    try:
        data = request.get_json()
        note = data.get('note', '')

        success = JobService.add_user_note(job_id, note)

        if success:
            return jsonify({
                'success': True,
                'message': 'Note updated'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Job not found'
            }), 404

    except Exception as e:
        logger.error(f"Error in add_note: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/scrape', methods=['POST'])
def trigger_scrape():
    """
    手动触发爬取

    请求体（可选）：
        - company: 公司名称（如果指定，只爬取该公司）
        - async: 是否异步执行（默认 false）
    """
    try:
        data = {}
        if request.is_json:
            try:
                data = request.get_json() or {}
            except:
                data = {}
        company = data.get('company')
        run_async = data.get('async', False)

        if company:
            # 爬取单个公司（同步）
            result = ScraperService.run_single_scraper(company)
            return jsonify({
                'success': True,
                'data': result
            })
        elif run_async:
            # 异步爬取所有公司
            # Note: run_all_scrapers_async handles stuck states internally
            # Pass app context for database operations in background thread
            started = ScraperService.run_all_scrapers_async(app=current_app._get_current_object())
            if started:
                return jsonify({
                    'success': True,
                    'message': 'Scraping started in background',
                    'async': True
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Failed to start scraping'
                }), 500
        else:
            # 同步爬取所有公司
            result = ScraperService.run_all_scrapers()

            # 自动导出 Excel
            try:
                ExcelService.auto_sync_excel()
            except Exception as e:
                logger.warning(f"Error auto-syncing Excel after scrape: {e}")

            return jsonify({
                'success': True,
                'data': result
            })

    except Exception as e:
        logger.error(f"Error in trigger_scrape: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/scrape/progress', methods=['GET'])
def get_scrape_progress():
    """Get current scraping progress"""
    try:
        progress = ScraperService.get_progress()
        return jsonify({
            'success': True,
            'data': progress
        })
    except Exception as e:
        logger.error(f"Error getting scrape progress: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/export', methods=['GET'])
def export_excel():
    """触发 Excel 导出并返回下载链接"""
    try:
        # 导出 Excel
        excel_path = ExcelService.auto_sync_excel()

        # 检查文件是否存在
        if os.path.exists(excel_path):
            return jsonify({
                'success': True,
                'message': 'Excel exported successfully',
                'download_url': '/api/download/excel'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Export failed'
            }), 500

    except Exception as e:
        logger.error(f"Error in export_excel: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/download/excel', methods=['GET'])
def download_excel():
    """下载 Excel 文件"""
    try:
        excel_path = Config.EXCEL_EXPORT_PATH

        if os.path.exists(excel_path):
            return send_file(
                excel_path,
                as_attachment=True,
                download_name='jobs_export.xlsx',
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
        else:
            return jsonify({
                'success': False,
                'error': 'Excel file not found'
            }), 404

    except Exception as e:
        logger.error(f"Error in download_excel: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/stats', methods=['GET'])
def get_statistics():
    """获取统计信息"""
    try:
        stats = JobService.get_statistics()

        return jsonify({
            'success': True,
            'data': stats
        })

    except Exception as e:
        logger.error(f"Error in get_statistics: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/companies', methods=['GET'])
def get_companies():
    """获取所有公司列表"""
    try:
        companies = JobService.get_all_companies()

        return jsonify({
            'success': True,
            'data': companies
        })

    except Exception as e:
        logger.error(f"Error in get_companies: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/locations', methods=['GET'])
def get_locations():
    """获取所有地点列表"""
    try:
        locations = JobService.get_all_locations()

        return jsonify({
            'success': True,
            'data': locations
        })

    except Exception as e:
        logger.error(f"Error in get_locations: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/available-companies', methods=['GET'])
def get_available_companies():
    """获取所有可爬取的公司列表"""
    try:
        companies = ScraperService.get_available_companies()

        return jsonify({
            'success': True,
            'data': companies
        })

    except Exception as e:
        logger.error(f"Error in get_available_companies: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/trends/snapshots', methods=['GET'])
def get_snapshots():
    """Get all historical snapshots"""
    try:
        snapshots = SnapshotService.get_all_snapshots()
        
        return jsonify({
            'success': True,
            'data': snapshots
        })
        
    except Exception as e:
        logger.error(f"Error getting snapshots: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/trends/history', methods=['GET'])
def get_trend_history():
    """Get historical trend data"""
    try:
        weeks = int(request.args.get('weeks', 12))
        trend_data = SnapshotService.get_trend_data(weeks=weeks)
        
        return jsonify({
            'success': True,
            'data': trend_data
        })
        
    except Exception as e:
        logger.error(f"Error getting trend history: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/trends/year-over-year', methods=['GET'])
def get_year_over_year():
    """Get year-over-year comparison"""
    try:
        category = request.args.get('category')
        company = request.args.get('company')
        
        comparison = SnapshotService.get_year_over_year_comparison(
            category=category,
            company=company
        )
        
        return jsonify({
            'success': True,
            'data': comparison
        })
        
    except Exception as e:
        logger.error(f"Error getting year-over-year comparison: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
