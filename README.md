#  Facebook Messenger/Chat Crawler

First and foremost, I as the programmer can not have access to your Facebook information via this project. Anything this code produces is only on your local computer as a file.


I call this a crawler very loosely. The summary of this program is that it goes through the messages of one chat in Facebook, aggregates some counts, and crates a JSON file with the messages and counts for you to view. Also does some very, very basic analysis. 


I use the fbchat API to request messages: https://fbchat.readthedocs.io/en/stable/index.html


Check below about getting many messages (5000+)

## Details

There are two main files part of this project: `chatCrawler.py` and `userinfo.py`.


`userinfo.py` is the one with your login information and the chat details you want to analyze. This file has important information and is *not* tracked by git. You can find what you need to fill out in `userinfo_template.py`. Make sure to rename it when filled.
If you do not know the Id of the person or group, just put that as `None` and put the name of the person or group. The script will find the id for you and continue on.


`chatCrawler.py` is the bulk (...99%) of this project. It does some checks, and things but as a user, you just need to think about these few lines at the bottom. 


### Modifications needed for you to use this

There are a couple lines at the bottom that act as the "Settings". 


`outfile` is the variable in which the name of the json file is kept


`pprintFile` is the variable in which the name of the ppprint file is kept. This is essentially the same as the json file and doesn't really do anything


`xwords` is the number of words you want to look at. For instance if you put 10, it shows you the top 10 most frequently used words in your chat along with how many times


`numberMessages` The number of messages to read. Put `None` to read the entire chat. It reads from bottom to top, but is reversed so we see it correctly


Note: As of now, There are errors when trying to get a lot of messages (10000+)

`createMessageIdLists` make message id lists for authors and unsent  (If True, json file can get large).


### Output

The output is a json file with the name given in the `outfile` variable.  It is created automatically and is overwritten if you run it again without changing the name. 


Look below for a basic structure of the json object. 


###  Running the program
This was made with the intent of running via the console. After all edits have been made run it with this command (or whatever works on your computer)


`py -3 chatCrawler.py`


`python3 chatCrawler.py`


Output will come to your console and a file will be created with the name you provided. 


### Basic Structure


Look at the output for the full object

```
{
    "messageCount":number,
    "chatName":"name",
    "chatID":"9999999999",
    "messageCount":100,
    "messages": [{<json-ized Message Object>}, ...],
    "authors":{authorID:{data}, author2ID:{data}, ...},
    "attachments": {count: number, <some other counts>},
    "unsent": {count: number, <counts by user>},
    "timestamps": [{timestamp, authorid, authorname}...],
    "mentions" {count, {counts per person mentioned}...}:,
    "reactions": {count, counts per reaction type},
    "topXwords": {word: count, ...}
    "wordCount": {authorid: {authorname, total words from cleaned messages},...}
    
}
```

NOTE: "topXwords" is not the actual field. X is replaced by the number you put in `xwords` to make "top10words" or "top124words", etc


### Many messages
I have now fixed the issue of getting stuck when asking for a lot of messages by getting them in chunks. However, so that the requests do not look suspicious, there is a delay of 3-15 seconds in between chunks. Each chunk is 10000 messages. It does stop early if you ask for less than 10000, or a number not a multiple of 10000. You can change the chunk size in the `getMessages`method.

The larger the number of total messages you are trying to get, the more time you may have to wait. The progress is displayed onto the console. 

## Inspiration

I am in some chats that have a LOT of messages and I wanted to know how many messages we had. But I also wanted to know who sent the most messages, what topics came up most (word count), ect. Some of the things I kept track of like mentions and reactions, only happened once I looked at what was available to me via the fbchat API.

Right now, this only aggregates some minor things and I would love to get into analyzing aspects of the chat. Perhaps find the times we're the most active by the timestamp, or find what sort of attachment is the most popular, or see the sense of our chat by seeing what kinds of reactions we do. I would like to get into the data analysis side a little more, but I think I will need to gather some more data for that. I think this is pretty good for a one-day type of project! :) 