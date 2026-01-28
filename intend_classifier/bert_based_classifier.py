from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import torch
from typing import Tuple

class DistilBERTIntentClassifier:
    def __init__(self, model_name="distilbert-base-uncased"):
        # Load fine-tuned model OR start with base + classification head
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(
            model_name, 
            num_labels=4,  # claims, billing, scheduling, triage
            ignore_mismatched_sizes=True
        )
        self.intent_labels = ["billing", "claims", "scheduling", "triage"]
    
    def predict(self, text: str) -> Tuple[str, float]:
        inputs = self.tokenizer(
            text, 
            return_tensors="pt",
            max_length=128,
            truncation=True,
            padding=True
        )
        
        with torch.no_grad():
            outputs = self.model(**inputs)
            probs = torch.softmax(outputs.logits, dim=-1)
            confidence, pred_idx = torch.max(probs, dim=-1)
        
        intent = self.intent_labels[pred_idx]
        return intent, confidence.item()
