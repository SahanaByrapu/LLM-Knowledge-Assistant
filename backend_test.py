import requests
import sys
import os
import tempfile
from datetime import datetime
import time
import json

class KnowledgeAssistantTester:
    def __init__(self, base_url="https://mcp-knowledge-base.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name, success, response_data=None, error=None):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
        
        result = {
            "test": name,
            "success": success,
            "response": response_data,
            "error": str(error) if error else None,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status} - {name}")
        if error:
            print(f"   Error: {error}")
        return success

    def run_test(self, name, method, endpoint, expected_status, data=None, files=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'} if not files else {}
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method == 'POST':
                if files:
                    response = requests.post(url, files=files, timeout=30)
                else:
                    response = requests.post(url, json=data, headers=headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=30)

            success = response.status_code == expected_status
            response_data = response.json() if response.content else {}
            
            return self.log_test(name, success, response_data, 
                               None if success else f"Expected {expected_status}, got {response.status_code}")

        except Exception as e:
            return self.log_test(name, False, None, str(e))

    def test_api_status(self):
        """Test API root endpoint"""
        return self.run_test("API Status Check", "GET", "", 200)

    def test_document_upload_pdf(self):
        """Test PDF document upload"""
        # Create a simple text file as PDF for testing
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            tmp.write(b'%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]>>endobj\nxref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \ntrailer<</Size 4/Root 1 0 R>>\nstartxref\n174\n%%EOF')
            tmp.flush()
            
            with open(tmp.name, 'rb') as f:
                files = {'file': ('test_document.pdf', f, 'application/pdf')}
                success = self.run_test("Document Upload - PDF", "POST", "documents/upload", 200, files=files)
            
            os.unlink(tmp.name)
            return success

    def test_document_upload_txt(self):
        """Test TXT document upload"""
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as tmp:
            tmp.write(b'This is a test document for the Knowledge Assistant RAG system. It contains sample text that can be used for testing search and retrieval functionality.')
            tmp.flush()
            
            with open(tmp.name, 'rb') as f:
                files = {'file': ('test_document.txt', f, 'text/plain')}
                success = self.run_test("Document Upload - TXT", "POST", "documents/upload", 200, files=files)
            
            os.unlink(tmp.name)
            return success

    def test_get_documents(self):
        """Test getting all documents"""
        return self.run_test("Get Documents", "GET", "documents", 200)

    def test_create_conversation(self):
        """Test creating a new conversation"""
        return self.run_test("Create Conversation", "POST", "conversations", 200)

    def test_get_conversations(self):
        """Test getting all conversations"""
        return self.run_test("Get Conversations", "GET", "conversations", 200)

    def test_chat_flow(self):
        """Test complete chat flow with RAG"""
        print("\n🔄 Testing complete chat flow...")
        
        # First create a conversation
        try:
            response = requests.post(f"{self.api_url}/conversations", timeout=30)
            if response.status_code != 200:
                return self.log_test("Chat Flow - Create Conversation", False, None, f"Failed to create conversation: {response.status_code}")
            
            conv_data = response.json()
            conv_id = conv_data['id']
            print(f"   Created conversation: {conv_id}")
            
            # Send a chat message
            chat_data = {
                "conversation_id": conv_id,
                "message": "What is in the uploaded documents?"
            }
            
            response = requests.post(f"{self.api_url}/chat", json=chat_data, timeout=60)
            if response.status_code != 200:
                return self.log_test("Chat Flow - Send Message", False, None, f"Failed to send message: {response.status_code}")
            
            response_data = response.json()
            
            # Check if response has expected structure
            if 'message' in response_data and 'sources' in response_data:
                print(f"   AI Response: {response_data['message']['content'][:100]}...")
                print(f"   Sources found: {len(response_data['sources'])}")
                return self.log_test("Chat Flow - Complete", True, response_data)
            else:
                return self.log_test("Chat Flow - Complete", False, response_data, "Invalid response structure")
                
        except Exception as e:
            return self.log_test("Chat Flow - Complete", False, None, str(e))

    def test_get_messages(self, conv_id=None):
        """Test getting messages for a conversation"""
        if not conv_id:
            # Try to get an existing conversation first
            try:
                response = requests.get(f"{self.api_url}/conversations", timeout=30)
                if response.status_code == 200:
                    conversations = response.json()
                    if conversations:
                        conv_id = conversations[0]['id']
                    else:
                        return self.log_test("Get Messages", False, None, "No conversations available")
                else:
                    return self.log_test("Get Messages", False, None, "Could not fetch conversations")
            except Exception as e:
                return self.log_test("Get Messages", False, None, str(e))
        
        return self.run_test("Get Messages", "GET", f"conversations/{conv_id}/messages", 200)

    def test_delete_operations(self):
        """Test delete operations for conversations and documents"""
        print("\n🗑️  Testing delete operations...")
        
        # Get existing items to delete
        try:
            # Test deleting a conversation
            conv_response = requests.get(f"{self.api_url}/conversations", timeout=30)
            if conv_response.status_code == 200:
                conversations = conv_response.json()
                if conversations:
                    conv_id = conversations[0]['id']
                    delete_success = self.run_test("Delete Conversation", "DELETE", f"conversations/{conv_id}", 200)
                else:
                    print("   No conversations to delete")
                    delete_success = True
            else:
                delete_success = False
            
            # Test deleting a document
            doc_response = requests.get(f"{self.api_url}/documents", timeout=30)
            if doc_response.status_code == 200:
                documents = doc_response.json()
                if documents:
                    doc_id = documents[0]['id']
                    delete_doc_success = self.run_test("Delete Document", "DELETE", f"documents/{doc_id}", 200)
                else:
                    print("   No documents to delete")
                    delete_doc_success = True
            else:
                delete_doc_success = False
                
            return delete_success and delete_doc_success
            
        except Exception as e:
            return self.log_test("Delete Operations", False, None, str(e))

    def run_full_test_suite(self):
        """Run complete test suite"""
        print("🚀 Starting Knowledge Assistant RAG API Tests")
        print(f"📍 Testing endpoint: {self.base_url}")
        print("=" * 60)
        
        # Core API tests
        self.test_api_status()
        
        # Document management tests
        self.test_document_upload_txt()
        time.sleep(2)  # Wait for processing
        self.test_document_upload_pdf()
        time.sleep(2)  # Wait for processing
        self.test_get_documents()
        
        # Conversation management tests
        self.test_create_conversation()
        self.test_get_conversations()
        
        # Chat and RAG functionality
        self.test_chat_flow()
        time.sleep(3)  # Wait for chat completion
        self.test_get_messages()
        
        # Cleanup tests
        self.test_delete_operations()
        
        # Print summary
        print("=" * 60)
        print(f"📊 Test Summary: {self.tests_passed}/{self.tests_run} tests passed")
        print(f"📈 Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed!")
            return True
        else:
            print("⚠️  Some tests failed - check logs above")
            return False

def main():
    tester = KnowledgeAssistantTester()
    success = tester.run_full_test_suite()
    
    # Save detailed results
    with open('/tmp/backend_test_results.json', 'w') as f:
        json.dump(tester.test_results, f, indent=2)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())