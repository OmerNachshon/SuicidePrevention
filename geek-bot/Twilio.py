from flask import Flask, request
from twilio.rest import Client
import os
from twilio.twiml.messaging_response import MessagingResponse
from Gmail import Google
LOGS_LABEL = 'Label_2545976027983307541'		#label id of all logs from bots
app = Flask(__name__)

#authentication
os.environ['TWILIO_ACCOUNT_SID'] = 'AC713c1a16a4014d333a67b144d5401052'
os.environ['TWILIO_AUTH_TOKEN'] = '061fdec017243971bee9b600cdad23de'
account_sid = os.environ['TWILIO_ACCOUNT_SID']
auth_token = os.environ['TWILIO_AUTH_TOKEN']
client = Client(username=account_sid, password=auth_token)
# creating the gmail service
GMAIL_SERVICE = Google.GmailClient()
OM_GMAIL_BOX='om.suicide.prevention@gmail.com'

@app.route("/", methods=["GET", "POST"])

# chatbot logic
def bot():
	# creating object of MessagingResponse
	resp = MessagingResponse()
	msg = resp.message()
	incoming_msg = request.values.get('Body', '').lower()
	sender_num=request.values.get('From','')
	sender_name=request.values.get('ProfileName','')
	print(sender_name)
	print(sender_num)
	res=GMAIL_SERVICE.is_suicidal(incoming_msg)[0][0]	#preprocess input ,clean text and run model on input from user
	print(incoming_msg)
	print(res)

	#if res indicates suicidal message , send to gmail box
	if res==1:
		email_msg=GMAIL_SERVICE.create_message(sender=OM_GMAIL_BOX,to=OM_GMAIL_BOX,subject=f'LOG - {sender_name} , {sender_num}',message_text=incoming_msg)
		GMAIL_SERVICE.send_message(email_msg)

	if 'hi' in incoming_msg.split(' ') or 'hello' in incoming_msg.split(' ')or 'hey' in incoming_msg.split(' '):
		message = client.messages.create(body=f"""Hi {sender_name},\nmy name is Twilio,\nCan you please share with me how you have been lately?\nI'd like to hear how you are feeling...""",
			from_='whatsapp:+14155238886',to=sender_num)
	else:
		message = client.messages.create(body=f"({res})\n {sender_name} , if you feel you need more assistance , please use the emergency numbers.\n\n Emergency numbers:\n\nAran-1201\nPolice 100\nAmbulance 101\n\nEmergency websites:\n\nSahar- https://sahar.org.il/ "f"\n\nEmails:\n\n om.suicide.prevention@gmail.com",
			from_='whatsapp:+14155238886', to=sender_num)

	return str(resp)

if __name__ == "__main__":
	app.run(host="localhost", port=5002)
