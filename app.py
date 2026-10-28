import sys

import json

import html

import traceback

from pathlib import Path

from database.db import init_db, save_analysis,get_recent_analyses,get_analysis

import gradio as gr
# =========================================================# 1. CONFIGURATION# =========================================================
BASE_DIR = Path(__file__).resolve().parent

if str(BASE_DIR) not in sys.path:

    sys.path.insert(0, str(BASE_DIR))



from agent.career_agent import run_career_analysis



try:

    from agent.chat_agent import start_chat

    from agent.chat_agent import chat as chat_agent

except (ImportError, AttributeError):

    start_chat = None

    chat_agent = None



try:

    from tool.job_search import search_jobs

except (ImportError, AttributeError):

    search_jobs = None
# =========================================================# 2. HELPERS# =========================================================
def to_list(value):

    if value is None:

        return []

    if isinstance(value, str):

        return [item.strip() for item in value.split(",") if item.strip()]

    if isinstance(value, (list, tuple, set)):

        return [str(item).strip() for item in value if item is not None and str(item).strip()]

    return [str(value)]





def safe_percentage(value):

    try:

        return max(0.0, min(100.0, float(value)))

    except (TypeError, ValueError):

        return 0.0





def esc(value):

    return html.escape(str(value if value is not None else ""))





def normalize_result(data):

    if isinstance(data, str):

        data = json.loads(data)

    if not isinstance(data, dict):

        raise ValueError("Unexpected response from career_agent.")



    data["matched_skills"] = to_list(data.get("matched_skills", data.get("matched", [])))

    data["missing_skills"] = to_list(

        data.get("missing_skills", data.get("skill_gaps", data.get("missing", [])))

    )

    data["required_skills"] = to_list(data.get("required_skills", data.get("required", [])))

    data["match_percentage"] = safe_percentage(data.get("match_percentage", 0))

    data.setdefault("job_title", "Career Analysis")

    data.setdefault("roadmap", {})

    data.setdefault("jobs", [])

    if not isinstance(data["jobs"], list):

        data["jobs"] = []

    return data
# =========================================================# 3. HTML RENDERERS# =========================================================
def render_skill_panel(title, skills, empty_message, css_class):

    skills = to_list(skills)

    chips = "".join(

        f'<span class="skill-chip {css_class}">{esc(skill)}</span>'

        for skill in skills

    )

    if not skills:

        chips = f'<div class="empty-state">{esc(empty_message)}</div>'



    return f"""

    <section class="panel">

      <div class="panel-heading">

        <div>

          <div class="eyebrow">SKILL INTELLIGENCE</div>

          <h3>{esc(title)}</h3>

        </div>

        <span class="count-pill">{len(skills)}</span>

      </div>

      <div class="skill-chip-list">{chips}</div>

    </section>

    """





def render_match_card(score, title, matched, missing, required):

    radius = 45

    circumference = 2 * 3.141592653589793 * radius

    progress = circumference * score / 100



    if score >= 70:

        status = "Strong match"

        description = "Your skills align well with this role."

    elif score >= 40:

        status = "Good starting point"

        description = "Focus on your skill gaps to improve your fit."

    else:

        status = "Growth opportunity"

        description = "Build the essential skills for this position."



    return f"""

    <section class="match-card">

      <div class="match-header">

        <div>

          <div class="eyebrow">CAREER INTELLIGENCE</div>

          <h2>{esc(title)}</h2>

          <p class="muted">Your profile compared with the job requirements.</p>

        </div>

        <span class="status-pill"><span class="status-dot"></span> Analysis complete</span>

      </div>

      <div class="match-content">

        <div class="score-ring">

          <svg viewBox="0 0 110 110" role="img" aria-label="Match score {score:.0f}%">

            <circle cx="55" cy="55" r="{radius}" class="ring-track"/>

            <circle cx="55" cy="55" r="{radius}" class="ring-progress"

              stroke-dasharray="{progress:.2f} {circumference-progress:.2f}"

              transform="rotate(-90 55 55)"/>

          </svg>

          <div class="score-label"><strong>{score:.0f}%</strong><span>MATCH SCORE</span></div>

        </div>

        <div class="score-description">

          <div class="eyebrow">YOUR CAREER SNAPSHOT</div>

          <h3>{status}</h3>

          <p class="muted">{description}</p>

          <div class="mini-stats">

            <div class="mini-stat"><span class="mini-dot green"></span><span>Matched</span><strong>{len(matched)}</strong></div>

            <div class="mini-stat"><span class="mini-dot coral"></span><span>Skill gaps</span><strong>{len(missing)}</strong></div>

            <div class="mini-stat"><span class="mini-dot purple"></span><span>Required</span><strong>{len(required)}</strong></div>

          </div>

        </div>

      </div>

    </section>

    """





def render_skill_map(required, matched, missing):

    if not required:

        required = list(dict.fromkeys(matched + missing))

    if not required:

        return """

        <section class="panel"><h3>Skill Gap Map</h3>

        <div class="empty-state">Run an analysis to see your skill map.</div></section>

        """



    matched_set = {skill.lower() for skill in matched}

    missing_set = {skill.lower() for skill in missing}

    rows = []



    for skill in required:

        key = skill.lower()

        if key in matched_set:

            status, color, width = "Matched", "bar-green", 100

        elif key in missing_set:

            status, color, width = "To learn", "bar-coral", 28

        else:

            status, color, width = "Unclassified", "bar-purple", 55



        rows.append(f"""

        <div class="skill-map-row">

          <div class="skill-map-label"><span>{esc(skill)}</span><span class="map-status">{status}</span></div>

          <div class="bar-track"><div class="bar-fill {color}" style="width:{width}%"></div></div>

        </div>

        """)



    return f"""

    <section class="panel">

      <div class="panel-heading">

        <div><div class="eyebrow">YOUR PROFILE</div><h3>Skill Gap Map</h3></div>

        <span class="count-pill">{len(required)} skills</span>

      </div>

      {''.join(rows)}

      <p class="muted footnote">Bars represent skill status, not measured proficiency.</p>

    </section>

    """





def render_roadmap(roadmap):

    if isinstance(roadmap, str):

        try:

            roadmap = json.loads(roadmap)

        except json.JSONDecodeError:

            return f'<section class="panel">{esc(roadmap)}</section>'



    if not isinstance(roadmap, dict):

        roadmap = {}



    steps = roadmap.get("learning_steps", [])

    projects = roadmap.get("projects", [])

    duration = roadmap.get("estimated_duration", "Flexible")

    if not isinstance(steps, list):

        steps = []

    if not isinstance(projects, list):

        projects = []



    step_html = []

    for index, step in enumerate(steps, start=1):

        if isinstance(step, dict):

            title = step.get("title", f"Learning step {index}")

            description = step.get("description", "")

            step_duration = step.get("duration", "")

            resources = to_list(step.get("resources", []))

        else:

            title, description, step_duration, resources = f"Learning step {index}", str(step), "", []



        resources_html = "".join(f"<li>{esc(resource)}</li>" for resource in resources)

        duration_html = f'<span class="duration-pill">{esc(step_duration)}</span>' if step_duration else ""

        resources_block = f'<ul class="resource-list">{resources_html}</ul>' if resources_html else ""

        step_html.append(f"""

        <div class="roadmap-step">

          <div class="step-number">{index:02d}</div>

          <div class="step-content"><h4>{esc(title)}</h4><p>{esc(description)}</p>

          {duration_html}{resources_block}</div>

        </div>

        """)



    project_html = []

    for project in projects:

        if isinstance(project, dict):

            name = project.get("name", project.get("project", "Project"))

            description = project.get("description", "")

            acquired = to_list(project.get("skills_acquired", []))

        else:

            name, description, acquired = str(project), "", []

        tags = "".join(f'<span class="project-tag">{esc(skill)}</span>' for skill in acquired)

        project_html.append(f"""

        <div class="project-card"><h4>{esc(name)}</h4><p>{esc(description)}</p><div>{tags}</div></div>

        """)



    steps_content = "".join(step_html) or '<div class="empty-state">No learning steps available.</div>'

    projects_content = "".join(project_html) or '<div class="empty-state">No projects suggested.</div>'



    return f"""

    <section class="panel">

      <div class="panel-heading">

        <div><div class="eyebrow">PERSONAL DEVELOPMENT</div><h3>Your Learning Roadmap</h3></div>

        <span class="duration-pill">{esc(duration)}</span>

      </div>

      <div class="roadmap-list">{steps_content}</div>

    </section>

    <section class="panel">

      <div class="eyebrow">PRACTICAL EXPERIENCE</div><h3>Recommended Projects</h3>

      <div class="project-grid">{projects_content}</div>

    </section>

    """





def render_jobs(jobs):

    """Render real listings returned by tool/job_search.py."""

    if not isinstance(jobs, list) or not jobs:

        return """

        <section class="panel">

          <div class="eyebrow">CAREER OPPORTUNITIES</div><h3>Recommended Jobs</h3>

          <div class="empty-state">No job listings found. Try another job title or search again later.</div>

        </section>

        """



    cards = []

    for job in jobs:

        if not isinstance(job, dict):

            continue

        title = esc(job.get("title", "Unknown title"))

        company = esc(job.get("company", "Unknown company"))

        location = esc(job.get("location", "Not specified"))

        url = str(job.get("url", "") or "").strip()



        if url.startswith(("https://", "http://")):

            link_html = f'<a href="{esc(url)}" target="_blank" rel="noopener noreferrer">View job ↗</a>'

        else:

            link_html = '<span class="muted">Application link unavailable</span>'



        description = html.escape(str(job.get("description", "") or "").strip())

        if len(description) > 450:

            description = description[:450] + "…"

        description_html = f'<p class="job-description">{description}</p>' if description else ""



        cards.append(f"""

        <article class="project-card job-card">

          <div class="eyebrow">OPEN POSITION</div>

          <h4>{title}</h4>

          <p><strong>Company:</strong> {company}</p>

          <p><strong>Location:</strong> {location}</p>

          {description_html}

          <div class="job-link">{link_html}</div>

        </article>

        """)



    if not cards:

        return '<section class="panel"><h3>Recommended Jobs</h3><div class="empty-state">No valid job listings returned.</div></section>'



    return f"""

    <section class="panel">

      <div class="eyebrow">CAREER OPPORTUNITIES</div>

      <h3>Recommended Jobs</h3>

      <p class="muted">Listings are fetched from Remotive. Check each listing for eligibility and details.</p>

      <div class="project-grid">{''.join(cards)}</div>

    </section>

    """
# =========================================================# 4. CAREER ANALYSIS CALLBACK# =========================================================
def analyze_job(description, skills_text, goal):

    empty = """

    <section class="panel"><h3>Analysis unavailable</h3>

    <p class="muted">Please check your input and try again.</p></section>

    """



    if not description or not description.strip():

        return empty, empty, empty, '{"error": "Job description is required."}', "Enter a job description."

    if not skills_text or not skills_text.strip():

        return empty, empty, empty, '{"error": "Current skills are required."}', "Enter your current skills."



    skills = [

        item.strip()

        for item in skills_text.replace("\n", ",").split(",")

        if item.strip()

    ]



    try:

        raw_result = run_career_analysis(

            description.strip(),

            skills,

            (goal or "").strip()

        )

        result = normalize_result(raw_result)

        from agent.skill_analyzer import analyze_skills



        required = result.get("required_skills", [])

        if not isinstance(required, list):

            required = []



        matched_result = analyze_skills(required, skills)



        result["matched_skills"] = matched_result["matched_skills"]

        result["missing_skills"] = matched_result["missing_skills"]

        result["match_percentage"] = matched_result["match_percentage"]
# Search jobs independently so a Remotive/network error doesn't break AI analysis.
        job_keyword = str(result.get("job_title") or goal or "").strip()

        if not job_keyword:

            job_keyword = (goal or "").strip()



        jobs = []

        if search_jobs is not None and job_keyword:

            try:

                jobs = search_jobs(job_keyword, limit=5) or []

            except Exception:

                traceback.print_exc()

                jobs = []

        result["jobs"] = jobs

        analysis_id = save_analysis(

        description=description.strip(),

        user_skills=skills,

        goal=(goal or "").strip(),

        result=result,

        )



        print(f"Analysis saved successfully. ID: {analysis_id}")



        matched = result["matched_skills"]

        missing = result["missing_skills"]

        required = result["required_skills"]

        score = result["match_percentage"]



        overview = render_match_card(

            score, result.get("job_title", "Career Analysis"),

            matched, missing, required

        )

        overview += render_jobs(jobs)



        skill_details = f"""

        <div class="detail-grid">

          {render_skill_panel("Matched Skills", matched, "No matching skills reported.", "chip-green")}

          {render_skill_panel("Skill Gaps", missing, "No missing skills reported.", "chip-coral")}

        </div>

        {render_skill_map(required, matched, missing)}

        """



        roadmap_html = render_roadmap(result.get("roadmap"))

        return (

            overview,

            skill_details,

            roadmap_html,

            json.dumps(result, indent=2, ensure_ascii=False),

            f"Analysis complete · {score:.1f}% match · {len(jobs)} job listings"

        )



    except Exception as exc:

        traceback.print_exc()

        tb = esc(traceback.format_exc())

        error_html = f"""

        <section class="panel error-panel">

          <div class="eyebrow">ANALYSIS ERROR</div><h3>Unable to complete the analysis</h3>

          <p>{esc(exc)}</p><pre style="font-size:11px;white-space:pre-wrap">{tb}</pre>

        </section>

        """

        return (

            error_html,

            error_html,

            error_html,

            json.dumps({"error": str(exc)}, ensure_ascii=False, indent=2),

            "Analysis failed. Check the terminal."

        )
# =========================================================# 5. CHAT CALLBACK# =========================================================
def send_chat(message, history, session_id):

    history = list(history or [])



    if not message or not message.strip():

        return "", history, session_id



    if chat_agent is None or start_chat is None:

        history.append({

            "role": "assistant",

            "content": "The chat agent is not configured correctly."

        })

        return "", history, session_id



    try:
# Create a new database session if this is the first message.
        if session_id is None:

            session_id = start_chat()



        response = chat_agent(message.strip(), session_id)



        if isinstance(response, dict):

            response = response.get(

                "response",

                response.get("answer", response.get("message", str(response)))

            )



        response = str(response or "No response received.")



        history.append({

            "role": "user",

            "content": message.strip()

        })

        history.append({

            "role": "assistant",

            "content": response

        })



    except Exception as exc:

        traceback.print_exc()

        history.append({

            "role": "assistant",

            "content": f"Chat error: {exc}"

        })



    return "", history, session_id





def clear_chat():
# Start a new session; old messages remain saved in the database.
    if start_chat is not None:

        try:

            session_id = start_chat()

            return [], session_id

        except Exception:

            traceback.print_exc()



    return [], None
# =========================================================# 6. NAVIGATION# =========================================================
def navigate(page):
    names = ["dashboard", "analysis", "roadmap", "results", "history", "chat"]
    return tuple(gr.update(visible=(page == name)) for name in names)
# =========================================================# 7. CSS# =========================================================
CSS = """

@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Playfair+Display:wght@600;700&display=swap');

:root { --bg:#0b1019; --surface:#121a27; --surface2:#172130; --border:#293443; --text:#f0f1ed; --muted:#97a3b4; --coral:#ff856c; --green:#65d6a1; --purple:#b7a0ff; }

.gradio-container { max-width:1600px !important; background:var(--bg) !important; color:var(--text) !important; font-family:'DM Sans',sans-serif !important; }

body,.main,.wrap { background:var(--bg) !important; }

footer { display:none !important; }

\#hero { background:linear-gradient(110deg,#151e2d,#111725 70%,#251c29); border:1px solid var(--border); border-radius:20px; padding:27px 30px; margin-bottom:17px; }

.brand { color:var(--coral); font-size:11px; font-weight:700; letter-spacing:3px; }

\#hero h1 { font-family:'Playfair Display',serif; font-size:clamp(27px,4vw,42px); margin:11px 0 8px; color:#fff; }

\#hero p,.muted { color:var(--muted) !important; }

.panel,.match-card { background:var(--surface); border:1px solid var(--border); border-radius:16px; padding:22px; margin:12px 0; color:var(--text); }

.panel h3,.match-card h2 { color:var(--text); margin:5px 0 12px; }

.eyebrow { color:var(--coral); font-size:10px; font-weight:700; letter-spacing:2px; margin-bottom:8px; }

.panel-heading,.match-header { display:flex; align-items:center; justify-content:space-between; gap:16px; margin-bottom:18px; }

.count-pill,.duration-pill,.status-pill { display:inline-block; border:1px solid var(--border); border-radius:999px; padding:6px 11px; color:var(--muted); font-size:12px; }

.status-pill { color:var(--green); }

.status-dot { display:inline-block; width:7px; height:7px; background:var(--green); border-radius:50%; margin-right:6px; }

.match-content { display:flex; align-items:center; gap:28px; flex-wrap:wrap; }

.score-ring { width:110px; height:110px; position:relative; flex-shrink:0; }

.score-ring svg { width:110px; height:110px; }

.ring-track,.ring-progress { fill:none; stroke-width:9; }

.ring-track { stroke:#293443; }

.ring-progress { stroke:var(--coral); stroke-linecap:round; }

.score-label { position:absolute; inset:0; display:flex; flex-direction:column; align-items:center; justify-content:center; }

.score-label strong { font-size:25px; color:#fff; }

.score-label span { font-size:8px; color:var(--muted); letter-spacing:1px; }

.score-description { flex:1; min-width:220px; }

.mini-stats { display:flex; gap:18px; flex-wrap:wrap; margin-top:18px; }

.mini-stat { display:flex; align-items:center; gap:7px; font-size:12px; color:var(--muted); }

.mini-stat strong { color:var(--text); }

.mini-dot { width:8px; height:8px; border-radius:50%; display:inline-block; }

.green { background:var(--green); } .coral { background:var(--coral); } .purple { background:var(--purple); }

.detail-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(260px,1fr)); gap:12px; }

.skill-chip-list { display:flex; flex-wrap:wrap; gap:8px; }

.skill-chip { display:inline-block; padding:7px 11px; border-radius:999px; font-size:12px; border:1px solid var(--border); }

.chip-green { color:var(--green); background:#173027; } .chip-coral { color:var(--coral); background:#34221f; }

.skill-map-row { margin:16px 0; }

.skill-map-label { display:flex; justify-content:space-between; gap:12px; font-size:13px; margin-bottom:7px; }

.map-status,.footnote { color:var(--muted); font-size:11px; }

.bar-track { height:7px; border-radius:99px; overflow:hidden; background:#253040; }

.bar-fill { height:100%; border-radius:99px; }

.bar-green { background:var(--green); } .bar-coral { background:var(--coral); } .bar-purple { background:var(--purple); }

.roadmap-list { display:flex; flex-direction:column; gap:14px; }

.roadmap-step { display:flex; gap:14px; padding:14px; background:var(--surface2); border:1px solid var(--border); border-radius:12px; }

.step-number { color:var(--coral); font-weight:700; font-size:18px; }

.step-content { flex:1; } .step-content h4,.project-card h4 { margin:0 0 8px; color:var(--text); } .step-content p,.project-card p { color:var(--muted); font-size:13px; line-height:1.6; }

.resource-list { color:var(--muted); font-size:12px; }

.project-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(240px,1fr)); gap:12px; margin-top:14px; }

.project-card { background:var(--surface2); border:1px solid var(--border); border-radius:12px; padding:16px; min-width:0; }

.project-tag { display:inline-block; color:var(--purple); background:#29243e; padding:4px 8px; border-radius:99px; font-size:10px; margin:4px 4px 0 0; }

.job-description { max-height:150px; overflow:auto; }

.job-link a { color:var(--green) !important; font-weight:700; text-decoration:none; }

.empty-state { border:1px dashed var(--border); border-radius:10px; padding:18px; color:var(--muted); font-size:13px; }

.error-panel { border-color:#8b3d3d; }

textarea,input { background:#0e1520 !important; color:var(--text) !important; border-color:var(--border) !important; }

button { border-radius:10px !important; }

"""

def load_analysis_history():

    analyses = get_recent_analyses(limit=50)



    choices = []

    for item in analyses:

        analysis_id = item.get("id")

        goal = item.get("goal") or "Career analysis"

        choices.append((f"#{analysis_id} - {goal}", str(analysis_id)))



    return gr.update(choices=choices, value=None), None





def show_selected_analysis(analysis_id):

    if not analysis_id:

        return None



    try:

        return get_analysis(int(analysis_id))

    except (TypeError, ValueError):

        return None
# =========================================================# 8. GRADIO APP# =========================================================
with gr.Blocks(css=CSS, title="CareerRadar AI") as demo:

    chat_session_id = gr.State(value=None)

    gr.HTML("""

    <div id="hero">

      <div class="brand">CAREERRADAR AI</div>

      <h1>Navigate your next career move.</h1>

      <p>Analyze your skills, uncover gaps, build a learning roadmap, and explore relevant remote opportunities.</p>

    </div>

    """)



    with gr.Row():

        with gr.Column(scale=1, min_width=180):

            gr.Markdown("### Navigation")

            nav_dashboard = gr.Button("Overview")

            nav_analysis = gr.Button("Skill Analysis")

            nav_roadmap = gr.Button("Learning Roadmap")

            nav_results = gr.Button("Raw Results")

            nav_history = gr.Button("Analysis History")

            nav_chat = gr.Button("Career Chat")

            gr.Markdown("---")

            gr.Markdown("**Tip:** Separate your current skills with commas.")



        with gr.Column(scale=5):

            with gr.Column(visible=True) as page_dashboard:

                gr.Markdown("## Career overview")

                analysis_status = gr.Markdown("Enter a job description and your current skills to begin.")

                overview_html = gr.HTML("""

                <section class="panel"><div class="eyebrow">GET STARTED</div><h3>Your career dashboard</h3>

                <p class="muted">Run an analysis to see your match score, recommended jobs, skill gaps, and roadmap.</p></section>

                """)



            with gr.Column(visible=False) as page_analysis:

                gr.Markdown("## Analyze a job")

                job_description = gr.Textbox(

                    label="Job description",

                    placeholder="Paste the job description here...",

                    lines=8

                )

                user_skills = gr.Textbox(

                    label="Your current skills",

                    placeholder="Python, SQL, Git, HTML, CSS",

                    lines=3

                )

                career_goal = gr.Textbox(

                    label="Target role / career goal (optional)",

                    placeholder="e.g. Junior Python Developer"

                )

                analyze_button = gr.Button("Analyze my career fit", variant="primary")



            with gr.Column(visible=False) as page_roadmap:

                gr.Markdown("## Skill gaps and learning roadmap")

                skill_html = gr.HTML("""

                <section class="panel"><h3>Skill analysis</h3><div class="empty-state">Run an analysis first.</div></section>

                """)

                roadmap_html = gr.HTML("""

                <section class="panel"><h3>Learning roadmap</h3><div class="empty-state">Your roadmap will appear here.</div></section>

                """)



            with gr.Column(visible=False) as page_results:

                gr.Markdown("## Full analysis data")

                results_json = gr.Code(label="Analysis JSON", language="json", value='{"status":"Waiting for analysis"}')

            with gr.Column(visible=False) as page_history:

               gr.Markdown("## Analysis History")

               gr.Markdown("View your previously saved career analyses.")



               history_dropdown = gr.Dropdown(

               label="Select a previous analysis",

               choices=[],

               interactive=True,

               allow_custom_value=False

               )



               history_refresh = gr.Button("Refresh history")

               history_details = gr.JSON(label="Saved analysis details")

            with gr.Column(visible=False) as page_chat:

                gr.Markdown("## Career chat")

                chatbot = gr.Chatbot(label="Career Chat", height=400)

                with gr.Row():

                    chat_message = gr.Textbox(label="Message", placeholder="How can I improve my Python developer profile?", scale=5)

                    chat_send = gr.Button("Send", variant="primary")

                chat_clear = gr.Button("Clear conversation")



    page_outputs = [
        page_dashboard,
        page_analysis,
        page_roadmap,
        page_results,
        page_history,
        page_chat,
    ]

    nav_dashboard.click(lambda: navigate("dashboard"), outputs=page_outputs)
    nav_analysis.click(lambda: navigate("analysis"), outputs=page_outputs)
    nav_roadmap.click(lambda: navigate("roadmap"), outputs=page_outputs)
    nav_results.click(lambda: navigate("results"), outputs=page_outputs)
    nav_history_event = nav_history.click(
        lambda: navigate("history"),
        outputs=page_outputs
    )
    nav_history_event.then(
        fn=load_analysis_history,
        outputs=[history_dropdown, history_details]
    )
    nav_chat.click(lambda: navigate("chat"), outputs=page_outputs)

    analyze_button.click(

        fn=analyze_job,

        inputs=[job_description, user_skills, career_goal],

        outputs=[overview_html, skill_html, roadmap_html, results_json, analysis_status],

        show_progress="full"

    )

    analyze_button.click(lambda: navigate("dashboard"), outputs=page_outputs)



    chat_send.click(

      fn=send_chat,

      inputs=[chat_message, chatbot, chat_session_id],

      outputs=[chat_message, chatbot, chat_session_id]

    )



    chat_message.submit(

       fn=send_chat,

      inputs=[chat_message, chatbot, chat_session_id],

      outputs=[chat_message, chatbot, chat_session_id]

    )



    chat_clear.click(

       fn=clear_chat,

      inputs=[],

      outputs=[chatbot, chat_session_id]

    )


    history_refresh.click(
        fn=load_analysis_history,
        outputs=[history_dropdown, history_details]
    )

    history_dropdown.change(
        fn=show_selected_analysis,
        inputs=history_dropdown,
        outputs=history_details
    )

init_db()

if __name__ == "__main__":

    demo.launch(css=CSS)
