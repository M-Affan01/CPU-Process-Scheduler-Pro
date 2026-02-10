import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import random

# ================== SCHEDULER CLASSES ==================

class ModernProcessScheduler:
    def __init__(self, processes):
        self.processes = processes
        self.execution_order = []
        self.avg_waiting_time = 0
        self.avg_turnaround_time = 0
        self.cpu_utilization = 0
        self.timeline = []

    def calculate_metrics(self):
        if not self.processes:
            return
        total_waiting = sum(p['waiting_time'] for p in self.processes)
        total_turnaround = sum(p['turnaround_time'] for p in self.processes)
        total_burst = sum(p['burst_time'] for p in self.processes)
        n = len(self.processes)
        self.avg_waiting_time = total_waiting / n
        self.avg_turnaround_time = total_turnaround / n
        if self.execution_order:
            total_time = self.execution_order[-1]['completion_time']
            self.cpu_utilization = (total_burst / total_time) * 100 if total_time > 0 else 0

class FCFSScheduler(ModernProcessScheduler):
    def schedule(self):
        ready = sorted(self.processes, key=lambda x: x['arrival_time'])
        current_time = 0
        completed = []
        for proc in ready:
            if current_time < proc['arrival_time']:
                current_time = proc['arrival_time']
            start = current_time
            completion = start + proc['burst_time']
            turnaround = completion - proc['arrival_time']
            waiting = turnaround - proc['burst_time']
            proc.update({
                'start_time': start,
                'completion_time': completion,
                'turnaround_time': turnaround,
                'waiting_time': waiting
            })
            self.execution_order.append(proc.copy())
            current_time = completion
            completed.append(proc)
        self.processes = completed
        self.calculate_metrics()

class SJFScheduler(ModernProcessScheduler):
    def schedule(self):
        current_time = 0
        completed = []
        remaining = self.processes.copy()
        while remaining:
            arrived = [p for p in remaining if p['arrival_time'] <= current_time]
            if not arrived:
                current_time = min(p['arrival_time'] for p in remaining)
                continue
            proc = min(arrived, key=lambda x: x['burst_time'])
            remaining.remove(proc)
            start = current_time
            completion = start + proc['burst_time']
            turnaround = completion - proc['arrival_time']
            waiting = turnaround - proc['burst_time']
            proc.update({
                'start_time': start,
                'completion_time': completion,
                'turnaround_time': turnaround,
                'waiting_time': waiting
            })
            self.execution_order.append(proc.copy())
            current_time = completion
            completed.append(proc)
        self.processes = completed
        self.calculate_metrics()

class RRScheduler(ModernProcessScheduler):
    def __init__(self, processes, quantum=2):
        super().__init__(processes)
        self.quantum = quantum

    def schedule(self):
        proc_list = []
        for p in self.processes:
            proc_list.append({
                'id': p['id'],
                'arrival_time': p['arrival_time'],
                'burst_time': p['burst_time'],
                'remaining': p['burst_time'],
                'completed_at': None,
                'first_start': None
            })
        current_time = 0
        queue = []
        completed = []

        while len(completed) < len(proc_list):
            for proc in proc_list:
                if proc not in queue and proc not in completed and proc['arrival_time'] <= current_time:
                    queue.append(proc)

            if not queue:
                future = [p for p in proc_list if p not in completed]
                if future:
                    current_time = min(p['arrival_time'] for p in future)
                    continue

            proc = queue.pop(0)
            if proc['first_start'] is None:
                proc['first_start'] = current_time

            exec_time = min(self.quantum, proc['remaining'])
            start_time = current_time
            current_time += exec_time
            proc['remaining'] -= exec_time

            # In RR, we need to add each burst segment to execution_order for Gantt chart
            self.execution_order.append({
                'id': proc['id'],
                'burst_time': exec_time,
                'completion_time': current_time,
                'arrival_time': proc['arrival_time']
            })

            # Check for newly arrived processes during this execution segment
            for p in proc_list:
                if p not in queue and p not in completed and p['id'] != proc['id'] and p['arrival_time'] <= current_time:
                    queue.append(p)

            if proc['remaining'] == 0:
                proc['completed_at'] = current_time
                completed.append(proc)
            else:
                queue.append(proc)

        # Compute metrics
        for proc in completed:
            original = next(p for p in self.processes if p['id'] == proc['id'])
            turnaround = proc['completed_at'] - proc['arrival_time']
            waiting = turnaround - original['burst_time']
            original.update({
                'start_time': proc['first_start'],
                'completion_time': proc['completed_at'],
                'turnaround_time': turnaround,
                'waiting_time': waiting
            })
        self.processes = [next(p for p in self.processes if p['id'] == proc['id']) for proc in completed]
        self.calculate_metrics()

# ================== STREAMLIT APP ==================

st.set_page_config(page_title="Process Scheduler Pro", layout="wide", page_icon="🚀")

# Modern Styling
st.markdown("""
<style>
    .main {
        background-color: #0f0f15;
        color: #e0e0ff;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        background-color: #4a6cf7;
        color: white;
        font-weight: bold;
    }
    .stMetric {
        background-color: #1a1a22;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #333;
    }
</style>
""", unsafe_allow_html=True)

st.title("⚡ Ultra-Modern Process Scheduling Simulator")
st.subheader("Compare FCFS, SJF & Round Robin with Completion Times")

# Sidebar for Inputs
with st.sidebar:
    st.header("➕ Add Processes")
    with st.form("add_proc_form", clear_on_submit=True):
        arrival = st.number_input("⏰ Arrival Time", min_value=0, step=1, value=0)
        burst = st.number_input("⚡ Burst Time", min_value=1, step=1, value=1)
        submitted = st.form_submit_button("➕ Add Process")
        
    if submitted:
        if 'processes' not in st.session_state:
            st.session_state.processes = []
        if 'current_id' not in st.session_state:
            st.session_state.current_id = 1
            
        st.session_state.processes.append({
            'id': st.session_state.current_id,
            'arrival_time': arrival,
            'burst_time': burst
        })
        st.session_state.current_id += 1
        st.success(f"Added Process P{st.session_state.current_id-1}")

    st.divider()
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑️ Clear All"):
            st.session_state.processes = []
            st.session_state.current_id = 1
            st.session_state.results = None
            st.rerun()
    with col2:
        if st.button("🎲 Random (5)"):
            st.session_state.processes = []
            st.session_state.current_id = 1
            for i in range(5):
                st.session_state.processes.append({
                    'id': st.session_state.current_id,
                    'arrival_time': random.randint(0, 8),
                    'burst_time': random.randint(1, 7)
                })
                st.session_state.current_id += 1
            st.rerun()

    st.divider()
    
    quantum = st.number_input("⏱️ RR Quantum", min_value=1, step=1, value=2)
    
    if st.button("▶️ Run FCFS", type="primary"):
        st.session_state.run_type = 'FCFS'
    if st.button("▶️ Run SJF", type="primary"):
        st.session_state.run_type = 'SJF'
    if st.button("▶️ Run RR", type="primary"):
        st.session_state.run_type = 'RR'
    if st.button("📊 Compare All", type="secondary"):
        st.session_state.run_type = 'COMPARE'

# Main Content Area
if 'processes' in st.session_state and st.session_state.processes:
    st.write("### 📋 Current Processes")
    df = pd.DataFrame(st.session_state.processes)
    st.dataframe(df.set_index('id'), use_container_width=True)

    # Simulation Logic
    if 'run_type' in st.session_state:
        run_type = st.session_state.run_type
        
        def get_scheduler(rtype, procs):
            if rtype == 'FCFS': return FCFSScheduler(procs)
            if rtype == 'SJF': return SJFScheduler(procs)
            if rtype == 'RR': return RRScheduler(procs, quantum)
            return None

        def plot_gantt(scheduler, title):
            fig, ax = plt.subplots(figsize=(12, 3))
            fig.patch.set_facecolor('#0f0f15')
            ax.set_facecolor('#1a1a22')
            
            for spine in ax.spines.values(): spine.set_visible(False)
            ax.tick_params(colors='#e0e0ff')
            ax.set_yticks([])
            
            colors = plt.cm.tab10(np.linspace(0, 1, 10))
            
            time = 0
            for p in scheduler.execution_order:
                color = colors[(p['id'] - 1) % 10]
                # In RR, slices might not start at 'time' if there's idle time
                # but our schedulers jump idle time. Let's use cumulative sum for 'time'
                # Actually, execution_order has 'completion_time' and 'burst_time'
                start_time = p['completion_time'] - p['burst_time']
                ax.barh(0, p['burst_time'], left=start_time, height=0.7, color=color, edgecolor='white', linewidth=1.2)
                ax.text(start_time + p['burst_time']/2, 0, f"P{p['id']}", color='white', 
                        ha='center', va='center', fontweight='bold')
                ax.text(p['completion_time'], -0.4, str(p['completion_time']), color='#a0a0c0', ha='center', fontsize=9)
            
            if scheduler.execution_order:
                ax.text(scheduler.execution_order[0]['completion_time'] - scheduler.execution_order[0]['burst_time'], -0.4, 
                        str(scheduler.execution_order[0]['completion_time'] - scheduler.execution_order[0]['burst_time']), 
                        color='#a0a0c0', ha='center', fontsize=9)

            ax.set_title(title, color='#4a6cf7', fontweight='bold')
            return fig

        def plot_execution_flow(scheduler):
            proc_intervals = {}
            for item in scheduler.execution_order:
                pid = item['id']
                start = item['completion_time'] - item['burst_time']
                end = item['completion_time']
                if pid not in proc_intervals: proc_intervals[pid] = []
                proc_intervals[pid].append((start, end))

            pids = sorted(proc_intervals.keys())
            fig, ax = plt.subplots(figsize=(12, max(3, len(pids) * 0.6)))
            fig.patch.set_facecolor('#0f0f15')
            ax.set_facecolor('#1a1a22')
            colors = plt.cm.tab10(np.linspace(0, 1, 10))

            for i, pid in enumerate(pids):
                y = len(pids) - i - 1
                color = colors[(pid - 1) % 10]
                for (start, end) in proc_intervals[pid]:
                    ax.barh(y, end - start, left=start, height=0.6, color=color, edgecolor='white')
                    ax.text(end, y, f" {end}", va='center', color='#a0a0c0', fontsize=8)
                ax.text(-0.5, y, f"P{pid}", va='center', ha='right', fontweight='bold', color='#e0e0ff')

            ax.set_yticks([])
            ax.set_xlabel("Time", color='#e0e0ff')
            ax.tick_params(colors='#e0e0ff')
            ax.set_title("Execution Flow – Per Process Timeline", color='#4a6cf7', fontweight='bold')
            return fig

        if run_type in ['FCFS', 'SJF', 'RR']:
            st.divider()
            st.header(f"🎯 {run_type} Results")
            
            s = get_scheduler(run_type, [p.copy() for p in st.session_state.processes])
            s.schedule()
            
            res_df = pd.DataFrame(s.processes)
            
            tab1, tab2, tab3 = st.tabs(["📈 Gantt Chart", "📋 Metrics", "🎬 Execution Flow"])
            
            with tab1:
                st.pyplot(plot_gantt(s, f"{run_type} Gantt Chart"))
            
            with tab2:
                col_m1, col_m2, col_m3 = st.columns(3)
                col_m1.metric("Avg Waiting Time", f"{s.avg_waiting_time:.2f}")
                col_m2.metric("Avg Turnaround", f"{s.avg_turnaround_time:.2f}")
                col_m3.metric("CPU Utilization", f"{s.cpu_utilization:.2f}%")
                
                st.table(res_df[['id', 'arrival_time', 'burst_time', 'waiting_time', 'turnaround_time', 'completion_time']].set_index('id'))

            with tab3:
                st.pyplot(plot_execution_flow(s))
                
        elif run_type == 'COMPARE':
            st.divider()
            st.header("📊 Algorithm Comparison")
            
            fcfs = get_scheduler('FCFS', [p.copy() for p in st.session_state.processes])
            sjf = get_scheduler('SJF', [p.copy() for p in st.session_state.processes])
            rr = get_scheduler('RR', [p.copy() for p in st.session_state.processes])
            
            fcfs.schedule()
            sjf.schedule()
            rr.schedule()
            
            comp_data = [
                {'Algorithm': 'FCFS', 'Avg Wait': fcfs.avg_waiting_time, 'Avg TAT': fcfs.avg_turnaround_time, 'CPU%': fcfs.cpu_utilization},
                {'Algorithm': 'SJF', 'Avg Wait': sjf.avg_waiting_time, 'Avg TAT': sjf.avg_turnaround_time, 'CPU%': sjf.cpu_utilization},
                {'Algorithm': 'Round Robin', 'Avg Wait': rr.avg_waiting_time, 'Avg TAT': rr.avg_turnaround_time, 'CPU%': rr.cpu_utilization}
            ]
            st.table(pd.DataFrame(comp_data).set_index('Algorithm'))
            
            best_wait = min(comp_data, key=lambda x: x['Avg Wait'])['Algorithm']
            st.success(f"🏆 Recommendation: **{best_wait}** minimizes average waiting time for this workload.")
            
            st.write("#### Comparison Gantt Charts")
            st.pyplot(plot_gantt(fcfs, "FCFS"))
            st.pyplot(plot_gantt(sjf, "SJF"))
            st.pyplot(plot_gantt(rr, f"Round Robin (Q={quantum})"))

else:
    st.info("Add some processes using the sidebar to start the simulation!")

st.markdown("---")
st.markdown("Built with ❤️ for OS enthusiasts")