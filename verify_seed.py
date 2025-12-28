import mongoengine
from app import QuizQuestion, MONGODB_DB, MONGODB_URI

def verify():
    mongoengine.connect(db=MONGODB_DB, host=MONGODB_URI)
    
    difficulties = ['beginner', 'intermediate', 'advanced']
    for diff in difficulties:
        count = QuizQuestion.objects(difficulty=diff, is_active=True).count()
        print(f"Difficulty {diff}: {count} questions")

if __name__ == "__main__":
    verify()
