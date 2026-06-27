import re

with open("backend/app/resume_extraction/router.py", "r") as f:
    content = f.read()

old_func = """def fetch_full_resume(resume_id: str) -> dict[str, Any]:
    resume = db_client.table("resumes").select("*").eq("id", resume_id).execute().data[0]

    contact_rows = db_client.table("contacts").select("*").eq("resume_id", resume_id).execute().data
    contact = contact_rows[0] if contact_rows else {}

    skills = [x["skill"] for x in db_client.table("skills").select("*").eq("resume_id", resume_id).execute().data]
    prog_langs = [x["language"] for x in db_client.table("programming_languages").select("*").eq("resume_id", resume_id).execute().data]
    spoken_langs = [x["language"] for x in db_client.table("spoken_languages").select("*").eq("resume_id", resume_id).execute().data]
    keywords = [x["keyword"] for x in db_client.table("keywords").select("*").eq("resume_id", resume_id).execute().data]

    experiences: list[dict[str, Any]] = []
    exp_rows = db_client.table("experiences").select("*").eq("resume_id", resume_id).execute().data
    for exp in exp_rows:
        exp_id = exp["id"]
        bullets = [x["bullet"] for x in db_client.table("experience_bullets").select("*").eq("experience_id", exp_id).execute().data]
        techs = [x["tech"] for x in db_client.table("experience_technologies").select("*").eq("experience_id", exp_id).execute().data]
        exp["description_bullets"] = bullets
        exp["technologies"] = techs
        experiences.append(exp)

    education: list[dict[str, Any]] = []
    edu_rows = db_client.table("education").select("*").eq("resume_id", resume_id).execute().data
    for edu in edu_rows:
        edu_id = edu["id"]
        notes = [x["note"] for x in db_client.table("education_notes").select("*").eq("education_id", edu_id).execute().data]
        edu["notes"] = notes
        education.append(edu)

    projects: list[dict[str, Any]] = []
    proj_rows = db_client.table("projects").select("*").eq("resume_id", resume_id).execute().data
    for proj in proj_rows:
        proj_id = proj["id"]
        techs = [x["tech"] for x in db_client.table("project_technologies").select("*").eq("project_id", proj_id).execute().data]
        proj["technologies"] = techs
        projects.append(proj)

    try:
        certifications = db_client.table("certifications").select("*").eq("resume_id", resume_id).execute().data
    except Exception:
        certifications = []

    return {
        "resume_id": resume_id,
        "full_name": resume.get("full_name"),
        "headline": resume.get("headline"),
        "summary": resume.get("summary"),
        "contact": contact,
        "skills": skills,
        "programming_languages": prog_langs,
        "spoken_languages": spoken_langs,
        "experience": experiences,
        "education": education,
        "projects": projects,
        "certifications": certifications,
        "keywords": keywords,
    }"""

new_func = """async def fetch_full_resume(resume_id: str) -> dict[str, Any]:
    async def get_table_data(table_name: str) -> list[dict[str, Any]]:
        try:
            return await asyncio.to_thread(
                lambda: db_client.table(table_name).select("*").eq("resume_id", resume_id).execute().data
            )
        except Exception:
            return []

    async def get_resume_table() -> list[dict[str, Any]]:
        try:
            return await asyncio.to_thread(
                lambda: db_client.table("resumes").select("*").eq("id", resume_id).execute().data
            )
        except Exception:
            return []

    results = await asyncio.gather(
        get_resume_table(),
        get_table_data("contacts"),
        get_table_data("skills"),
        get_table_data("programming_languages"),
        get_table_data("spoken_languages"),
        get_table_data("keywords"),
        get_table_data("experiences"),
        get_table_data("education"),
        get_table_data("projects"),
        get_table_data("certifications"),
    )

    resume_data = results[0]
    resume = resume_data[0] if resume_data else {}
    contact_rows = results[1]
    contact = contact_rows[0] if contact_rows else {}
    skills = [x["skill"] for x in results[2]]
    prog_langs = [x["language"] for x in results[3]]
    spoken_langs = [x["language"] for x in results[4]]
    keywords = [x["keyword"] for x in results[5]]

    exp_rows = results[6]
    edu_rows = results[7]
    proj_rows = results[8]
    certifications = results[9]

    exp_ids = [e["id"] for e in exp_rows if "id" in e]
    edu_ids = [e["id"] for e in edu_rows if "id" in e]
    proj_ids = [p["id"] for p in proj_rows if "id" in p]

    async def get_child_data(table_name: str, col_name: str, ids: list[str]) -> list[dict[str, Any]]:
        if not ids:
            return []
        try:
            return await asyncio.to_thread(
                lambda: db_client.table(table_name).select("*").in_(col_name, ids).execute().data
            )
        except Exception:
            return []

    child_results = await asyncio.gather(
        get_child_data("experience_bullets", "experience_id", exp_ids),
        get_child_data("experience_technologies", "experience_id", exp_ids),
        get_child_data("education_notes", "education_id", edu_ids),
        get_child_data("project_technologies", "project_id", proj_ids),
    )

    all_exp_bullets, all_exp_techs, all_edu_notes, all_proj_techs = child_results

    exp_bullets_map = defaultdict(list)
    for b in all_exp_bullets:
        exp_bullets_map[b["experience_id"]].append(b["bullet"])

    exp_techs_map = defaultdict(list)
    for t in all_exp_techs:
        exp_techs_map[t["experience_id"]].append(t["tech"])

    edu_notes_map = defaultdict(list)
    for n in all_edu_notes:
        edu_notes_map[n["education_id"]].append(n["note"])

    proj_techs_map = defaultdict(list)
    for t in all_proj_techs:
        proj_techs_map[t["project_id"]].append(t["tech"])

    experiences = []
    for exp in exp_rows:
        exp["description_bullets"] = exp_bullets_map[exp.get("id")]
        exp["technologies"] = exp_techs_map[exp.get("id")]
        experiences.append(exp)

    education = []
    for edu in edu_rows:
        edu["notes"] = edu_notes_map[edu.get("id")]
        education.append(edu)

    projects = []
    for proj in proj_rows:
        proj["technologies"] = proj_techs_map[proj.get("id")]
        projects.append(proj)

    return {
        "resume_id": resume_id,
        "full_name": resume.get("full_name"),
        "headline": resume.get("headline"),
        "summary": resume.get("summary"),
        "contact": contact,
        "skills": skills,
        "programming_languages": prog_langs,
        "spoken_languages": spoken_langs,
        "experience": experiences,
        "education": education,
        "projects": projects,
        "certifications": certifications,
        "keywords": keywords,
    }"""

if old_func in content:
    with open("backend/app/resume_extraction/router.py", "w") as f:
        f.write(content.replace(old_func, new_func))
    print("Replaced successfully")
else:
    print("Old func not found")
