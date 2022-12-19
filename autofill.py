from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import undetected_chromedriver as uc

import logging

import random
# import time
import names
import markovify
import os
import sys
from anticaptchaofficial.recaptchav2proxyless import *
from dotenv import load_dotenv
load_dotenv()


cities = ["Dallas", "Austin", "Houston", "Hazel", "Fort Worth"]
corpus = open("./corpus.txt",encoding='utf8').read()
model = markovify.Text(corpus)
input_text = ""
for (i) in range(random.randint(1, 10)):
    input_text += model.make_sentence()

# [name, email, location, info]
form_types = [
    ["input_2_1", "input_2_3", "input_2_4", "input_2_5", "gform_submit_button_2"],
    ["et_pb_contact_name_0", "et_pb_contact_email_0", "et_pb_contact_location_of_show_0", "et_pb_contact_other_info_0", "et_builder_submit_button"],
]

# finding the submit button seems to work well by looking for type=submit
submit_buttons = [
    # [By.ID, "gform_submit_button_2"],
    [By.XPATH, "//*[@id='popup']//input[@type='submit']"]
]

class FormType():
    use_solver = False

    def __init__(self, name, email, location, info):
        self.name = name
        self.email = email
        self.location = location
        self.info = info


class Selenium():
    def __init__(self):
        self.driver = uc.Chrome(use_subprocess=True, version_main=os.getenv('CHROME_VERSION'))
        self.wait = WebDriverWait(self.driver, 3000000000)

        # setup anti-captcha solver
        self.solver = recaptchaV2Proxyless()
        self.init_solver()

    def wait_for(self, condition, timeout=10):
        return WebDriverWait(self.driver, timeout=timeout).until(condition)

    def run(self):
        try:
            logging.debug('Reloading page')
            self.driver.get('https://defendkidstx.com/')

            self.check_page_loaded()
            time.sleep(random.randrange(1, 3))

            self.click_report_button()
            time.sleep(random.randrange(1, 2))

            self.fill_form()

            if not self.use_solver:
                self.check_recaptcha()

            time.sleep(random.randrange(1, 4))
            self.submit()

        except Exception:
            logging.warning('Something happened!')
            pass

    def check_page_loaded(self):
        try:
            return self.wait_for(EC.title_contains("Defend"), 10)
        except TimeoutException:
            if "Access denied" in self.driver.title:
                logging.warning('Temporarily blocked (nice!)')
            else:
                logging.warning('Unable to load page')
            raise Exception

    def click_report_button(self):
        try:
            # Click the report button
            # self.wait_for(EC.element_to_be_clickable((By.XPATH, "//img[@title='report-resize-mins']")), 5).click()
            self.driver.find_element(By.XPATH, "//img[@title='report-resize-min']").click()
            logging.debug('Report button clicked!')
        except NoSuchElementException:
            logging.warning('Report button not found!')
            raise Exception

    def check_recaptcha(self):
        try:
            # self.driver.switch_to.frame(self.driver.find_element(By.XPATH, "//div[@id='input_2_6']//iframe[contains(@title,'reCAPTCHA')]"))
            # self.wait_for(EC.frame_to_be_available_and_switch_to_it((By.XPATH, "//*[@id='popup']//iframe")), 5)

            # test if reCAPTCHA is present
            self.driver.find_element(By.XPATH, "//*[@id='popup']//iframe")

            if self.use_solver:
                captcha_solution = self.get_captcha_solution()
                if not self.fill_captcha(captcha_solution):
                    logging.warning("error filling captcha")
            else:
                self.driver.switch_to.frame(self.driver.find_element(By.XPATH, "//*[@id='popup']//iframe"))

                # Click on the checkbox
                logging.debug('Clicking reCAPTCHA')
                checkbox = self.wait_for(EC.element_to_be_clickable((By.ID, "recaptcha-anchor")), 5)
                checkbox.click()

                # Wait until the reCAPTCHA box is checked
                logging.info('Waiting for reCAPTCHA')
                self.wait_for(lambda x: checkbox.get_attribute("aria-checked") == 'true', 600)
                logging.debug('reCAPTCHA finished!')

                self.driver.switch_to.default_content()

        except NoSuchElementException:
            self.driver.switch_to.default_content()
            logging.debug('reCAPTCHA not found')
        except TimeoutException:
            self.driver.switch_to.default_content()
            logging.debug('reCAPTCHA timed out')

    def check_exists_by_id(self, id):
        try:
            element = self.driver.find_element(By.ID, id)
            if element:
                return element.is_displayed()
        except NoSuchElementException:
            return False

    def get_form_type(self) -> FormType:
        for check_type in form_types:
            logging.debug(f"checking name {check_type[0]}")
            form_type = FormType(check_type[0], check_type[1], check_type[2], check_type[3])
            try:
                self.driver.find_element(By.ID, form_type.name).is_displayed()
                return form_type
                # if self.check_exists_by_id(form_type.name):
                    # return form_type
            except NoSuchElementException:
                logging.debug(f"form_type is not {form_type.name}")
                continue
        logging.warning("Looks like they may have found a way to beat this scraper. Perhaps you could help update it!")

    # it might be possible to get the form element and run its submit method instead of finding the submit button
    def submit(self):
        for button in submit_buttons:
            logging.debug(f"trying button {button[1]}")
            try:
                self.driver.find_element(button[0], button[1]).click()
                return
            except NoSuchElementException:
                logging.warning(f"couldn't find button {button[1]}")

    def init_solver(self):
        self.use_solver = False
        api_key = os.getenv("ANTICAPTCHA_API_KEY")
        if len(api_key) == 0:
            logging.info("No Anti-Captcha API Key Provided, disabling")
            return
        if len(api_key) != 32:
            logging.warning(f"Invalid Anti-Captcha API Key: {api_key}")
            return
        self.solver.set_verbose(1)
        self.solver.set_key(api_key)
        self.solver.set_website_url("https://www.defendkidstx.com/")
        # found in the recaptcha request
        self.solver.set_website_key("6Lf4g08jAAAAADLHLYYA6jsr0qXWgOM_btlJP3iD")
        # use_solver determines if anything runs when any anti-captcha function is called
        self.use_solver = True

    def get_captcha_solution(self) -> str:
        logging.debug("[BEGIN CAPTCHA SOLVE]")
        # solve_and_return_solution blocks until completed
        g_response = self.solver.solve_and_return_solution()
        if g_response != 0:
            logging.info("g-response: "+g_response)
        else:
            logging.warning("anticaptcha task finished with error "+self.solver.error_code)
            # probably not the best idea to just exit on error, could be handled better
            sys.exit(2)
        logging.debug("[END CAPTCHA SOLVE]")
        return g_response

    def fill_captcha(self, captcha_solution):
        try:
            element = self.driver.find_element(By.XPATH, ("//textarea[@name='g-recaptcha-response']"))
            # I was having issues using send_keys, so we're setting the form value directly
            element.__setattr__("value", captcha_solution)
            # element.send_keys(captcha_solution)
        except NoSuchElementException:
            logging.warning("could not find recaptcha textarea")
            return False
        return True

    def fill_form(self):
        logging.debug("Filling out form")
        name = names.get_full_name()
        # they have two alternate input forms, presumably to prevent me from doing things like this - this should account for both
        form_type = self.get_form_type()

        try:
            # if the form hasn't opened properly, this will raise an error and retry
            self.driver.find_element(By.ID, form_type.name).send_keys(name)
            time.sleep(random.random())
            self.driver.find_element(By.ID, form_type.email).send_keys(name.replace(
                    " ", "") + str(random.randint(100000, 500000)) + "@gmail.com")
            # Location cannot contain any special characters, only letters and numbers
            self.driver.find_element(By.ID, form_type.location).send_keys(random.choice(cities))
            time.sleep(random.random())
            self.driver.find_element(By.ID, form_type.info).send_keys(input_text)
            time.sleep(random.random())
        except NoSuchElementException:
            logging.warning("Couldn't fill out form!")


logging.basicConfig(level=logging.INFO)
logging.getLogger('selenium').setLevel(logging.INFO)
logging.getLogger('urllib3').setLevel(logging.INFO)
logging.getLogger('undetected_chromedriver').setLevel(logging.INFO)

form_filler = Selenium()
while True:
    form_filler.run()
    time.sleep(random.randrange(4, 8))
