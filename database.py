from pymongo import MongoClient
import os
import atexit

class MongoDBClient:
    def __init__(self, uri="mongodb://localhost:27017/", db_name="boar_system"):
        try:
            self.client = MongoClient(uri)
            self.db = self.client[db_name]
            self.detections = self.db["detections"]
            self.predictions = self.db["predictions"]
            print("[MongoDB] Connected successfully to local database.")
        except Exception as e:
            print(f"[MongoDB] Connection error: {e}")
            self.client = None

    def upsert_prediction(self, date_str: str, risk: str, probability: float):
        """Insert or replace a prediction explicitly for a given day."""
        if self.client:
            try:
                self.predictions.update_one(
                    {"date": date_str},
                    {"$set": {"date": date_str, "risk": risk, "probability": probability}},
                    upsert=True
                )
            except Exception as e:
                print(f"[MongoDB] Failed to upsert prediction: {e}")

    def find_prediction(self, date_str: str):
        """Fetch a specific daily prediction if it exists."""
        if self.client:
            return self.predictions.find_one({"date": date_str})
        return None

    def insert_detection(self, document: dict):
        """Insert a detection event containing timestamp and feature count."""
        if self.client:
            try:
                self.detections.insert_one(document)
            except Exception as e:
                print(f"[MongoDB] Failed to insert document: {e}")

    def get_collection(self, name: str):
        if self.client:
            return self.db[name]
        return None
        
    def close(self):
        if self.client:
            self.client.close()

# Global database manager
db_manager = MongoDBClient()

# Auto disconnect on exit
@atexit.register
def cleanup():
    db_manager.close()
