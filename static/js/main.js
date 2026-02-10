/**
 * 职位追踪系统 - 主 JavaScript 文件
 */

// 显示通知
function showNotification(message, type = 'info') {
    const toast = document.getElementById('notification-toast');
    const toastBody = document.getElementById('toast-message');

    // 设置消息内容
    toastBody.textContent = message;

    // 设置样式
    toast.classList.remove('bg-info', 'bg-success', 'bg-danger', 'bg-warning');
    if (type === 'success') {
        toast.classList.add('bg-success', 'text-white');
    } else if (type === 'error') {
        toast.classList.add('bg-danger', 'text-white');
    } else if (type === 'warning') {
        toast.classList.add('bg-warning');
    } else {
        toast.classList.add('bg-info', 'text-white');
    }

    // 显示 Toast
    const bsToast = new bootstrap.Toast(toast, {
        autohide: true,
        delay: 3000
    });
    bsToast.show();
}

// Scraping progress tracking
let scrapeProgressInterval = null;

// 触发爬取（从顶部导航栏调用）
function triggerScrape() {
    if (!confirm('Start scraping all companies? This may take 30-60 minutes.')) {
        return;
    }

    // Show progress modal
    showScrapeProgressModal();

    $.ajax({
        url: '/api/scrape',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({ async: true }),
        success: function(response) {
            if (response.success && response.async) {
                // Start polling for progress
                startProgressPolling();
            } else if (response.success) {
                // Sync scrape completed
                hideScrapeProgressModal();
                const summary = response.data.summary;
                showNotification(
                    `Scraping complete! ${summary.total_new} new, ${summary.total_updated} updated`,
                    'success'
                );
                if (typeof loadJobs === 'function') {
                    setTimeout(() => loadJobs(currentPage || 1), 1000);
                }
            } else {
                hideScrapeProgressModal();
                showNotification('Scrape failed: ' + response.error, 'error');
            }
        },
        error: function(xhr) {
            hideScrapeProgressModal();
            showNotification('Scrape failed. Please try again.', 'error');
        }
    });
}

function showScrapeProgressModal() {
    // Create modal if it doesn't exist
    if (!document.getElementById('scrapeProgressModal')) {
        const modalHtml = `
        <div class="modal fade" id="scrapeProgressModal" data-bs-backdrop="static" tabindex="-1">
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content">
                    <div class="modal-header bg-primary text-white">
                        <h5 class="modal-title"><i class="bi bi-arrow-repeat me-2"></i>Scraping in Progress</h5>
                    </div>
                    <div class="modal-body">
                        <div class="mb-3">
                            <div class="d-flex justify-content-between mb-1">
                                <span id="scrapeCurrentCompany">Starting...</span>
                                <span id="scrapeProgressText">0 / 0</span>
                            </div>
                            <div class="progress" style="height: 25px;">
                                <div id="scrapeProgressBar" class="progress-bar progress-bar-striped progress-bar-animated"
                                     role="progressbar" style="width: 0%"></div>
                            </div>
                        </div>
                        <div class="row text-center mb-3">
                            <div class="col">
                                <div class="text-success fw-bold" id="scrapeCompleted">0</div>
                                <small class="text-muted">Completed</small>
                            </div>
                            <div class="col">
                                <div class="text-danger fw-bold" id="scrapeFailed">0</div>
                                <small class="text-muted">Failed</small>
                            </div>
                            <div class="col">
                                <div class="text-primary fw-bold" id="scrapeRemaining">0</div>
                                <small class="text-muted">Remaining</small>
                            </div>
                        </div>
                        <div id="scrapeCompanyList" class="small" style="max-height: 150px; overflow-y: auto;">
                            <div class="text-muted">Waiting for progress...</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>`;
        document.body.insertAdjacentHTML('beforeend', modalHtml);
    }

    const modal = new bootstrap.Modal(document.getElementById('scrapeProgressModal'));
    modal.show();
}

function hideScrapeProgressModal() {
    const modalEl = document.getElementById('scrapeProgressModal');
    if (modalEl) {
        const modal = bootstrap.Modal.getInstance(modalEl);
        if (modal) modal.hide();
    }
    stopProgressPolling();
}

function startProgressPolling() {
    // Poll every 2 seconds
    scrapeProgressInterval = setInterval(checkScrapeProgress, 2000);
    checkScrapeProgress(); // Check immediately
}

function stopProgressPolling() {
    if (scrapeProgressInterval) {
        clearInterval(scrapeProgressInterval);
        scrapeProgressInterval = null;
    }
}

function checkScrapeProgress() {
    $.ajax({
        url: '/api/scrape/progress',
        method: 'GET',
        success: function(response) {
            if (response.success) {
                updateProgressUI(response.data);
            }
        },
        error: function() {
            // Silently fail, will retry
        }
    });
}

function updateProgressUI(progress) {
    const total = progress.total_companies || 1;
    const current = progress.current_index || 0;
    const percentage = Math.round((current / total) * 100);
    const completed = progress.completed_companies || [];
    const failed = progress.failed_companies || [];
    const remaining = total - completed.length - failed.length;

    // Update progress bar
    $('#scrapeProgressBar').css('width', percentage + '%').text(percentage + '%');
    $('#scrapeProgressText').text(`${current} / ${total}`);
    $('#scrapeCurrentCompany').text(progress.current_company ? `Scraping: ${progress.current_company}` : 'Starting...');
    $('#scrapeCompleted').text(completed.length);
    $('#scrapeFailed').text(failed.length);
    $('#scrapeRemaining').text(remaining);

    // Update company list
    let listHtml = '';
    completed.forEach(c => {
        listHtml += `<div class="text-success"><i class="bi bi-check-circle me-1"></i>${c}</div>`;
    });
    failed.forEach(c => {
        listHtml += `<div class="text-danger"><i class="bi bi-x-circle me-1"></i>${c}</div>`;
    });
    if (progress.current_company && !completed.includes(progress.current_company) && !failed.includes(progress.current_company)) {
        listHtml += `<div class="text-primary"><i class="bi bi-arrow-repeat me-1 spin"></i>${progress.current_company}</div>`;
    }
    $('#scrapeCompanyList').html(listHtml || '<div class="text-muted">Waiting...</div>');

    // Check if scraping is complete
    if (!progress.is_running && progress.results) {
        stopProgressPolling();
        setTimeout(() => {
            hideScrapeProgressModal();
            const summary = progress.results.summary;
            showNotification(
                `Scraping complete! ${summary.total_new} new, ${summary.total_updated} updated, ${summary.successful_companies} succeeded, ${summary.failed_companies} failed`,
                summary.failed_companies > 0 ? 'warning' : 'success'
            );
            if (typeof loadJobs === 'function') {
                loadJobs(currentPage || 1);
            }
        }, 1000);
    }
}

// 导出 Excel（从顶部导航栏调用）
function exportExcel() {
    showNotification('正在导出 Excel...', 'info');

    $.ajax({
        url: '/api/export',
        method: 'GET',
        success: function(response) {
            if (response.success) {
                showNotification('Excel 导出成功！正在下载...', 'success');
                // 自动下载
                window.location.href = response.download_url;
            } else {
                showNotification('导出失败: ' + response.error, 'error');
            }
        },
        error: function() {
            showNotification('导出失败，请稍后重试', 'error');
        }
    });
}

// 格式化日期
function formatDate(dateString) {
    const date = new Date(dateString);
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

// 格式化日期时间
function formatDateTime(dateString) {
    const date = new Date(dateString);
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    return `${year}-${month}-${day} ${hours}:${minutes}`;
}

// 截断文本
function truncateText(text, maxLength) {
    if (!text) return '';
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
}

// 防抖函数
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// 节流函数
function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// 页面加载完成后执行
$(document).ready(function() {
    // 为所有表单输入添加回车键监听
    $('input').on('keypress', function(e) {
        if (e.which === 13) { // Enter key
            e.preventDefault();
            if (typeof applyFilters === 'function') {
                applyFilters();
            }
        }
    });

    // 添加加载动画
    $(document).ajaxStart(function() {
        $('body').addClass('loading');
    }).ajaxStop(function() {
        $('body').removeClass('loading');
    });

    // 错误处理
    window.onerror = function(msg, url, lineNo, columnNo, error) {
        console.error('Error:', msg, url, lineNo, columnNo, error);
        return false;
    };
});

// 导出到全局作用域
window.showNotification = showNotification;
window.triggerScrape = triggerScrape;
window.exportExcel = exportExcel;
window.formatDate = formatDate;
window.formatDateTime = formatDateTime;
window.truncateText = truncateText;
window.debounce = debounce;
window.throttle = throttle;
