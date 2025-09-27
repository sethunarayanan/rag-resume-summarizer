import os
import re
import asyncio
from uuid import uuid4
from pypdf import PdfReader
from starlette.datastructures import UploadFile
from fastapi import status
from concurrent.futures import ProcessPoolExecutor

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.llms import HuggingFacePipeline
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from transformers import pipeline

from app.config.settings import mongo_db, chroma_client
from app.models.models import ResumeMeta, ResumeChunk

LLM_MODEL_NAME = "google/flan-t5-small"
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
CHUNK_SIZE = 350  # smaller chunk size because of local models
MAX_INPUT_LENGTH = 512

embedding_model = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
hf_pipeline = pipeline("text2text-generation", model=LLM_MODEL_NAME)
llm = HuggingFacePipeline(pipeline=hf_pipeline)

chroma_collection_chunk = chroma_client.get_or_create_collection(ResumeChunk.__name__.lower())
mongo_collection_meta = mongo_db[ResumeMeta.__name__.lower()]

prompt = PromptTemplate(
    template="Clean sentence structure and summarize in 5 sentences:\n\n{text}",
    input_variables=["text"]
)
chain = LLMChain(llm=llm, prompt=prompt)

executor = ProcessPoolExecutor(max_workers=4)

async def preprocess_text(text: str) -> str:
    text = re.sub(r'\nPage \d+\n', '\n', text)
    text = re.sub(r'\n\s*\n', '\n', text)
    return text.strip()

async def extract_pdf_text(file):
    pdf_reader = PdfReader(file.file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text() or ""
    prepro_text = await preprocess_text(text)
    return prepro_text

async def add_pdf_to_mongo(file, text):
    resume_doc = ResumeMeta(
        file_name=file.filename,
        content_text=text,
        status="processing"
    )
    res = await mongo_collection_meta.insert_one(resume_doc.model_dump())
    return str(resume_doc.id)

def chunk_text(text: str, chunk_size: int = CHUNK_SIZE):
    return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]

async def embed_and_save_chunks(chunks, resume_id):
    chunk_ids = []
    for chunk in chunks:
        emb = embedding_model.embed_documents([chunk])[0]
        chunk_id = str(uuid4())
        chroma_collection_chunk.add(
            ids=[chunk_id],
            documents=[chunk],
            embeddings=[emb],
            metadatas=[{"resume_id": resume_id, "chunk_id": chunk_id, "chunk_length": len(chunk)}],
        )
        chunk_ids.append(chunk_id)
    await mongo_collection_meta.update_one(
        {"id": resume_id},
        {"$set": {"chroma_ids": chunk_ids}}
    )
    return chunk_ids

def query_vector_db(resume_id, query_text, top_k=3):
    query_filter = {"resume_id": resume_id}
    results = chroma_collection_chunk.query(
        query_texts=[query_text],
        n_results=top_k,
        where=query_filter
    )
    return results.get('documents', [])

async def process_pdf_file(file):
    text = await extract_pdf_text(file)
    resume_id = await add_pdf_to_mongo(file, text)
    chunks = chunk_text(text, CHUNK_SIZE)
    await embed_and_save_chunks(chunks, resume_id)
    return resume_id

async def process_resume_file(file):
    try:
        if file.content_type != "application/pdf":
            return {
                "status": status.HTTP_400_BAD_REQUEST,
                "message": "Only pdfs allowed"
            }
        resume_id = await process_pdf_file(file)
        relevant_chunks = query_vector_db(resume_id, "Summarize this resume skills", top_k=3)
        flat_chunks = [c for sublist in relevant_chunks for c in (sublist if isinstance(sublist, list) else [sublist])]
        context = "\n\n".join(flat_chunks)
        summary = chain.invoke({"text": context})
        result = await mongo_collection_meta.update_one(
            {"id": resume_id},
            {"$set": {"summary": str(summary["text"]), "status": "complete"}}
        )
        return {
            "status": status.HTTP_200_OK,
            "data": {
                "resume_id": resume_id,
                "summary": str(summary["text"])
            }
        }
    except Exception as ex:
        return {
            "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "message": str(ex)
        }

def get_upload_file(file_path):
    f = open(file_path, "rb")
    upload_file = UploadFile(filename=os.path.basename(file_path), file=f)
    return upload_file

async def process_resume(file_path):
    try:
        upload_file = get_upload_file(file_path)
        text = await extract_pdf_text(upload_file)
        resume_id = await add_pdf_to_mongo(upload_file, text)
        chunks = chunk_text(text, CHUNK_SIZE)
        total_chunks = await embed_and_save_chunks(chunks, resume_id)
        print(f"Total chunks embedded: {total_chunks} with resume_id: {resume_id}")
    except Exception as ex:
        print(f"ex: {ex}")  

async def process_resume_file_bulk():
    try:
        resume_folder = os.path.join(os.getcwd(), "app", "assets", "resume_dataset")
        tasks = []
        for file_name in os.listdir(resume_folder):
            if file_name.lower().endswith(".pdf"):
                file_path = os.path.join(resume_folder, file_name)
                tasks.append(process_resume(file_path))
        await asyncio.gather(*tasks)
        return {
            "status": status.HTTP_201_CREATED,
        }
    except Exception as ex:
        return {
            "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "message": str(ex)
        }
    
async def send_resume_progress(websocket, resume_id, active_connections):
    try:
        while True:
            resume_doc = await mongo_collection_meta.find_one({"id": resume_id})
            if resume_doc:
                if resume_doc.get("summary"):
                    for ws in active_connections[resume_id]:
                        await ws.send_json({
                            "status": "complete",
                            "summary": resume_doc["summary"]
                        })
                        await ws.close()
                    active_connections[resume_id].clear()
                    break
                else:
                    await websocket.send_json({"status": "processing"})
            await asyncio.sleep(1)  # Avoid busy waiting
    except Exception as ex:
        if resume_id in active_connections and websocket in active_connections[resume_id]:
            active_connections[resume_id].remove(websocket)
        return {
            "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "message": str(ex)
        }