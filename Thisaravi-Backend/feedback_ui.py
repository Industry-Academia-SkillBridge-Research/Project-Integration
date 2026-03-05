import streamlit as st
import json
from feedback.storage import (
    load_unreviewed_outputs,
    load_all_feedback,
    save_feedback,
    get_current_prompt_version,
)
from feedback.schemas import FeedbackEntry, FeedbackRatings
from parsers import parse_response

# Page Config
st.set_page_config(
    page_title="Expert Feedback Portal",
    page_icon="clipboard",
    layout="wide",
)

st.markdown("## Expert Feedback Portal")
st.markdown("Review model outputs and provide structured ratings + comments.")
st.markdown("---")

# --- Sidebar: Status ---
with st.sidebar:
    st.header("Status")
    all_feedback = load_all_feedback()
    st.metric("Total Reviews", len(all_feedback))

    if all_feedback:
        avg_overall = sum(
            f.ratings.overall_quality for f in all_feedback
        ) / len(all_feedback)
        st.metric("Avg Overall", f"{avg_overall:.1f}/5")

    st.metric("Prompt Version", get_current_prompt_version())
    st.markdown("---")
    reviewer_id = st.text_input("Your Reviewer ID", value="expert_01")

# --- Load Unreviewed Outputs ---
unreviewed = load_unreviewed_outputs()

if not unreviewed:
    st.info("No unreviewed model outputs available. Generate some outputs first via the main UI.")
    st.stop()

# Build display labels for the dropdown
output_labels = []
for i, out in enumerate(unreviewed):
    inp = out.get("model_input", {})
    student = inp.get("student_data", {})
    job = inp.get("job_data", {})
    demo = student.get("demographics", "Unknown")
    role = job.get("target_job_role", "Unknown")
    output_labels.append(f"#{i+1}: {demo} -> {role}")

selected_idx = st.selectbox(
    "Select Output to Review",
    range(len(output_labels)),
    format_func=lambda i: output_labels[i],
)

selected_output = unreviewed[selected_idx]

# --- Display Input ---
st.markdown("### Original Input")
col_s, col_j = st.columns(2)

inp = selected_output.get("model_input", {})
student_data = inp.get("student_data", {})
job_data = inp.get("job_data", {})

with col_s:
    st.markdown("**Student Profile**")
    st.write(f"**Demographics:** {student_data.get('demographics', 'N/A')}")
    st.write(f"**Major:** {student_data.get('major', 'N/A')}")
    st.write(f"**Interests:** {', '.join(student_data.get('interests', []))}")
    st.write(f"**Skills:** {', '.join(student_data.get('current_skills', []))}")
    st.write(f"**Personality:** {student_data.get('personality', 'N/A')}")

with col_j:
    st.markdown("**Target Job**")
    st.write(f"**Role:** {job_data.get('target_job_role', 'N/A')}")
    st.write(f"**Required Skills:** {', '.join(job_data.get('required_skills', []))}")
    st.write(f"**Description:** {job_data.get('description', 'N/A')}")

# --- Display Model Output (Parsed) ---
st.markdown("### Model Output")
raw_output = selected_output.get("model_output", "")

# Try to parse and display structured
parsed = parse_response(raw_output)
if "error" not in parsed:
    gap = parsed.get("gap_analysis", {})
    proj = parsed.get("project_recommendation", {})

    c1, c2 = st.columns([1, 2])
    with c1:
        match = gap.get("match_percentage", 0)
        st.metric("Match Score", f"{match}%")
    with c2:
        st.info(gap.get("analysis_summary", "N/A"))

    missing = gap.get("missing_skills", [])
    if missing:
        st.write(f"**Missing Skills:** {', '.join(missing)}")

    st.markdown(f"**Project:** {proj.get('project_title', 'N/A')}")
    st.write(f"*{proj.get('objective', '')}*")
    st.write(f"**Tech Stack:** {', '.join(proj.get('tech_stack', []))}")

    steps = proj.get("implementation_steps", [])
    for i, step in enumerate(steps):
        st.markdown(f"{i+1}. {step}")
else:
    st.code(raw_output[:2000], language="text")

# --- Rating Form ---
st.markdown("---")
st.markdown("### Your Ratings (1-5)")

col_r1, col_r2 = st.columns(2)

with col_r1:
    skill_gap = st.slider("Skill Gap Accuracy", 1, 5, 3, key="r_skill")
    project_rel = st.slider("Project Relevance", 1, 5, 3, key="r_proj")
    overall = st.slider("Overall Quality", 1, 5, 3, key="r_overall")

with col_r2:
    tech_stack = st.slider("Tech Stack Appropriateness", 1, 5, 3, key="r_tech")
    impl_steps = st.slider("Implementation Step Quality", 1, 5, 3, key="r_impl")

st.markdown("### Comments")
comments = st.text_area(
    "Explain your reasoning (what could be improved?)",
    height=150,
    key="comments",
)

# --- Submit ---
if st.button("Submit Feedback", type="primary", use_container_width=True):
    if not comments.strip():
        st.warning("Please provide comments explaining your ratings.")
    else:
        entry = FeedbackEntry(
            model_input=inp,
            model_output=raw_output,
            model_provider=selected_output.get("model_provider", "unknown"),
            ratings=FeedbackRatings(
                skill_gap_accuracy=skill_gap,
                project_relevance=project_rel,
                tech_stack_appropriateness=tech_stack,
                implementation_step_quality=impl_steps,
                overall_quality=overall,
            ),
            free_text_comments=comments,
            reviewer_id=reviewer_id,
            prompt_version=selected_output.get("prompt_version", get_current_prompt_version()),
        )
        save_feedback(entry)
        st.success(f"Feedback submitted! (ID: {entry.feedback_id})")
        st.rerun()

st.markdown("---")
st.caption("Expert Feedback Portal | Self-Evolution System")
