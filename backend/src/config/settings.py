import os
DATABASE_URL=os.getenv("DATABASE_URL","postgresql+psycopg://rater:rater-demo@db/rater")
REDIS_URL=os.getenv("REDIS_URL","redis://redis:6379/0")
JWT_SECRET=os.getenv("JWT_SECRET","rater-concordance-development-secret-change")
SEED_DEMO=os.getenv("SEED_DEMO","true").lower()=="true"
