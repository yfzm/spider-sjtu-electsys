"""
  Author: Li Hao
  Last edited at 2018/1/31
"""

import codecs
import time

from selenium import webdriver, common
from PIL import Image
import pytesseract
from selenium.webdriver.support.select import Select


class Spider:
    def __init__(self, username, password, log):
        self.login_path = 'http://electsys.sjtu.edu.cn/edu/login.aspx'
        self.username = username
        self.password = password
        self.log = log

        self.driver = webdriver.PhantomJS(executable_path='D:/Program Files/phantomjs-2.1.1/bin/phantomjs.exe')
        # self.driver.set_window_size(1200, 800)
        if self.log:
            print 'Initialization...'

    def get_and_save_capt(self, element):
        self.driver.get_screenshot_as_file('cache/screenshot.png')

        left = int(element.location['x'])
        top = int(element.location['y'])
        right = left + int(element.size['width'])
        bottom = top + int(element.size['height'])

        im = Image.open('cache/screenshot.png')
        im = im.crop((left + 2, top + 2, right - 2, bottom - 2))
        im.save('cache/captcha.png')

    @staticmethod
    def get_ocr_capt():
        text = pytesseract.image_to_string(Image.open('cache/captcha.png'))
        return text.replace(' ', '').replace('\n', '')

    def is_succeeded(self):
        try:
            self.driver.find_element_by_xpath('//*[@id="form-input"]/div[4]/input')
            return False
        except common.exceptions.NoSuchElementException:
            return True

    def login(self):
        if self.log:
            print 'Prepare to log in'

        count = 0
        while True:
            self.driver.get(self.login_path)
            input_user = self.driver.find_element_by_id('user')
            input_pass = self.driver.find_element_by_id('pass')
            input_capt = self.driver.find_element_by_id('captcha')
            img_capt = self.driver.find_element_by_xpath('//*[@id="form-input"]/div[3]/img')
            btn_submit = self.driver.find_element_by_xpath('//*[@id="form-input"]/div[4]/input')

            self.get_and_save_capt(img_capt)
            captcha = self.get_ocr_capt()

            input_user.send_keys(str(self.username))
            input_pass.send_keys(str(self.password))
            input_capt.send_keys(captcha)
            time.sleep(1)

            if self.log:
                print 'Attempt %d time(s): auto-recognize captcha: %s' % (count + 1, captcha)

            btn_submit.click()

            if self.is_succeeded():
                if self.log:
                    print 'Login successfully'
                break

            count += 1
            if count >= 5:
                raise StandardError('Failed to log in, maybe there is something wrong with your username or password.')

            time.sleep(1)

    def switch_to_score(self):
        self.driver.switch_to.frame('leftFrame')
        btn_score = self.driver.find_element_by_xpath(
            '//*[@id="sdtleft"]/table/tbody/tr[2]/td[1]/table/tbody/tr[31]/td[2]/a')
        if self.log:
            print 'Attempt to switch to score page'
        btn_score.click()
        time.sleep(3)

        self.driver.switch_to.default_content()
        self.driver.switch_to.frame('main')
        s_year = Select(self.driver.find_element_by_id('ddlXN'))
        s_year.select_by_value('2017-2018')
        s_year = Select(self.driver.find_element_by_id('ddlXQ'))
        s_year.select_by_value('1')
        btn_search = self.driver.find_element_by_id('btnSearch')
        if self.log:
            print 'Switch to score page successfully'
        btn_search.click()
        time.sleep(3)

    def save_score(self):
        if self.log:
            print 'Prepare to save score to file'
        score_file = codecs.open('score.csv', 'w', 'gb2312')
        subjects = self.driver.find_elements_by_xpath('//*[@id="dgScore"]/tbody/tr')

        for subject in subjects:
            string_temp = ''
            for td in subject.find_elements_by_tag_name('td'):
                string_temp += (td.text.strip() + ',')
            score_file.write(string_temp[:-1] + '\n')

        score_file.close()

        if self.log:
            print 'Score saved in score.csv successfully'

    @staticmethod
    def get_grade_point(score):
        if score == 'A+':
            return 4.3
        elif score == 'A':
            return 4.0
        elif score == 'A-':
            return 3.7
        elif score == 'B+':
            return 3.3
        elif score == 'B':
            return 3.0
        elif score == 'B-':
            return 2.7
        elif score == 'C+':
            return 2.3
        elif score == 'C':
            return 2.0
        elif score == 'C-':
            return 1.7
        elif score == 'D':
            return 1.0
        else:
            score = eval(score)

        if score >= 95:
            return 4.3
        elif score >= 90:
            return 4.0
        elif score >= 85:
            return 3.7
        elif score >= 80:
            return 3.3
        elif score >= 75:
            return 3.0
        elif score >= 70:
            return 2.7
        elif score >= 67:
            return 2.3
        elif score >= 65:
            return 2.0
        elif score >= 62:
            return 1.7
        elif score >= 60:
            return 1.0
        else:
            return 0.0

    @staticmethod
    def get_gpa():
        score_file = codecs.open('score.csv', 'r', 'gb2312')
        gpa = 0.0
        total_score = 0.0
        count = 0
        for line in score_file:
            count += 1

            if count == 1:
                continue

            elements = line.split(',')
            gpa += eval(elements[2]) * Spider.get_grade_point(elements[3])
            total_score += eval(elements[2])

        score_file.close()

        if total_score > 0:
            gpa /= total_score

        return gpa

    def run(self):
        try:
            self.login()
            self.switch_to_score()
            self.save_score()
            print 'Succeed!'
            print 'Your GPA: %.2f' % self.get_gpa()
        except StandardError as e:
            print e

        self.driver.quit()


if __name__ == '__main__':
    spider = Spider(username='ZhangZhe', password='glgjssyqyhfbqz')
    spider.run()
