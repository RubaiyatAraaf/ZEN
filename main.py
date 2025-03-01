import streamlit as st
import firebase_admin
from firebase_admin import credentials
from firebase_admin import auth
import json
import requests
from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
import os
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import google.generativeai as genai
from langchain.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains.question_answering import load_qa_chain
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv
import datetime
import shutil
import pretty_errors

try:
    app = firebase_admin.get_app()
except ValueError as e:
    cred = credentials.Certificate("outshutzen.json")
    firebase_admin.initialize_app(cred)

load_dotenv()
os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

def main():
    st.set_page_config(
    page_title="Outshut | <ZEN>",
    page_icon="🎪")
# Usernm = []

    if 'username' not in st.session_state:
        st.session_state.username = ''
    if 'useremail' not in st.session_state:
        st.session_state.useremail = ''


    def sign_up_with_email_and_password(email, password, username=None, return_secure_token=True):
        try:
            rest_api_url = "https://identitytoolkit.googleapis.com/v1/accounts:signUp"
            payload = {
                "email": email,
                "password": password,
                "returnSecureToken": return_secure_token
            }
            if username:
                payload["displayName"] = username 
            payload = json.dumps(payload)
            r = requests.post(rest_api_url, params={"key": "AIzaSyAjy4ND6n32WMh0hMnGukriDnZ5bHpes-U"}, data=payload)
            try:
                return r.json()['email']
            except:
                st.warning(r.json())
        except Exception as e:
            st.warning(f'Signup failed: {e}')

    def sign_in_with_email_and_password(email=None, password=None, return_secure_token=True):
        rest_api_url = "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword"

        try:
            payload = {
                "returnSecureToken": return_secure_token
            }
            if email:
                payload["email"] = email
            if password:
                payload["password"] = password
            payload = json.dumps(payload)
            print('payload sigin',payload)
            r = requests.post(rest_api_url, params={"key": "AIzaSyAjy4ND6n32WMh0hMnGukriDnZ5bHpes-U"}, data=payload)
            try:
                data = r.json()
                user_info = {
                    'email': data['email'],
                    'username': data.get('displayName')  # Retrieve username if available
                }
                return user_info
            except:
                st.warning(data)
        except Exception as e:
            st.warning(f'Signin failed: {e}')

    def reset_password(email):
        try:
            rest_api_url = "https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode"
            payload = {
                "email": email,
                "requestType": "PASSWORD_RESET"
            }
            payload = json.dumps(payload)
            r = requests.post(rest_api_url, params={"key": "AIzaSyAjy4ND6n32WMh0hMnGukriDnZ5bHpes-U"}, data=payload)
            if r.status_code == 200:
                return True, "Reset email Sent"
            else:
                # Handle error response
                error_message = r.json().get('error', {}).get('message')
                return False, error_message
        except Exception as e:
            return False, str(e)

    # Example usage
    # email = "example@example.com"
           

    def f(): 
        try:
            # user = auth.get_user_by_email(email)
            # print(user.uid)
            # st.session_state.username = user.uid
            # st.session_state.useremail = user.email

            userinfo = sign_in_with_email_and_password(st.session_state.email_input,st.session_state.password_input)
            st.session_state.username = userinfo['username']
            st.session_state.useremail = userinfo['email']

            
            global Usernm
            Usernm=(userinfo['username'])
            
            st.session_state.signedout = True
            st.session_state.signout = True    
  
            
        except: 
            st.warning("Email or Password is incorrect")

    def t():
        st.session_state.signout = False
        st.session_state.signedout = False   
        st.session_state.username = ''


    def forget():
        st.markdown("---")
        st.write("Forgot Password?")
        email = st.text_input('Email')
        if st.button('Send Password Reset Link'):
            print(email)
            success, message = reset_password(email)
            if success:
                st.success("Password reset email sent successfully.")
            else:
                st.warning(f"Password reset failed: {message}") 
        
    if "signedout"  not in st.session_state:
        st.session_state["signedout"] = False
    if 'signout' not in st.session_state:
        st.session_state['signout'] = False    
        

        
    
    if  not st.session_state["signedout"]: # only show if the state is False, hence the button has never been clicked
        st.markdown("<h1 style='text-align:center;'><🎪ZEN ></h1>", unsafe_allow_html=True)
        choice = st.selectbox('Login/Signup',['Login','Sign up'])
        email = st.text_input('Email Address')
        password = st.text_input('Password',type='password')
        st.session_state.email_input = email
        st.session_state.password_input = password

        

        
        if choice == 'Sign up':
            username = st.text_input("Enter your unique username")

            if username and not all(char.isalnum() for char in username):
                st.warning("Username cannot contain spaces or special characters.")
                username = ""  # Clear the input field
            
            if st.button('Create my account'):
                # user = auth.create_user(email = email, password = password,uid=username)
                
                # Creating Startup Folder For New User
                current_directory = os.getcwd()
                user_dir = os.path.join(current_directory, username)
                if os.path.exists(user_dir):
                   st.warning("Username already exists")
                   username = ""
                else:    
                    os.mkdir(user_dir, mode = 0o777, dir_fd = None)
                    default_faiss_path = "Default/index.faiss"
                    default_pkl_path = "Default/index.pkl"
                    target_faiss_path = os.path.join(username, "index.faiss")
                    target_pkl_path = os.path.join(username, "index.pkl")
                    # Copy the default files to the target locations
                    shutil.copyfile(default_faiss_path, target_faiss_path)
                    shutil.copyfile(default_pkl_path, target_pkl_path)

                    user = sign_up_with_email_and_password(email=email,password=password,username=username)

                    st.success("Account created successfully! | Now 'LOGIN' with your Email and Password")
                    st.balloons()
        else:
            # st.button('Login', on_click=f)          
            st.button('Login', on_click=f)
            # if st.button('Forget'):
            forget()
            # st.button('Forget',on_click=forget)

    def get_pdf_text(pdf_docs):
            text=""
            for pdf in pdf_docs:
                pdf_reader= PdfReader(pdf)
                for page in pdf_reader.pages:
                    text+= page.extract_text()
            return  text



    def get_text_chunks(text):
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=10000, chunk_overlap=1000)
        chunks = text_splitter.split_text(text)
        return chunks


    def get_vector_store(text_chunks):
        embeddings = GoogleGenerativeAIEmbeddings(model = "models/embedding-001")
        vector_store = FAISS.from_texts(text_chunks, embedding=embeddings)
        vector_store.save_local(st.session_state.username)
        


    def get_conversational_chain():

        prompt_template = """
        Answer the question as detailed as possible from the provided context, make sure to provide all the details, if the answer is not in
        provided context just say, "Response is not available in the context", don't provide the wrong answer\n\n
        Context:\n {context}?\n
        Question: \n{question}\n

        Answer:
        """

        model = ChatGoogleGenerativeAI(model="gemini-1.5-flash-latest",
                                temperature=0.3)

        prompt = PromptTemplate(template = prompt_template, input_variables = ["context", "question"])
        chain = load_qa_chain(model, chain_type="stuff", prompt=prompt)

        return chain



    def user_input(user_question):
        embeddings = GoogleGenerativeAIEmbeddings(model = "models/embedding-001")
        
        new_db = FAISS.load_local(st.session_state.username, embeddings, allow_dangerous_deserialization=True)
        docs = new_db.similarity_search(user_question)

        chain = get_conversational_chain()

        
        response = chain(
            {"input_documents":docs, "question": user_question}
            , return_only_outputs=True)

        print(response)
        st.write("ZEN: ", response["output_text"])

        
    def reset_index_files():
        default_faiss_path = "Default/index.faiss"
        default_pkl_path = "Default/index.pkl"
        target_faiss_path = os.path.join(st.session_state.username, "index.faiss")
        target_pkl_path = os.path.join(st.session_state.username, "index.pkl")

        # Copy the default files to the target locations
        shutil.copyfile(default_faiss_path, target_faiss_path)
        shutil.copyfile(default_pkl_path, target_pkl_path)

            
            
    if st.session_state.signout:
            st.header("Talk with your Books and Notes🚀")
            st.markdown("---")
            user_question = st.text_input("Ask ZEN your Questions:")

            if user_question:
                user_input(user_question)

            with st.sidebar:
                st.markdown("<h1 style='font-size: 40px;'><🎪ZEN ></h1>", unsafe_allow_html=True)
                pdf_docs = st.file_uploader("Upload Your Books or Notes 🗂️", accept_multiple_files=True, type="pdf")


                if st.button("Submit & Process"):
                    with st.spinner("Processing..."):
                        raw_text = get_pdf_text(pdf_docs)
                        text_chunks = get_text_chunks(raw_text)
                        get_vector_store(text_chunks)

                    # Save the pdf in the User folder    
                    if pdf_docs is not None:
                        for pdf_file in pdf_docs:
                            # Get the current date and time in a suitable format
                            now = datetime.datetime.now()
                            filename = now.strftime("%Y-%m-%d_%H-%M-%S.pdf")
                            userfolder = st.session_state.username
                            # Save the file to the folder with the generated filename
                            save_path = os.path.join(userfolder, filename)
                            with open(save_path, "wb") as f:
                                f.write(pdf_file.read())

                        st.success("Done")

                st.markdown("---")
                if st.button("Reset Your Progress"):
                    reset_index_files()
                    st.success("New Session Started")
                st.markdown("---")
                st.text('UserID: '+st.session_state.username)
                st.text('Email: '+st.session_state.useremail)
                st.button('Sign out', on_click=t)



if __name__ == "__main__":
    main()


