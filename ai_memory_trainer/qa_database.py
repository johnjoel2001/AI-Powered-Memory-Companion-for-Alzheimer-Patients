from datetime import datetime
from dataclasses import dataclass


@dataclass
class QA:
    id: str
    question: str
    answer: str
    creation_time: datetime
    practice_times: int
    success_rate: float
    last_use_time: datetime


class QADatabase:
    def __init__(self):
        self._db = {}
        self._init_test_data()
    
    def _init_test_data(self):
        now = datetime.now()
        test_qas = [
            QA("1", "Who was having lunch with you yesterday?", "My daughter", now, 0, 0.0, now),
            QA("2", "Where were you having lunch yesterday?", "At the Italian restaurant downtown", now, 0, 0.0, now),
            QA("3", "What did you talk about with your daughter yesterday?", "Her new job promotion", now, 0, 0.0, now)
        ]
        for qa in test_qas:
            self._db[qa.id] = qa
    
    def add_qa(self, qa: QA):
        self._db[qa.id] = qa
    
    def get_qa(self, id: str) -> QA:
        return self._db.get(id)
    
    def get_all_qas(self) -> list[QA]:
        return list(self._db.values())
    
    def update_qa(self, id: str, qa: QA):
        self._db[id] = qa
    
    def delete_qa(self, id: str):
        self._db.pop(id, None)



