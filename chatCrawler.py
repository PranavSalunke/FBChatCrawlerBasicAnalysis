# self made crawler to copy/download a partiular chat and gather some data about it
# creates a json file with data about the chat

import userinfo
import fbchat
from fbchat.models import *
from fbchat import ThreadType
import random
import time
import datetime
import traceback
import pprint
import json
import nltk
#  USE PYTHON 3


# ==========HELPER METHODS==========

def localTimeIsUTC():
    # returns true if local time is utc time
    now = datetime.datetime.now()
    nowutc = datetime.datetime.utcnow()
    nowformated = now.strftime("%A %m/%d/%Y %H:%M")  # example: Thursday 01/24/2019 12:14
    nowutcformated = nowutc.strftime("%A %m/%d/%Y %H:%M")

    return (nowformated == nowutcformated)  # if equal, local time is utc


def makeMessageJSON(messsageObj):
    # NOTE: not perfect since some fields have their own class that I'm not taking into consideration
    # reaction objects originally have the person who reacted and what reaction. Now instead of the object, I make it  list of tuples
    # attachment is either true or false in the returned dict instead of object
    # attachment is either true or false in the returned dict instead of object
    # some fields will be missing from the original

    msg = {}
    msg["text"] = messsageObj.text
    msg["mentions"] = len(messsageObj.mentions) > 0  # if there are mentions or not
    msg["uid"] = messsageObj.uid
    msg["author"] = messsageObj.author
    msg["timestamp"] = messsageObj.timestamp
    msg["is_read"] = str(messsageObj.is_read)
    msg["read_by"] = messsageObj.read_by  # list
    msg["unsent"] = str(messsageObj.unsent)

    msg["attachments"] = len(messsageObj.attachments) > 0  # if  empty list or not

    # for reactions, must make the value in the dict not an object
    # ex. MessageReaction.WOW -> WOW
    reactKeys = messsageObj.reactions.keys()
    newReactDict = {}
    if len(reactKeys) > 0:  # has reactions. Makes into a list of tuples
        for k in reactKeys:
            # find coresponding value
            val = messsageObj.reactions[k]
            newval = None

            if val is fbchat.MessageReaction.LOVE:
                newval = "LOVE"
            elif val is fbchat.MessageReaction.SMILE:
                newval = "SMILE"
            elif val is fbchat.MessageReaction.WOW:
                newval = "WOW"
            elif val is fbchat.MessageReaction.SAD:
                newval = "SAD"
            elif val is fbchat.MessageReaction.ANGRY:
                newval = "ANGRY"
            elif val is fbchat.MessageReaction.YES:
                newval = "YES"
            elif val is fbchat.MessageReaction.NO:
                newval = "NO"

            newReactDict[k] = newval

        msg["reactions"] = newReactDict
    return msg


def getAttachmentType(attachment):
    # might not have all possibilities. Returns None if type cant be found
    if attachment is fbchat.ShareAttachment:
        return "share"
    elif attachment is fbchat.Sticker:
        return "sticker"
    elif attachment is fbchat.FileAttachment:
        return "file"
    elif attachment is fbchat.AudioAttachment:
        return "audio"
    elif attachment is fbchat.ImageAttachment:
        return "image"
    elif attachment is fbchat.VideoAttachment:
        return "video"
    else:
        return None

# ========END HELPER METHODS=========


class CustomClient(fbchat.Client):
    # ==========HELPER METHODS==========
    def buildFrienddict(self):
        users = self.fetchAllUsers()
        tempdict = {}
        tempdict[userinfo.uid] = userinfo.name
        for user in users:
            tempdict[str(user.uid)] = str(user.name)
        return tempdict


def beginCrawl(outfile, pprintFile):
    # start the fbchat client
    userEmail = userinfo.email
    userPassword = userinfo.pw
    userID = userinfo.uid
    machineLocalIsUTC = localTimeIsUTC()  # detect if local is utc time
    logfileName = "crawler_logfile.txt"
    try:
        client = CustomClient(userEmail, userPassword)
    except fbchat.models.FBchatUserError:
        enterLog(logfileName, "Error logging in")
        exit()

    # update cookie
    with open("cookies.txt", "w") as cookies:
        session_cookies = client.getSession()
        cookies.write("%s\n" % (session_cookies))

    frienddict = client.buildFrienddict()  # can do frienddict["id"] to get the name of the user with that id

    targetChat = userinfo.targetChat
    targetChatId = targetChat["Id"]
    targetChatName = targetChat["Name"]
    targetData = {}

    # init targetData
    targetData["messageCount"] = 0
    targetData["messages"] = []  # all the messages; raw messages (Message objects from fbchat converted into dicts)
    targetData["authors"] = {}  # {authorid: {authorid, author name, count, [list of messageIds]}}
    targetChat["attachments"] = {"count": 0, "type": {}, "sharesource": {}}  # total and count per type of attachment. if Share, put source as well
    targetChat["unsent"] = {"count": 0, "authors": {}, "messageIds": []}  # authors: {author: count}
    targetChat["timestamps"] = []  # [(timestamp, author)...]
    targetChat["mentions"] = {}  # {total count, mentionedID: {count for mentioned, who mentionedID/Name}}
    targetChat["reactions"] = {}  # {total count, reactions and their count, reactorsID: {count for reactor, reactions and their count}
    targetChat["topXwords"] = {}  # {word: count}

    # fetch a `Thread` object
    thread = client.fetchThreadInfo(targetChatId)[targetChatId]
    targetData["messageCount"] = thread.message_count

    # begin crawl
    safetyLimit = 20  # number of messages to get before stopping. Put message_count for all

    # Gets the last x messages sent to the thread
    messages = client.fetchThreadMessages(thread_id=targetChatId, limit=safetyLimit)
    #  message come in reversed order, reverse them
    messages.reverse()

    xwords = 10  # the most common words that arent the common stopwords: https://en.wikipedia.org/wiki/Stop_words
    stopwords = nltk.corpus.stopwords.words("english")

    # process every message
    for message in messages:  # process all the messages
        print(message)
        msgTextOrig = message.text
        msgText = message.text  # will be modified
        muid = message.uid

        # ## make Message object JSON serializable
        msgJSON = makeMessageJSON(message)
        targetData["messages"].append(msgJSON)

        # ## update authors
        #  {authorid: {authorid, author name, count, [list of messageIds]}}
        authorId = message.author  # gives id
        authorName = frienddict[authorId]
        existingAuthorDict = targetData["authors"].get(authorId)  # returns None if doesnt exist
        if existingAuthorDict is None:
            # create new entry
            targetData["authors"][authorId] = {"id": authorId, "name": authorName, "count": 1, "msgList": [muid]}
        else:
            # update existing entry
            targetData["authors"][authorId]["msgList"].append(muid)
            targetData["authors"][authorId]["count"] += 1

        # ## update attachments
        # {"count": 0, "type": {}}  # type of attachment and count per type. if ShareAttachment, put source as well
        attachmentList = message.attachments
        for attachment in attachmentList:
            targetChat["attachments"]["count"] += 1
            attachmentType = getAttachmentType(attachment)
            # possible types: "share", "sticker", "file", "audio", "image", "video", None (not a string)
            currcount = targetChat["attachments"]["type"].get(attachmentType, 0)  # 0 if its not there so far
            targetChat["attachments"]["type"][attachmentType] = currcount + 1

            if attachmentType == "share":
                currcount = targetChat["attachments"]["sharesource"].get(attachment.source, 0)
                targetChat["attachments"]["sharesource"][attachment.source] = currcount+1

        # ## update unsent

        # ## update timetamps

        # ## update mentions

        # ## update reactions

        # ## update top x words (most complicated if done efficiently)
        # remove stop words

    # print out the data
    print("\n\n  |================|")
    print("  |======DATA======|")
    print("  V================V\n\n")
    pprint.pprint(targetData)

    print("\n\n written to file %s\n" % (outfile))
    with open(outfile, 'w') as outfile:
        json.dump(targetData, outfile, indent=4)

    if pprintFile is not None:
        print("\n pprint output sent to %s" % (pprintFile))
        with open(pprintFile, "w") as pprintFileObj:
            # remove all special characters
            pformated = pprint.pformat(targetData)
            pformated = pformated.encode("ascii", "namereplace")
            pformated = pformated.decode("ascii")
            pprintFileObj.write(pformated)

    client.logout()


outfile = "chatdata.json"  # will be overwritten
pprintFile = "chatdataPPrint.txt"  # None to print to stdout
beginCrawl(outfile=outfile, pprintFile=pprintFile)
