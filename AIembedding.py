import os
import gc
import gzip
import xml.etree.ElementTree as ET
from dotenv import load_dotenv
from PyPDF2 import PdfReader
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain.chains.question_answering import load_qa_chain
from langchain_openai.chat_models import ChatOpenAI
from langchain_community.document_loaders import CSVLoader


# Text splitter for splitting the text into chunks
class CustomTextSplitter(CharacterTextSplitter):
    def __init__(self, separators, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.separators = separators

    def split_text(self, text):
        import re
        chunks = []
        pattern = '|'.join(map(re.escape, self.separators))
        splits = re.split(pattern, text)
        return self._merge_splits(splits, self.separators[0])

# Class to handle the creation of VectorDB and AI Embeddings
class AIembedding:
    def __init__(self):

        # Debug environment variables
        load_dotenv('personal_environment.env', override=True)

        # Load the environment variables
        #load_dotenv('environment.env', override=True)

        self.max_tokens = 2500
        self.query_temp = 0.0
        self.data_folder = './docs/'
        self.doc_metadata_file = 'docs_metadata.xml'
        # Structure to hold file metadata
        self.file_info = {}

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

        self.doc_chain = load_qa_chain(llm, chain_type="stuff")
        self.chain_path = os.path.join(self.data_folder, 'chain.json')
        self.docsearch_path = os.path.join(self.data_folder, 'docsearch')
        self.compressed_raw_text_file = os.path.join(self.data_folder, 'temporary_cached_data.gz')

        if os.environ["OPENAI_API_KEY"]:
            self.enabled = True
        else:
            self.enabled = False

    def load_doc_metadata(self):
        # Check if the XML file exists
        if not os.path.exists(self.doc_metadata_file):
            print("XML file not found. Metadata will not be useed.")
            return

        tree = ET.parse(self.doc_metadata_file)
        root = tree.getroot()

        for file_type in root.findall('type'):
            type_name = file_type.attrib['type']
            self.file_info[type_name] = []
            
            for item in file_type.findall('fileItem'):
                name = item.find('name').text
                purpose = item.find('purpose').text
                self.file_info[type_name].append({'name': name, 'purpose': purpose})

    def run(self):
        
        skipped_path = ""

        if os.path.exists(self.compressed_raw_text_file):
            os.remove(self.compressed_raw_text_file)

        # Index the documents
        with gzip.open(self.compressed_raw_text_file, 'wt', encoding='utf-8') as f:
            for root, _, files in os.walk(self.data_folder):
                for file in files:
                    if file.endswith('.pdf'):
                        try:
                            pdf_path = os.path.join(root, file)
                            reader = PdfReader(pdf_path)
                            for i, page in enumerate(reader.pages):
                                text = page.extract_text()
                                if text:
                                    f.write(text)
                            # Release memory after processing each PDF
                            del reader
                            gc.collect()
                            print(f"Processed PDF {pdf_path}")
                        except Exception as e:
                            print(f"Error processing PDF {pdf_path}: {e}")
                    elif file.endswith('.csv'):
                        try:
                            csv_path = os.path.join(root, file)
                            reader = CSVLoader(csv_path)
                            data = reader.load()
                            for i, row in enumerate(data):
                                if row:
                                    f.write(row.page_content)
                            # Release memory after processing each csv
                            del reader
                            gc.collect()
                            print(f"Processed CSV {csv_path}")
                        except Exception as e:
                            print(f"Error processing CSV {csv_path}: {e}")
                    elif file.endswith('.txt'):
                        try:
                            txt_path = os.path.join(root, file)
                            with open(txt_path, 'r', encoding='utf-8') as txt_file:
                                txt_text = txt_file.read()
                            f.write(txt_text)
                            print(f"Processed TXT {txt_path}")
                        except Exception as e:
                            print(f"Error processing TXT {txt_path}: {e}")
                    elif file.endswith('.xml'):
                        try:
                            xml_path = os.path.join(root, file)
                            # Create a context for iteratively parsing the XML file
                            context = ET.iterparse(xml_path, events=('start', 'end'))
                            context = iter(context)
                            # Process the XML file chunk by chunk
                            for event, elem in context:
                                if event == 'end':
                                    # Write the text content of the current element to the gz file
                                    if elem.text:
                                        #f.write(elem.text)
                                        f.write(ET.tostring(elem, encoding='unicode'))
                                    # Clean up the processed element to save memory
                                    elem.clear()
                            print(f"Processed XML {xml_path}")
                        except Exception as e:
                            print(f"Error processing XML {xml_path}: {e}")
                    else:
                        skipped_path = os.path.join(root, file)
                        print(f"Skipped file {skipped_path}")


        # Initialize an empty list to store processed text chunks
        processed_texts_cache = []

        #Need to replace the magic numbers with variables and include them in the environment file
        with gzip.open(self.compressed_raw_text_file, 'rt', encoding='utf-8') as f:
            text_splitter = CustomTextSplitter(
                separators=['\n', '. '],
                chunk_size=3000,
                chunk_overlap=500,
                length_function=len,
            )
            
            current_chunk = ''
            for line in f:
                current_chunk += line
                if len(current_chunk) >= text_splitter._chunk_size:  # Corrected attribute name
                    # Process the current chunk
                    processed_chunk = text_splitter.split_text(current_chunk)
                    
                    # Append the processed chunk to the cache
                    processed_texts_cache.extend(processed_chunk)
                    
                    # Keep the chunk_overlap part of the current chunk for the next iteration
                    current_chunk = current_chunk[-text_splitter._chunk_overlap:]  # Corrected attribute name

        # Process the remaining part of the last chunk
        if current_chunk:
            processed_chunk = text_splitter.split_text(current_chunk)
            processed_texts_cache.extend(processed_chunk)

        print(f"Processed {len(processed_texts_cache)} chunks")

        # Remove the compressed raw text file
        os.remove(self.compressed_raw_text_file)
        print(f"Removed {self.compressed_raw_text_file}")
        
        print("Creating the VectorDB and AI Embeddings")
        try:
            docsearch = FAISS.from_texts(processed_texts_cache, self.embeddings)
            print("Created the VectorDB and AI Embeddings")
        except Exception as e:
            print(f"Error creating the VectorDB and AI Embeddings: {e}")
            return

        try:
            docsearch.save_local(self.docsearch_path)
            print("Saved the VectorDB and AI Embeddings")
        except Exception as e:
            print(f"Error saving the VectorDB and AI Embeddings: {e}")
            return
        
        try:
            self.doc_chain.save(self.chain_path)
            print("Saved the Chain")
        except Exception as e:
            print(f"Error saving the Chain: {e}")
            return