from chalice import Chalice
import json
import random
import datetime
from urllib2 import Request, urlopen
from bs4 import BeautifulSoup
from pytz import timezone

app = Chalice(app_name='contest_alarm')

targetUrl = "http://codeforces.com/contests" #Codeforces contest page
hookUrl = "https://hooks.slack.com/services/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" #RUN Slack hook Url to channel #contest_alarm
channelName = "contest_alarm"
botName = "Codeforces Bot"
hourDifference = 6 # Korea is UTC + 9 and Codeforces system is UTC + 9
timeFormat = "%Y/%m/%d %I:%M %p"

@app.route('/local')
def local(): #This function is just for chalice local test.
    returnValue = index(None, None)
    return returnValue

@app.route('/')
def index(event, context): #This function is main function that works in AWS Lambda.
    response = urlopen(targetUrl)
    parseHtmlInfo(response, hookUrl, channelName)
    return {'ok': 'yes'}


def generateAttachPayload(title, text):
    attachPayload = {}
    attachPayload["title"] = title
    attachPayload["text"] = text
    attachPayload["color"] = "#%06X" % random.randint(0, 0xFFFFFF)
    return attachPayload

def generateAndSendPayload(titleText, attachments, targetChannelUrl, targetChannelName):
    payload = {}
    payload["channel"] = targetChannelName
    payload["username"] = botName
    payload["text"] = titleText
    payload["attachments"] = attachments
    req = Request(targetChannelUrl, json.dumps(payload))
    urlopen(req)

def parseHtmlInfo(response, targetChannelUrl, targetChannelName):
    bsObj = BeautifulSoup(response.read(), "html.parser")
    contestInfo = bsObj.findAll("div", {"class": "datatable"})[0]

    allRows = contestInfo.findAll("tr")
    numRows = len(allRows) - 1

    headRow = allRows[0].findAll("th")

    attachments = []
    titleText = "*<%s|Go to Codeforces contests list>*\n" % (targetUrl)
    currentTime = datetime.datetime.now(timezone('Asia/Seoul')).strftime(timeFormat)
    titleText += "Current time: %s" % (currentTime)
    for contNum in range(numRows):
        if (contNum >=3):
            break
        attachText = ""
        attachTitle = ""
        dataRow = allRows[contNum + 1].findAll("td")
        for i in range(len(headRow)):
            headText = headRow[i].text.strip()
            dataText = dataRow[i].text.strip()
            if (len(headText) == 0):
                if (len(dataText) == 0):  # Check exception case
                    continue
                else:  # Attributes with no headTexts
                    newDataList = []
                    dataList = dataText.split(" ")
                    for i in range(len(dataList)):
                        if (len(dataList[i]) != 0):
                            newDataList.append(dataList[i])
                    newDataText = " ".join(newDataList)
                    attachText += "%s\n" % (newDataText)
            else:
                if (len(dataText) == 0):
                    dataText = "Unknown"
                if (headText == "Name"):  # Contest name
                    attachTitle += "%s : %s\n" % (headText, dataText)
                elif (headText == "Start"):  # Contest start time
                    startTime = datetime.datetime.strptime(dataText, "%b/%d/%Y %H:%M")
                    startTime += datetime.timedelta(hours=hourDifference)
                    adjustedDate = startTime.strftime(timeFormat)
                    attachText += "%s : %s\n" % (headText, adjustedDate)
                elif (headText == "Writers"):
                    continue
                else:  # Other attributes
                    attachText += "%s : %s\n" % (headText, dataText)
        attachPayload = generateAttachPayload(attachTitle, attachText)
        attachments.append(attachPayload)

    generateAndSendPayload(titleText, attachments, targetChannelUrl, targetChannelName)

