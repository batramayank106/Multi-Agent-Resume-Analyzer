import time
import streamlit as st


def show_entrance(label="Loading...", duration=0.6):
    pass


def show_ats_loading(duration=0.8):
    pass


def show_pipeline_animation(agents, step_delay=0.5, active_index=None, complete=False):
    placeholder = st.empty()

    def _render(index, status="running", current_agent_name=None):
        nodes_html = ""
        for j, a in enumerate(agents):
            if j < index:
                nodes_html += f'<div class="pl-node done"><div class="pl-check">\u2713</div><span>{a}</span></div>'
            elif j == index:
                nodes_html += f'<div class="pl-node active"><div class="pl-pulse"></div><span>{a}</span></div>'
            else:
                nodes_html += f'<div class="pl-node"><div class="pl-dot"></div><span>{a}</span></div>'
            if j < len(agents) - 1:
                if j < index:
                    nodes_html += f'<div class="pl-arrow active"></div>'
                else:
                    nodes_html += f'<div class="pl-arrow"></div>'

        if status == "running":
            agent_label = current_agent_name or (agents[index] if index < len(agents) else "")
            title = f"Running Analysis Pipeline — {agent_label}"
        else:
            title = "Analysis Complete"

        placeholder.markdown(f"""
        <div class="pl-wrap">
            <p class="pl-title">{title}</p>
            <div class="pl-flow">{nodes_html}</div>
        </div>
        """, unsafe_allow_html=True)

    if complete:
        _render(len(agents), "complete")
        return

    if active_index is not None:
        _render(active_index, "running", agents[active_index] if active_index < len(agents) else None)
    else:
        for i in range(len(agents)):
            _render(i, "running", agents[i])
            time.sleep(step_delay)
        _render(len(agents), "complete")
