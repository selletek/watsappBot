from twilio.rest import Client 
 
account_sid = 'AC52b0b9741607dacd7e6d4ca36d62a00c' 
auth_token = 'dfb7eb018b360f1f81506d16f79748fa' 
client = Client(account_sid, auth_token) 
 
message = client.messages.create( 
                              from_='whatsapp:+14155238886',  
                              body='Your appointment is coming up on July 21 at 3PM',      
                              to='whatsapp:+923129601966' 
                          ) 
 
print(message.sid)