import os
import pickle

directory = "../temp/Cache-20-Openai-semantic/Cache/runtime_calls/__main___CustomOpenParse.__wrapped__"

files = os.listdir(directory)
files = [os.path.join(directory, file) for file in files]
files = [file for file in files if os.path.isdir(file)]
files = [os.path.join(file, os.listdir(file)[0]) for file in files]
files = [os.path.join(file, os.listdir(file)[0]) for file in files]

for file in files:
    with open(file, "rb") as f:
        res = pickle.load(f)
    for i in range(len(res)):
        res[i][1]["is_table_value"] = str(res[i][1]["is_table_value"]).lower()
    with open(file, "wb") as f:
        pickle.dump(res, f)
