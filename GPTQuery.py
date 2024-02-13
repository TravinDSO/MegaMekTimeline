import os
import time
import math
from dotenv import load_dotenv
from langchain_community.callbacks import get_openai_callback
from langchain_openai import OpenAIEmbeddings
from langchain_openai.chat_models import ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain.chains.question_answering import load_qa_chain

class GPTQuery:
    def __init__(self):
   
        # Debug environment variables
        load_dotenv('personal_environment.env', override=True)

        # Load the environment variables
        #load_dotenv('environment.env', override=True)

        self.max_tokens = 2500
        self.query_temp = 0.7
        self.total_docs_var = 100
        self.data_folder = './docs/'

        # Load the OPENAI environment variables from the .env file depending on use_azure
        self.use_azure = os.getenv("USE_AZURE").lower()
        if self.use_azure == "true":
            os.environ["OPENAI_API_TYPE"] = "azure"
            os.environ["OPENAI_API_BASE"] = os.getenv("AZURE_OPENAI_API_ENDPOINT")
            os.environ["OPENAI_API_KEY"] = os.getenv("AZURE_OPENAI_API_KEY")
            self.EMBEDDINGS_MODEL = os.getenv("AZURE_EMBEDDINGS_MODEL")
            self.AZURE_OPENAI_API_MODEL = os.getenv("AZURE_OPENAI_API_MODEL")
            OpenAIEmbeddings.deployment = os.getenv("AZURE_OPENAI_API_MODEL")
            llm = ChatOpenAI(max_tokens=self.max_tokens,deployment_id=self.AZURE_OPENAI_API_MODEL,temperature=self.query_temp,top_p=1,frequency_penalty=0,presence_penalty=0)
            self.embeddings = OpenAIEmbeddings(model=self.EMBEDDINGS_MODEL,chunk_size=16)
        else:
            os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
            self.EMBEDDINGS_MODEL = os.getenv("EMBEDDINGS_MODEL")
            self.OPENAI_API_MODEL = os.getenv("OPENAI_API_MODEL")
            llm = ChatOpenAI(max_tokens=self.max_tokens,model_name=self.OPENAI_API_MODEL,temperature=self.query_temp,top_p=1,frequency_penalty=0,presence_penalty=0)
            self.embeddings = OpenAIEmbeddings(model=self.EMBEDDINGS_MODEL,chunk_size=1000)

        self.docsearch_path = os.path.join(self.data_folder, 'docsearch')
        self.docsearch = FAISS.load_local(self.docsearch_path, self.embeddings)
        self.doc_chain = load_qa_chain(llm, chain_type="stuff")

        # Check if embeddings file exists
        if self.docsearch is None:
            print("Embeddings file not found. Please run the indexing process.")
            exit()
        else:
            self.enabled = True

    def calculate_num_docs(self,num_tokens, max_context_length):
        num_docs = 1000
        ratio = max_context_length / num_tokens
        num_docs = math.floor(ratio * num_docs)
        num_docs = num_docs // 10 * 10  # round down to nearest 10
        num_docs = num_docs - 5 # subtract 5 to be safe
        return num_docs

    def save_docs(self,docs):
        with open('docs.txt', 'w') as f:
            for doc in docs:
                f.write("%s\n" % doc)

    def query(self):

        query = input("What is your question? ")
        if query is None or query == "":
            return "I'm sorry, I don't have an answer for that."

        number_of_docs = int(float(self.total_docs_var))
        docs = self.docsearch.similarity_search(query, k=number_of_docs)

        with get_openai_callback() as cb:
            try:
                answer = self.doc_chain.run(input_documents=docs, question=query)
                self.save_docs(docs) #Save docs to file for debugging
                return answer
            except Exception as e:
                if "maximum context length" in str(e):
                    try:
                        #Rate limit pause
                        time.sleep(5)
                        # Extract max_context_length
                        max_context_length = int(str(e).split("maximum context length is ")[1].split(" tokens.")[0])
                        # Extract num_tokens
                        num_tokens = int(str(e).split("you requested ")[1].split(" tokens")[0])
                        number_of_docs = self.calculate_num_docs(num_tokens, max_context_length)
                        docs = self.docsearch.similarity_search(query, k=number_of_docs)
                        self.save_docs(docs) #Save docs to file for debugging
                        answer = self.doc_chain.run(input_documents=docs, question=query)
                        return answer
                    except:
                        try:
                            #Rate limit pause
                            time.sleep(5)
                            adjusted_number_of_docs = float(self.total_docs_var.get()) * 0.5
                            number_of_docs = (int(adjusted_number_of_docs))           
                            docs = self.docsearch.similarity_search(query, k=number_of_docs)
                            self.save_docs(docs) #Save docs to file for debugging
                            answer = self.doc_chain.run(input_documents=docs, question=query)
                            return answer
                        except:
                            try:
                                #Rate limit pause
                                time.sleep(5)
                                number_of_docs = 5
                                docs = self.docsearch.similarity_search(query, k=number_of_docs)
                                self.save_docs(docs) #Save docs to file for debugging
                                answer = self.doc_chain.run(input_documents=docs, question=query)
                                return answer
                            except:
                                return "I'm sorry, I don't have an answer for that."