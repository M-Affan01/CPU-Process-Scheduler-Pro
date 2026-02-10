import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import time
import random

# ================== SCHEDULER ENGINE V4.0 ==================

class CPUCore:
    @staticmethod
    def fcfs(processes):
        ready = sorted([p.copy() for p in processes], key=lambda x: x['arrival_time'])
        current_time, execution_order = 0, []
        for p in ready:
            if current_time < p['arrival_time']: current_time = p['arrival_time']
            start = current_time
            comp = start + p['burst_time']
            p.update({'start_time': start, 'completion_time': comp, 'turnaround_time': comp - p['arrival_time'], 'waiting_time': (comp - p['arrival_time']) - p['burst_time']})
            execution_order.append(p.copy())
            current_time = comp
        return ready, execution_order

    @staticmethod
    def sjf(processes):
        current_time, completed, execution_order = 0, [], []
        remaining = [p.copy() for p in processes]
        while remaining:
            arrived = [p for p in remaining if p['arrival_time'] <= current_time]
            if not arrived:
                current_time = min(p['arrival_time'] for p in remaining)
                continue
            p = min(arrived, key=lambda x: x['burst_time'])
            remaining.remove(p)
            start = current_time
            comp = start + p['burst_time']
            p.update({'start_time': start, 'completion_time': comp, 'turnaround_time': comp - p['arrival_time'], 'waiting_time': (comp - p['arrival_time']) - p['burst_time']})
            execution_order.append(p.copy())
            current_time = comp
            completed.append(p)
        return completed, execution_order

    @staticmethod
    def rr(processes, quantum):
        proc_list = [{'id': p['id'], 'arrival_time': p['arrival_time'], 'burst_time': p['burst_time'], 'rem': p['burst_time'], 'first_start': None, 'comp': None} for p in processes]
        current_time, queue, completed, execution_order = 0, [], [], []
        while len(completed) < len(proc_list):
            for p in proc_list:
                if p not in queue and p not in completed and p['arrival_time'] <= current_time: queue.append(p)
            if not queue:
                future = [p for p in proc_list if p not in completed]
                if future: current_time = min(p['arrival_time'] for p in future); continue
            p = queue.pop(0)
            if p['first_start'] is None: p['first_start'] = current_time
            exec_t = min(quantum, p['rem'])
            start = current_time
            current_time += exec_t
            p['rem'] -= exec_t
            execution_order.append({'id': p['id'], 'start_time': start, 'completion_time': current_time})
            for next_p in proc_list:
                if next_p not in queue and next_p not in completed and next_p['arrival_time'] <= current_time and next_p != p: queue.append(next_p)
            if p['rem'] == 0: p['comp'] = current_time; completed.append(p)
            else: queue.append(p)
        
        final_procs = []
        for p in proc_list:
            tat = p['comp'] - p['arrival_time']
            final_procs.append({'id': p['id'], 'arrival_time': p['arrival_time'], 'burst_time': p['burst_time'], 'start_time': p['first_start'], 'completion_time': p['comp'], 'turnaround_time': tat, 'waiting_time': tat - p['burst_time']})
        return final_procs, execution_order

# ================== ICON SYSTEM (SVG) ==================

ICONS = {
    'cpu': '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="4" width="16" height="16" rx="2" ry="2"></rect><rect x="9" y="9" width="6" height="6"></rect><line x1="9" y1="1" x2="9" y2="4"></line><line x1="15" y1="1" x2="15" y2="4"></line><line x1="9" y1="20" x2="9" y2="23"></line><line x1="15" y1="20" x2="15" y2="23"></line><line x1="20" y1="9" x2="23" y2="9"></line><line x1="20" y1="15" x2="23" y2="15"></line><line x1="1" y1="9" x2="4" y2="9"></line><line x1="1" y1="15" x2="4" y2="15"></line></svg>',
    'list': '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="8" y1="6" x2="21" y2="6"></line><line x1="8" y1="12" x2="21" y2="12"></line><line x1="8" y1="18" x2="21" y2="18"></line><line x1="3" y1="6" x2="3.01" y2="6"></line><line x1="3" y1="12" x2="3.01" y2="12"></line><line x1="3" y1="18" x2="3.01" y2="18"></line></svg>',
    'plus': '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>',
    'chart': '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line></svg>',
    'pulse': '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline></svg>',
    'settings': '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>'
}

# ================== DESIGN SYSTEM V4.0 ==================

st.set_page_config(page_title="CPU-PRO CORE // V4.0", layout="wide", page_icon="✨")

st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=IBM+Plex+Mono&display=swap');

    :root {{
        --bg-main: #050508;
        --surface: #0a0a0f;
        --card: #13131a;
        --primary: #6366f1;
        --primary-glow: rgba(99, 102, 241, 0.4);
        --accent: #22d3ee;
        --success: #10b981;
        --text-1: #e2e8f0;
        --text-2: #94a3b8;
        --border: rgba(255, 255, 255, 0.05);
    }}

    .stApp {{
        background: var(--bg-main);
        color: var(--text-1);
        font-family: 'Space Grotesk', sans-serif;
    }}

    .platinum-header {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 1.5rem 3rem;
        background: rgba(10, 10, 15, 0.95);
        border-bottom: 2px solid var(--border);
        margin-bottom: 2rem;
        position: sticky;
        top: 0;
        z-index: 1001;
    }}

    .brand {{
        display: flex;
        align-items: center;
        gap: 15px;
        font-size: 1.6rem;
        font-weight: 700;
        letter-spacing: -1px;
        color: #fff;
    }}

    .brand-accent {{
        background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }}

    .icon-box {{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        padding: 10px;
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid var(--border);
        border-radius: 12px;
        color: var(--primary);
    }}

    .custom-card {{
        background: var(--card);
        border: 1px solid var(--border);
        border-radius: 24px;
        padding: 2rem;
        margin-bottom: 2rem;
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.3);
    }}

    .card-label {{
        display: flex;
        align-items: center;
        gap: 10px;
        font-size: 0.9rem;
        font-weight: 600;
        color: var(--text-2);
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-bottom: 2rem;
    }}

    /* Global Overrides for Professionalism */
    .stMetric {{ background: transparent !important; padding: 0 !important; border: none !important; }}
    .stMetric label {{ color: var(--text-2) !important; font-size: 0.8rem !important; text-transform: uppercase !important; letter-spacing: 1px !important; }}
    .stMetric value {{ font-size: 2rem !important; font-weight: 700 !important; font-family: 'Space Grotesk' !important; }}

    .stButton button {{
        background: var(--primary) !important;
        border-radius: 12px !important;
        border: none !important;
        font-weight: 600 !important;
        text-transform: none !important;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
        color: white !important;
        padding: 0.6rem 2rem !important;
    }}

    .stButton button:hover {{
        background: #4f46e5 !important;
        transform: translateY(-1px);
        box-shadow: 0 8px 20px var(--primary-glow);
    }}

    section[data-testid="stSidebar"] {{ display: none !important; }}
    
    ::-webkit-scrollbar {{ width: 4px; height: 4px; }}
    ::-webkit-scrollbar-thumb {{ background: rgba(255, 255, 255, 0.1); border-radius: 10px; }}
    
    .status-dot {{
        height: 8px;
        width: 8px;
        background-color: var(--success);
        border-radius: 50%;
        display: inline-block;
        margin-right: 8px;
        box-shadow: 0 0 10px var(--success);
    }}
</style>
""", unsafe_allow_html=True)

# App Shell
st.markdown(f"""
<div class="platinum-header">
    <div class="brand">
        <div class="icon-box">{ICONS['cpu']}</div>
        CPU-PRO <span class="brand-accent">PLATINUM V4.0</span>
    </div>
    <div style="display: flex; align-items: center; gap: 30px;">
        <div style="font-size: 0.8rem; color: var(--text-2); border-right: 1px solid var(--border); padding-right: 20px;">
            <span class="status-dot"></span> SYSTEM READY
        </div>
        <div style="font-family: 'IBM Plex Mono', monospace; font-size: 0.75rem; color: #6366f1;">
            BUILD_ID_2026.02_CORE
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Initialization
if 'procs' not in st.session_state: st.session_state.procs = []
if 'p_count' not in st.session_state: st.session_state.p_count = 1
if 'results' not in st.session_state: st.session_state.results = None

# KPI Summary Strip
if st.session_state.procs:
    k1, k2, k3, k4 = st.columns(4)
    with k1: st.metric("ACTIVE_THREADS", len(st.session_state.procs))
    with k2: st.metric("QUEUE_LOAD", f"{sum(p['burst_time'] for p in st.session_state.procs)} U")
    with k3: st.metric("COMPUTE_NODES", "CORE_01")
    with k4: st.metric("PLATFORM_STATE", "NOMINAL")

# 2-Column Desktop Grid
col_config, col_visuals = st.columns([1, 1.4], gap="large")

with col_config:
    # INPUT HUB
    st.markdown(f"""<div class="custom-card"><div class="card-label">
        <span style="color:var(--primary);">{ICONS['plus']}</span> THREAD CONFIGURATION
    </div>""", unsafe_allow_html=True)
    
    with st.form("add_proc", clear_on_submit=True):
        f_at = st.number_input("Arrival Offset (t)", min_value=0, step=1, value=0)
        f_bt = st.number_input("Burst Duration (ms)", min_value=1, step=1, value=5)
        if st.form_submit_button("COMMIT TO QUEUE"):
            st.session_state.procs.append({'id': st.session_state.p_count, 'arrival_time': f_at, 'burst_time': f_bt})
            st.session_state.p_count += 1
            st.rerun()
    
    st.markdown('<div style="margin-top: 2rem;"></div>', unsafe_allow_html=True)
    
    # GLOBAL ACTIONS
    a1, a2 = st.columns(2)
    if a1.button("🎲 SYNC RANDOM_5"):
        for _ in range(5):
            st.session_state.procs.append({'id': st.session_state.p_count, 'arrival_time': random.randint(0, 10), 'burst_time': random.randint(1, 15)})
            st.session_state.p_count += 1
        st.rerun()
    if a2.button("🗑️ PURGE ALL"):
        st.session_state.procs, st.session_state.p_count, st.session_state.results = [], 1, None
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # QUEUE REGISTRY
    st.markdown(f"""<div class="custom-card"><div class="card-label">
        <span style="color:var(--primary);">{ICONS['list']}</span> QUEUE REGISTRY (ACTIVE)
    </div>""", unsafe_allow_html=True)
    if st.session_state.procs:
        st.dataframe(pd.DataFrame(st.session_state.procs).set_index('id'), use_container_width=True, height=350)
    else:
        st.markdown('<p style="color:var(--text-2); font-size:0.9rem;">No active threads in registry.</p>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col_visuals:
    # ANALYTICS DASHBOARD
    st.markdown(f"""<div class="custom-card"><div class="card-label">
        <span style="color:var(--primary);">{ICONS['chart']}</span> ANALYTICS & EXECUTION ENGINE
    </div>""", unsafe_allow_html=True)
    
    e1, e2 = st.columns([1.5, 1])
    engine = e1.selectbox("Select Core Algorithm", ["FCFS - Sequential", "SJF - Optimal Latency", "RR - Fair Share", "Full Benchmark Audit"])
    quantum = e2.number_input("Quantum (T)", min_value=1, value=2, disabled=("RR" not in engine and "Audit" not in engine))
    
    if st.button("IGNITE SIMULATION ENGINE"):
        if not st.session_state.procs:
            st.error("Engine Halt: Thread registry is empty.")
        else:
            with st.spinner("Quantum alignment in progress..."):
                time.sleep(0.8)
                if "FCFS" in engine: res = CPUCore.fcfs(st.session_state.procs); st.session_state.results = ('FCFS', res)
                elif "SJF" in engine: res = CPUCore.sjf(st.session_state.procs); st.session_state.results = ('SJF', res)
                elif "RR" in engine: res = CPUCore.rr(st.session_state.procs, quantum); st.session_state.results = ('RR', res)
                else:
                    d1 = CPUCore.fcfs(st.session_state.procs)
                    d2 = CPUCore.sjf(st.session_state.procs)
                    d3 = CPUCore.rr(st.session_state.procs, quantum)
                    st.session_state.results = ('AUDIT', (d1, d2, d3))
    
    st.divider()

    if st.session_state.results:
        rtype, rdata = st.session_state.results
        
        if rtype == 'AUDIT':
            t1, t2 = st.tabs(["Performance Comparison", "Strategy Recommendation"])
            (f_p, f_o), (s_p, s_o), (r_p, r_o) = rdata
            
            with t1:
                comp_df = pd.DataFrame({
                    'Metric': ['Avg Wait', 'Avg Wait', 'Avg Wait', 'Avg Turnaround', 'Avg Turnaround', 'Avg Turnaround'],
                    'Value': [pd.DataFrame(f_p)['waiting_time'].mean(), pd.DataFrame(s_p)['waiting_time'].mean(), pd.DataFrame(r_p)['waiting_time'].mean(),
                              pd.DataFrame(f_p)['turnaround_time'].mean(), pd.DataFrame(s_p)['turnaround_time'].mean(), pd.DataFrame(r_p)['turnaround_time'].mean()],
                    'Algorithm': ['FCFS', 'SJF', 'RR', 'FCFS', 'SJF', 'RR']
                })
                fig = px.bar(comp_df, x='Algorithm', y='Value', color='Metric', barmode='group', 
                             template="plotly_dark", color_discrete_sequence=['#6366f1', '#22d3ee'])
                fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
                                  font_family='Space Grotesk', margin=dict(l=0,r=0,t=20,b=0))
                st.plotly_chart(fig, use_container_width=True)
            
            with t2:
                best = min([('FCFS', pd.DataFrame(f_p)['waiting_time'].mean()), ('SJF', pd.DataFrame(s_p)['waiting_time'].mean()), ('RR', pd.DataFrame(r_p)['waiting_time'].mean())], key=lambda x: x[1])
                st.markdown(f"""
                <div style="background:rgba(16,185,129,0.1); border-left:4px solid #10b981; padding:20px; border-radius:12px;">
                    <h3 style="color:#10b981; margin:0;">AUDIT WINNER: {best[0]}</h3>
                    <p style="color:var(--text-2); margin-top:10px;">Optimal latency achieved with <b>{best[1]:.2f} units</b> average wait time.</p>
                </div>
                """, unsafe_allow_html=True)

        else:
            final_p, exec_o = rdata
            stats_df = pd.DataFrame(final_p)
            
            # KPI Strip
            m1, m2, m3 = st.columns(3)
            m1.metric("AVG_WAIT_TIME", f"{stats_df['waiting_time'].mean():.2f}")
            m2.metric("AVG_TAT", f"{stats_df['turnaround_time'].mean():.2f}")
            total_time = pd.DataFrame(exec_o)['completion_time'].max()
            util = (sum(p['burst_time'] for p in st.session_state.procs) / total_time * 100)
            m3.metric("CPU_UTILIZATION", f"{util:.1f}%")
            
            # GANTT CHART
            st.markdown('<div style="margin-top:2rem;"></div>', unsafe_allow_html=True)
            fig_g = px.timeline([dict(Task=f"P{x['id']}", Start=x['start_time'], Finish=x['completion_time'], Color=f"P{x['id']}") for x in exec_o],
                                 x_start="Start", x_end="Finish", y="Task", color="Color", template="plotly_dark",
                                 title="Visual Execution Sequence (Gantt Chart)", color_discrete_sequence=px.colors.qualitative.G10)
            
            fig_g.layout.xaxis.type = 'linear'
            for i in range(len(fig_g.data)):
                d = exec_o[i]
                fig_g.data[i].x = [d['completion_time'] - d['start_time']]
                fig_g.data[i].base = d['start_time']
                
            fig_g.update_layout(showlegend=False, height=350, margin=dict(l=0, r=0, t=40, b=0),
                                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                                xaxis_title="Core Cycles (t)", yaxis_title="")
            st.plotly_chart(fig_g, use_container_width=True)

            # DEEP METRICS
            with st.expander("DEEP_KERNEL_METRIC_REPORT"):
                st.dataframe(stats_df.set_index('id'), use_container_width=True)

    else:
        st.markdown('<p style="color:var(--text-2); border:1px dashed var(--border); padding:40px; text-align:center; border-radius:20px;">Ready for simulation. Ignite engine to visualize data.</p>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# Footer
st.markdown(f"""
<div style="text-align: center; margin-top: 5rem; padding: 3rem; color: #475569; border-top: 1px solid var(--border);">
    <div style="display: flex; justify-content: center; gap: 40px; margin-bottom: 1.5rem;">
        <div style="font-weight: 700; color: #64748b;">LATEST REVISION: FEB 2026</div>
        <div style="color: #64748b;">INTEGRATED SCHEDULING SYSTEM</div>
        <div style="color: #64748b;">PLATINUM LICENSE: 0x48291A</div>
    </div>
    <div style="font-family: 'IBM Plex Mono', monospace; font-size: 0.7rem; letter-spacing: 0.2em; opacity: 0.5;">
        CORE_KERNEL_LOADED // ALL_SYSTEMS_OPTIMAL // STABLE_READY
    </div>
</div>
""", unsafe_allow_html=True)
