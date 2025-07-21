import os
import uuid
import logging
from datetime import datetime, timezone

import azure.functions as func
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.agents.models import ListSortOrder
from azure.cosmos import CosmosClient

load_dotenv()

class FunctionService:
    def __init__(self):
        # Configure logger
        self.logger = logging.getLogger(__name__)

        # Load configuration
        self.project_endpoint = os.getenv("PROJECT_ENDPOINT")
        self.agent_id = os.getenv("AGENT_ID")
        self.model_deployment_name = os.getenv("MODEL_DEPLOYMENT_NAME")
        self.cosmos_endpoint = os.getenv("COSMOS_ENDPOINT")
        self.cosmos_db_name = os.getenv("COSMOS_DATABASE_NAME")
        self.cosmos_container_name = os.getenv("COSMOS_CONTAINER_NAME")

        # Initialize credentials
        self.credential = DefaultAzureCredential()

        # Initialize Cosmos DB client
        try:
            self.cosmos_client = CosmosClient(self.cosmos_endpoint, self.credential)
            self.database = self.cosmos_client.get_database_client(self.cosmos_db_name)
            self.container = self.database.get_container_client(self.cosmos_container_name)
        except Exception as e:
            self.logger.error("Failed to initialize CosmosDB client: %s", e)
            raise RuntimeError("CosmosDB initialization failed") from e

        # Initialize AI Project client
        try:
            self.project_client = AIProjectClient(
                endpoint=self.project_endpoint,
                credential=self.credential
            )
        except Exception as e:
            self.logger.error("Error initializing AIProjectClient: %s", e)
            self.project_client = None

    def get_agent(self):
        if not self.project_client:
            raise RuntimeError("AIProjectClient is not initialized.")
        try:
            agent = self.project_client.agents.get_agent(self.agent_id)
            return agent
        except Exception as e:
            self.logger.error("Failed to fetch agent: %s", e)
            raise

    def run_agent_query(self, thread, question: str) -> str:
        if not self.project_client:
            raise RuntimeError("AIProjectClient is not initialized.")

        # Create user message
        user_msg = self.project_client.agents.messages.create(
            thread_id=thread.id,
            role="user",
            content=question
        )
        self.logger.info("Created user message, ID: %s", user_msg.id)

        # Run the agent
        run = self.project_client.agents.runs.create_and_process(
            thread_id=thread.id,
            agent_id=self.agent_id
        )
        self.logger.info("Agent run status: %s", run.status)
        if run.last_error:
            self.logger.warning("Agent run error: %s", run.last_error)

        # Retrieve and return the assistant's last response
        messages = self.project_client.agents.messages.list(
            thread_id=thread.id,
            order=ListSortOrder.ASCENDING
        )
        for msg in messages:
            if msg.role == "assistant":
                return msg.text_messages[-1].text.value
        return ""

    def save_message_to_cosmosdb(self, session_id: str, message: str, role: str):
        try:
            self.container.create_item({
                "id": str(uuid.uuid4()),
                "sessionid": session_id,
                "message": message,
                "role": role,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
        except Exception as e:
            self.logger.error("Failed to save message to CosmosDB: %s", e)
            raise

