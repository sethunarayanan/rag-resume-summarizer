 
from os import getenv
from motor.motor_asyncio import AsyncIOMotorClient
from chromadb import Client, HttpClient, AdminClient
from chromadb.config import Settings

# Mongo db
MONGO_AUTH_URI=f"mongodb://{getenv('MONGO_INITDB_ROOT_USERNAME')}:{getenv('MONGO_INITDB_ROOT_PASSWORD')}@mongo:{getenv('MONGO_PORT')}?authSource=admin"
mongo_client = AsyncIOMotorClient(MONGO_AUTH_URI)
mongo_db = mongo_client[getenv("MONGO_INITDB_DATABASE")]

# Chroma db
chroma_admin_client = AdminClient(
    settings=Settings(
        chroma_api_impl="chromadb.api.fastapi.FastAPI",
        chroma_server_host="chroma",
        chroma_server_http_port=8001
    )
)

if not chroma_admin_client.get_tenant(name="default_tenant"):
    chroma_admin_client.create_tenant("default_tenant")
    print("Tenant 'default_tenant' created successfully.")

chroma_client = Client(
    settings=Settings(
        chroma_api_impl="chromadb.api.fastapi.FastAPI",
        chroma_server_host="chroma",
        chroma_server_http_port=8001
    )
)