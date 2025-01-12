import sys, os
import configparser
from pathlib import Path
from instagrapi import Client
from datetime import datetime
import sqlite3

MAX_MEDIAS_READ=6
InstaParamsFname="./.session.json"

conn = sqlite3.connect('instagram.db')
c = conn.cursor()
try:
    with conn:
        c.execute("""CREATE TABLE  spytrack (
                    uname text,
                    id text,
                    following_name  text,
                    following_id    text,
                    following_tag   text,
                    following_count int,
                    time            text
        )""")
        #conn.commit()
except sqlite3.OperationalError:
    print("table spytrack already exists")
else:
    print("table spytrack connect error")

home = Path.home()
config = configparser.ConfigParser()
config.read(home.joinpath('.credentials'))
logname = config['Instagram']['logname']
password = config['Instagram']['password']

cl = Client()
if os.path.exists(InstaParamsFname):
    print("Instagram Params found")
    cl.load_settings(InstaParamsFname)
else:
    with open(InstaParamsFname, "w") as param_file:
        param_file.write("empty")

# adds a random delay between 1 and 3 seconds after each request
cl.delay_range = [1, 5]
if not cl.login(logname, password):
    print(f"Instagram login error!")
    sys.exit(0)
cl.dump_settings(InstaParamsFname)


def get_user_id (user_name):
    try:
        full_info = cl.user_info_by_username(user_name)
        return full_info.pk
    except:
        print(f"An exception in get_user_id for name '{user_name}'")

class Following_Channel:
    def __init__(self, following_name, following_id):
        self.following_name = following_name
        self.following_id = following_id
        self.following_tag = None
        self.media_count = 0
        self.time = None
    def set_following_tag (self, following_tag, following_count):
        self.following_tag = following_tag
        self.media_count = following_count
    def set_count (self, count):
        self.media_count = count    
    def set_time (self, time_str):
        self.time = time_str
    def is_tag(self):
        return bool(self.following_tag)
    def get_dict (self):
        rdic = {'cname' :  self.following_name,
                'cid' : self.following_id,
                'ctag' : "",
                'ccount' : self.media_count,
                'time' : self.time}
        if self.following_tag: rdic['ctag'] = self.following_tag
        return rdic
    def __repr__(self):
        return f"Channel: name:{self.following_name} id:{self.following_id} tag:{self.following_tag} tag_count:{self.media_count} time:{self.time}"

def get_following_list (user_id):
    ret = dict()
    try:
        fillowing_list = cl.user_following_v1(user_id)
        for source in fillowing_list:
            channel = Following_Channel(source.username, source.pk)
            # try:
            #     tag = cl.hashtag_info(source.username)
            #     channel.set_following_tag(tag.id, tag.media_count)
            # except:
            #     print(f"An exception occurred in get_following_list for user '{user_id}' : can't get tag of {source.username}")
            try:
                # if not tag:
                # if is private channel
                info=cl.user_info(source.pk)
                channel.set_count(info.media_count)
            except:
                print(f"An exception occurred in get_following_list for user '{user_id}' : can't full info of {source.username}")
            ret[source.username] = channel
        return ret
    except:
        print(f"An exception occurred in get_following_list for user '{user_id}' : can't get following_list")
        return ret

def read_db_following_list (user_name):
    ret = dict()
    try:
        c.execute("SELECT * FROM spytrack WHERE uname=:uname", {'uname': user_name} )
        for channel_record in c.fetchall():
            channel = Following_Channel(channel_record[2], channel_record[3])
            if  channel_record[4]:
                channel.set_following_tag(channel_record[4], channel_record[5])
            channel.set_time(channel_record[6])
            ret[channel_record[2]] = channel
        return ret
    except:
        print(f"An exception occurred in DB read for user '{user_id}' : can't get following_list")
        return ret

def write_db_following_channel (user_name, user_id, channel):
    spytrack_data = channel.get_dict()
    spytrack_data['uname'] = user_name
    spytrack_data['uid'] = user_id
    spytrack_data['time'] = str(datetime.now())
    try:
        c.execute("""INSERT INTO spytrack VALUES (
                    :uname,
                    :uid,
                    :cname,
                    :cid,
                    :ctag,
                    :ccount,
                    :time)""", spytrack_data)
        conn.commit()
    except:
        print(f"An exception occurred in DB write for user '{user_id}' : can't write following_list {channel}")

def  media_type_str (media):
    if media.media_type == 1:
        return 'Photo'
    elif media.media_type == 2 and media.product_type == "feed":
        return 'Video'
    elif media.media_type == 2 and media.product_type == "igtv":
        return 'IGTV'
    elif media.media_type == 2 and media.product_type == "clips":
        return 'Reels'
    elif media.media_type == 8:
        return 'Album'
    return 'Unknown'

def media_description (media):
    mdic = dir(media)
    description = "media: "
    if 'media_type' in mdic:
            description += media_type_str(media) + " :"
    if 'title' in mdic:
            description += " '" + mdic.title + "' "
    if 'user' in mdic:
            description += " from " + media.user.username
    if 'taken_at'  in mdic:
            description += " at " + str(media.taken_at)
    return description

def does_user_like_madia (user_pk, media):
    likers = cl.media_likers(media.pk)
    if media.like_count > len(likers):
        # it is not possible get full likers list
        print(f"Media '{media.pk}' from {str(media.taken_at)} get {len(likers)} from {media.like_count} likes : can't get full list")
    for lover in likers:
        if lover.pk == user_pk:
            return True
    return False

def download_media (media):
        if media.media_type == 1:
            # Photo
            cl.photo_download(media.pk, './images')
        # elif media.media_type == 2 and media.product_type == "feed":
        #     # Video
        #     paths.append(cl.video_download(media.pk))
        # elif media.media_type == 2 and media.product_type == "igtv":
        #     # IGTV
        #     paths.append(cl.video_download(media.pk))
        # elif media.media_type == 2 and media.product_type == "clips":
        #     # Reels
        #     paths.append(cl.video_download(media.pk))
        # elif media.media_type == 8:
        #     # Album
        #     for path in cl.album_download(media.pk):
        #         paths.append(path)


def is_media_actual (media, channel):
    # does it first  channel overlooking?
    if not channel.time: return True
    observation_days = datetime.timedelta(days=10)
    if media.taken_at < (datetime.now() - observation_days): return True
    return False

def spy_user_in_the_channel (user_name, user_id, channel):
    amount = channel.media_count
    if amount > MAX_MEDIAS_READ*2:
        # it is huge channel: read last media only
        amount = MAX_MEDIAS_READ
    media_list = cl.user_medias(channel.following_id, amount)
    print(f"Channel {channel.following_name} contains {len(media_list)} medias")
    for media in media_list:
        if not is_media_actual(media, channel):
            print(f"Media '{media.pk}' from {str(media.taken_at)} is out of date")
            continue
        if does_user_like_madia(user_id, media):
            print(f"User {user_name} likse {media_description(media)} from {channel.following_name}")
    write_db_following_channel (user_name, user_id, channel)

# def spy_user_in_tag_channel (user_name, user_id, channel):
#     amount=MAX_MEDIAS_READ
#     try:
#         media_list = cl.hashtag_medias_v1(channel.following_name, amount=amount,tab_key='recent')
#         print(f"Channel {channel.following_name} contains {len(media_list)} medias")
#         for media in media_list:
#             if not is_media_actual(media, channel): continue
#             if does_user_like_madia(user_name, media.pk):
#                 print(f"User {user_name} likse {media_description(media_description)} from {channel.following_name}")
#     except:
#         print(f"An exception occurred spy_user_in_tag_channel for user '{user_name}' : can't get following_list {channel.following_name}")   
#     write_db_following_channel (user_name, user_id, channel)

def spy(user_name):
    user_id = get_user_id (user_name)
    if not user_id:
        sys.exit(0)

    print(f"Look on User {user_name} {user_id}")
    following_list = get_following_list(user_id)

    db_following_list = read_db_following_list(user_name)
    following_set =  set(following_list.keys())
    db_following_set =  set(db_following_list.keys())

    unsubscribe_set = db_following_set - following_set
    subscribe_set = following_set - db_following_set
    continue_set = following_set & db_following_set

    # go over new channel
    for cname in subscribe_set:
        channel = following_list[cname]
        print(f"User {user_name} subscribes to {channel}")
        spy_user_in_the_channel(user_name, user_id,channel)
        # if channel.is_tag():
        #     spy_user_in_tag_channel(user_name, user_id,channel)
        # else:
        #     spy_user_in_the_channel(user_name, user_id,channel)

    for cname in continue_set:
        channel = following_list[cname]
        print(f"User {user_name} continue following on {channel}")
        spy_user_in_the_channel(user_name, user_id, channel)

users = []
try:
    c.execute("SELECT name FROM following")
    for user in c.fetchall():
        users.append(user[0].strip())
except:
    print(f"An exception occurred in DB read : can't get users list")
    sys.exit(0)
for user in users:
    spy(user)
