import chromadb
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
from app.setting import current_config
from concurrent.futures import ThreadPoolExecutor
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import ChatOpenAI
from app.utils.system_prompt import system_prompt

import boto3
import io
import os
from uuid import uuid4
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

class HandleChromadb:
    def __init__(self):
        self.client = chromadb.PersistentClient(path="chroma_db")
        self.embedings_function = OpenAIEmbeddingFunction(
            model_name=current_config.OPENAI_EMBEDDING_MODEL,
            api_key=current_config.OPENAI_API_KEY
        )
        self.llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0,
            max_tokens=None
            )
        self.system_prompt = system_prompt
        self.collection_name = "documents"
    
    
    def get_or_create_collection(self):
        """Create a new collection in the ChromaDB."""
        collection = self.client.get_or_create_collection(
            name=self.collection_name,
            embedding_function=self.embedings_function
        )
        print(f"New collection created: {collection.name}")
        return collection


    def save_vector(self, vector: list, metadata: dict):
        """Save a vector to a specific collection."""
        print(f"Saving vector to collection: {self.collection_name}")

        collection = self.client.get_or_create_collection(
            name=self.collection_name,
            embedding_function=self.embedings_function
        )
        
        documents = vector
        metadatas = [metadata] * len(documents)
        ids = [metadata.get("id", "default_id") + f"_{i}" for i in range(len(documents))]
        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        print(f"Vector added to collection {self.collection_name}.")

    def list_collections(self):
        """List all collections in the ChromaDB."""
        return self.client.list_collections()
    
    
    def query_collection(self, query: str, filter: dict = None):
        """Query a specific collection."""
        collection = self.client.get_collection(name=self.collection_name, embedding_function=self.embedings_function)
        results = collection.query(
            query_texts=[query],
            n_results=13,
            where=filter,
            include=["documents", "metadatas"]
        )
        
        print(results['metadatas'])
        return results['documents']
        
    
    def get_ai_response(self, query: str, context: str, message_history: list = None):
        """Get AI response for a query."""""
        
        def format_message_history(message_history):
            formatted = []
            for msg in message_history or []:
                if msg["role"] == "user":
                    formatted.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    formatted.append(AIMessage(content=msg["content"]))
                elif msg["role"] == "system":
                    formatted.append(SystemMessage(content=msg["content"]))
            return formatted

        messages = [
            SystemMessage(content=self.system_prompt),
            *format_message_history(message_history),
            HumanMessage(content=f"{query}\n\nContext:\n{context}")
        ]

        response = self.llm.invoke(messages)
        return response.content.strip()
        
        
class AWSHelper:
    def __init__(self):
        self.s3_bucket_name = current_config.S3_BUCKET_NAME
        self.aws_region = current_config.AWS_REGION
        self.s3_client = boto3.client("s3", region_name=self.aws_region)

    def upload_file(self, file_stream, filename: str, content_type: str, user_id: str) -> str:
        """Upload a file to S3 and return the file URL."""
        unique_filename = f"{user_id}/{filename}"

        # self.s3_client.upload_fileobj(
        #     Fileobj=file_stream,
        #     Bucket=self.s3_bucket_name,
        #     Key=unique_filename,
        #     ExtraArgs={
        #         "ContentType": content_type,
        #         "ACL": "public-read"
        #     }
        # )
        file_url = f"https://{self.s3_bucket_name}.s3.{self.aws_region}.amazonaws.com/{unique_filename}"
        return file_url
    
    def remove_user_documents(self, user_id: str):
        """Remove all documents for a user from the S3 bucket."""
        prefix = f"{user_id}/"
        paginator = self.s3_client.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=self.s3_bucket_name, Prefix=prefix)

        keys_to_delete = []
        for page in pages:
            for obj in page.get('Contents', []):
                keys_to_delete.append({'Key': obj['Key']})

        if keys_to_delete:
            # S3 delete_objects can delete up to 1000 objects at a time
            for i in range(0, len(keys_to_delete), 1000):
                self.s3_client.delete_objects(
                    Bucket=self.s3_bucket_name,
                    Delete={'Objects': keys_to_delete[i:i+1000]}
                )

    def save_to_local(self, file_stream, filename: str, user_id: str = None):
        """Save a file locally."""
        
        # create a directory for the user if it doesn't exist
        directory = str(user_id)
        os.makedirs(directory, exist_ok=True)
        
        file_path = os.path.join(directory, filename)
        
        with open(file_path, 'wb') as f:
            f.write(file_stream.read())


    def concurrent_upload(self, file_obj, filename: str, content_type: str, user_id: str):
        """Upload a file to S3 and save it locally concurrently."""        
        file_bytes = file_obj.read()

        s3_stream = io.BytesIO(file_bytes)
        local_stream = io.BytesIO(file_bytes)

        with ThreadPoolExecutor(max_workers=10) as executor:
            future_s3 = executor.submit(self.upload_file, s3_stream, filename, content_type, user_id)
            future_local = executor.submit(self.save_to_local, local_stream, filename, user_id)

            future_local.result()
            return  future_s3.result()

    
class ProcessPdfDocument(HandleChromadb):
    def __init__(self):
        super().__init__()
        self.splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)


    def split_text_into_chunks(self, text: str, metadata: dict = None):
        
        print(f"Splitting text into chunks for collection: {self.collection_name}")
        chunks = self.splitter.split_text(text)
        
        self.get_or_create_collection()
        
        self.save_vector(
            vector=chunks,
            metadata=metadata
        )


    def load_pdf(self, file_path: str, metadata: dict = None):
        try:
            # Load the PDF file using PyPDFLoader
            loader = PyPDFLoader(file_path)
            for page in loader.load():
                print(page.page_content)
                self.split_text_into_chunks(page.page_content, metadata)
                
        except Exception as e:
            
            # Handle any exceptions that occur during PDF processing
            print(f"[ERROR] Failed to process PDF '{file_path}': {e}")
            
        finally:
            # Clean up the temporary file
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"Removed temporary file: {file_path}")
    
    
    def process_pdf(self, user_id: str, file_name, file_id):
        str_user_id = str(user_id)
        
        self.load_pdf(
            file_path=os.path.join(str_user_id, file_name),
            metadata={"source": file_name, "user_id": str_user_id, "id": file_id}
        )

precess_pdf = ProcessPdfDocument()
save_pdf = AWSHelper()

if __name__ == "__main__":
    
    user_id = "dce575c7-cc61-4f9c-95f0-8f7eea4fd86e"
    
    process_pdf = ProcessPdfDocument()
    context = process_pdf.query_collection(
        query="what is the summary of the pdf content",
        filter={
        "$and": [
            {"user_id": {"$eq": user_id}},
            {"id": {"$in": ["3f15ea0d-6505-4b55-9e8e-d6f26d07fb5a", "f104c2a8-b147-4508-8e78-fc8f421d1108", "b185caa6-5b8f-43f0-83c6-288fc83cd5a4"]}}
        ]
        }
    )
    
    message_history = [
    {"role": "user", "content": "Hi, what’s your return policy?"},
    {"role": "assistant", "content": "You can return items within 30 days."},
    {"role": "user", "content": "Is that from the delivery date or order date?"}
    ]
    
    response = process_pdf.get_ai_response(
        query="what is the summary of the pdf content",
        context=context,
        message_history=message_history
    )
    
    print(response)
