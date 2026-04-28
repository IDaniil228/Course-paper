import json

with open('csv/Full_2023_2021.jsonl', 'r', encoding='utf-8') as f:
    data = [json.loads(line) for line in f]

for d in  data:
    del d["article"]["vector_embedding"]
print(data[1])

