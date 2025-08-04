from clerk_backend_api import Clerk
import os

clerk = Clerk(bearer_auth=os.getenv("CLERK_API_KEY"))


