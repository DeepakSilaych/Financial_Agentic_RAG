import re
from copy import copy
import state, config, nodes
from retriever import retriever
from utils import log_message
from .quant_qual import qq_classifier
import uuid
import concurrent.futures
from utils import send_logs
from config import LOGGING_SETTINGS


def metadata_fallback(
    metadata_filters, documents, metadata_retries, doc_grading_retries
):
    # Assuming metadata_filters initialized as : ['company_name' , 'year' , 'intra_metadata']
    if len(documents) == 1 and documents[0] == "None":
        pass
    else:
        if len(metadata_filters) == 0:
            pass
        elif metadata_retries == config.MAX_METADATA_FILTERING_RETRIES:
            metadata_filters = []
        elif metadata_retries != 0:
            metadata_filters.pop()
        elif doc_grading_retries == config.MAX_DOC_GRADING_RETRIES:
            metadata_filters = []
        elif doc_grading_retries == 1:
            pass
        elif doc_grading_retries != 0:
            metadata_filters.pop()
        else:
            pass
    return metadata_filters


def clean_question_for_bm25(question: str) -> str:
    return re.sub(r"[^a-zA-Z0-9\-\$\s\n\?]", "", question)


def retrieve_documents(state: state.InternalRAGState):
    question_group_id = state.get("question_group_id", 1)
    log_message(
        f"------RETRIEVING DOCUMENTS------", f"question_group{question_group_id}"
    )

    question = clean_question_for_bm25(state["question"])
    documents = state.get("documents", ["None"])
    metadata_filters = state.get("metadata_filters", copy(config.METADATA_FILTER_INIT))
    metadata_retries = state.get("metadata_retries", 0)
    doc_grading_retries = state.get("doc_grading_retries", 0)
    metadata_filters = metadata_fallback(
        metadata_filters, documents, metadata_retries, doc_grading_retries
    )
    state["metadata_retries"] = metadata_retries
    state["doc_grading_retries"] = doc_grading_retries
    state["metadata_filters"] = metadata_filters

    # Retrieval using rewriting and hyde
    if "xxxxxxxxxx" in question:
        log_message(
            f"------RETRIEVING DOCUMENTS USING HYDE------",
            f"question_group{question_group_id}",
        )
        questions = question.split("xxxxxxxxxx")
        docs1 = retriever.similarity_search(
            questions[0],
            config.NUM_DOCS_TO_RETRIEVE,
        )
        log_message(
            f"------RETRIEVING DOCUMENTS USING REWRITING------",
            f"question_group{question_group_id}",
        )
        docs2 = retriever.similarity_search(
            questions[1],
            config.NUM_DOCS_TO_RETRIEVE,
        )
        docs = docs1 + docs2
    else:
        docs = retriever.similarity_search(
            question,
            config.NUM_DOCS_TO_RETRIEVE,
        )

    if len(docs) == 0:
        state["metadata_retries"] += 1
    state["documents"] = docs
    state["original_question"] = state.get("original_question", question)
    return state


def retrieve_documents_with_metadata(state: state.InternalRAGState):
    """Retrieve documents using the specified method."""
    question_group_id = state.get("question_group_id", 1)
    log_message(
        f"------RETRIEVING DOCUMENTS------", f"question_group{question_group_id}"
    )

    question = clean_question_for_bm25(state["question"])
    metadata = state["metadata"]
    documents = state.get("documents", ["None"])
    metadata_filters = state.get("metadata_filters", copy(config.METADATA_FILTER_INIT))
    metadata_retries = state.get("metadata_retries", 0)
    doc_grading_retries = state.get("doc_grading_retries", 0)
    answer_grading_retries = state.get("answer_generation_retries", 0)
    if (
        metadata_filters != config.METADATA_FILTER_INIT
        and not metadata_retries
        and not doc_grading_retries
        and not answer_grading_retries
    ):
        metadata_filters = config.METADATA_FILTER_INIT
    metadata_filters = metadata_fallback(
        metadata_filters, documents, metadata_retries, doc_grading_retries
    )

    metadata = {k: v for k, v in metadata.items() if k in metadata_filters}
    source_files = state.get("query_path", [])
    if len(source_files) != 0:
        metadata["path"] = source_files

    # split the question even if it doesn't contain the delimiter as that will just yield the original question
    questions = question.split("xxxxxxxxxx")
    docs = []
    formatted_metadata = nodes.convert_metadata_to_jmespath(metadata)
    log_message(f"\n\nformatted metadata :\n\n {formatted_metadata} \n\n")
    for question in questions:
        docs.extend(
            retriever.similarity_search(
                question,
                config.NUM_DOCS_TO_RETRIEVE,
                metadata_filter=formatted_metadata or None,
            )
        )

    original_question = state.get("original_question", question)

    ###### log_tree part
    id = str(uuid.uuid4())
    child_node = nodes.retrieve_documents_with_metadata.__name__ + "//" + id
    prev_node_rewrite = child_node
    parent_node = state.get("prev_node", "START")
    log_tree = {}

    if not LOGGING_SETTINGS["retrieve_documents_with_metadata"] or state.get("send_log_tree_logs" , "") == "False":
        child_node = parent_node

    log_tree[parent_node] = [child_node]
    ######

    ##### Server Logging part
    output_state = {
        "documents": docs,
        "documents_after_metadata_filter": docs,
        "original_question": original_question,
        "formatted_metadata": formatted_metadata,
        "metadata_retries": metadata_retries,
        "doc_grading_retries": doc_grading_retries,
        "metadata_filters": metadata_filters,
        "prev_node_rewrite" : prev_node_rewrite , 
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


def retriever_helper(retriever, question, num_docs, filter):
    docs = []
    if filter == "":
        docs = retriever.similarity_search(question, num_docs)
    else:
        docs = retriever.similarity_search(question, num_docs, metadata_filter=filter)
    return docs


def retrieve_documents_with_quant_qual(state: state.InternalRAGState):
    """Retrieve documents using the specified method."""

    question_group_id = state.get("question_group_id", 1)
    log_message(
        f"------RETRIEVING DOCUMENTS------", f"question_group{question_group_id}"
    )
    # print(f"------RETRIEVING DOCUMENTS------")

    question = clean_question_for_bm25(state["question"])
    metadata = state["metadata"]
    documents = state.get("documents", ["None"])
    metadata_filters = state.get("metadata_filters", copy(config.METADATA_FILTER_INIT))
    metadata_retries = state.get("metadata_retries", 0)
    doc_grading_retries = state.get("doc_grading_retries", 0)
    answer_grading_retries = state.get("answer_generation_retries", 0)

    # state["metadata_retries"] = metadata_retries
    # state["doc_grading_retries"] = doc_grading_retries
    # state["metadata_filters"] = metadata_filters

    if (
        metadata_filters != config.METADATA_FILTER_INIT
        and not metadata_retries
        and not doc_grading_retries
        and not answer_grading_retries
    ):
        metadata_filters = config.METADATA_FILTER_INIT
    metadata_filters = metadata_fallback(
        metadata_filters, documents, metadata_retries, doc_grading_retries
    )
    metadata = {k: v for k, v in metadata.items() if k in metadata_filters}
    source_files = state.get("query_path", [])
    if len(source_files) != 0:
        metadata["path"] = source_files

    metadata_text = copy(metadata)
    metadata_text["table"] = "False"
    metadata_table = copy(metadata)
    metadata_table["table"] = "True"
    metadata_kv = copy(metadata)
    metadata_kv["is_table_value "] = "True"

    metadata["is_table_value"] = "False"
    metadata["table"] = "False"

    metadata_text = nodes.convert_metadata_to_jmespath(metadata_text)
    metadata_table = nodes.convert_metadata_to_jmespath(metadata_table)
    metadata_kv = nodes.convert_metadata_to_jmespath(metadata_kv)
    formatted_metadata = nodes.convert_metadata_to_jmespath(metadata)

    ## Retrieval using rewriting and hyde
    questions = question.split("xxxxxxxxxx")
    docs = []
    docs_kv = []

    for question in questions:
        ## Routing
        cat = state["category"]
        if cat == "Quantitative":
            ## Quantitative
            if config.WORKFLOW_SETTINGS["with_table_for_quant_qual"]:
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future_text = executor.submit(
                        retriever_helper,
                        retriever,
                        question,
                        config.NUM_DOCS_TO_RETRIEVE,
                        metadata_text,
                    )
                    future_table = executor.submit(
                        retriever_helper,
                        retriever,
                        question,
                        config.NUM_DOCS_TO_RETRIEVE_TABLE,
                        metadata_table,
                    )
                    future_kv = executor.submit(
                        retriever_helper,
                        retriever,
                        question,
                        config.NUM_DOCS_TO_RETRIEVE_KV,
                        metadata_kv,
                    )
                    docs += (
                        future_text.result()
                        + future_table.result()
                        + future_kv.result()
                    )
                    docs_kv += future_kv.result()
            else:
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future_text_table = executor.submit(
                        retriever_helper,
                        retriever,
                        question,
                        config.NUM_DOCS_TO_RETRIEVE,
                        formatted_metadata,
                    )
                    future_kv = executor.submit(
                        retriever_helper,
                        retriever,
                        question,
                        config.NUM_DOCS_TO_RETRIEVE_KV,
                        metadata_kv,
                    )
                    docs += future_text_table.result() + future_kv.result()
                    docs_kv += future_kv.result()
        else:
            ## Qualitative
            docs += retriever_helper(
                retriever, question, config.NUM_DOCS_TO_RETRIEVE, formatted_metadata
            )

    ## Fallback when 0 doc retrieved
    flag = False
    if len(docs) == 0:
        flag = True
        docs += retriever_helper(retriever, question, config.NUM_DOCS_TO_RETRIEVE, "")
    # state["documents"] = docs
    fallback_qq_retriever = flag
    # state["documents_after_metadata_filter"] = docs
    documents_with_kv = docs_kv
    # state["prev_node = nodes.retrieve_documents_with_quant_qual.__name__
    original_question = state.get("original_question", question)
    formatted_metadata = formatted_metadata

    ###### log_tree part
    # import uuid , nodes 
    id = str(uuid.uuid4())
    child_node = nodes.retrieve_documents_with_quant_qual.__name__ + "//" + id
    parent_node = state.get("prev_node" , "START")
    if parent_node == "":
        parent_node = "START"
    log_tree = {}

    if not LOGGING_SETTINGS['retrieve_documents_with_quant_qual'] or state.get("send_log_tree_logs" , "") == "False":
        child_node = parent_node  
    
    log_tree[parent_node] = [child_node]
    ######

    ##### Server Logging part

    output_state = {
        "documents": docs,
        "documents_after_metadata_filter": docs,
        "documents_with_kv" : documents_with_kv ,
        "fallback_qq_retriever" : fallback_qq_retriever,
        "original_question": original_question,
        "formatted_metadata": formatted_metadata,
        "metadata_retries": metadata_retries,
        "doc_grading_retries": doc_grading_retries,
        "metadata_filters": metadata_filters,
        "prev_node": child_node,
        "log_tree": log_tree,
    }


    send_logs(
        parent_node = parent_node , 
        curr_node= child_node , 
        child_node=None , 
        input_state=state , 
        output_state=output_state , 
        text=child_node.split("//")[0] ,
    )
    
    ######

    return output_state 
    # return output_state
