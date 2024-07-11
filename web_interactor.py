import os
import numpy as np
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait, Select

PATH_DATA = "./Data"
TIMEOUT = 10  # seconds

class WebInteractor:
    def __init__(self, url, credentials=None):
        self.URL = url
        self._driver = self._driver_setup()
        self._driver.get(self.URL["base_url"])

        # Accept and close privacy preference window
        self._wait(By.XPATH, "/html/body/div[1]/div/div/div/div[2]/div/button[2]", TIMEOUT).click()

        if credentials is not None:
            self._login(credentials)

    def _driver_setup(self):
        service = Service()
        options = webdriver.ChromeOptions()
        options.add_experimental_option("detach", True)
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--ignore-ssl-errors')
        driver = webdriver.Chrome(service=service, options=options)
        return driver

    def _login(self, credentials):
        # Open login menu
        self._wait(By.ID, "menu-button-user", TIMEOUT).click()

        # Input credentials and click login button
        self._wait(By.NAME, "email", TIMEOUT).send_keys(credentials["email"])
        self._wait(By.NAME, "password", TIMEOUT).send_keys(credentials["password"])
        self._wait(By.CLASS_NAME, "button-login", TIMEOUT).click()

        self._wait(By.ID, "user-cert", TIMEOUT)

    ''' 
        Wait until an element is visible on the page, then retrieve that element.
    '''
    def _wait(self, locator, value, timeout):
        return WebDriverWait(self._driver, timeout).until(EC.visibility_of_element_located((locator, value)))

    '''
        Scrape puzzles with the specified size, difficulty and ID.
        For puzzles larger than 20 in size, the IDs need to be specified since they cannot be accessed randomly. 
    '''
    def scrape_puzzle(self, size, difficulty=None, amount=None, ids=None):
        # If IDs are specified or puzzles larger than 20 in size
        if ids is not None:
            for id in ids:
                # Make sure there are no duplicate
                if not os.path.exists(f"{PATH_DATA}/{size}{difficulty if difficulty is not None else ''}/{id}.txt"):
                    id, borders = self.open_puzzle(size, difficulty, id)
                    self.save_puzzle(id, borders, size, difficulty)
        else:
            scraped = 0
            while scraped < amount:
                id, borders = self.open_puzzle(size, difficulty)
                # Make sure there are no duplicate
                if not os.path.exists(f"{PATH_DATA}/{size}{difficulty if difficulty is not None else ''}/{id}.txt"):
                    self.save_puzzle(id, borders, size, difficulty)
                    scraped += 1

    '''
        This method opens a puzzle with the specified size, difficulty and ID.
        For puzzles larger than size 20, there are no choices for the difficulty. Therefore, the difficulty should not be specified. 
        The method can open:
        - A random puzzle, where the ID should not be specified.
        - A specific puzzle, where the ID should be specified.
            For puzzles larger than size 20, a specific puzzle is accessed by opening the corresponding puzzle's URL and selecting the ID from a select element.

        @return id: string
        @return borders: dict
    '''
    def open_puzzle(self, size, difficulty=None, id=None):
        # Open puzzle #
        url = self.URL["base_url"]
        # Specific puzzles larger than 20 in size
        if size <= 20 and id:
            url += self.URL["specific_url"]
        else:
            if size <= 20:
                url += self.URL["size_url"][size][difficulty]
            else:
                url += self.URL["size_url"][size]
        self._driver.get(url)

        # Specific puzzles
        if id is not None:
            if size <= 20:
                # Input puzzle attributes and click button
                self._wait(By.ID, "specid", TIMEOUT).send_keys(id)
                Select(self._wait(By.ID, "size", TIMEOUT)).select_by_value(self.URL["size_url"][size][difficulty][-1])
                self._wait(By.XPATH, "//*[@id='pageContent']/div[2]/div[2]/form[1]/table/tbody/tr[3]/td[2]/input",
                           TIMEOUT).click()
            else:
                select_element = Select(self._wait(By.NAME, "date", TIMEOUT))
                # Open puzzle only when the specified id exists
                if id in [option.get_attribute("value") for option in select_element.options]:
                    select_element.select_by_value(id)
                    self._wait(By.NAME, "specific", TIMEOUT).click()
                else:
                    return None, None

        # Get puzzle ID #
        if size <= 20:
            id = self._wait(By.ID, "puzzleID", TIMEOUT).text
        else:
            id = Select(self._wait(By.NAME, "date", TIMEOUT)).first_selected_option.get_attribute("value")

        # Get borders #
        # vertical_lines: 2-dimensional array[size][size - 1], flattened into bitstring. Holds information about the presence of a right border in a cell (except the last cell of every row).
        # horizontal_lines: 2-dimensional array[size - 1][size], flattened into bitstring. Holds information about the presence of a bottom border in a cell (except every cell in the last row).
        self._wait(By.CLASS_NAME, "cell", TIMEOUT)
        cells = self._driver.find_elements(By.CLASS_NAME, "cell")
        vertical_lines = ""
        horizontal_lines = ""

        for i in range(size):
            for j in range(size):
                classes = cells[i * size + j].get_attribute("class").split()
                if j + 1 < size:
                    if "br" in classes:
                        vertical_lines += "1"
                    else:
                        vertical_lines += "0"
                if i + 1 < size:
                    if "bb" in classes:
                        horizontal_lines += "1"
                    else:
                        horizontal_lines += "0"
        borders = {"horizontal": horizontal_lines, "vertical": vertical_lines}
        return id, borders

    def save_puzzle(self, id, borders, size, difficulty=None):
        data = [
            f"{id}\n",
            f"{size} {difficulty if difficulty is not None else ''}\n",
            f"{borders['horizontal']}\n",
            f"{borders['vertical']}\n"
        ]
        path = f"{PATH_DATA}/{size}{difficulty if difficulty is not None else ''}/{id}.txt"
        file = open(path, "x")
        file.writelines(data)
        file.close()

    '''
        @params answer: 2-dimensional array of integer
    '''
    def input_answer(self, answer):
        self._wait(By.ID, "btnSettings", TIMEOUT).click()
        self._wait(By.CLASS_NAME, "rotate", TIMEOUT).click()
        self._wait(By.ID, "btnSettings", TIMEOUT).click()

        self._wait(By.CLASS_NAME, "cell", TIMEOUT)
        cells = self._driver.find_elements(By.CLASS_NAME, "cell")
        # Convert answer from a 2-dimensional array to a 1-dimensional array
        answer = [cell for row in answer for cell in row]

        for ans, cell in zip(answer, cells):
            cell.click()
            if ans == 0:
                cell.click()  # Right click

        # Click submit button
        self._wait(By.ID, "btnReady", TIMEOUT).click()

    '''
        @return answer: 2-dimensional array of integer
    '''
    def get_answer(self, size, id, difficulty=None):
        self.open_puzzle(size, difficulty, id)
        self._wait(By.ID, "btnGiveUp", TIMEOUT).click()
        alert = WebDriverWait(self._driver, timeout=2).until(lambda d: d.switch_to.alert)
        alert.accept()

        self._wait(By.CLASS_NAME, "cell", TIMEOUT)
        cells = self._driver.find_elements(By.CLASS_NAME, "cell")
        answer = []
        for i in range(size ** 2):
            classes = cells[i].get_attribute("class").split()
            if "cell-on" in classes:
                answer.append(1)
            else:
                answer.append(0)
        return np.array(answer).reshape(size, size)

    def close(self):
        self._driver.close()
