"""
工具模块包

包含各种工具函数和类
"""

# 导入K线数据相关工具函数
from utils.kline_utils import fetch_and_save_kline

# 导入股票符号相关工具函数
from utils.symbol_utils import get_symbol_info, search_symbols

# 导入策略相关工具函数
from utils.strategy_utils import (
    get_strategy_list,
    get_strategy_detail,
    delete_strategy
)

# 导入回测相关工具函数
from utils.backtest_utils import (
    run_backtest,
    format_choose_stock,
    extract_symbols_from_strategy,
    extract_backtest_params,
    extract_buy_sell_points,
    calculate_performance_metrics
)

# 导入回测管理相关工具函数
from utils.backtest_manager import (
    submit_backtest_task,
    get_all_tasks,
    find_task_by_params,
    cleanup_old_tasks
)

# 导入提示模板相关工具函数
from utils.prompt_utils import (
    update_prompt_metadata,
    register_prompt_with_metadata,
    patch_fastmcp
)
