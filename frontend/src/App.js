import { useState, useEffect, useRef, useCallback } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import axios from "axios";
import { Toaster, toast } from "sonner";
import { 
  Upload, 
  FileText, 
  MessageSquare, 
  Plus, 
  Trash2, 
  Send, 
  Library, 
  File,
  X,
  ChevronRight,
  BookOpen,
  Loader2,
  FileType,
  Clock
} from "lucide-react";
import { Button } from "./components/ui/button";
import { ScrollArea } from "./components/ui/scroll-area";
import { Separator } from "./components/ui/separator";
import { Progress } from "./components/ui/progress";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Sidebar Component
const Sidebar = ({ 
  conversations, 
  documents, 
  activeConversation, 
  onSelectConversation, 
  onNewConversation, 
  onDeleteConversation,
  onUploadClick,
  onDeleteDocument,
  isLoading 
}) => {
  const [showDocuments, setShowDocuments] = useState(false);

  return (
    <div className="w-72 h-screen flex flex-col" style={{ backgroundColor: '#121212' }}>
      {/* Header */}
      <div className="p-6 border-b border-stone-800">
        <div className="flex items-center gap-3">
          <Library className="w-6 h-6 text-orange-600" strokeWidth={1.5} />
          <h1 className="text-xl font-bold text-stone-100" style={{ fontFamily: 'Libre Baskerville, serif' }}>
            Cognitive Library
          </h1>
        </div>
      </div>

      {/* Toggle Buttons */}
      <div className="p-4 flex gap-2">
        <button
          onClick={() => setShowDocuments(false)}
          className={`flex-1 py-2 px-3 text-xs font-medium uppercase tracking-wider transition-colors ${
            !showDocuments 
              ? 'bg-orange-600 text-white' 
              : 'bg-stone-800 text-stone-400 hover:text-stone-200'
          }`}
          data-testid="show-conversations-btn"
        >
          Chats
        </button>
        <button
          onClick={() => setShowDocuments(true)}
          className={`flex-1 py-2 px-3 text-xs font-medium uppercase tracking-wider transition-colors ${
            showDocuments 
              ? 'bg-orange-600 text-white' 
              : 'bg-stone-800 text-stone-400 hover:text-stone-200'
          }`}
          data-testid="show-documents-btn"
        >
          Documents
        </button>
      </div>

      {/* Content */}
      <ScrollArea className="flex-1 px-4">
        {!showDocuments ? (
          /* Conversations List */
          <div className="space-y-2 pb-4">
            {conversations.map((conv, index) => (
              <div
                key={conv.id}
                className={`group flex items-center justify-between p-3 cursor-pointer transition-colors animate-slideIn ${
                  activeConversation?.id === conv.id 
                    ? 'bg-stone-800 text-stone-100' 
                    : 'text-stone-400 hover:bg-stone-800/50 hover:text-stone-200'
                }`}
                style={{ animationDelay: `${index * 50}ms` }}
                onClick={() => onSelectConversation(conv)}
                data-testid={`conversation-item-${conv.id}`}
              >
                <div className="flex items-center gap-3 min-w-0">
                  <MessageSquare className="w-4 h-4 flex-shrink-0" strokeWidth={1.5} />
                  <span className="text-sm truncate">{conv.title}</span>
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onDeleteConversation(conv.id);
                  }}
                  className="opacity-0 group-hover:opacity-100 p-1 hover:bg-stone-700 transition-opacity"
                  data-testid={`delete-conversation-${conv.id}`}
                >
                  <Trash2 className="w-3.5 h-3.5 text-stone-500 hover:text-red-400" />
                </button>
              </div>
            ))}
            {conversations.length === 0 && (
              <div className="text-stone-500 text-sm text-center py-8">
                No conversations yet
              </div>
            )}
          </div>
        ) : (
          /* Documents List */
          <div className="space-y-2 pb-4">
            {documents.map((doc, index) => (
              <div
                key={doc.id}
                className="group flex items-center justify-between p-3 bg-stone-800/30 hover:bg-stone-800/50 transition-colors animate-slideIn"
                style={{ animationDelay: `${index * 50}ms` }}
                data-testid={`document-item-${doc.id}`}
              >
                <div className="flex items-center gap-3 min-w-0">
                  <FileText className="w-4 h-4 text-orange-500 flex-shrink-0" strokeWidth={1.5} />
                  <div className="min-w-0">
                    <span className="text-sm text-stone-200 truncate block">{doc.filename}</span>
                    <span className="text-xs text-stone-500">{doc.chunk_count} chunks</span>
                  </div>
                </div>
                <button
                  onClick={() => onDeleteDocument(doc.id)}
                  className="opacity-0 group-hover:opacity-100 p-1 hover:bg-stone-700 transition-opacity"
                  data-testid={`delete-document-${doc.id}`}
                >
                  <Trash2 className="w-3.5 h-3.5 text-stone-500 hover:text-red-400" />
                </button>
              </div>
            ))}
            {documents.length === 0 && (
              <div className="text-stone-500 text-sm text-center py-8">
                No documents uploaded
              </div>
            )}
          </div>
        )}
      </ScrollArea>

      {/* Action Buttons */}
      <div className="p-4 border-t border-stone-800 space-y-2">
        {!showDocuments ? (
          <Button
            onClick={onNewConversation}
            disabled={isLoading}
            className="w-full bg-orange-600 hover:bg-orange-700 text-white rounded-none uppercase text-xs tracking-wider py-3"
            data-testid="new-conversation-btn"
          >
            <Plus className="w-4 h-4 mr-2" />
            New Conversation
          </Button>
        ) : (
          <Button
            onClick={onUploadClick}
            disabled={isLoading}
            className="w-full bg-orange-600 hover:bg-orange-700 text-white rounded-none uppercase text-xs tracking-wider py-3"
            data-testid="upload-document-btn"
          >
            <Upload className="w-4 h-4 mr-2" />
            Upload Document
          </Button>
        )}
      </div>
    </div>
  );
};

// Chat Message Component
const ChatMessage = ({ message, index }) => {
  const isUser = message.role === 'user';
  
  return (
    <div 
      className={`message-enter ${isUser ? 'flex justify-end' : ''}`}
      style={{ animationDelay: `${index * 100}ms` }}
      data-testid={`chat-message-${message.id}`}
    >
      {isUser ? (
        <div className="bg-stone-100 text-stone-800 rounded-tr-lg rounded-bl-lg p-4 max-w-[80%]">
          <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.content}</p>
        </div>
      ) : (
        <div className="border-l-2 border-orange-600 pl-4 py-2 max-w-[90%]">
          <p className="text-stone-900 leading-relaxed whitespace-pre-wrap">{message.content}</p>
          
          {/* Sources */}
          {message.sources && message.sources.length > 0 && (
            <div className="mt-4 space-y-2">
              <p className="text-xs font-medium uppercase tracking-wider text-stone-500">Sources</p>
              {message.sources.map((source, i) => (
                <div 
                  key={i} 
                  className="bg-stone-50 border border-stone-200 p-3"
                  data-testid={`source-citation-${i}`}
                >
                  <div className="flex items-center gap-2 mb-1">
                    <FileType className="w-3.5 h-3.5 text-orange-600" />
                    <span className="text-xs font-mono text-stone-500">{source.filename}</span>
                  </div>
                  <p className="text-xs text-stone-600 line-clamp-2">{source.content}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// Upload Modal Component
const UploadModal = ({ isOpen, onClose, onUpload, isUploading, uploadProgress }) => {
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef(null);

  const handleDragOver = useCallback((e) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    setIsDragging(false);
    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      onUpload(files[0]);
    }
  }, [onUpload]);

  const handleFileSelect = (e) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      onUpload(files[0]);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 animate-fadeIn">
      <div className="bg-white w-full max-w-lg mx-4 shadow-lg" data-testid="upload-modal">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-stone-200">
          <h2 className="text-xl font-bold" style={{ fontFamily: 'Libre Baskerville, serif' }}>
            Upload Document
          </h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-stone-100 transition-colors"
            data-testid="close-upload-modal"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`border-2 border-dashed p-12 text-center cursor-pointer transition-colors ${
              isDragging 
                ? 'border-orange-600 bg-orange-50' 
                : 'border-stone-300 hover:border-stone-400'
            }`}
            data-testid="upload-dropzone"
          >
            {isUploading ? (
              <div className="space-y-4">
                <Loader2 className="w-12 h-12 mx-auto text-orange-600 animate-spin" />
                <p className="text-sm text-stone-600">Processing document...</p>
                <Progress value={uploadProgress} className="w-48 mx-auto" />
              </div>
            ) : (
              <>
                <Upload className="w-12 h-12 mx-auto text-stone-400 mb-4" strokeWidth={1.5} />
                <p className="text-stone-600 mb-2">Drag and drop a file here, or click to browse</p>
                <p className="text-xs text-stone-400">Supported: PDF, TXT, MD, DOCX</p>
              </>
            )}
            <input
              ref={fileInputRef}
              type="file"
              className="hidden"
              accept=".pdf,.txt,.md,.docx"
              onChange={handleFileSelect}
              data-testid="file-input"
            />
          </div>
        </div>
      </div>
    </div>
  );
};

// Main Chat Interface
const ChatInterface = ({ conversation, messages, onSendMessage, isLoading }) => {
  const [inputValue, setInputValue] = useState("");
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    inputRef.current?.focus();
  }, [conversation?.id]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (inputValue.trim() && !isLoading) {
      onSendMessage(inputValue);
      setInputValue("");
    }
  };

  if (!conversation) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center p-8 bg-[#FAFAF9]">
        <div className="text-center max-w-md animate-fadeIn">
          <BookOpen className="w-16 h-16 mx-auto text-stone-300 mb-6" strokeWidth={1} />
          <h2 className="text-3xl font-bold mb-4 text-stone-800" style={{ fontFamily: 'Libre Baskerville, serif' }}>
            Welcome to Cognitive Library
          </h2>
          <p className="text-stone-500 leading-relaxed mb-8">
            Upload your documents and start asking questions. Your AI assistant will help you find answers with precise citations.
          </p>
          <div className="flex items-center justify-center gap-8 text-sm text-stone-400">
            <div className="flex items-center gap-2">
              <FileText className="w-4 h-4" />
              <span>Upload docs</span>
            </div>
            <ChevronRight className="w-4 h-4" />
            <div className="flex items-center gap-2">
              <MessageSquare className="w-4 h-4" />
              <span>Ask questions</span>
            </div>
            <ChevronRight className="w-4 h-4" />
            <div className="flex items-center gap-2">
              <BookOpen className="w-4 h-4" />
              <span>Get answers</span>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col h-screen bg-[#FAFAF9]">
      {/* Chat Header */}
      <div className="border-b border-stone-200 p-6">
        <h2 className="text-lg font-medium text-stone-800" style={{ fontFamily: 'Libre Baskerville, serif' }}>
          {conversation.title}
        </h2>
        <div className="flex items-center gap-2 mt-1 text-xs text-stone-400">
          <Clock className="w-3 h-3" />
          <span>{new Date(conversation.created_at).toLocaleDateString()}</span>
        </div>
      </div>

      {/* Messages Area */}
      <ScrollArea className="flex-1 p-6">
        <div className="max-w-3xl mx-auto space-y-6">
          {messages.length === 0 ? (
            <div className="text-center py-16 animate-fadeIn">
              <MessageSquare className="w-10 h-10 mx-auto text-stone-300 mb-4" strokeWidth={1} />
              <p className="text-stone-500">Start a conversation by sending a message</p>
            </div>
          ) : (
            messages.map((msg, index) => (
              <ChatMessage key={msg.id} message={msg} index={index} />
            ))
          )}
          
          {/* Typing Indicator */}
          {isLoading && (
            <div className="border-l-2 border-orange-600 pl-4 py-2 animate-fadeIn">
              <div className="flex items-center gap-1.5">
                <div className="w-2 h-2 bg-orange-600 rounded-full typing-dot" />
                <div className="w-2 h-2 bg-orange-600 rounded-full typing-dot" />
                <div className="w-2 h-2 bg-orange-600 rounded-full typing-dot" />
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>
      </ScrollArea>

      {/* Input Area */}
      <div className="border-t border-stone-200 p-6">
        <form onSubmit={handleSubmit} className="max-w-3xl mx-auto">
          <div className="flex items-end gap-4">
            <div className="flex-1 relative">
              <textarea
                ref={inputRef}
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSubmit(e);
                  }
                }}
                placeholder="Ask a question about your documents..."
                className="w-full border-x-0 border-t-0 border-b-2 border-stone-200 bg-transparent px-0 py-3 focus:border-orange-600 focus:ring-0 placeholder:text-stone-400 resize-none outline-none text-stone-800"
                rows={1}
                disabled={isLoading}
                data-testid="chat-input"
              />
            </div>
            <Button
              type="submit"
              disabled={!inputValue.trim() || isLoading}
              className="bg-orange-600 hover:bg-orange-700 text-white rounded-none px-6 py-3 disabled:opacity-50"
              data-testid="send-message-btn"
            >
              <Send className="w-4 h-4" />
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};

// Main App Component
const Home = () => {
  const [conversations, setConversations] = useState([]);
  const [documents, setDocuments] = useState([]);
  const [activeConversation, setActiveConversation] = useState(null);
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);

  // Fetch conversations and documents on mount
  useEffect(() => {
    fetchConversations();
    fetchDocuments();
  }, []);

  const fetchConversations = async () => {
    try {
      const response = await axios.get(`${API}/conversations`);
      setConversations(response.data);
    } catch (e) {
      console.error("Error fetching conversations:", e);
      toast.error("Failed to load conversations");
    }
  };

  const fetchDocuments = async () => {
    try {
      const response = await axios.get(`${API}/documents`);
      setDocuments(response.data);
    } catch (e) {
      console.error("Error fetching documents:", e);
      toast.error("Failed to load documents");
    }
  };

  const fetchMessages = async (conversationId) => {
    try {
      const response = await axios.get(`${API}/conversations/${conversationId}/messages`);
      setMessages(response.data);
    } catch (e) {
      console.error("Error fetching messages:", e);
      toast.error("Failed to load messages");
    }
  };

  const handleNewConversation = async () => {
    try {
      setIsLoading(true);
      const response = await axios.post(`${API}/conversations`);
      const newConv = response.data;
      setConversations([newConv, ...conversations]);
      setActiveConversation(newConv);
      setMessages([]);
      toast.success("New conversation created");
    } catch (e) {
      console.error("Error creating conversation:", e);
      toast.error("Failed to create conversation");
    } finally {
      setIsLoading(false);
    }
  };

  const handleSelectConversation = async (conv) => {
    setActiveConversation(conv);
    await fetchMessages(conv.id);
  };

  const handleDeleteConversation = async (convId) => {
    try {
      await axios.delete(`${API}/conversations/${convId}`);
      setConversations(conversations.filter(c => c.id !== convId));
      if (activeConversation?.id === convId) {
        setActiveConversation(null);
        setMessages([]);
      }
      toast.success("Conversation deleted");
    } catch (e) {
      console.error("Error deleting conversation:", e);
      toast.error("Failed to delete conversation");
    }
  };

  const handleUpload = async (file) => {
    setIsUploading(true);
    setUploadProgress(0);
    
    const formData = new FormData();
    formData.append('file', file);

    try {
      // Simulate progress
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => Math.min(prev + 10, 90));
      }, 200);

      const response = await axios.post(`${API}/documents/upload`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      clearInterval(progressInterval);
      setUploadProgress(100);
      
      setDocuments([response.data, ...documents]);
      toast.success(`${file.name} uploaded successfully`);
      
      setTimeout(() => {
        setShowUploadModal(false);
        setIsUploading(false);
        setUploadProgress(0);
      }, 500);
    } catch (e) {
      console.error("Error uploading document:", e);
      toast.error(e.response?.data?.detail || "Failed to upload document");
      setIsUploading(false);
      setUploadProgress(0);
    }
  };

  const handleDeleteDocument = async (docId) => {
    try {
      await axios.delete(`${API}/documents/${docId}`);
      setDocuments(documents.filter(d => d.id !== docId));
      toast.success("Document deleted");
    } catch (e) {
      console.error("Error deleting document:", e);
      toast.error("Failed to delete document");
    }
  };

  const handleSendMessage = async (message) => {
    if (!activeConversation) return;

    // Add optimistic user message
    const tempUserMsg = {
      id: 'temp-' + Date.now(),
      conversation_id: activeConversation.id,
      role: 'user',
      content: message,
      sources: [],
      created_at: new Date().toISOString()
    };
    setMessages([...messages, tempUserMsg]);
    setIsLoading(true);

    try {
      const response = await axios.post(`${API}/chat`, {
        conversation_id: activeConversation.id,
        message: message
      });

      // Update messages with actual response
      setMessages(prev => {
        const filtered = prev.filter(m => m.id !== tempUserMsg.id);
        return [...filtered, 
          { ...tempUserMsg, id: response.data.message.id.replace('temp-', '') },
          response.data.message
        ];
      });

      // Update conversation title in list
      setConversations(prev => prev.map(c => 
        c.id === activeConversation.id 
          ? { ...c, title: message.slice(0, 50) + (message.length > 50 ? '...' : '') }
          : c
      ));
    } catch (e) {
      console.error("Error sending message:", e);
      toast.error("Failed to send message");
      // Remove optimistic message on error
      setMessages(prev => prev.filter(m => m.id !== tempUserMsg.id));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex h-screen overflow-hidden" data-testid="main-app">
      <Sidebar
        conversations={conversations}
        documents={documents}
        activeConversation={activeConversation}
        onSelectConversation={handleSelectConversation}
        onNewConversation={handleNewConversation}
        onDeleteConversation={handleDeleteConversation}
        onUploadClick={() => setShowUploadModal(true)}
        onDeleteDocument={handleDeleteDocument}
        isLoading={isLoading}
      />
      
      <ChatInterface
        conversation={activeConversation}
        messages={messages}
        onSendMessage={handleSendMessage}
        isLoading={isLoading}
      />

      <UploadModal
        isOpen={showUploadModal}
        onClose={() => setShowUploadModal(false)}
        onUpload={handleUpload}
        isUploading={isUploading}
        uploadProgress={uploadProgress}
      />

      <Toaster position="bottom-right" richColors />
    </div>
  );
};

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Home />} />
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;
