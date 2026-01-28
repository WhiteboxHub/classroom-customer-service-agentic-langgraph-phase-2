from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    Trainer,
    TrainingArguments,
    DataCollatorWithPadding
)
from datasets import Dataset
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score

# -----------------------------
# 1. Load CSV
# -----------------------------
df = pd.read_csv("./train_data.csv")

# -----------------------------
# 2. Convert intent -> label ids
# -----------------------------
label_list = sorted(df["intent"].unique())  # e.g. ['billing','claims','scheduling','triage']
label2id = {label: i for i, label in enumerate(label_list)}
id2label = {i: label for label, i in label2id.items()}

df["labels"] = df["intent"].map(label2id)

# -----------------------------
# 3. Split train/val
# -----------------------------
train_df, val_df = train_test_split(
    df, test_size=0.2, random_state=42, stratify=df["labels"]
)

train_dataset = Dataset.from_pandas(train_df.reset_index(drop=True))
val_dataset = Dataset.from_pandas(val_df.reset_index(drop=True))

# -----------------------------
# 4. Load Tokenizer + Model
# -----------------------------
model_name = "distilbert-base-uncased"
tokenizer = AutoTokenizer.from_pretrained(model_name)

model = AutoModelForSequenceClassification.from_pretrained(
    model_name,
    num_labels=len(label_list),
    id2label=id2label,
    label2id=label2id
)

# -----------------------------
# 5. Tokenization
# -----------------------------
def tokenize(batch):
    return tokenizer(batch["text"], truncation=True)

train_dataset = train_dataset.map(tokenize, batched=True)
val_dataset = val_dataset.map(tokenize, batched=True)

# Remove non-needed columns
train_dataset = train_dataset.remove_columns(["text", "intent"])
val_dataset = val_dataset.remove_columns(["text", "intent"])

# -----------------------------
# 6. Data collator (dynamic padding)
# -----------------------------
data_collator = DataCollatorWithPadding(tokenizer=tokenizer)

# -----------------------------
# 7. Metrics
# -----------------------------
def compute_metrics(eval_pred):
    logits, labels = eval_pred
    preds = np.argmax(logits, axis=-1)
    return {
        "accuracy": accuracy_score(labels, preds),
        "f1_macro": f1_score(labels, preds, average="macro")
    }

# -----------------------------
# 8. Training arguments
# -----------------------------
training_args = TrainingArguments(
    output_dir="./distilbert-intent",
    num_train_epochs=5,
    per_device_train_batch_size=16,
    per_device_eval_batch_size=16,
    eval_strategy="epoch",
    save_strategy="epoch",
    logging_strategy="steps",
    logging_steps=20,
    learning_rate=2e-5,
    weight_decay=0.01,
    load_best_model_at_end=True,
    metric_for_best_model="f1_macro",
    report_to="none"
)

# -----------------------------
# 9. Trainer
# -----------------------------
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=val_dataset,
    tokenizer=tokenizer,
    data_collator=data_collator,
    compute_metrics=compute_metrics
)

trainer.train()

# -----------------------------
# 10. Save model + tokenizer
# -----------------------------
trainer.save_model("./distilbert-intent")
tokenizer.save_pretrained("./distilbert-intent")

print("Training complete! Model saved to ./distilbert-intent")


