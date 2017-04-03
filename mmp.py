import math
import sys
import time
import requests
from PIL import Image
from requests.adapters import HTTPAdapter


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

    def __init__(self):
        pass

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
        print("Probing absolute pixel {},{}".format(ax, ay))

        while True:
            r = s.get("http://reddit.com/api/place/pixel.json?x={}&y={}".format(ax, ay), timeout=5)
            if r.status_code == 200:
                data = r.json()
                break
            else:
                print("ERROR: ", r, r.text)
            time.sleep(5)

        old_color = data["color"] if "color" in data else 0
        if old_color == new_color:
            print("Color #{} at {},{} already exists (placed by {}), skipping".format(new_color, ax, ay, data[
                "user_name"] if "user_name" in data else "<nobody>"))
        else:
            print("Placing color #{} at {},{}".format(new_color, ax, ay))
            r = s.post("https://www.reddit.com/api/place/draw.json",
                       data={"x": str(ax), "y": str(ay), "color": str(new_color)})

            secs = float(r.json()["wait_seconds"])
            if "error" not in r.json():
                print("Placed color - waiting {} seconds".format(secs))
            else:
                print("Cooldown already active - waiting {} seconds".format(int(secs)))
            time.sleep(secs + 2)

            if "error" in r.json():
                self.place_pixel(ax, ay, new_color)


class Session:
    session = None
    login = None
    username = None
    password = None

    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.session.mount('https://www.reddit.com', HTTPAdapter(max_retries=5))
        self.session.headers["User-Agent"] = "PlacePlacer"
        self.is_login_valid(self.username, self.password)
        self.session.headers['x-modhash'] = self.login.json()["json"]["data"]["modhash"]

    def is_login_valid(self, usr, pwd):
        self.login = self.session.post("https://www.reddit.com/api/login/{}".format(self.username),
                             data={"user": self.username, "passwd": self.password, "api_type": "json"})
        if self.login.status_code == 200:
            print("RESP 200!!")
        else:
            print("failed login")


def main():
    # read from command line arguments
    # img = Image.open(sys.argv[1]) #open up desired image
    # origin = (int(sys.argv[2]), int(sys.argv[3])) #position of top left image (x and y on canvas)
    # username = sys.argv[4]
    # password = sys.argv[5]

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

    for account in range(0, int(numberOfAccounts)):
        #     #for each account query user for username and password for reddit
        usr = input("Enter your username for reddit: ")
        passwrd = input("Enter your password: ")

        # for each username and password, create a new thread for each and test each one
        #create new thread here???
        while 1:
            interationOf = Session(usr, passwrd)
            break

    #     #create a new thread
    #     #establish a valid session
    #     #login/...

    # establish_valid_session()
    # s = requests.Session()
    # s.mount('https://www.reddit.com', HTTPAdapter(max_retries=5))
    # s.headers["User-Agent"] = "PlacePlacer"
    # #try/catch this when checking for valid username/pw, will if response code != 200, then ask user to reinput
    # r = s.post("https://www.reddit.com/api/login/{}".format(username),
    #            data={"user": username, "passwd": password, "api_type": "json"})
    # s.headers['x-modhash'] = r.json()["json"]["data"]["modhash"]

    # for y in range(img.height):
    #     for x in range(img.width):
    #         pixel = img.getpixel((x, y))
    #
    #         if pixel[3] > 0:
    #             pal = obj.find_palette((pixel[0], pixel[1], pixel[2]))
    #
    #             ax = x + origin[0]
    #             ay = y + origin[1]
    #
    #             obj.place_pixel(ax, ay, pal)

if __name__ == "__main__":
    main()
