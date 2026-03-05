import streamlit as st
import json
from feedback.pipeline import (
    run_analysis_phase,
    run_evolution_phase,
    run_preview_phase,
    run_regeneration_phase,
    get_evolution_status,
)
from feedback.storage import (
    load_all_feedback,
    load_pattern_reports,
    load_prompt_evolutions,
    get_current_prompt_version,
    get_current_system_prompt,
)

# Page Config
st.set_page_config(
    page_title="Self-Evolution Dashboard",
    page_icon="gear",
    layout="wide",
)

st.markdown("## Self-Evolution Dashboard")
st.markdown("Manually trigger each phase of the prompt evolution cycle.")
st.markdown("---")

# --- Status Header ---
status = get_evolution_status()

col_s1, col_s2, col_s3 = st.columns(3)
with col_s1:
    st.metric("Prompt Version", status["current_prompt_version"])
with col_s2:
    st.metric("Total Feedback", status["total_feedback"])
with col_s3:
    st.metric("Evolutions", status["total_evolutions"])

st.markdown("---")

# --- Sidebar: Provider Selection ---
with st.sidebar:
    st.header("Configuration")
    provider = st.radio("LLM Provider", ("ollama", "gemini"), index=0)
    st.markdown("---")
    st.markdown("**Current System Prompt:**")
    current_prompt = get_current_system_prompt()
    st.code(current_prompt[:500] + "..." if len(current_prompt) > 500 else current_prompt, language="text")

# ========================================================================
# PHASE 1: Pattern Analysis
# ========================================================================
st.markdown("### Phase 1: Pattern Analysis")
st.markdown("Analyze accumulated expert feedback to identify systematic patterns.")

feedback_count = status["total_feedback"]
if feedback_count < 3:
    st.warning(f"Only {feedback_count} feedback entries collected. Recommend at least 10 for meaningful analysis.")

if st.button("Run Analysis", disabled=feedback_count == 0):
    with st.spinner("Analyzing feedback patterns..."):
        try:
            report = run_analysis_phase(provider=provider)
            st.success(f"Analysis complete! Report ID: {report.report_id}")
            st.session_state["latest_report_id"] = report.report_id
        except Exception as e:
            st.error(f"Analysis failed: {e}")

# Display latest report if available
reports = load_pattern_reports()
if reports:
    latest_report = reports[-1]

    with st.expander(f"Latest Report: {latest_report.report_id}", expanded=True):
        st.write(f"**Feedback Analyzed:** {latest_report.total_feedback_analyzed}")

        # Rating averages
        st.markdown("**Average Ratings:**")
        for dim, avg in latest_report.avg_ratings.items():
            label = dim.replace("_", " ").title()
            bar_val = avg / 5.0
            st.progress(bar_val, text=f"{label}: {avg}/5")

        # Weak dimensions
        if latest_report.low_scoring_dimensions:
            st.error("**Weak Dimensions:** " + ", ".join(
                d.replace("_", " ").title() for d in latest_report.low_scoring_dimensions
            ))

        if latest_report.strong_dimensions:
            st.success("**Strong Dimensions:** " + ", ".join(
                d.replace("_", " ").title() for d in latest_report.strong_dimensions
            ))

        # Themes
        st.markdown("**Recurring Themes:**")
        for t in latest_report.recurring_themes:
            st.markdown(f"- {t}")

        st.markdown("**Actionable Insights:**")
        for r in latest_report.actionable_insights:
            st.markdown(f"- {r}")

st.markdown("---")

# ========================================================================
# PHASE 2: Prompt Evolution
# ========================================================================
st.markdown("### Phase 2: Prompt Evolution")
st.markdown("Evolve the system prompt based on the pattern analysis.")

# Select report to base evolution on
if reports:
    report_options = [f"{r.report_id} ({r.timestamp[:10]})" for r in reports]
    selected_report_idx = st.selectbox(
        "Select Pattern Report",
        range(len(report_options)),
        format_func=lambda i: report_options[i],
        index=len(report_options) - 1,
    )
    selected_report = reports[selected_report_idx]

    col_ev1, col_ev2 = st.columns(2)

    with col_ev1:
        if st.button("Preview Evolution"):
            with st.spinner("Generating preview..."):
                try:
                    diff = run_preview_phase(selected_report.report_id, provider=provider)
                    st.session_state["evolution_diff"] = diff
                except Exception as e:
                    st.error(f"Preview failed: {e}")

    with col_ev2:
        if st.button("Apply Evolution", type="primary"):
            with st.spinner("Evolving prompt..."):
                try:
                    evolution = run_evolution_phase(selected_report.report_id, provider=provider)
                    st.success(f"Prompt evolved! {evolution.parent_prompt_version} -> {evolution.new_prompt_version}")
                    st.session_state["latest_evolution_id"] = evolution.evolution_id
                except Exception as e:
                    st.error(f"Evolution failed: {e}")

    # Show preview diff if available
    if "evolution_diff" in st.session_state:
        st.markdown("**Preview Diff:**")
        st.code(st.session_state["evolution_diff"], language="diff")

else:
    st.info("Run pattern analysis first (Phase 1) before evolving the prompt.")

st.markdown("---")

# ========================================================================
# PHASE 3: Dataset Regeneration
# ========================================================================
st.markdown("### Phase 3: Dataset Regeneration")
st.markdown("Regenerate training data using the evolved system prompt.")

evolutions = load_prompt_evolutions()
if evolutions:
    evo_options = [
        f"{e.evolution_id}: {e.parent_prompt_version} -> {e.new_prompt_version} ({e.timestamp[:10]})"
        for e in evolutions
    ]
    selected_evo_idx = st.selectbox(
        "Select Evolution",
        range(len(evo_options)),
        format_func=lambda i: evo_options[i],
        index=len(evo_options) - 1,
    )
    selected_evo = evolutions[selected_evo_idx]

    target_count = st.number_input("Target Entry Count", min_value=1, max_value=500, value=200)

    gen_mode = st.radio(
        "Generation Mode",
        ("v2", "v1"),
        format_func=lambda m: "v2 \u2013 JSON  (student-advisorv2-json)" if m == "v2" else "v1 \u2013 Text  (student-advisorv1-text)",
        index=0,
        horizontal=True,
    )

    # Preview the output filename (must match pipeline.py naming)
    try:
        _evo_num = selected_evo.new_prompt_version.split("_")[-1]
    except (AttributeError, IndexError):
        _evo_num = "1"
    if gen_mode == "v1":
        _preview_name = f"student_advisor_dataset_v1_evolved_{_evo_num}.jsonl"
    else:
        _preview_name = f"student_advisor_dataset_v2_evolved_{_evo_num}.jsonl"
    st.caption(f"Output file: {_preview_name}")

    if st.button("Start Regeneration"):
        with st.spinner(f"Regenerating {target_count} entries with evolved prompt..."):
            try:
                output_path = run_regeneration_phase(
                    selected_evo.evolution_id,
                    provider=provider,
                    target_count=target_count,
                    generation_mode=gen_mode,
                )
                st.success(f"Dataset generated: {output_path}")
            except Exception as e:
                st.error(f"Regeneration failed: {e}")
else:
    st.info("Apply a prompt evolution first (Phase 2) before regenerating data.")

st.markdown("---")

# ========================================================================
# PHASE 4: Re-Fine-Tuning Instructions
# ========================================================================
st.markdown("### Phase 4: Re-Fine-Tuning")
st.markdown("Upload the new dataset and re-fine-tune the model.")

if evolutions:
    latest_evo = evolutions[-1]
    try:
        _evo_num_p4 = latest_evo.new_prompt_version.split("_")[-1]
    except (AttributeError, IndexError):
        _evo_num_p4 = "1"
    dataset_name_v1 = f"student_advisor_dataset_v1_evolved_{_evo_num_p4}.jsonl"
    dataset_name_v2 = f"student_advisor_dataset_v2_evolved_{_evo_num_p4}.jsonl"

    st.markdown(f"**v1 (Text) Dataset:** `datasets/{dataset_name_v1}`")
    st.markdown(f"**v2 (JSON) Dataset:** `datasets/{dataset_name_v2}`")
    st.markdown("**Instructions:**")
    st.markdown(f"""
1. Run the dataset verification and upload script to push the dataset to HuggingFace
2. Open the Colab notebook `notebooks/gemma_3_4b_student_advisor_v2.ipynb`
3. Change the `my_dataset` variable to point to the new HuggingFace dataset
4. Run all cells (same LoRA fine-tuning pipeline)
5. Download the GGUF model and register with Ollama:
   ```
   ollama create student-advisor:{latest_evo.new_prompt_version} -f Modelfile
   ```
6. Update `.env` to point to the new model tag
""")
else:
    st.info("No evolutions applied yet.")

st.markdown("---")

# ========================================================================
# Evolution History
# ========================================================================
st.markdown("### Evolution History")

if evolutions:
    for evo in reversed(evolutions):
        with st.expander(f"{evo.parent_prompt_version} -> {evo.new_prompt_version} ({evo.timestamp[:10]})"):
            st.write(f"**Change Summary:** {evo.change_summary}")
            st.write(f"**Report ID:** {evo.pattern_report_id}")

            col_p1, col_p2 = st.columns(2)
            with col_p1:
                st.markdown("**Original Prompt:**")
                st.code(evo.original_prompt[:600], language="text")
            with col_p2:
                st.markdown("**Evolved Prompt:**")
                st.code(evo.evolved_prompt[:600], language="text")
else:
    st.info("No evolutions have been applied yet.")

st.markdown("---")
st.caption("Self-Evolution Dashboard | Feedback-Driven Prompt Optimization")
