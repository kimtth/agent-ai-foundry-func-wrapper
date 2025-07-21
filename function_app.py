import logging
import azure.functions as func

from function_service import FunctionService
import json

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize your service once at module load
service = FunctionService()


@app.route(route="chat/conversation", methods=["POST"])
def func_conversation(req: func.HttpRequest) -> func.HttpResponse:
    # 1. Parse body
    try:
        body = req.get_json() if req.get_body() else {}
    except Exception as e:
        logger.error("Error parsing JSON body: %s", e)
        return func.HttpResponse("Invalid JSON body.", status_code=400)

    thread_id = body.get("thread_id")
    question = body.get("question")
    if not thread_id or not question:
        return func.HttpResponse(
            "Please provide both 'thread_id' and 'question' parameters.",
            status_code=400,
        )

    # 2. Load existing thread
    thread = service.project_client.agents.threads.get(thread_id)
    logger.info("📝 Using existing thread, ID: %s", thread.id)

    # 3. Save user message: Cosmos DBS
    service.save_message_to_cosmosdb(thread.id, question, "user")

    # 4. Run agent
    answer = service.run_agent_query(thread, question)
    if answer:
        logger.info("🤖 Assistant replied: %s", answer)
        service.save_message_to_cosmosdb(thread.id, answer, "assistant")

    return func.HttpResponse(
        body=json.dumps({"question": question, "answer": answer}), status_code=200
    )


@app.route(route="chat/newchat", methods=["POST"])
def func_newchat(req: func.HttpRequest) -> func.HttpResponse:
    # 1. Fetch the agent
    try:
        agent = service.get_agent()
    except Exception as e:
        logger.error("Error fetching agent: %s", e)
        return func.HttpResponse(
            "Agent not found. Please check your configuration.", status_code=404
        )

    # 2. Create a new thread
    if agent:
        thread = service.project_client.agents.threads.create()
        logger.info("📝 Created new thread, ID: %s", thread.id)

        return func.HttpResponse(
            json.dumps({"thread_id": thread.id}),
            status_code=200,
            mimetype="application/json",
        )
