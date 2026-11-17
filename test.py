# import smtplib
# from email.mime.text import MIMEText
# from email.mime.multipart import MIMEMultipart
#
# class SOSSystem:
#     def __init__(self):
#         # Static Configuration
#         self.sender_email = "nithinjambula89@gmail.com"
#         self.sender_password = "njmr izng bzrm dkbo"
#         self.emergency_contacts = [
#             "nithinjambula44@gmail.com"
#         ]
#
#         # Static Location
#         self.location = {
#             'latitude': '12.34',
#             'longitude': '56.78'
#         }
#
#         # SMTP Settings
#         self.smtp_server = "smtp.gmail.com"
#         self.smtp_port = 587
#
#     def create_message(self):
#         subject = "EMERGENCY SOS ALERT!"
#         body = f"""
#         EMERGENCY SOS ALERT!
#
#         This is an automated emergency message.
#         Location: {self.location['latitude']}, {self.location['longitude']}
#         Maps Link: https://www.google.com/maps?q={self.location['latitude']},{self.location['longitude']}
#
#         Please take immediate action!
#         """
#         return subject, body
#
#     def send_sos(self):
#         try:
#             subject, body = self.create_message()
#
#             with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
#                 server.starttls()
#                 server.login(self.sender_email, self.sender_password)
#
#                 for contact in self.emergency_contacts:
#                     message = MIMEMultipart()
#                     message['From'] = self.sender_email
#                     message['To'] = contact
#                     message['Subject'] = subject
#                     message.attach(MIMEText(body, 'plain'))
#                     server.send_message(message)
#
#             return f"SOS alert sent successfully to {', '.join(self.emergency_contacts)}"
#         except Exception as e:
#             return f"Failed to send SOS alert: {str(e)}"
#
# if __name__ == "__main__":
#     sos = SOSSystem()
#     print(sos.send_sos())

from utilities import SOSSystem


def test_sos():
    sos = SOSSystem()

    # Test each trigger word
    test_phrases = [
        "help me please",
        "this is an emergency",
        "need sos now",
        "danger ahead",
        "call police",
        "need ambulance",
        "medical emergency",
        "accident happened"
    ]

    for phrase in test_phrases:
        print(f"Testing phrase: '{phrase}'")
        result = sos.handle_voice_command(phrase)
        print(f"Result: {result}\n")


if __name__ == "__main__":
    test_sos()