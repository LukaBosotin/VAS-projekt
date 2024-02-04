import json
from spade.agent import Agent
from spade.behaviour import FSMBehaviour, State
from spade.message import Message
from asyncio import sleep
import smtplib
from email.mime.text import MIMEText

class AgentMailSender(Agent):
    def __init__(self, jid, password): 
        super().__init__(jid, password)
        self.user_max_price = None
        self.offers = None
        self.found_products_within_price = []
        self.email_sender = "vas.test1611@gmail.com"
        self.passwd_sender = "exrl rxcd rlgp hgoy"
        self.email_recipient = None
        self.subject = "Obavijest o dostupnome proizvodu na temelju zadane cijene"


    class Behavior(FSMBehaviour):
        async def on_start(self):
            print(f"Pokrećem agenta 2")

        async def on_end(self):
            print(f"Završavam agenta 2")

    async def setup(self):
        fsm = self.Behavior()
        fsm.add_state(name="WaitForMessage", state=self.WaitForMessage(), initial=True)
        fsm.add_state(name="ProcessData", state=self.ProcessData())
        fsm.add_state(name="SendEmail", state=self.SendEmail())
        
        fsm.add_transition(source="WaitForMessage", dest= "WaitForMessage")
        fsm.add_transition(source="WaitForMessage", dest= "ProcessData")
        fsm.add_transition(source="ProcessData", dest="SendEmail")
        fsm.add_transition(source="ProcessData", dest="WaitForMessage")
        self.add_behaviour(fsm)

    class WaitForMessage(State):
        async def run(self):
            msg = await self.receive(timeout=100)
            if msg:
                self.agent.offers = json.loads(msg.body)['offers']
                if self.agent.user_max_price is None or self.agent.user_max_price <= 0:
                    while True:
                        try:
                            input_price = int(input("Unesite traženu cijenu proizvoda: "))
                            if input_price > 0:
                                self.agent.user_max_price = input_price
                                break
                        except Exception:
                            print("Unijeli ste nepravilnu cijenu, pokušajte ponovno.")

                if self.agent.email_recipient is None or not self.agent.is_email_format_valid(self.agent.email_recipient):
                    while True:
                        try:
                            input_email = input("Unesite email na koji će se poslati obavijest o cijenama: ")
                            if self.agent.is_email_format_valid(input_email):
                                self.agent.email_recipient = input_email
                                break
                        except Exception:
                            print("Unijeli ste nepravilan email, pokušajte ponovno.")        
                
                self.set_next_state('ProcessData')
            else:
                self.set_next_state('WaitForMessage')
    
    class ProcessData(State):
        async def run(self):
            self.agent.found_products_within_price = []
            for product in self.agent.offers:
                if product['price'] <= self.agent.user_max_price:
                    self.agent.found_products_within_price.append(product)

            if len(self.agent.found_products_within_price) == 0:
                print("Agent 2: Nisam pronašao željeni proizvod koji zadovoljava Vašu cijenu")
                msg = Message(to="agent1@DESKTOP-TQI23PE", body=json.dumps({'found': False}))
                await self.send(msg)
                await sleep(2)
                self.set_next_state('WaitForMessage')
            else:
                print("Agent 2: Pronašao sam željeni proizvod koji zadovoljava Vašu cijenu, šaljem Vam obavijest na email")
                msg = Message(to="agent1@DESKTOP-TQI23PE", body=json.dumps({'found': True}))
                await self.send(msg)
                await sleep(2)
                self.set_next_state('SendEmail')

    def is_email_format_valid(self, email):
        return '@' in email and '.' in email.split('@')[1]


    class SendEmail(State):
        async def run(self):
            mail_body = "Pronađeni su sljedeći proizvodi koji zadovoljavaju vaše kriterije:\n"
            for product in self.agent.found_products_within_price:
                mail_body += "\n"
                mail_body += "Naziv proizvoda: " + product['product_name'] + "\n"
                mail_body += "Cijena proizvoda: " + str(product['price']) + " €" + "\n"
                mail_body += "Naziv trgovine: " + product['shop_name'] + "\n"
                mail_body += "Link do proizvoda u trgovini: " + product['shop_link'] + "\n"
                mail_body += "------------------------------------------"

            msg = MIMEText(mail_body)
            msg['Subject'] = self.agent.subject
            msg['From'] = self.agent.email_sender
            msg['To'] = self.agent.email_recipient

            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp_server:
                smtp_server.login(self.agent.email_sender, self.agent.passwd_sender)
                smtp_server.sendmail(self.agent.email_sender, self.agent.email_recipient, msg.as_string())
                print("Agent 2: Poslao sam obavijest na email.")

            await self.agent.stop()