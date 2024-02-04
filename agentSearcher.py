import time
import json

from spade.message import Message
from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from asyncio import sleep
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException 


class AgentSearcher(Agent):
    def __init__(self, jid, password, checkPricesMinutes): 
        super().__init__(jid, password)
        self.delaySeconds = checkPricesMinutes * 60
        self.product_search_name = ""
        self.selected_product_number = 0
        

    class Behavior(CyclicBehaviour):
        async def on_start(self):
            print("Pokrećem agenta pretraživaća (Agent 1)")

        async def on_end(self):
            print("Gasim agenta pretraživaća (Agent 1)")

        async def run(self):
            try:
                if self.agent.product_search_name == "":
                    self.agent.product_search_name = input('Unesite naziv proizvoda: ')

                options = webdriver.ChromeOptions()
                options.add_experimental_option("excludeSwitches", ["enable-logging"])

                web_browser = webdriver.Chrome(options=options)
                web_browser_wait = WebDriverWait(web_browser, 10)
                web_browser.get('https://www.nabava.net')

                web_browser_wait.until(EC.presence_of_element_located((By.XPATH,'/html/body/header/div/form/input[1]'))).send_keys(self.agent.product_search_name)
                web_browser_wait.until(EC.presence_of_element_located((By.XPATH,'/html/body/header/div/form/input[1]'))).send_keys(Keys.ENTER)
                time.sleep(1)
                parent_products_div = web_browser.find_element(by=By.XPATH, value='//*[@class="search-results content__section--no-side-margins  "]')
                products_elements = parent_products_div.find_elements(by=By.CLASS_NAME, value='product')
                relevant_products = products_elements[:10]
                for i, product_element in enumerate(relevant_products):
                    price_element = product_element.find_element(by=By.CLASS_NAME, value='product__price')
                    name_element = product_element.find_element(by=By.CLASS_NAME, value='product__link')
                    print(f"{i+1}: {name_element.text} | {price_element.text}")
                
                if self.agent.selected_product_number == 0:
                    while True:
                        try:
                            print("\n")
                            selected_input_number = int(input("Odaberi proizvod [1-10]: "))
                            if selected_input_number >= 1 and selected_input_number <= 10:
                                self.agent.selected_product_number = selected_input_number
                                break
                        except Exception:
                            print("Krivi unos, pokušajte ponovno.")
                
                seleceted_product = relevant_products[self.agent.selected_product_number-1]
                product_link_element = seleceted_product.find_element(by=By.CLASS_NAME, value='product__link')
                product_link_element.click()
                time.sleep(2)

                offers = web_browser.find_element(by=By.XPATH, value='//*[@class="content__section content__section--no-top-margin content__section--no-side-margins"]')
                all_offers = offers.find_elements(by=By.CLASS_NAME, value='offer')

                offers_info = []
                for offer in all_offers:
                    offer_price_element = offer.find_element(by=By.CLASS_NAME, value='offer__price')
                    offer_stock = offer.find_element(by=By.CLASS_NAME, value='offer__availability')
                    offer_name_element = offer.find_element(by=By.CLASS_NAME, value='offer__name')
                    offer_name_text = offer_name_element.find_element(by=By.XPATH, value='.//h2').text
                    offer_shop_link = offer.find_element(by=By.CLASS_NAME, value='offer__buttons-to-store')
                    offer_shop_link_text = offer_shop_link.get_attribute('href')
                    
                    try:
                        offer_shop_name = offer.find_element(by=By.CLASS_NAME, value='offer__store-logo')
                        offer_shop_name_text = offer_shop_name.get_attribute('alt')
                    except NoSuchElementException:
                        offer_shop_name = offer.find_element(by=By.CLASS_NAME, value='offer__store-link')
                        offer_shop_name_text = offer_shop_name.text
                        

                    offer_stock_html = offer_stock.get_attribute('outerHTML')
                    if 'availability-5.svg' in offer_stock_html:
                        #ponuda nije dostupna,pa idi na iducu ponudu
                        continue

                    offer_price_text = offer_price_element.text
                    offer_price_text = offer_price_text.replace('.', '')
                    offer_price_text = offer_price_text.replace(',', '.')
                    offer_price_text = offer_price_text.replace(' €', '')
                    offer_price = float(offer_price_text)
                    
                    product_info = {'product_name': offer_name_text, 'price': offer_price, 'shop_name': offer_shop_name_text, 'shop_link': offer_shop_link_text}
                    offers_info.append(product_info)
                
                web_browser.quit()

                msg = Message(to="agent2@DESKTOP-TQI23PE", body=json.dumps({'offers': offers_info}))
                await self.send(msg)
                
                print("Agent 1: Poslana je poruka drugom agentu.")

                msg = await self.receive(timeout=10000)
                if msg:
                    found_lower_offer = json.loads(msg.body)['found']
                    if found_lower_offer:
                        await self.agent.stop()
                        return

                print(f"Agent 1: Ponovno ću provjeriti cijene nakon {self.agent.delaySeconds} sekundi / {int(self.agent.delaySeconds / 60)} minuta")
                await sleep(self.agent.delaySeconds)
            except Exception:
                print("Pojavila se greška prilikom pretraživanja, pokušajte ponovno.")
                self.agent.selected_product_number = 0
                self.agent.product_search_name = ""
                await sleep(1)
         

    async def setup(self):
        behaviour = self.Behavior()
        self.add_behaviour(behaviour)