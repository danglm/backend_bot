from app.db.base import Base
from app.db.session import engine
from app.models.business import CompanyCustomers, CompanyBusinesses

def sync():
    print("Syncing new tables...")
    Base.metadata.create_all(bind=engine)
    print("Done")

if __name__ == "__main__":
    sync()
