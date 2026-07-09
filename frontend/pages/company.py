import streamlit as st
from frontend.utils.state import init, page_guide
from frontend.utils.sanitize import xss_escape


def render():
    init()
    st.markdown(
        "<h1 style='font-size: 2.2rem;'>Company Insights</h1>",
        unsafe_allow_html=True,
    )

    page_guide(
        "Company Insights",
        "Researches the company extracted from your JD or resume experience. Returns overview, culture fit indicators, growth opportunities, red flags, employee review insights, and salary estimate in ₹INR/LPA.",
        "Company name and overall suitability (POOR/FAIR/GOOD/EXCELLENT) at top. Below: overview, culture/growth/red-flag sections, employee reviews (culture score, pros/cons, WLB, career growth), and salary range. Salary is an LLM estimate — not real-time market data.",
        "Run a full analysis with a JD. Use the culture fit and red flags to decide if the company aligns with your values. Use salary as a rough benchmark. Cross-check with Glassdoor/AmbitionBox for actual numbers.",
    )

    result = st.session_state.get("analysis_result")
    cr = (result or {}).get("company_result", {}) if result else None
    sr = (result or {}).get("salary_result", {}) if result else None

    if not cr:
        st.info("Run a full analysis from the ATS Analysis page first.")
        return

    company = xss_escape(cr.get("company_name", "Unknown"))
    suitability = cr.get("overall_suitability", "UNKNOWN")
    overview = cr.get("company_overview", "")
    culture = cr.get("culture_fit_indicators", [])
    growth = cr.get("growth_opportunities", [])
    red_flags = cr.get("red_flags", [])
    industry_position = cr.get("industry_position", "")

    culture_score = cr.get("culture_score")
    review_summary = cr.get("review_summary", "")
    pros = cr.get("pros", [])
    cons = cr.get("cons", [])
    work_life_balance = cr.get("work_life_balance", "Average")
    career_growth = cr.get("career_growth", "Average")

    salary_range = (sr or {}).get("salary_range")
    salary_currency = (sr or {}).get("currency", "USD")
    salary_confidence = (sr or {}).get("confidence", "Low")
    salary_factors = (sr or {}).get("factors", [])

    suit_color = {"EXCELLENT": "#5db872", "GOOD": "#5db8a6", "FAIR": "#d4a017", "POOR": "#c64545", "UNKNOWN": "#6c6a64"}.get(suitability, "#6c6a64")

    st.markdown(
        f"""
        <div style="background: #efe9de; border: 1px solid #e6dfd8; border-radius: 10px; padding: 1.5rem; margin-bottom: 1.5rem;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <div style="font-family: Inter, sans-serif; font-size: 0.7rem; font-weight: 500; letter-spacing: 1.5px;
                                text-transform: uppercase; color: #6c6a64;">Company</div>
                    <div style="font-family: Playfair Display, serif; font-size: 1.8rem; color: #141413;">{company}</div>
                </div>
                <div style="text-align: right;">
                    <div style="font-family: Inter, sans-serif; font-size: 0.7rem; font-weight: 500; letter-spacing: 1.5px;
                                text-transform: uppercase; color: #6c6a64;">Suitability</div>
                    <div style="font-family: Playfair Display, serif; font-size: 1.8rem; color: {suit_color};">{suitability}</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if industry_position:
        st.markdown(
            f"""
            <div style="background: #f5f0e8; border: 1px solid #e6dfd8; border-radius: 8px; padding: 0.8rem 1rem; margin-bottom: 1rem;
                        display: flex; align-items: center; gap: 0.6rem;">
                <span style="font-size: 1.2rem;">🏢</span>
                <span style="font-size: 0.85rem; color: #3d3d3a;"><strong>Industry Position:</strong> {xss_escape(industry_position)}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    if overview:
        st.markdown(
            "<h3 style='font-size: 1.2rem;'>Overview</h3>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<div style='background: #f5f0e8; border: 1px solid #e6dfd8; border-radius: 8px; padding: 1rem; "
            f"font-size: 0.9rem; color: #3d3d3a; line-height: 1.6;'>{xss_escape(overview)}</div>",
            unsafe_allow_html=True,
        )

    # Salary Estimate Card
    if salary_range:
        conf_color = {"High": "#5db872", "Medium": "#d4a017", "Low": "#c64545"}.get(salary_confidence, "#6c6a64")
        st.markdown(
            f"""
            <div style="background: #f5f0e8; border: 1px solid #e6dfd8; border-radius: 10px; padding: 1rem; margin-bottom: 1.5rem;
                        display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <div style="font-family: Inter, sans-serif; font-size: 0.7rem; font-weight: 500; letter-spacing: 1.5px;
                                text-transform: uppercase; color: #6c6a64;">Salary Estimate</div>
                    <div style="font-family: Playfair Display, serif; font-size: 1.6rem; color: #141413;">{salary_range} <span style="font-size:1rem;color:#6c6a64;">{salary_currency}</span></div>
                    <div style="font-size:0.8rem;color:#6c6a64;margin-top:0.3rem;">
                        Confidence: <span style="color:{conf_color};font-weight:500;">{salary_confidence}</span>
                        {f' — {" · ".join(xss_escape(f) for f in salary_factors[:3])}' if salary_factors else ''}
                    </div>
                </div>
                <div style="text-align:right;">
                    <span style="font-size:2rem;">💰</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Employee Reviews Card (if enhanced data available)
    if culture_score is not None and culture_score > 0:
        wlb_color = {"Good": "#5db872", "Average": "#d4a017", "Poor": "#c64545"}.get(work_life_balance, "#6c6a64")
        cg_color = {"Good": "#5db872", "Average": "#d4a017", "Poor": "#c64545"}.get(career_growth, "#6c6a64")
        st.markdown(
            f"""
            <div style="background: #efe9de; border: 1px solid #e6dfd8; border-radius: 10px; padding: 1rem; margin-bottom: 1rem;">
                <div style="font-family: Inter, sans-serif; font-size: 0.7rem; font-weight: 500; letter-spacing: 1.5px;
                            text-transform: uppercase; color: #6c6a64; margin-bottom: 0.5rem;">Employee Reviews</div>
                <div style="display:flex; gap:1.5rem; align-items:center; margin-bottom:0.5rem;">
                    <div><span style="font-size:0.85rem;color:#6c6a64;">Culture Score</span>
                        <span style="font-size:1.4rem;font-weight:600;color:#141413;margin-left:0.5rem;">{culture_score}</span>
                        <span style="font-size:0.85rem;color:#6c6a64;">/100</span></div>
                    <div><span style="font-size:0.85rem;color:#6c6a64;">Work-Life</span>
                        <span style="font-size:1.1rem;font-weight:500;color:{wlb_color};margin-left:0.5rem;">{work_life_balance}</span></div>
                    <div><span style="font-size:0.85rem;color:#6c6a64;">Career Growth</span>
                        <span style="font-size:1.1rem;font-weight:500;color:{cg_color};margin-left:0.5rem;">{career_growth}</span></div>
                </div>
                {f'<div style="font-size:0.85rem;color:#3d3d3a;line-height:1.5;margin-bottom:0.5rem;">{xss_escape(review_summary)}</div>' if review_summary else ''}
            </div>
            """,
            unsafe_allow_html=True,
        )

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(
            "<h3 style='font-size: 1rem;'>Culture Fit</h3>",
            unsafe_allow_html=True,
        )
        for item in culture:
            st.markdown(f"<p style='font-size: 0.85rem; color: #3d3d3a;'>• {xss_escape(item)}</p>", unsafe_allow_html=True)
        if not culture:
            st.markdown("<p style='font-size: 0.85rem; color: #6c6a64;'>No indicators available.</p>", unsafe_allow_html=True)

    with col2:
        st.markdown(
            "<h3 style='font-size: 1rem;'>Growth Opportunities</h3>",
            unsafe_allow_html=True,
        )
        for item in growth:
            st.markdown(f"<p style='font-size: 0.85rem; color: #3d3d3a;'>• {xss_escape(item)}</p>", unsafe_allow_html=True)
        if not growth:
            st.markdown("<p style='font-size: 0.85rem; color: #6c6a64;'>No opportunities listed.</p>", unsafe_allow_html=True)

    with col3:
        st.markdown(
            "<h3 style='font-size: 1rem;'>Red Flags</h3>",
            unsafe_allow_html=True,
        )
        for item in red_flags:
            st.markdown(f"<p style='font-size: 0.85rem; color: #c64545;'>⚠ {xss_escape(item)}</p>", unsafe_allow_html=True)
        if not red_flags:
            st.markdown("<p style='font-size: 0.85rem; color: #6c6a64;'>No red flags detected.</p>", unsafe_allow_html=True)

    with col4:
        st.markdown(
            "<h3 style='font-size: 1rem;'>Employee Reviews</h3>",
            unsafe_allow_html=True,
        )
        if pros:
            st.markdown("<p style='font-size:0.85rem;color:#5db872;margin-bottom:0.2rem;'><strong>Pros</strong></p>", unsafe_allow_html=True)
            for p in pros[:3]:
                st.markdown(f"<p style='font-size: 0.8rem; color: #3d3d3a; margin-bottom:0.15rem;'>✅ {xss_escape(p)}</p>", unsafe_allow_html=True)
        if cons:
            st.markdown("<p style='font-size:0.85rem;color:#c64545;margin:0.3rem 0 0.2rem 0;'><strong>Cons</strong></p>", unsafe_allow_html=True)
            for c in cons[:3]:
                st.markdown(f"<p style='font-size: 0.8rem; color: #3d3d3a; margin-bottom:0.15rem;'>⚠ {xss_escape(c)}</p>", unsafe_allow_html=True)
        if not pros and not cons:
            st.markdown("<p style='font-size: 0.85rem; color: #6c6a64;'>No review data available.</p>", unsafe_allow_html=True)
