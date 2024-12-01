'''from langchain.chat_models import ChatOpenAI
from langchain.embeddings import OpenAIEmbeddings
from langchain.cache import RedisSemanticCache
from langchain_core.globals import set_llm_cache
from langchain.schema import AIMessage

# Initialize ChatOpenAI and Embeddings
llm = ChatOpenAI(model="gpt-4o-mini", openai_api_key='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')
embeddings = OpenAIEmbeddings(openai_api_key='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')


class CustomRedisSemanticCache(RedisSemanticCache):
    def update(self, prompt, llm_string, return_val):
        # Extract text content from AIMessage before caching
        if isinstance(return_val[0], AIMessage):
            return_val = [return_val[0].content]
        super().update(prompt, llm_string, return_val)

semantic_cache = CustomRedisSemanticCache(
    redis_url="redis://localhost:6379",
    embedding=embeddings
)

# Set the global LLM cache to use Redis Semantic Cache
set_llm_cache(semantic_cache)

# Function to generate embeddings for a query
def generate_embedding(query):
    embedding_vector = embeddings.embed_query(query)
    return embedding_vector
from langchain.schema import LLMResult

def handle_query(query):
    # Check cache for semantically similar query
    cached_response = semantic_cache.lookup(query, llm_string=str(llm))
    
    if cached_response:
        print("Using cached response")
        return cached_response[0].text
    else:
        print("Generating new response")
        # Generate new response using LLM
        response = llm.predict(query)  # For chat models, use `predict`
        
        # Convert response to LLMResult format for caching
        llm_result = LLMResult(generations=[[response]])
        
        # Update the cache with the new response
        semantic_cache.update(query, llm_string=str(llm), return_val=llm_result.generations)
        
        return response


# Example usage
user_query = "What is semantic caching?"
response = handle_query(user_query)
print(response)
'''

from langchain_community.llms import OpenAI
from langchain_community.chat_models import ChatOpenAI
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.cache import RedisSemanticCache
from langchain.schema import Generation
from langchain.globals import set_llm_cache
import asyncio

# Initialize OpenAI LLM and Embeddings
llm = ChatOpenAI(model="gpt-4o-mini",  openai_api_key='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')
embeddings = OpenAIEmbeddings(openai_api_key="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")

llm_string='openai/gpt-4o-mini'
# Set up Redis Semantic Cache
semantic_cache = RedisSemanticCache(
    redis_url="redis://127.0.0.1:6379",
    embedding=embeddings,
    score_threshold=0.2
)
set_llm_cache(semantic_cache)

# Handle user queries with cache
async def handle_query(query):
    # Check cache for semantically similar query
    #print(str(llm))
    cached_response = await semantic_cache.alookup(query, llm_string)
    print(cached_response[0])
    
    if cached_response:
        #print(f"Cache Hit: {cached_response[0].text}")
        #print(f"Using cached response ------------------\n")
        return cached_response[0].text
    
    else:
        print("Generating new response ------------------\n")
        # Generate new response using LLM
        response = llm.predict(query)  # Predict returns a string
        
        # Wrap response in Generation object
        response_generation = [Generation(text=response)]
        
        # Update the cache with the new response
        semantic_cache.update(query, llm_string, return_val=response_generation)
        print(f"Added to cache: {query}")
        return response

# Example usage

if __name__ == "__main__":
    query = "What is semantic caching?"
    response = asyncio.run(handle_query(query))
    #print(response)


query = "What is semantic caching?"
embedding1 = embeddings.embed_query(query)
embedding2 = embeddings.embed_query(query)
#print(f"Embedding Consistency: {embedding1 == embedding2}")
#print(response)

'''
import time

# Set the cache for LangChain to use
set_llm_cache(semantic_cache)


# Function to test semantic cache
def test_semantic_cache(prompt):
    start_time = time.time()
    result = llm.invoke(prompt)
    end_time = time.time()
    return result, end_time - start_time


# Original query
original_prompt = "What is the capital of France?"
result1, time1 = test_semantic_cache(original_prompt)
print(
    f"Original query:\nPrompt: {original_prompt}\nResult: {result1}\nTime: {time1:.2f} seconds\n"
)

# Semantically similar query
similar_prompt = "Can you tell me the capital city of France?"
result2, time2 = test_semantic_cache(similar_prompt)
print(
    f"Similar query:\nPrompt: {similar_prompt}\nResult: {result2}\nTime: {time2:.2f} seconds\n"
)

print(f"Speed improvement: {time1 / time2:.2f}x faster")

# Clear the semantic cache
semantic_cache.clear()
print("Semantic cache cleared")
'''