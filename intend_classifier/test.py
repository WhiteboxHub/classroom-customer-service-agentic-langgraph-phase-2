from transformers import pipeline

print("Step 1: Starting...")

print("Step 2: Loading pipeline...")
clf = pipeline(
    "text-classification",
    model="./distilbert-intent",
    tokenizer="./distilbert-intent",
    device=-1   
)

# clf = pipeline(
#     "text-classification",
#     model="./distilbert-lora",
#     tokenizer="./distilbert-lora",
#     device=-1   
# )

print("Step 3: Pipeline loaded ")

print("Step 4: Predicting...")
print(clf("why is my claims status pending"))

print("okhh  Done")
