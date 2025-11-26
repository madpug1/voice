from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch

def create_sample_pdf():
    """Create a sample knowledge base PDF for testing."""
    filename = "sample_knowledge.pdf"
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter
    
    # Title
    c.setFont("Helvetica-Bold", 24)
    c.drawString(1*inch, height - 1*inch, "Sample Knowledge Base")
    
    # Content
    c.setFont("Helvetica", 12)
    y = height - 1.5*inch
    
    content = [
        "This is a sample document for testing the RAG application.",
        "",
        "Topic 1: Artificial Intelligence",
        "Artificial Intelligence (AI) is the simulation of human intelligence",
        "in machines designed to think and learn like humans. AI systems can",
        "perform tasks such as visual perception, speech recognition, decision-making,",
        "and language translation.",
        "",
        "Topic 2: Machine Learning",
        "Machine Learning is a subset of AI that enables systems to learn and",
        "improve from experience without being explicitly programmed. It focuses",
        "on developing computer programs that can access data and use it to learn.",
        "",
        "Topic 3: Natural Language Processing",
        "Natural Language Processing (NLP) is a branch of AI that helps computers",
        "understand, interpret, and manipulate human language. NLP draws from many",
        "disciplines including computer science and computational linguistics.",
        "",
        "Topic 4: Computer Vision",
        "Computer Vision is a field of AI that trains computers to interpret and",
        "understand the visual world. Using digital images from cameras and videos",
        "and deep learning models, machines can accurately identify and classify objects.",
        "",
        "This document contains information about various AI topics that can be",
        "queried through the RAG system. The system will retrieve relevant chunks",
        "and generate appropriate responses based on this knowledge base.",
    ]
    
    for line in content:
        c.drawString(1*inch, y, line)
        y -= 0.25*inch
        if y < 1*inch:
            c.showPage()
            c.setFont("Helvetica", 12)
            y = height - 1*inch
    
    c.save()
    print(f"Created {filename}")

if __name__ == "__main__":
    try:
        create_sample_pdf()
    except ImportError:
        print("reportlab not installed. Creating text-based PDF instead...")
        # Fallback: create a simple text file that can be manually converted
        with open("sample_knowledge.txt", "w") as f:
            f.write("""Sample Knowledge Base

This is a sample document for testing the RAG application.

Topic 1: Artificial Intelligence
Artificial Intelligence (AI) is the simulation of human intelligence in machines designed to think and learn like humans. AI systems can perform tasks such as visual perception, speech recognition, decision-making, and language translation.

Topic 2: Machine Learning
Machine Learning is a subset of AI that enables systems to learn and improve from experience without being explicitly programmed. It focuses on developing computer programs that can access data and use it to learn.

Topic 3: Natural Language Processing
Natural Language Processing (NLP) is a branch of AI that helps computers understand, interpret, and manipulate human language. NLP draws from many disciplines including computer science and computational linguistics.

Topic 4: Computer Vision
Computer Vision is a field of AI that trains computers to interpret and understand the visual world. Using digital images from cameras and videos and deep learning models, machines can accurately identify and classify objects.

This document contains information about various AI topics that can be queried through the RAG system. The system will retrieve relevant chunks and generate appropriate responses based on this knowledge base.
""")
        print("Created sample_knowledge.txt - Please convert to PDF manually or install reportlab")
