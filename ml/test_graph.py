import requests
import random
import time
from typing import List, Dict

def generate_random_node(existing_nodes: List[str]) -> Dict:
    # Generate random node ID
    node_id = f"node_{random.randint(1000, 9999)}"
    
    # Generate random text description
    actions = ["processes", "analyzes", "transforms", "validates", "filters", "aggregates"]
    data_types = ["data", "text", "numbers", "documents", "records", "files"]
    text = f"This node {random.choice(actions)} {random.choice(data_types)}"
    
    # Randomly select parent nodes (0 to 3 parents)
    num_parents = random.randint(0, min(3, len(existing_nodes)))
    parent_nodes = []
    if num_parents > 0 and existing_nodes:
        parent_nodes = random.sample(existing_nodes, num_parents)
    
    return {
        "current_node": node_id,
        "text": text,
        "parent_node": "$$".join(parent_nodes) if parent_nodes else ""
    }

def main():
    base_url = "http://127.0.0.1:8000"
    existing_nodes = []

    print("Starting to generate and send nodes...")

    # Generate and send 20 nodes
    for i in range(20):
        node_data = generate_random_node(existing_nodes)
        existing_nodes.append(node_data["current_node"])
        
        try:
            response = requests.post(f"{base_url}/receive_nodes/", json=node_data)
            if response.status_code == 200:
                print(f"Successfully sent node {i+1}/20: {node_data['current_node']}")
                print(f"Parents: {node_data['parent_node'] or 'None'}")
                print(f"Text: {node_data['text']}")
                print("-" * 50)
            else:
                print(f"Error sending node {i+1}: {response.status_code}")
                print(response.json())
        except Exception as e:
            print(f"Exception while sending node {i+1}: {str(e)}")
        
        # Add a small delay between nodes to make visualization smoother
        time.sleep(0.5)

    print("\nFinished sending all nodes!")

if __name__ == "__main__":
    main()
