import math
import sys
import time
import threading
import random
import requests

from PIL import Image
from requests.adapters import HTTPAdapter
from threading import Barrier

class Canvas:
    RGB_CODE_DICTIONARY = {
        (255, 255, 255): 0,
        (228, 228, 228): 1,
        (136, 136, 136): 2,
        (34, 34, 34): 3,
        (255, 167, 209): 4,
        (229, 0, 0): 5,
        (229, 149, 0): 6,
        (160, 106, 66): 7,
        (229, 217, 0): 8,
        (148, 224, 68): 9,
        (2, 190, 1): 10,
        (0, 211, 211): 11,
        (0, 131, 199): 12,
        (0, 0, 234): 13,
        (207, 110, 228): 14,
        (130, 0, 128): 15
    }

    sessionObj = None
    loginObj = None
    percent = None
    threadID = None

    def __init__(self, sessionObj, loginObj, percent, threadID):
        self.sessionObj = sessionObj
        self.loginObj = loginObj
        self.percent = percent
        self.threadID = threadID

    def distance(self, c1, c2):
        (r1, g1, b1) = c1
        (r2, g2, b2) = c2
        return math.sqrt((r1 - r2) ** 2 + (g1 - g2) ** 2 + (b1 - b2) ** 2)

    def find_palette(self, point):
        colors = list(self.RGB_CODE_DICTIONARY.keys())
        closest_colors = sorted(colors, key=lambda color: self.distance(color, point))
        closest_color = closest_colors[0]
        code = self.RGB_CODE_DICTIONARY[closest_color]
        return code

    def place_pixel(self, ax, ay, new_color):
        consoleMsg = "[{}] - Probing absolute pixel ({},{})".format(self.threadID, ax, ay)

        while True:
            self.loginObj = self.sessionObj.get("http://reddit.com/api/place/pixel.json?x={}&y={}".format(ax, ay),
                                                timeout=5)
            if self.loginObj.status_code == 200:
                data = self.loginObj.json()
                break
            else:
                print("ERROR: ", self.loginObj, self.loginObj.text)
            time.sleep(5)

        old_color = data["color"] if "color" in data else 0
        if old_color == new_color:
            print("{}: skipping, color #{} set by {}".format(consoleMsg, new_color, data[
                "user_name"] if "user_name" in data else "<nobody>"))
            time.sleep(.5)
        else:
            print("{}: Placing color #{} ...".format(consoleMsg, new_color, ax, ay))
            self.loginObj = self.sessionObj.post("https://www.reddit.com/api/place/draw.json",
                                                 data={"x": str(ax), "y": str(ay), "color": str(new_color)})

            secs = float(self.loginObj.json()["wait_seconds"])
            if "error" not in self.loginObj.json():
                consoleMsg = "-[{}]-->Success! Placed color @({},{}), waiting {} seconds. {}% complete."
            else:
                consoleMsg = "-[{}]-->Cooldown is active for ({},{}), waiting {} seconds. {}% complete."

            timeToWait = int(secs) + 2
            while timeToWait > 0:
                prog = consoleMsg.format(self.threadID, ax, ay, timeToWait, self.percent)
                time.sleep(1)
                timeToWait -= 1
                if timeToWait > 0:
                    print(prog, end='           \r')
                else:
                    print(prog)

            if "error" in self.loginObj.json():
                self.place_pixel(ax, ay, new_color)

    def shuffle2d(self, arr2d, rand=random):
        """Shuffes entries of 2-d array arr2d, preserving shape."""
        reshape = []
        data = []
        iend = 0
        for row in arr2d:
            data.extend(row)
            istart, iend = iend, iend + len(row)
            reshape.append((istart, iend))
        rand.shuffle(data)
        return [data[istart:iend] for (istart, iend) in reshape]


class Session:
    session = None
    login = None
    username = None
    password = None

    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.session = requests.Session()  # create persistent session
        self.session.mount('https://www.reddit.com', HTTPAdapter(max_retries=5))
        self.session.headers["User-Agent"] = "PlacePlacer"
        self.ensure_valid_login()

    def ensure_valid_login(self):
        while 1:
            try:
                self.login = self.session.post("https://www.reddit.com/api/login/{}".format(self.username),
                                               data={"user": self.username, "passwd": self.password,
                                                     "api_type": "json"})
                self.session.headers['x-modhash'] = self.login.json()["json"]["data"]["modhash"]
            except KeyError:
                print("Bad login info, please verify the username/password combination "
                      "for \'{}\' and try again!".format(self.username))
                self.username = input("Re-enter username (prev='{}'): ".format(self.username))
                self.password = input("Re-enter password (prev='{}'): ".format(self.username))
            else:
                break


def distribute_pixel_placement(barrier, mutex, threadID, percentage, img, startPosition):
    mutex.acquire() # allows user to input each username/pw without being interrupted by other threads
    usr = input("[{}] Username: ".format(threadID + 1))
    pwd = input("[{}] Password: ".format(threadID + 1))
    mutex.release()
    barrier.wait() # once user has entered the information, threads are released
    while 1:
        thrSession = Session(usr, pwd)
        thrCanvas = Canvas(thrSession.session, thrSession.login, percentage, threadID)

        print("Thread-{} :starting image placement for img height: {}, width: {}".format(threadID, img.height, img.width))
        TwoDimArray = thrCanvas.shuffle2d([[[i,j] for i in range(img.width)] for j in range(img.height)])
        total = img.width * img.height
        checked = 0
        for x in range(img.width):
            for y in range(img.height):
                xx = TwoDimArray[x][y]
                pixel = img.getpixel((xx[0], xx[1]))

                if pixel[3] > 0:
                    pal = thrCanvas.find_palette((pixel[0], pixel[1], pixel[2]))

                    ax = xx[0] + startPosition[0]
                    ay = xx[1] + startPosition[1]

                    thrCanvas.place_pixel(ax, ay, pal)
                    checked += 1
                    thrCanvas.percent = round((checked/total) * 100, 2)

        consoleMessage = "All pixels placed, sleeping {}s..."
        timeToWait = 60
        while timeToWait > 0:
            msg = consoleMessage.format(timeToWait)
            time.sleep(1)
            timeToWait -= 1
            if timeToWait > 0:
                print(msg, end='              \r')
            else:
                print(msg)


def main():
    # read from command line arguments
    #targetImage = Image.open(sys.argv[1]) # open up desired image
    #start = (int(sys.argv[2]), int(sys.argv[3])) # position of top left image (x and y on canvas)
    targetImage = Image.open("test.png")  # todo: add check for if file exists
    start = (808, 641) # todo: get rid of hard code
    percentage = 0

    # can reprocess this so that it creates a thread for each valid username and password combination ...
    # use console in and process one by one ...

    while 1:
        numberOfAccounts = input("Please enter the number of accounts you would like to use: ")
        try:
            isInteger = int(numberOfAccounts)
            if isInteger <= 0:
                raise ValueError("Number of accounts must be greater than or equal to 0")
            print("Input accepted!")
            break
        except ValueError as err:
            print(err.args)

    mutex = threading.Lock()
    barrier = Barrier(int(numberOfAccounts), timeout=50)
    for account in range(0, int(numberOfAccounts)):
        new_thread = threading.Thread(target=distribute_pixel_placement,
                                      args=(barrier, mutex, account, percentage, targetImage, start,))
        # new_thread.daemon = True
        new_thread.start()

if __name__ == "__main__":
    main()
