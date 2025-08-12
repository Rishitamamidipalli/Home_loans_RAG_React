

import os
from rag_system import HomeLoanRAGSystem

# ===== EDIT THIS PATH TO YOUR PDF FILE =====
PDF_PATH = r"Home Loan Requirements Details.pdf"  # Change this to your PDF file name/path
# ============================================

def main():
    print("=== Home Loan Document Ingestion ===")
    
    # Check if PDF file exists
    if not os.path.exists(PDF_PATH):
        print(f"❌ Error: PDF file not found: {PDF_PATH}")
        print("Please make sure the PDF file exists and update the PDF_PATH variable in this script.")
        return
    
    print(f"📄 PDF file: {PDF_PATH}")
    print(f"🔧 Initializing RAG system...")
    
    # Initialize RAG system with Qdrant Cloud
    rag_system = HomeLoanRAGSystem()
    
    if not rag_system.is_initialized():
        print("❌ Error: Failed to initialize RAG system.")
        print("Check that all required packages are installed: pip install -r requirements.txt")
        return
    
    print("✅ RAG system initialized successfully!")
    
    # Ingest the PDF
    print(f"📚 Ingesting PDF: {PDF_PATH}")
    print("This may take a few minutes...")
    
    success = rag_system.ingest_pdf(PDF_PATH)
    
    if success:
        print("✅ PDF ingested successfully!")
        
        # Show collection info
        info = rag_system.get_collection_info()
        print(f"📊 Collection info: {info}")
        
        # Test search
        print("\n🔍 Testing search functionality...")
        test_queries = [
            "What are the eligibility criteria for home loans?",
            "What documents are required?",
            "What are the interest rates?"
        ]
        
        for i, query in enumerate(test_queries, 3):
            print(f"\n{i}. Test query: {query}")
            results = rag_system.search_similar_documents(query, top_k=2)
            if results:
                print(f"   ✅ Found {len(results)} relevant documents")
                for j, result in enumerate(results):
                    print(f"      {j+1}. Score: {result['score']:.3f}")
                    print(f"         Preview: {result['content'][:100]}...")
            else:
                print("   ❌ No relevant documents found")
        
        print("\n🎉 Setup complete! Your RAG system is ready to use.")
        print("You can now run your Streamlit app: streamlit run main.py")
        
    else:
        print("❌ Failed to ingest PDF")
        print("Check the error messages above for troubleshooting.")

if __name__ == "__main__":
    main()
