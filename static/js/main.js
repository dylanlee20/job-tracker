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

// 触发爬取（从顶部导航栏调用）
function triggerScrape() {
    if (!confirm('确定要立即执行一次爬取吗？这可能需要几分钟时间。')) {
        return;
    }

    showNotification('爬取任务已启动，请稍候...', 'info');

    $.ajax({
        url: '/api/scrape',
        method: 'POST',
        contentType: 'application/json',
        success: function(response) {
            if (response.success) {
                if (response.data.summary) {
                    // 全部爬取的结果
                    const summary = response.data.summary;
                    showNotification(
                        `爬取完成！新增 ${summary.total_new} 个职位，更新 ${summary.total_updated} 个职位`,
                        'success'
                    );
                } else if (response.data.stats) {
                    // 单个公司爬取的结果
                    const stats = response.data.stats;
                    showNotification(
                        `爬取完成！新增 ${stats.new_jobs} 个职位，更新 ${stats.updated_jobs} 个职位`,
                        'success'
                    );
                } else {
                    showNotification('爬取完成！', 'success');
                }

                // 重新加载页面（如果在职位列表页）
                if (typeof loadJobs === 'function') {
                    setTimeout(() => loadJobs(currentPage || 1), 1000);
                }
            } else {
                showNotification('爬取失败: ' + response.error, 'error');
            }
        },
        error: function(xhr) {
            showNotification('爬取失败，请检查网络连接或稍后重试', 'error');
        }
    });
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
