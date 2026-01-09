import torch
import numpy as np
from transformers import AutoTokenizer, AutoModel
from sklearn.metrics.pairwise import cosine_similarity


class DistilBertIntentClassifier:
    """
    Lightweight intent classifier using DistilBERT embeddings + cosine similarity
    """

    def __init__(self):
        self.tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased")
        self.model = AutoModel.from_pretrained("distilbert-base-uncased")
        self.model.eval()

        # Intent prototypes (VERY IMPORTANT)
        self.intent_texts = {
            "claims": [
                "check my claim status",
                "claim denied",
                "insurance claim",
                "claim reimbursement"
            ],
            "billing": [
                "billing issue",
                "invoice problem",
                "payment due",
                "charged incorrectly"
            ],
            "scheduling": [
                "book appointment",
                "schedule a visit",
                "reschedule appointment",
                "cancel appointment"
            ]
        }

        # Precompute intent embeddings
        self.intent_embeddings = {
            intent: self._embed_texts(texts)
            for intent, texts in self.intent_texts.items()
        }

    def classify(self, query: str) -> tuple[str, float]:
        """
        Returns: (intent, confidence)
        """
        query_embedding = self._embed_texts([query])[0]

        scores = {}
        for intent, embeddings in self.intent_embeddings.items():
            sim = cosine_similarity(
                [query_embedding],
                embeddings
            ).max()
            scores[intent] = float(sim)

        best_intent = max(scores, key=scores.get)
        confidence = scores[best_intent]

        # Thresholding for safe fallback
        if confidence < 0.55:
            return "end", confidence

        return best_intent, confidence

    def _embed_texts(self, texts: list[str]) -> np.ndarray:
        with torch.no_grad():
            inputs = self.tokenizer(
                texts,
                padding=True,
                truncation=True,
                return_tensors="pt"
            )
            outputs = self.model(**inputs)
            embeddings = outputs.last_hidden_state.mean(dim=1)
            return embeddings.numpy()
