from langchain_core.runnables import RunnableConfig
from langchain.callbacks.tracers import ConsoleCallbackHandler

BASE_DATA_DIRECTORY = "MultiData/base_data"

VECTOR_STORE_HOST = "127.0.0.1"
VECTOR_STORE_PORT = 7000
VECTOR_STORE_TIMEOUT = 10

FAST_VECTOR_STORE_HOST = "127.0.0.1"
FAST_VECTOR_STORE_PORT = 7000
FAST_VECTOR_STORE_TIMEOUT = 10
FAST_VECTOR_STORE_DATA_DIR = "MultiData/fast_data"
FAST_VECTOR_STORE_CACHE_DIR = "MultiCache/fast_cache"

SLOW1_VECTOR_STORE_HOST = "127.0.0.1"
SLOW1_VECTOR_STORE_PORT = 7001
SLOW1_VECTOR_STORE_TIMEOUT = 10
SLOW1_VECTOR_STORE_DATA_DIR = "MultiData/server1_data"
SLOW1_VECTOR_STORE_CACHE_DIR = "MultiCache/server1_cache"

SLOW2_VECTOR_STORE_HOST = "127.0.0.1"
SLOW2_VECTOR_STORE_PORT = 7002
SLOW2_VECTOR_STORE_TIMEOUT = 10
SLOW2_VECTOR_STORE_DATA_DIR = "MultiData/server2_data"
SLOW2_VECTOR_STORE_CACHE_DIR = "MultiCache/server2_cache"

CACHE_STORE_HOST = "127.0.0.1"
CACHE_STORE_PORT= 8000

MULTI_SERVER_HOST = "127.0.0.1"
MULTI_SERVER_PORT = 8080

# Number of documents to retrieve from the vector store
NUM_DOCS_TO_RETRIEVE = 5
NUM_DOCS_TO_RETRIEVE_TABLE = 2
NUM_DOCS_TO_RETRIEVE_KV = 30

# Number of retries for anthropic
MAX_RETRIES_ANTHROPIC = 5

# Number of previous messages to consider for conversational awareness
NUM_PREV_MESSAGES = 5

# Threshold number for docs relevance check to pass
DOCS_RELEVANCE_THRESHOLD = 1

# Number of metrics and charts for post processing
NUM_METRICS = 3
NUM_CHARTS = 5

# Max retries for different nodes
MAX_DOC_GRADING_RETRIES = 2
MAX_METADATA_FILTERING_RETRIES = 2
MAX_HALLUCINATION_RETRIES = 1
MAX_ANSWER_GENERATION_RETRIES = 1

METADATA_FILTER_INIT = ["company_name", "year"]  # ["company_name" , "year" , "topics"]

# Max number of personas to create
MAX_PERSONAS_GENERATED = 4
MAX_QUESTIONS_GENERATED_BY_EACH_PERSONA = 3
MAX_QUESTIONS_GENERATED_BY_PERSONAS_SUPERVISOR = 5

TOKENIZER_CACHE_DIR = "hub/"

CHAIN_DEBUG_CONFIG: RunnableConfig = {"callbacks": [ConsoleCallbackHandler()]}

EVAL_QUERY_BATCH_SIZE = 10

# Set to "stdout" to log to stdout, "server" to send the logs to the server, or a file name to log to a file
LOG_FILE_NAME = "pipeline_log.txt"

WORKFLOW_SETTINGS = {
    "query_expansion": True,
    "metadata_filtering": True,
    "assess_metadata_filters": True,
    "metadata_filtering_with_quant_qual": False,
    "reranking": False,
    "grade_documents": True,
    "assess_graded_documents": True,
    "rewrite_with_hyde": True,
    "check_hallucination": True,
    "hallucination_checker": "llm",  # "hhem"
    "grade_answer": False,
    "grade_web_answer": False,
    "with_table_for_quant_qual": False,
    "with_site_blocker": False,
    "vision": False,
}

GLOBAL_SET_OF_FINANCE_TERMS = {
    "financial_accounting",
    "managerial_accounting",
    "corporate_finance",
    "investment_management",
    "capital_markets",
    "financial_modeling",
    "valuation_techniques",
    "portfolio_management",
    "behavioral_finance",
    "risk_management",
    "banking_and_financial_institutions",
    "investment_banking",
    "central_banking_and_monetary_policy",
    "credit_analysis",
    "trade_finance",
    "payments_and_settlement_systems",
    "economic_analysis",
    "taxation_and_public_finance",
    "financial_regulation",
    "treasury_management",
    "alternative_investments",
    "derivatives_and_options",
    "quantitative_finance",
    "sustainable_finance",
    "personal_financial_planning",
    "wealth_management",
    "project_and_infrastructure_finance",
    "real_estate_finance",
    "commodities_markets",
    "cryptocurrencies_and_blockchain",
    "market_analysis_and_benchmarking",
    "financial_statement_analysis",
    "strategic_finance_and_swot_analysis",
    "big_data_and_analytics_in_finance",
    "customer_and_employee_analysis",
    "emerging_markets_and_global_finance" "Other",
}

GLOBAL_SET_OF_10K_ITEMS = {
    "item_1_business",
    "item_1a_risk_factors",
    "item_1b_unresolved_staff_comments",
    "item_2_properties",
    "item_3_legal_proceedings",
    "item_4_mine_safety_disclosures",
    "item_5_market_for_registrant_s_common_equity_related_stockholder_matters_and_issuer_purchases_of_equity_securities",
    "item_6_selected_financial_data",
    "item_7_management_s_discussion_and_analysis_of_financial_condition_and_results_of_operations",
    "item_7a_quantitative_and_qualitative_disclosures_about_market_risk",
    "item_8_financial_statements_and_supplementary_data",
    "item_9_changes_in_and_disagreements_with_accountants_on_accounting_and_financial_disclosure",
    "item_9a_controls_and_procedures",
    "item_9b_other_information",
    "item_10_directors_executive_officers_and_corporate_governance",
    "item_11_executive_compensation",
    "item_12_security_ownership_of_certain_beneficial_owners_and_management_and_related_stockholder_matters",
    "item_13_certain_relationships_and_related_transactions_and_director_independence",
    "item_14_principal_accountant_fees_and_services",
    "item_15_exhibits_financial_statement_schedules",
    "item_16_form_10k_summary" "Other",
}
