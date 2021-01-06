import requests
import re
import base64
import ujson

class JWC_Spider():
    def __init__(self, student_id='', password='', state=0):
        self.student_id = student_id
        self.password = password
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
        self.state = state # 0 => unvarified   1 => need captcha   2 => varified

    def __b64Img(self, img, header='base64://'):
        try:
            b64_img = str(base64.b64encode(img), 'utf-8')
            return (True, header + b64_img)
        except:
            return (False, 'base64编码失败')
    
    def need_reverify(self) -> bool:
        if self.state != 2: return False
        url = 'http://zhjw.scu.edu.cn/'
        self.headers["Accept"] = "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9"
        self.headers["Referer"] = "http://zhjw.scu.edu.cn/student/personalManagement/personalApplication/curriculumReplacement/index"
        self.headers['X-Requested-With'] = ''
        response = self.session.get(url, headers=self.headers)
        if response.status_code != requests.codes.ok: return True
        return re.search(r"欢迎您", response.content.decode("utf-8")) is None
    
    def get_name(self): # bool, str
        url = 'http://zhjw.scu.edu.cn/student/rollManagement/rollInfo/index'
        self.headers['Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9'
        self.headers['Referer'] = 'http://zhjw.scu.edu.cn/'
        response = self.session.get(url, headers=self.headers)
        if response.status_code != requests.codes.ok:
            return (False, '请求教务处网站失败')
        res = re.findall(r'title=".*的照片', response.content.decode('utf-8'))
        name = res[0][7:].replace('的照片', '')
        return (True, name)

    def get_headPic(self): # bool, base64(str)
        url = 'http://zhjw.scu.edu.cn/main/queryStudent/img?'
        self.headers['Accept'] = 'image/avif,image/webp,image/apng,image/*,*/*;q=0.8'
        self.headers['Referer'] = 'http://zhjw.scu.edu.cn/student/courseSelect/thisSemesterCurriculum/index'
        stdPic_req = self.session.get(url, headers=self.headers)
        if stdPic_req.status_code != requests.codes.ok:
            return (False, '头像请求失败')
        return self.__b64Img(stdPic_req.content)

    def get_captcha(self, student_id: str, password: str): # 返回 bool, 验证码的base64编码
        self.student_id = student_id
        self.password = password
        url = 'http://zhjw.scu.edu.cn/img/captcha.jpg'
        captcha_req = self.session.get(url)
        if captcha_req.status_code != requests.codes.ok:
            return (False, '验证码请求失败')
        if self.state != 3:
            self.state = 1
        return self.__b64Img(captcha_req.content)
    
    
    def set_captcha(self, str_captcha: str): # bool, str
        # 模拟登陆
        url = 'http://zhjw.scu.edu.cn/j_spring_security_check'
        data = {
            'j_username': self.student_id,
            'j_password': self.password,
            'j_captcha': str_captcha,
            '_spring_security_remember_me': 'on'
        }
        self.headers['Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9'
        self.headers['Referer'] = 'http://zhjw.scu.edu.cn/login'
        self.headers['X-Requested-With'] = ''
        response = self.session.post(url, data=data, headers=self.headers)
        if response.status_code != requests.codes.ok:
            return (False, 'SCU教务处访问失败')
        isError = re.findall(r'errorCode=', response.content.decode('utf-8'))
        if isError:
            return (False, '账号/密码/验证码错误，验证失败')
        else:
            return (True, '验证成功')
    
    def get_now_course(self, flag=0): # 0=>all 1=>today 2=>tomorrow
        url = 'http://zhjw.scu.edu.cn/student/courseSelect/thisSemesterCurriculum/ajaxStudentSchedule/curr/callback'
        self.headers['Accept'] = '*/*'
        self.headers['Referer'] = 'http://zhjw.scu.edu.cn/student/courseSelect/thisSemesterCurriculum/index'
        self.headers['X-Requested-With'] = 'XMLHttpRequest'
        response = self.session.get(url, headers=self.headers)
        course_json = ujson.loads(response.content.decode('utf-8'))
        retinfo = {
            "totalUnits": 0,
            "courseNum": 0,
            "courseList": [] # { "courseName": xxx, "teacher": xxx, "type": xxx, "time_and_locate": []}
        }
        retinfo["totalUnits"] = course_json["dateList"][0]["totalUnits"]
        retinfo["courseNum"] = len(course_json["dateList"][0]["selectCourseList"])
        for idx in range(retinfo["courseNum"]):
            tcourse = course_json["dateList"][0]["selectCourseList"][idx]
            oneCourse = {
                "courseName": tcourse["courseName"],
                "teacher": tcourse["attendClassTeacher"],
                "type": tcourse["coursePropertiesName"],
                "time_and_locate": []
            }
            for timePlace in tcourse["timeAndPlaceList"]:
                locate = timePlace["campusName"] + "-" + timePlace["teachingBuildingName"] + "-" + timePlace["classroomName"]
                classtime = "{} | 星期{} | 第{}到{}节".format(timePlace["weekDescription"], timePlace["classDay"], timePlace["classSessions"], timePlace["classSessions"] + timePlace["continuingSession"] - 1)
                oneCourse["time_and_locate"].append({"time": classtime, "locate": locate})
            retinfo["courseList"].append(oneCourse)
        return retinfo

