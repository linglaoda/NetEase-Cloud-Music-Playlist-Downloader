import requests
import json
import os
from tqdm import tqdm
import random
import time
from mutagen import File
from mutagen.flac import Picture, FLAC
import eyed3

# ------- 目录结构 -------
# audio 
# 下载完毕后的音乐
# errorfiles
# 修改音乐属性失败的音乐,通常因为歌曲封面过大而导致写入失败
# image
# 歌曲封面图片
# lrc
# 歌词文件

# ------- Config -------

api_cookies = { #请求API用的cookie
    'MUSIC_U': 'f9276fcbced6bc03ffdaea6c047540737b3ad54769742eeb47934f6a233e00cfcbc9237f9717c2ec016b04c134433e7e92916cfd50031c6aea322b431da93472f9f279d9a909ff3e43fdf0fde39e0496c3061cd18d77b7a0',
    'NMTID': '00OxMs6xOCEJRNjlUQgm45AEr2C16oAAAGCqw0Faw',
    }
download_headers = { #下载音乐用的headers
    'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36 QIHU 360SE'
}
songlist_id='7505540822' #网易云歌单ID
api_url='http://192.168.31.66:4100' #网易云API地址，执行完登录操作后将会获得一个cookie，需将其复制至"api_cookies"数组中

# ------- Function -------

def download(url: str, fname: str,headers: dict): #进度条下载(转载自网络)
    # 用流stream的方式获取url的数据
    resp = requests.get(url, stream=True, headers=headers)
    # 拿到文件的长度，并把total初始化为0
    total = int(resp.headers.get('content-length', 0))
    # 打开当前目录的fname文件(名字你来传入)
    # 初始化tqdm，传入总数，文件名等数据，接着就是写入，更新等操作了
    with open(fname, 'wb') as file, tqdm(
        desc=fname,
        total=total,
        unit='iB',
        unit_scale=True,
        unit_divisor=1024,
    ) as bar:
        for data in resp.iter_content(chunk_size=1024):
            size = file.write(data)
            bar.update(size)

class netmusic_apis(): #网易云相关函数

    def get_music_list(): #获取音乐列表

        all_song_info=[]   

        json_text=requests.get(url=api_url+'/playlist/track/all?id='+songlist_id+'&limit=all',cookies=api_cookies).text
        json_text=json.loads(json_text)

        code=json_text['code']

        if code!=200:
            print('获取音乐列表:失败')
            print(json_text)
        else:
            print('获取音乐列表:成功')

            song_num=len(json_text['songs'])

            print('歌曲数量:'+str(song_num))

            i=0

            while i<song_num:

                song_info=[]

                name=json_text['songs'][i]['name']
                id=json_text['songs'][i]['id']
                ar=json_text['songs'][i]['ar']
                pic=json_text['songs'][i]['al']['picUrl']
                al_name=json_text['songs'][i]['al']['name'][0]

                song_info.append(name)
                song_info.append(id)
                song_info.append(ar)
                song_info.append(pic)
                song_info.append(al_name)

                all_song_info.append(song_info)

                i=i+1
            
            return(all_song_info)
                
    def get_download_url(song_id): #获取下载链接

        down_url=requests.get(url=api_url+'/song/download/url?id='+str(song_id),cookies=api_cookies).text
        down_url=json.loads(down_url)
        code=down_url['code']

        if code!=200:
            print('获取下载链接:失败')
            print(down_url)
        else:
            return(down_url['data']['url'])

class audio_edit(): #修改音频属性(mp3 flac)
    def mp3_edit(mp3_path, img_path,artist,album,title):
        audiofile = eyed3.load(mp3_path)

        audiofile.initTag(version=(2, 3, 0))  # version is important
        # Other data for demonstration purpose only (from docs)
        audiofile.tag.artist = artist
        audiofile.tag.album = album
        audiofile.tag.album_artist = artist
        audiofile.tag.title = title

        # Read image from local file (for demonstration and future readers)
        with open(img_path, "rb") as image_file:
            imagedata = image_file.read()
        audiofile.tag.images.set(3, imagedata, "image/jpeg", u"cover")
        audiofile.tag.save()

    def flac_edit(flac_path, img_path,artist,album,title): #修改flac属性
        audio = File(flac_path)
            
        image = Picture()
        image.type = 3
        if img_path.endswith('png'):
            mime = 'image/png'
        else:
            mime = 'image/jpeg'
        image.desc = 'front cover'
        with open(img_path, 'rb') as f: # better than open(albumart, 'rb').read() ?
            image.data = f.read()
        
        audio.add_picture(image)

        audio['ARTIST']=artist
        audio['ALBUM']=album
        audio['TITLE']=title


        audio.save()

# ------- Main Function -------

if __name__ == '__main__':

    #创建必要文件夹
    os.mkdir('audio')
    os.mkdir('image')
    os.mkdir('lrc')
    os.mkdir('errorfiles')

    music_list=netmusic_apis.get_music_list()
    music_num=len(music_list)

    i=0

    while i<music_num:

        nolrc=False

        print('-------------------------')
        #显示总进度条
        print(str(i+1)+'/'+str(music_num))

        
        name=music_list[i][0]
        id=music_list[i][1]
        ar=music_list[i][2]
        pic=music_list[i][3]
        ar_name=music_list[i][4]

        #替换name中的保留字
        name=name.replace('/','_')
        name=name.replace('\\','_')
        name=name.replace(':','_')
        name=name.replace('*','_')
        name=name.replace('?','_')
        name=name.replace('"','_')
        name=name.replace('<','_')
        name=name.replace('>','_')



        ar_num=len(ar)

        ar_i=0
        ars=''

        while ar_i<ar_num:
            ar_name=ar[ar_i]['name']
            
            if ar_i==ar_num-1:
                ars=ars+ar_name
            else:
                ars=ars+ar_name+','
            ar_i=ar_i+1


        down_url=netmusic_apis.get_download_url(id)

        #获取audio的后缀名
        audio_suffix=down_url.split('.')[-1]
        #获取image的后缀名
        image_suffix=pic.split('.')[-1]

        download(down_url,name+'.'+audio_suffix,download_headers)
        download(pic,name+'.'+image_suffix,download_headers)
        
        lrc=requests.get(url='https://music.163.com/api/song/media?id='+str(id),headers=download_headers)
        lrc=json.loads(lrc.text)

        if 'nolyric' in lrc or 'lyric' not in lrc:
            nolrc=True
        else:
            lrc=lrc['lyric']
        


        edit_runn=True

        try:
            if audio_suffix=='mp3':
                audio_edit.mp3_edit(name+'.'+audio_suffix,name+'.'+image_suffix,ars,ar_name,name)
            else:
                audio_edit.flac_edit(name+'.'+audio_suffix,name+'.'+image_suffix,ars,ar_name,name)
        except Exception as e:
            edit_runn=False
            print(e)

        if edit_runn==True:
            #将图片文件移动至image文件夹
            os.rename(name+'.'+image_suffix, 'image/'+name+'.'+image_suffix)
            #将音频文件移动至audio文件夹
            os.rename(name+'.'+audio_suffix, 'audio/'+name+'.'+audio_suffix)
            #将歌词文件写入至lrc文件夹
            if nolrc==False:
                with open('lrc/'+name+'.lrc','w',encoding='utf-8') as f:
                    f.write(lrc)
                print('歌词写入成功')
            else:
                print('无歌词')
        else:
            print('修改属性失败')
            #将图片文件移动至image文件夹
            os.rename(name+'.'+image_suffix, 'errorfiles/'+name+'.'+image_suffix)
            #将音频文件移动至audio文件夹
            os.rename(name+'.'+audio_suffix, 'errorfiles/'+name+'.'+audio_suffix)
            #将歌词文件写入至lrc文件夹
            if nolrc==False:
                with open('errorfiles/'+name+'.lrc','w',encoding='utf-8') as f:
                    f.write(lrc)
            


        #随机休眠
        r=random.randint(3,6)
        print('随机休眠'+str(r)+'秒')
        time.sleep(r)

        i=i+1
