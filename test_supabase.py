from app.dependencies.database import db_client

def test():
    print(dir(db_client.table("resumes").select))
test()
