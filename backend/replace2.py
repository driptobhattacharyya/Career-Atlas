
with open('backend/app/resume_extraction/router.py', 'r') as f:
    content = f.read()

# We need to change the call to fetch_full_resume
old_call = 'return {"success": True, "resume": fetch_full_resume(resume_id)}'
new_call = 'return {"success": True, "resume": await fetch_full_resume(resume_id)}'

content = content.replace(old_call, new_call)

with open('backend/app/resume_extraction/router.py', 'w') as f:
    f.write(content)
print("Replace 2 done")
