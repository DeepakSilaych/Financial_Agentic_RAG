"""
Document Grading Module

This module is responsible for grading the relevance of retrieved documents in response to a user query. 
It includes functionality to determine if the retrieved documents are relevant to the user's question and provides reasons for their relevance or irrelevance. 

### Key Components:

1. **DocumentGrade (BaseModel)**:
   - A data model representing the score and explanation for the relevance check of a document.
   - `binary_score`: A binary value indicating whether the document is relevant ("yes" or "no").
   - `reason`: A brief explanation for why the document is deemed relevant or irrelevant.

2. **DocumentGraderInput (BaseModel)**:
   - A data model that represents the input required for grading a document.
   - `question`: The original question posed by the user.
   - `document`: The content of the document to be evaluated for relevance.

3. **_system_prompt**:
   - A system-level prompt used for evaluating the relevance of a document based on its content and the user's question. It helps provide context to the grading task.

4. **grade_prompt (ChatPromptTemplate)**:
   - A template that defines how the document grading prompt is structured. It combines the system prompt with the document content and the user's question.

5. **document_grader**:
   - A pipeline that uses the `grade_prompt` and a large language model (via `llm.with_structured_output`) to grade the relevance of the documents. It outputs a `DocumentGrade` object with a binary score and reason.

6. **grade_document**:
   - A helper function that grades a single document based on the user’s question and the document’s content. It returns the grade and reason.

7. **grade_documents**:
   - The main function that grades a set of documents in parallel using `ThreadPoolExecutor` to improve performance. 
   - It filters out irrelevant documents and collects the reasons for irrelevance.
   - It logs the process and sends logs to the server.

### Parallel Document Grading:
- **Concurrency** is achieved by using the `ThreadPoolExecutor` to grade multiple documents concurrently, improving efficiency when dealing with many documents.

### Logging:
- The module includes logging functionality to keep track of the document grading process. Logs are sent to the server, and a tree structure is maintained for tracking the flow of the execution.
- It also includes a mechanism to retry document grading based on the `doc_grading_retries` parameter.

### Server Logs:
- Server logs are sent after the grading is completed, containing details about the graded documents, reasons for irrelevance, and other contextual information.
  
### Environment:
- The module utilizes environment variables loaded via `dotenv` for configuration.
  
### Example Workflow:
1. The function **grade_documents** is called with the current state of the system, including the question and a list of retrieved documents.
2. Each document is processed in parallel to determine its relevance to the question.
3. The relevant documents are filtered, and the reasons for irrelevance are collected.
4. The filtered documents and reasons for irrelevance are returned, along with updated state information.

### Dependencies:
- **concurrent.futures**: Used for parallel execution of document grading tasks.
- **pydantic**: For structured data validation and creation of input and output models.
- **langchain_core**: Used to create and process prompts for document grading.
- **uuid**: To generate unique identifiers for logging.
- **dotenv**: To load environment variables from a `.env` file.
- **utils.send_logs**: A utility function to send logs to the server.
- **config.LOGGING_SETTINGS**: For controlling logging behavior based on configuration settings.

"""

from concurrent.futures import ThreadPoolExecutor
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from prompt import prompts
import state, nodes
from llm import llm
import uuid
from dotenv import load_dotenv

load_dotenv()
from utils import send_logs
from config import LOGGING_SETTINGS


class DocumentGrade(BaseModel):
    """Binary score and reason for relevance check on retrieved documents."""

    binary_score: str = Field(
        description="Documents are relevant to the question, 'yes' or 'no'."
    )
    reason: str = Field(
        description="A brief reason explaining why the document is relevant or irrelevant."
    )


class DocumentGraderInput(BaseModel):
    question: str
    document: str


_system_prompt = prompts.document_grader_system_prompt

grade_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", _system_prompt),
        ("human", "Retrieved document: \n\n {document} \n\n User question: {question}"),
    ]
)
document_grader = grade_prompt | llm.with_structured_output(DocumentGrade)


def grade_document(question, document):
    """
    Helper function to grade a single document.
    """
    score = document_grader.invoke(
        {"question": question, "document": document.page_content}
    )
    return {"grade": score.binary_score, "reason": score.reason, "document": document}


def grade_documents(state: state.InternalRAGState):
    """
    Determines whether the retrieved documents are relevant to the question and collects reasons for irrelevance.

    Args:
        state (dict): The current graph state.

    Returns:
        state (dict): Updates documents key with only filtered relevant documents and includes reasons for irrelevance.
    """

    question = state["original_question"]
    documents = state["documents"]
    doc_grading_retries = state.get("doc_grading_retries", 0)

    # Sending all chunks for relevance grading parallely to improve efficiency
    with ThreadPoolExecutor() as executor:
        results = list(
            executor.map(lambda doc: grade_document(question, doc), documents)
        )

    filtered_docs = [res["document"] for res in results if res["grade"] == "yes"]
    reasons = [res["reason"] for res in results if res["grade"] == "no"]

    concatenated_reasons = " | ".join(reasons)
    # documents_kv = state.get("documents_with_kv", [])
    # filtered_docs.extend(documents_kv)

    ###### log_tree part
    # import uuid , nodes
    id = str(uuid.uuid4())
    child_node = nodes.grade_documents.__name__ + "//" + id
    prev_node_rewrite = child_node
    parent_node = state.get("prev_node", "START")
    if parent_node == "":
        parent_node = "START"
    log_tree = {}

    if not LOGGING_SETTINGS["grade_documents"] or state.get('send_log_tree_logs',"") == "False":
        child_node = parent_node

    log_tree[parent_node] = [child_node]
    ######

    ##### Server Logging part

    output_state = {
        "documents": filtered_docs,
        "irrelevancy_reason": concatenated_reasons,
        "doc_grading_retries": doc_grading_retries + 1,
        "prev_node_rewrite": prev_node_rewrite,
        "prev_node": child_node,
        "log_tree": log_tree,
    }

    send_logs(
        parent_node=parent_node,
        curr_node=child_node,
        child_node=None,
        input_state=state,
        output_state=output_state,
        text=child_node.split("//")[0],
    )

    ######

    return output_state
