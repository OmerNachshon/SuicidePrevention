import base64
import datetime
import pickle
import warnings
import pandas as pd

warnings.filterwarnings("ignore")
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
from email.mime.text import MIMEText
import tensorflow as tf
import tensorflow as tf
# from keras.layers import Embedding,Dense,LSTM,Bidirectional,GlobalMaxPooling1D,InputLayer,Dropout
# from keras.callbacks import EarlyStopping,ReduceLROnPlateau
# from keras.models import Sequential
import tensorflow as tf
import tensorflow.compat.v1 as tf

# from sklearn.preprocessing import LabelEncoder
from keras.preprocessing.text import Tokenizer
from keras.preprocessing.sequence import pad_sequences
from machine import clean_text
from google_auth_oauthlib.flow import Flow, InstalledAppFlow
from googleapiclient.discovery import build
# from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from google.auth.transport.requests import Request
# import pandas as pd


class GmailClient:
    def __init__(self):
        self.API='716788699125-24cq792btof1elffr4dj9j8l49grgn7m.apps.googleusercontent.com'
        self.CLIENT_FILE='Gmail/client_secret.json'
        self.API_NAME='gmail'
        self.API_VERSION='v1'
        self.SCOPES=['https://mail.google.com/']
        self.service=self.Create_Service(self.CLIENT_FILE,self.API_NAME,self.API_VERSION,self.SCOPES)

    def Create_Service(self,client_secret_file, api_name, api_version, *scopes):
        print(client_secret_file, api_name, api_version, scopes, sep='-')
        CLIENT_SECRET_FILE = client_secret_file
        API_SERVICE_NAME = api_name
        API_VERSION = api_version
        SCOPES = [scope for scope in scopes[0]]
        #print(SCOPES)

        cred = None
        working_dir = os.getcwd()
        token_dir = 'token files'

        pickle_file = f'token_{API_SERVICE_NAME}_{API_VERSION}.pickle'
        # print(pickle_file)

        ### Check if token dir exists first, if not, create the folder
        if not os.path.exists(os.path.join(working_dir, token_dir)):
            os.mkdir(os.path.join(working_dir, token_dir))

        if os.path.exists(os.path.join(working_dir, token_dir, pickle_file)):
            with open(os.path.join(working_dir, token_dir, pickle_file), 'rb') as token:
                cred = pickle.load(token)

        if not cred or not cred.valid:
            if cred and cred.expired and cred.refresh_token:
                cred.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
                cred = flow.run_local_server()

            with open(os.path.join(working_dir, token_dir, pickle_file), 'wb') as token:
                pickle.dump(cred, token)

        try:
            service = build(API_SERVICE_NAME, API_VERSION, credentials=cred)
            print(API_SERVICE_NAME, 'service created successfully')
            return service
        except Exception as e:
            print(e)
            print(f'Failed to create service instance for {API_SERVICE_NAME}')
            os.remove(os.path.join(working_dir, token_dir, pickle_file))
            return None

    def convert_to_RFC_datetime(self,year=1900, month=1, day=1, hour=0, minute=0):
        dt = datetime.datetime(year, month, day, hour, minute, 0).isoformat() + 'Z'
        return dt

    def get_mails(self, labelIds=None):
        if labelIds is None:
            labelIds = ['INBOX']
        results = self.service.users().messages().list(userId='me', labelIds=labelIds).execute()
        messages = results.get('messages', [])
        messages=[self.service.users().messages().get(userId='me',id=msg['id']).execute() for msg in messages]
        return messages

    @staticmethod
    def create_message(sender,to,subject,message_text):
        message=MIMEText(message_text)
        message['to']=to
        message['from']=sender
        message['subject']=subject

        raw_message=base64.urlsafe_b64encode(message.as_string().encode("utf-8"))
        return {
            'raw':raw_message.decode("utf-8")
        }

    def send_message(self,message):
        try:
            message=self.service.users().messages().send(userId='me',body=message).execute()
            print('Message Id: %s' % message['id'])
            return message
        except Exception as e:
            print('An error occurred: %s' % e)
            return None
    @staticmethod
    def is_suicidal(str_input):  # determines if message is suicidal or not
        #   machine will be used in this section
        with open('model.pkl', 'rb') as fp:
            lst=[str_input]
            model=pickle.load(fp)
            cleaned_train_text,clean_text_length = clean_text(lst)
            with open('tokenizer.pkl', 'rb') as fp2:
                tokenizer = pickle.load(fp2)
            train_text_seq = tokenizer.texts_to_sequences(cleaned_train_text)
            train_text_pad = pad_sequences(train_text_seq, maxlen=40)
            res=model.predict_classes(train_text_pad)
            return res


    def get_sender(self,msg):  # get sender email address from the message
        for header in msg['payload']['headers']:
            if header['name'] == 'From':
                return header['value']

    def create_description(self,msg):  # creating the description  , title = "suicidal" {default}
        desc = "sender :\n"
        for str in self.get_sender(msg):
            desc += str
        str += "\n"
        for str in msg['snippet']:
            desc += str
        return str

    def get_message(self,msg):
        return msg['snippet']

    def get_labels(self):
        results = self.service.users().labels().list(userId='me').execute()
        labels = results.get('labels', [])
        return labels