import os  # Imports the operating system module for file operations.
from PyPDF2 import PdfReader, PdfMerger  # Imports PDF reading and merging tools.
from langchain.text_splitter import RecursiveCharacterTextSplitter  # Imports text splitting for LangChain.
from langchain_google_genai import GoogleGenerativeAIEmbeddings  # Imports Google's embedding model.
import streamlit as st  # Imports Streamlit for web app development.
import google.generativeai as genai  # Imports Google's generative AI library.
from langchain.vectorstores import FAISS  # Imports FAISS for vector storage.
from langchain_google_genai import ChatGoogleGenerativeAI  # Imports Gemini chat model.
from langchain.chains.question_answering import load_qa_chain  # Imports question answering chain.
from langchain.prompts import PromptTemplate  # Imports prompt templates for LangChain.
from dotenv import load_dotenv  # Imports dotenv for loading environment variables.
from PIL import Image  # Imports Pillow (PIL) for image processing.
import pytesseract  # Imports pytesseract for OCR.
from pdf2image import convert_from_path  # Imports pdf2image for PDF to image conversion.

# Feature to convert PDF image to text
def pdf_to_text_ocr(pdf_files):  # Defines a function to convert PDF images to text.
    try:  # Starts a try block to handle potential errors.
        all_text = ""  # Initializes an empty string to store all extracted text.
        for pdf_file in pdf_files:  # Loops through each uploaded PDF file.
            images = convert_from_path(pdf_file.name)  # Converts PDF pages to images.
            text = ""  # Initializes an empty string to store text from each image.
            for image in images:  # Loops through each image.
                text += pytesseract.image_to_string(image)  # Converts image to text using OCR.
            all_text += text + "\n\n"  # Appends the extracted text to the main text string.
        st.session_state.ocr_output = all_text  # Stores the extracted text in Streamlit session state.
        st.success("Image to text conversion successful!")  # Displays success message.
    except Exception as e:  # Catches any exceptions.
        st.error(f"An error occurred: {e}")  # Displays an error message.

# --- Extract Images Function ---
def extract_images_from_pdf(pdf_file):  # Defines a function to extract images from a PDF.
    try:  # Starts a try block.
        images = convert_from_path(pdf_file.name)  # Converts PDF pages to images.
        st.session_state.extracted_images = images  # Stores the extracted images in Streamlit session state.
        st.success("Images extracted successfully!")  # Displays success message.
    except Exception as e:  # Catches any exceptions.
        st.error(f"An error occurred during image extraction: {e}")  # Displays error message.

# --- Merge PDFs Function ---
def merge_pdfs(pdf_files):  # Defines a function to merge multiple PDFs.
    try:  # Starts a try block.
        merger = PdfMerger()  # Creates a PDF merger object.
        for pdf in pdf_files:  # Loops through each uploaded PDF.
            merger.append(pdf)  # Appends each PDF to the merger.
        output_filename = "merged.pdf"  # Sets the output filename.
        merger.write(output_filename)  # Writes the merged PDF to a file.
        merger.close()  # Closes the merger.
        with open(output_filename, "rb") as f:  # Opens the merged PDF for reading.
            st.session_state.merged_pdf_data = f.read()  # Stores the PDF data in Streamlit session state.
            st.session_state.merged_pdf_filename = output_filename  # Stores the filename in session state.
        os.remove(output_filename)  # Removes the temporary merged PDF file.
        st.success("PDFs merged successfully!")  # Displays success message.
    except Exception as e:  # Catches any exceptions.
        st.error(f"An error occurred during PDF merging: {e}")  # Displays error message.

load_dotenv()  # Loads environment variables from .env file.
os.getenv("GOOGLE_API_KEY")  # Retrieves the Google API key from environment variables.
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))  # Configures Google Generative AI with the API key.

def get_pdf_text(pdf_docs):  # Defines a function to extract text from PDFs.
    text = ""  # Initializes an empty string to store extracted text.
    for pdf in pdf_docs:  # Loops through each uploaded PDF.
        pdf_reader = PdfReader(pdf)  # Creates a PDF reader object.
        for page in pdf_reader.pages:  # Loops through each page in the PDF.
            text += page.extract_text()  # Extracts text from the page and appends it.
    return text  # Returns the extracted text.

def get_text_chunks(text):  # Defines a function to split text into chunks.
    splitter = RecursiveCharacterTextSplitter(chunk_size=10000, chunk_overlap=1000)  # Creates a text splitter.
    chunks = splitter.split_text(text)  # Splits the text into chunks.
    return chunks  # Returns the text chunks.

def get_vector_store(chunks):  # Defines a function to create a vector store from text chunks.
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")  # Creates embeddings.
    vector_store = FAISS.from_texts(chunks, embedding=embeddings)  # Creates a FAISS vector store.
    vector_store.save_local("faiss_index")  # Saves the vector store locally.

def get_conversational_chain():  # Defines a function to create a conversational chain.
    prompt_template = """Answer the question as detailed as possible from the provided context, make sure to provide all the details, if the answer is not in provided context just say, "answer is not available in the context", don't provide the wrong answer\n\nContext:\n {context}?\nQuestion: \n{question}\n\nAnswer:"""  # Defines the prompt template.
    model = ChatGoogleGenerativeAI(model="models/gemini-1.5-flash-latest", client=genai, temperature=0.3)  # Creates a Gemini chat model.
    prompt = PromptTemplate(template=prompt_template, input_variables=["context", "question"])  # Creates a prompt object.
    chain = load_qa_chain(llm=model, chain_type="stuff", prompt=prompt)  # Creates a question answering chain.
    return chain  # Returns the conversational chain.

def clear_all():  # Defines a function to clear all session state variables.
    st.session_state.messages = [{"role": "assistant", "content": "upload some pdfs and ask me a question"}]  # Initializes chat messages.
    st.session_state.ocr_output = None  # Clears OCR output.
    st.session_state.extracted_images = None  # Clears extracted images.
    st.session_state.merged_pdf_data = None  # Clears merged PDF data.
    st.session_state.merged_pdf_filename = None  # Clears merged PDF filename.
    st.session_state.submit_process_done = False  # Resets submit process flag.
    st.session_state.extract_images_done = False  # Resets image extraction flag.
    st.session_state.ocr_done = False  # Resets OCR flag.
    st.session_state.merge_pdfs_done = False  # Resets merge PDFs flag.

def user_input(user_question):  # Defines a function to handle user input.
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")  # Creates embeddings.
    new_db = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)  # Loads the vector store.
    docs = new_db.similarity_search(user_question)  # Searches for similar documents.
    chain = get_conversational_chain()  # Gets the conversational chain.
    response = chain({"input_documents": docs, "question": user_question}, return_only_outputs=True)  # Gets the response.
    return response  # Returns the response.

def main():  # Defines the main function.
    st.set_page_config(page_title="PDF Chatbot", page_icon="🤖")  # Sets the page configuration.

    # Initializes session state variables if they don't exist.
    if "ocr_output" not in st.session_state:
        st.session_state.ocr_output = None
    if "extracted_images" not in st.session_state:
        st.session_state.extracted_images = None
    if "merged_pdf_data" not in st.session_state:
        st.session_state.merged_pdf_data = None
    if "merged_pdf_filename" not in st.session_state:
        st.session_state.merged_pdf_filename = None
    if "submit_process_done" not in st.session_state:
        st.session_state.submit_process_done = False
    if "extract_images_done" not in st.session_state:
        st.session_state.extract_images_done = False
    if "ocr_done" not in st.session_state:
        st.session_state.ocr_done = False
    if "merge_pdfs_done" not in st.session_state:
        st.session_state.merge_pdfs_done = False

    with st.sidebar:  # Creates a sidebar.
        st.title("Menu:")  # Sets the sidebar title.
        pdf_docs = st.file_uploader("Upload your PDF Files", accept_multiple_files=True)  # Creates a file uploader.

        if st.button("Submit & Process", key="submit_process") and pdf_docs:  # Creates a submit button.
            with st.spinner("Processing..."):  # Displays a spinner during processing.
                raw_text = get_pdf_text(pdf_docs)  # Extracts text from uploaded PDFs.
                text_chunks = get_text_chunks(raw_text)  # Splits the text into chunks.
                get_vector_store(text_chunks)  # Creates and saves the vector store.
                st.session_state.submit_process_done = True  # Sets the submit process flag.
                st.success("Done")  # Displays success message.

        if st.button("Extract Images from PDF", key="extract_images") and pdf_docs:  # Creates an extract images button.
            if len(pdf_docs) == 1:  # Checks if only one PDF is uploaded.
                extract_images_from_pdf(pdf_docs[0])  # Extracts images from the PDF.
                st.session_state.extract_images_done = True  # Sets image extraction flag.
            else:
                st.error("Please upload only one PDF for image extraction.")  # Displays error message.

        if st.button("Convert PDF images to Text", key="ocr_button") and pdf_docs:  # Creates an OCR button.
            with st.spinner("Converting PDF images to Text ..."):  # Displays a spinner during OCR.
                pdf_to_text_ocr(pdf_docs)  # Converts PDF images to text.
                st.session_state.ocr_done = True  # Sets OCR flag.

        if st.button("Merge PDFs", key="merge_pdfs") and pdf_docs:  # Creates a merge PDFs button.
            if len(pdf_docs) >= 2:  # Checks if at least two PDFs are uploaded.
                merge_pdfs(pdf_docs)  # Merges the PDFs.
                st.session_state.merge_pdfs_done = True  # Sets merge PDFs flag.
            else:
                st.error("Please upload at least two PDF files to merge.")  # Displays error message.

        st.sidebar.button('Clear', on_click=clear_all, key="clear_button")  # Creates a clear button.

    st.title("PDF Chatbot 🤖")  # Sets the main title.
    st.write("Welcome to the chat with your PDF tool!")  # Displays a welcome message.

    if st.session_state.submit_process_done:  # Checks if submit process is done.
        st.header("Submit and Process :")  # Displays a header.
        if "messages" in st.session_state:  # Checks if messages exist.
            for message in st.session_state.messages:  # Loops through messages.
                with st.chat_message(message["role"]):  # Displays each message.
                    st.write(message["content"])  # Writes the message content.

    if st.session_state.extract_images_done:  # Checks if image extraction is done.
        st.header("Extracted Images from your PDF :")  # Displays a header.
        if st.session_state.extracted_images:  # Checks if images exist.
            for image in st.session_state.extracted_images:  # Loops through images.
                st.image(image)  # Displays each image.

    if st.session_state.ocr_done:  # Checks if OCR is done.
        st.header("PDF Images to Text Conversion Results :")  # Displays a header.
        if st.session_state.ocr_output:  # Checks if OCR output exists.
            st.text(st.session_state.ocr_output)  # Displays the OCR output.

    if st.session_state.merge_pdfs_done:  # Checks if merge PDFs is done.
        st.header("Merged PDF:")  # Displays a header.
        if st.session_state.merged_pdf_data:  # Checks if merged PDF data exists.
            st.download_button(  # Creates a download button.
                label="Download Merged PDF",  # Sets the button label.
                data=st.session_state.merged_pdf_data,  # Sets the PDF data.
                file_name=st.session_state.merged_pdf_filename,  # Sets the filename.
                mime='application/pdf'  # Sets the MIME type.
            )

    if "messages" not in st.session_state.keys():  # Initializes chat messages if they don't exist.
        st.session_state.messages = [{"role": "assistant", "content": "upload some pdfs and ask me a question"}]

    if prompt := st.chat_input():  # Creates a chat input.
        st.session_state.messages.append({"role": "user", "content": prompt})  # Appends user message to chat.
        with st.chat_message("user"):  # Displays user message.
            st.write(prompt)  # Writes the user message.

    if st.session_state.messages[-1]["role"] != "assistant":  # Checks if the last message is not from the assistant.
        with st.chat_message("assistant"):  # Displays assistant message.
            with st.spinner("Thinking..."):  # Displays a spinner during processing.
                response = user_input(prompt)  # Gets the response from the model.
                placeholder = st.empty()  # Creates a placeholder for the response.
                full_response = ''  # Initializes an empty string for the full response.
                for item in response['output_text']:  # Loops through the response.
                    full_response += item  # Appends each item to the full response.
                placeholder.markdown(full_response)  # Displays the full response.
        if response is not None:  # Checks if a response exists.
            message = {"role": "assistant", "content": full_response}  # Creates an assistant message.
            st.session_state.messages.append(message)  # Appends the assistant message to chat.

if __name__ == "__main__":  # Checks if the script is run directly.
    main()  # Calls the main function.