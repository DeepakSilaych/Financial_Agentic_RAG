import re
from copy import copy
import state, config, nodes
from retriever import retriever
from utils import log_message
from .quant_qual import qq_classifier


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
    state["metadata_retries"] = metadata_retries
    state["doc_grading_retries"] = doc_grading_retries
    state["metadata_filters"] = metadata_filters

    # split the question even if it doesn't contain the delimiter as that will just yield the original question
    questions = question.split("xxxxxxxxxx")
    docs = []
    if len(metadata_filters) == 0:
        for question in questions:
            docs.extend(
                retriever.similarity_search(question, config.NUM_DOCS_TO_RETRIEVE)
            )
        state["formatted_metadata"] = ""
    else:
        formatted_metadata = nodes.convert_metadata_to_jmespath(
            metadata, metadata_filters
        )
        state["formatted_metadata"] = formatted_metadata
        log_message(f"\n\nformatted metadata :\n\n {formatted_metadata} \n\n")
        for question in questions:
            docs.extend(
                retriever.similarity_search(
                    question,
                    config.NUM_DOCS_TO_RETRIEVE,
                    metadata_filter=formatted_metadata,
                )
            )

    state["documents"] = docs
    state["documents_after_metadata_filter"] = docs
    state["prev_node"] = nodes.retrieve_documents_with_metadata.__name__
    state["original_question"] = state.get("original_question", question)

    # ##### log_tree part
    # state["log_tree"] = {}
    # curr_node = nodes.retrieve_documents_with_metadata.__name__
    # prev_node = state.get("prev_node" , "START")
    # state["log_tree"][prev_node] = [{"node" : curr_node , "state" : state}]

    # state["prev_node"]  = curr_node

    # #####

    return state


def retriever_helper(retriever, question, num_docs, filter):
    if filter == "":
        docs = retriever.similarity_search(question, num_docs)
        return docs
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

    state["metadata_retries"] = metadata_retries
    state["doc_grading_retries"] = doc_grading_retries
    state["metadata_filters"] = metadata_filters

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

    ## Metadata Filters
    metadata_text = "variant == `\"{'text'}\"`"
    metadata_table = "(variant == `\"{'table'}\"` || variant == `\"{'text','table'}\"`)"
    metadata_kv = "is_table_value == `true`"
    formatted_metadata = ""

    if metadata_filters:
        formatted_metadata = nodes.convert_metadata_to_jmespath(
            metadata, metadata_filters
        )
        metadata_text += " && " + formatted_metadata
        metadata_table += " && " + formatted_metadata
        metadata_kv += " && " + formatted_metadata
        formatted_metadata += " && is_table_value == `false`"
    # print(formatted_metadata)
    ## Retrieval using rewriting and hyde
    questions = question.split("xxxxxxxxxx")
    docs = []
    docs_kv = []

    for question in questions:
        ## Routing
        res = qq_classifier.invoke({"question": questions})
        cat = res.category
        reasioning = res.reason
        # print(cat)
        if cat == "Quantitative":
            ## Quantitative
            if config.WORKFLOW_SETTINGS["with_table_for_quant_qual"]:  
                ## For text ##
                docs.extend(
                    retriever_helper(retriever, question,  config.NUM_DOCS_TO_RETRIEVE, metadata_text)
                )       
                # print(retriever_helper(retriever, question,  config.NUM_DOCS_TO_RETRIEVE, ""))
                
                ## For table ##
                docs.extend(
                    retriever_helper(retriever, question,  config.NUM_DOCS_TO_RETRIEVE_TABLE, metadata_table)
                )

                # print(retriever_helper(retriever, question,  config.NUM_DOCS_TO_RETRIEVE_TABLE, metadata_table))

                ## For key-value
                docs_kv.extend(
                    retriever_helper(
                        retriever, question, config.NUM_DOCS_TO_RETRIEVE_KV, metadata_kv
                    )
                )
                # print(retriever_helper(retriever, question,  config.NUM_DOCS_TO_RETRIEVE_KV, metadata_kv))
            else:
                for question in questions:
                    ## For text/table ##
                    docs.extend(
                        retriever_helper(retriever, question,  config.NUM_DOCS_TO_RETRIEVE, formatted_metadata)
                    )  
                    # print(docs)

                    ## For key-value
                    docs_kv.extend(
                        retriever_helper(retriever, question,  config.NUM_DOCS_TO_RETRIEVE_KV, metadata_kv)
                    ) 

        else:       
            ## Qualitative 
            ## For text/table ##
            docs.extend(
                retriever_helper(
                    retriever, question, config.NUM_DOCS_TO_RETRIEVE, formatted_metadata
                )
            )
    # if (len(docs)+len(docs_kv)) == 0:
    #     state["metadata_retries"] += 1
    state["documents"] = docs
    state["documents_after_metadata_filter"] = docs
    state["documents_with_kv"] = docs_kv
    state["prev_node"] = nodes.retrieve_documents_with_quant_qual.__name__
    state["original_question"] = state.get("original_question", question)

    return state
