"""
GitHub Intelligence Agent using LangChain and RAG
"""

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import RetrievalQA
from typing import Dict, Any, List
import os
from dotenv import load_dotenv

load_dotenv()

class GitHubRAGAgent:
    """
    Advanced GitHub Analysis Agent with RAG capabilities
    """
    
    def __init__(self):
        # Initialize Groq LLM
        self.llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            temperature=0.7,
            max_tokens=2000,
            groq_api_key=os.getenv("GROQ_API_KEY")
        )
        
        # Initialize embeddings for RAG
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        
        # Text splitter for chunking documents
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        
        # Vector store (will be populated when analyzing repos)
        self.vector_store = None
        self.conversation_history = []
        
        print("✅ GitHub RAG Agent initialized with Groq LLM")
    
    def add_to_knowledge_base(self, texts: List[str], metadatas: List[Dict] = None):
        """
        Add documents to RAG knowledge base
        
        Args:
            texts: List of text documents
            metadatas: Optional metadata for each document
        """
        try:
            # Split texts into chunks
            chunks = []
            for text in texts:
                chunks.extend(self.text_splitter.split_text(text))
            
            # Create or update vector store
            if self.vector_store is None:
                self.vector_store = FAISS.from_texts(
                    chunks,
                    self.embeddings,
                    metadatas=metadatas
                )
            else:
                self.vector_store.add_texts(chunks, metadatas=metadatas)
            
            print(f"✅ Added {len(chunks)} chunks to knowledge base")
            return True
        except Exception as e:
            print(f"❌ Error adding to knowledge base: {e}")
            return False
    
    def query_with_rag(self, query: str) -> Dict[str, Any]:
        """
        Query using RAG (Retrieval-Augmented Generation)
        
        Args:
            query: User question
        
        Returns:
            Dict with answer and sources
        """
        if self.vector_store is None:
            return {
                "answer": "No knowledge base available. Please analyze a repository first.",
                "sources": []
            }
        
        try:
            # Retrieve relevant documents
            relevant_docs = self.vector_store.similarity_search(query, k=3)
            
            # Build context from retrieved documents
            context = "\n\n".join([doc.page_content for doc in relevant_docs])
            
            # Create prompt with context
            prompt = f"""Based on the following context, answer the question accurately and concisely.

Context:
{context}

Question: {query}

Answer:"""
            
            # Get response from LLM
            response = self.llm.invoke(prompt)
            
            return {
                "answer": response.content,
                "sources": [doc.page_content[:200] for doc in relevant_docs],
                "num_sources": len(relevant_docs)
            }
        
        except Exception as e:
            return {
                "answer": f"Error: {str(e)}",
                "sources": []
            }
    
    def analyze_repository(self, repo_data: Dict[str, Any]) -> str:
        """
        Analyze repository data and generate insights
        
        Args:
            repo_data: Dictionary with repository information
        
        Returns:
            AI-generated analysis
        """
        try:
            # Extract information
            repo_info = repo_data.get('info', {})
            code_stats = repo_data.get('code_stats', {})
            commits = repo_data.get('commits', [])
            contributors = repo_data.get('contributors', [])
            readme = repo_data.get('readme', '')
            
            # Build context
            context = f"""
Repository: {repo_info.get('name', 'Unknown')}
Description: {repo_info.get('description', 'No description')}
Stars: {repo_info.get('stars', 0):,}
Forks: {repo_info.get('forks', 0):,}
Primary Language: {code_stats.get('primary_language', 'Unknown')}
Open Issues: {repo_info.get('open_issues', 0)}
Total Contributors: {len(contributors)}
Recent Commits: {len(commits)}

Language Distribution:
{self._format_languages(code_stats.get('languages', {}))}

Top Contributors:
{self._format_contributors(contributors[:5])}

README Preview:
{readme[:500]}
            """
            
            # Add to RAG knowledge base
            documents = [
                f"Repository: {repo_info.get('name')}. {repo_info.get('description', '')}",
                f"README: {readme}",
                f"Code Stats: {str(code_stats)}",
                f"Contributors: {str(contributors[:10])}"
            ]
            self.add_to_knowledge_base(documents)
            
            # Generate analysis
            prompt = f"""As a GitHub expert, analyze this repository and provide comprehensive insights:

{context}

Provide a detailed analysis covering:
1. **Project Overview**: What is this project about?
2. **Technology Stack**: Key technologies and languages used
3. **Project Health**: Activity level, community engagement
4. **Code Quality Indicators**: Based on available metrics
5. **Recommendations**: For developers interested in this project

Be specific and data-driven in your analysis."""
            
            response = self.llm.invoke(prompt)
            return response.content
        
        except Exception as e:
            return f"Error analyzing repository: {str(e)}"
    
    def chat(self, message: str) -> str:
        """
        Chat with the agent (with conversation memory)
        
        Args:
            message: User message
        
        Returns:
            Agent response
        """
        try:
            # Add user message to history
            self.conversation_history.append(HumanMessage(content=message))
            
            # Create prompt with history
            response = self.llm.invoke(self.conversation_history)
            
            # Add AI response to history
            self.conversation_history.append(AIMessage(content=response.content))
            
            return response.content
        
        except Exception as e:
            return f"Error: {str(e)}"
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []
        print("✅ Conversation history cleared")
    
    def _format_languages(self, languages: Dict[str, float]) -> str:
        """Format language percentages"""
        if not languages:
            return "No language data available"
        
        sorted_langs = sorted(languages.items(), key=lambda x: x[1], reverse=True)
        return "\n".join([f"  - {lang}: {percent:.1f}%" for lang, percent in sorted_langs[:5]])
    
    def _format_contributors(self, contributors: List[Dict]) -> str:
        """Format contributor list"""
        if not contributors:
            return "No contributor data available"
        
        return "\n".join([
            f"  - {c.get('username', 'Unknown')}: {c.get('contributions', 0)} contributions"
            for c in contributors
        ])