import torch
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    Trainer,
    TrainingArguments,
    DataCollatorWithPadding,
    BitsAndBytesConfig
)
from peft import LoraConfig, get_peft_model
from datasets import Dataset
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score

df = pd.read_csv("./train_data.csv")

label_list = sorted(df["intent"].unique())
label2id = {l: i for i, l in enumerate(label_list)}
id2label = {i: l for l, i in label2id.items()}
df["labels"] = df["intent"].map(label2id)

train_df, val_df = train_test_split(
    df, test_size=0.2, stratify=df["labels"], random_state=42
)

train_ds = Dataset.from_pandas(train_df.reset_index(drop=True))
val_ds = Dataset.from_pandas(val_df.reset_index(drop=True))

bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_use_double_quant=True,
    bnb_4bit_compute_dtype=torch.float16
)

model_name = "distilbert-base-uncased"
tokenizer = AutoTokenizer.from_pretrained(model_name)

model = AutoModelForSequenceClassification.from_pretrained(
    model_name,
    num_labels=len(label_list),
    quantization_config=bnb_config,
    device_map="auto"
)

lora_config = LoraConfig(
    r=8,
    lora_alpha=16,
    target_modules=["q_lin", "v_lin"],
    lora_dropout=0.1,
    bias="none",
    task_type="SEQ_CLS"
)

model = get_peft_model(model, lora_config)
model.print_trainable_parameters()

def tokenize(batch):
    return tokenizer(batch["text"], truncation=True)

train_ds = train_ds.map(tokenize, batched=True).remove_columns(["text", "intent"])
val_ds = val_ds.map(tokenize, batched=True).remove_columns(["text", "intent"])

data_collator = DataCollatorWithPadding(tokenizer)

def compute_metrics(p):
    preds = np.argmax(p.predictions, axis=-1)
    return {
        "accuracy": accuracy_score(p.label_ids, preds),
        "f1_macro": f1_score(p.label_ids, preds, average="macro")
    }

args = TrainingArguments(
    output_dir="./distilbert-qlora",
    num_train_epochs=5,
    per_device_train_batch_size=16,
    per_device_eval_batch_size=16,
    evaluation_strategy="epoch",
    save_strategy="epoch",
    load_best_model_at_end=True,
    metric_for_best_model="f1_macro",
    report_to="none"
)

trainer = Trainer(
    model=model,
    args=args,
    train_dataset=train_ds,
    eval_dataset=val_ds,
    tokenizer=tokenizer,
    data_collator=data_collator,
    compute_metrics=compute_metrics
)

trainer.train()
trainer.save_model("./distilbert-qlora")
tokenizer.save_pretrained("./distilbert-qlora")
