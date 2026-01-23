import datetime

import streamlit as st

from svc.auth import get_auto_login_session
from svc.logger import setup_logger

# 设置logger
logger = setup_logger(__name__)

# 定义地区、延迟和股票池的映射关系
REGION_PARAMS = {
    "USA": {
        "delay": [1, 0],
        "universe": ["TOP3000", "TOP1000", "TOP500", "TOP200", "ILLIQUID_MINVOL1M", "TOPSP500"]
    },
    "GLB": {
        "delay": [1],
        "universe": ["TOP3000", "TOPDIV3000", "MINVOL1M"]
    },
    "EUR": {
        "delay": [1, 0],
        "universe": ["TOP2500","TOP1200", "TOP800", "TOP400", "ILLIQUID_MINVOL1M"]
    },
    "ASI": {
        "delay": [1],
        "universe": ["MINVOL1M", "ILLIQUID_MINVOL1M"]
    },
    "CHN": {
        "delay": [1, 0],
        "universe": ["TOP2000U"]
    },
    "JPN": {
        "delay": [1, 0],
        "universe": ["TOP1600", "TOP1200"]
    },
    "AMR": {
        "delay": [1, 0],
        "universe": ["TOP600"]
    },
    "IND": {
        "delay": [1],
        "universe": ["TOP500"]
    },
}

# 定义可用的分类列表
CATEGORIES = [
    ('All', ''),
    ('Analyst', 'analyst'),
    ('Broker', 'broker'),
    ('Earnings', 'earnings'),
    ('Fundamental', 'fundamental'),
    ('Imbalance', 'imbalance'),
    ('Insiders', 'insiders'),
    ('Institutions', 'institutions'),
    ('Macro', 'macro'),
    ('Model', 'model'),
    ('News', 'news'),
    ('Option', 'option'),
    ('Other', 'other'),
    ('Price Volume', 'pv'),
    ('Risk', 'risk'),
    ('Sentiment', 'sentiment'),
    ('Short Interest', 'shortinterest'),
    ('Social Media', 'socialmedia')
]

def render_sidebar():
    """渲染共享的侧边栏"""
    # 设置页面配置，使用宽屏布局
    st.set_page_config(
        page_title="Brain-Lit Application",
        page_icon="🧠",
        layout="wide"
    )

    if 'global_session' not in st.session_state:
        st.session_state.global_session = get_auto_login_session()
    
    with st.sidebar:
        st.title(f"欢迎, {st.session_state.global_session.user_id}!")
        st.markdown(f"**登录时间:** {datetime.datetime.fromtimestamp(st.session_state.global_session.last_login_time)}")
        st.markdown("---")
        
        # 添加数据集参数选择
        _render_common_parameters()
        
        st.markdown("---")
        st.markdown("### 页面导航")
        if st.button("🏠 主页"):
            st.switch_page("app.py")
        if st.button("📈 生成Alpha"):
            st.switch_page("pages/1_alpha_generate.py")
        if st.button("🔬 回测Alpha"):
            st.switch_page("pages/2_alpha_simulate.py")
        if st.button("✅ 检查Alpha"):
            st.switch_page("pages/3_alpha_check.py")
        if st.button("📥 提交Alpha"):
            st.switch_page("pages/4_alpha_submit.py")
        if st.button("🛡️ Risk Neutralization"):
            st.switch_page("pages/5_risk_neutralization.py")
        
        # st.markdown("---")
        # if st.button("🚪 退出登录"):
        #     _handle_logout()
            
def _render_common_parameters():
    """渲染公共参数选择区域"""
    st.markdown("### 数据参数")
    
    # 初始化session state中的参数
    if "selected_region" not in st.session_state:
        st.session_state.selected_region = None
    if "selected_universe" not in st.session_state:
        st.session_state.selected_universe = None
    if "selected_delay" not in st.session_state:
        st.session_state.selected_delay = None
    if "selected_category" not in st.session_state:
        st.session_state.selected_category = None
    
    # 地区选择 - 添加"所有"选项
    region_options = ["All"] + list(REGION_PARAMS.keys())
    default_region_index = 0  # 默认选择"All"
    if st.session_state.selected_region is not None and st.session_state.selected_region in region_options:
        default_region_index = region_options.index(st.session_state.selected_region)
    selected_region_display = st.selectbox(
        "地区", 
        region_options, 
        index=default_region_index,
        key="sidebar_region_select"
    )
    # 如果选择了"All"，则设置为None，否则设置为具体的地区
    if selected_region_display == "All":
        st.session_state.selected_region = None
        selected_region = None  # 用于后续逻辑的变量
    else:
        st.session_state.selected_region = selected_region_display
        selected_region = selected_region_display

    # 股票池选择 - 添加"所有"选项
    if selected_region is not None:
        universe_options = REGION_PARAMS[selected_region]["universe"]
    else:
        # 如果没有选择特定地区，则显示所有可能的股票池选项
        all_universe_options = set()
        for params in REGION_PARAMS.values():
            all_universe_options.update(params["universe"])
        universe_options = ["All"] + sorted(list(all_universe_options))
    
    default_universe_index = 0  # 默认选择"All"
    if st.session_state.selected_universe is not None and st.session_state.selected_universe in universe_options:
        default_universe_index = universe_options.index(st.session_state.selected_universe)
    selected_universe_display = st.selectbox(
        "股票池", 
        universe_options,
        index=default_universe_index,
        key="sidebar_universe_select"
    )
    # 如果选择了"All"，则设置为None，否则设置为具体的股票池
    if selected_universe_display == "All":
        st.session_state.selected_universe = None
    else:
        st.session_state.selected_universe = selected_universe_display

    # 延迟天数选择 - 添加"所有"选项
    if selected_region is not None:
        delay_options = REGION_PARAMS[selected_region]["delay"]
    else:
        # 如果没有选择特定地区，则显示所有可能的延迟选项
        all_delay_options = set()
        for params in REGION_PARAMS.values():
            all_delay_options.update(params["delay"])
        delay_options = ["All"] + sorted(list(all_delay_options))
    
    default_delay_index = 0  # 默认选择"All"
    if st.session_state.selected_delay is not None and st.session_state.selected_delay in delay_options:
        default_delay_index = delay_options.index(st.session_state.selected_delay)
    selected_delay_display = st.selectbox(
        "延迟天数", 
        delay_options,
        index=default_delay_index,
        key="sidebar_delay_select"
    )
    # 如果选择了"All"，则设置为None，否则设置为具体的延迟天数
    if selected_delay_display == "All":
        st.session_state.selected_delay = None
    else:
        st.session_state.selected_delay = selected_delay_display

    # 分类选择 - 添加"所有"选项
    category_options = [cat[0] for cat in CATEGORIES]
    category_values = [cat[1] for cat in CATEGORIES]
    current_category_index = 0
    if st.session_state.selected_category is not None and st.session_state.selected_category in category_values:
        current_category_index = category_values.index(st.session_state.selected_category)
    selected_category_name = st.selectbox(
        "分类", 
        category_options, 
        index=current_category_index,
        key="sidebar_category_select"
    )
    selected_category = CATEGORIES[category_options.index(selected_category_name)][1]
    # 如果选择了"All"，则设置为None，否则设置为具体的分类
    if selected_category == '':
        st.session_state.selected_category = None
    else:
        st.session_state.selected_category = selected_category
        
def _handle_logout():
    """处理退出登录逻辑"""
    try:
        # 调用session的logout方法
        session = st.session_state.global_session
        session.logout()
        
        # 清除浏览器存储的session
        try:
            import streamlit_js_eval
            streamlit_js_eval.set_cookie("brain_lit_session", "", -1)  # 删除cookie
            logger.info("已从浏览器cookie清除AutoLoginSession")
        except Exception as e:
            logger.error(f"从浏览器清除AutoLoginSession时出错: {e}")
            
        st.success("已退出登录")
        st.switch_page("app.py")
        # st.stop()  # 添加这行确保立即停止执行并跳转
    except Exception as e:
        logger.error(f"退出登录时发生错误: {e}")
        st.error("退出登录时发生错误，请重新尝试")