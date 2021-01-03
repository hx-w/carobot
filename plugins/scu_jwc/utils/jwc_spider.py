import requests
import re
import base64

class JWC_Spider():
    def __init__(self):
        self.username = ''
        self.password = ''
        self.session = requests.session()
        self.headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Connection': 'keep-alive',
            'Host': 'zhjw.scu.edu.cn',
            'Referer': 'http://zhjw.scu.edu.cn/login',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Mobile Safari/537.36',
            'Origin':'http://zhjw.scu.edu.cn',
        }

    def __b64Img(self, img, header='base64://'):
        try:
            b64_img = str(base64.b64encode(img), 'utf-8')
            return (True, header + b64_img)
        except:
            return (False, 'base64编码失败')
        

    def get_captcha(self, student_id: str, password: str): # 返回 Bool, 验证码的base64编码
        url = 'http://zhjw.scu.edu.cn/img/captcha.jpg'
        captcha_req = self.session.get(url)
        if captcha_req.status_code != requests.codes.ok:
            return (False, '验证码请求失败')
        return self.__b64Img(captcha_req.content)

