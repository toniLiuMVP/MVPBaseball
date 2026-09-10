#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""mvp_skip_intro.py —— 關掉 MVP Baseball 2005 的開場動畫。

    自包含:整支腳本就是這一個檔,只用 Python 內建模組,不需要安裝任何套件。

做法(重要,先看懂再跑)
    **不是刪檔,也不是內附一個現成的短片。**
    它拿你自己那一份影片,只留下開頭幾格畫面、把聲音整段丟掉,
    再照原本的格式重新組回去。產出的還是一個合法的 .vp6,
    遊戲照樣播得動,只是一瞬間就播完了。

    為什麼不是刪檔:檔案不見時遊戲的行為本站沒有驗過,而且沒辦法還原。
    為什麼不內附現成的:本站不提供任何遊戲檔案下載,一個都沒有。
    你手上那一份是你自己的,腳本只是幫你把它改短。

這個格式(本站在四份剛安裝好的安裝上量到的)
    data/frontend/movies/ 底下 16 個 .vp6,合計 69,524,060 bytes。
    每一個檔的檔頭都是同一個排法:

        位移 0    'MVhd'          四個字元的標記
        位移 4    32              檔頭有多長
        位移 12   寬 (16 位元)     16 個檔裡 15 個是 640
        位移 14   高 (16 位元)     16 個檔裡 15 個是 480
                                  唯一的例外是 creditm.vp6:
                                  四份原版量到的都是 128 × 96
        位移 16   影格數 (32 位元) ← 這一格是關鍵
        位移 28   32767           四份原版、16 個檔全部是這個值
        位移 32   開始是一連串區塊

    區塊都是「4 個字元的標記 + 4 個位元組的長度(含標記與長度自己)」。
    以原版 mvpintro.vp6(19,304,748 bytes、影格數 2302)為例:

        SCHl  1 個      音訊容器檔頭
        SCCl  1 個      音訊設定
        SCDl  2302 個   音訊資料(這一支剛好一格一塊,那不是通則,見下面「順帶量到的一件事」)
        SCEl  1 個      音訊結束
        MV0K  66 個     影像關鍵影格
        MV0F  2236 個   影像後續影格

    66 + 2236 = 2302,跟檔頭寫的影格數一個不差。
    SCHl / SCCl / SCDl / SCEl 就是本站在語音那幾課解開的同一組 EA 音訊標記。

    所以「把它變短」只要做三件事:
      1. 留下第一個 MV0K,加上後面幾個 MV0F
      2. 所有 SC 開頭的音訊區塊整組不要
      3. 把檔頭位移 16 那個影格數改成你留下的張數

用法
    python3 mvp_skip_intro.py "〔你的遊戲資料夾〕" --info
    python3 mvp_skip_intro.py "〔你的遊戲資料夾〕" --skip intro
    python3 mvp_skip_intro.py "〔你的遊戲資料夾〕" --skip intro --apply
    python3 mvp_skip_intro.py "〔你的遊戲資料夾〕" --skip intro --keep 10 --apply
    python3 mvp_skip_intro.py "〔你的遊戲資料夾〕" --restore
    python3 mvp_skip_intro.py --selftest

    --keep 決定留幾格畫面,不寫就是 25 格,至少要 1。留越少檔案越小。

安全網
    · 不加 --apply 就只是預覽,一個位元組都不會寫
    · 第一次寫入前自動備份成 〈原檔名〉.introbak,之後不覆蓋,
      所以還原永遠回到你第一次動它之前
    · 備份與寫入都是原子的:暫存檔用 tempfile.mkstemp 在**同一個資料夾**開,
      名字帶亂數而且是 O_EXCL 建出來的,別人沒辦法預先佔位。
      寫完 fsync、讀回來逐位元組比對,對得上才 os.replace 換上去;
      中途任何一步失敗就把暫存檔刪掉,正本一個位元組都不動
      (本站 2026-08-29 在別的腳本上踩過「半截備份」那個坑)
    · 要動到的遊戲檔與備份檔只要是符號連結就整個拒絕,連讀都不讀
      (--info 只是看,不寫任何東西,所以不受這一條限制:它會照樣把連結
      指到的那一份列出來)。
      舊版用固定的 .tmp 名字,誰先在資料夾裡放一個
      〈檔名〉.tmp → 資料夾外面某個檔的連結,寫入就會跟著連結出去把外面那個檔
      蓋掉,而 os.replace 還會把連結搬到遊戲檔頭上 —— 遊戲檔當場消失。
      本站 2026-09-05 實際重現過這一條,現在用 lstat 擋住(exists() 擋不住,
      它對「指向不存在目標的連結」回 False)
    · 寫回去之後會重新讀一次,確認影格數、區塊組成、檔頭都對得上,
      對不上就把**動手之前那一份**原子地寫回去(寫完再逐位元組比一次)並要你回報
    · --restore 之前會先驗那個備份自己:0 bytes、比檔頭還短、開頭不是 MVhd、
      區塊走不完、區塊長度加總跟檔案長度對不上、影像區塊數跟檔頭寫的影格數
      對不上 —— 任何一種都拒絕蓋回去,而且遊戲檔一個位元組都不動。
      蓋回去之後還會整份讀出來跟備份逐位元組比對,一樣才算還原成功
    · 一次處理多個檔的時候,某一個檔失敗不會讓其他檔跟著停;
      失敗的會列在最後,而且整體回傳非 0、順便把還原指令印給你。
      「讀不動那個檔」(權限、磁碟壞軌、那個名字其實是一個資料夾)也算失敗的一種,
      它會被列出來,而不是讓整批噴一段看不懂的錯誤中止 ——
      舊版噴的時候,前面已經換掉的檔一個字都不會被提到
    · 萬一還是發生本站沒有預料到的錯誤,收尾一樣會先講清楚
      「哪些檔已經被換掉了」再回非 0,不會只丟一段 traceback 就走人
    · 中途按 Ctrl+C:會照實講「有沒有檔案已經被換掉了」。
      沒換過才說「一個位元組都沒動」,換過就叫你跑 --restore。
      不管講的是哪一種,都回傳 130。
      「換名」跟「把它記下來」是兩個動作,中斷剛好落在中間的話,舊版的收尾
      會照舊狀態說「沒動到」,而遊戲檔其實已經換掉了(本站 2026-09-06 拿變體檔
      重現過:sha256 真的變了,畫面卻說沒動)。現在那兩行綁成一段不可中斷的
      動作(見 _NoInterrupt),而且狀態有三種:還沒動 / 正在換 / 已經換掉,
      萬一真的停在中間,說的是「正在替換 X」,不會說「沒動到」
    · --selftest 不在 python3 -O 底下跑:-O 會把 assert 整段拿掉,
      測試會變成一片假的綠燈。遇到 -O 直接以結束碼 2 收工

順帶量到的一件事(跟這一課有關,所以寫在這裡)
    creditm.vp6(工作人員名單)**出廠就是無聲的**:本站在四份剛安裝好的安裝
    (英文版、中文版、PK 版)上量到的區塊組成都是 MV0K 24 個 + MV0F 5377 個,
    合計 5401 格,一個音訊區塊都沒有。其他 15 個檔都有音訊,各自固定一個 SCHl、
    一個 SCCl、一個 SCEl;SCDl 的塊數則**沒有一條公式算得出來** ——
    15 個裡有 10 個剛好等於影格數,cameo20 / cameo33 / cameo35 / cameo37
    各多 1 塊,easports.vp6 是 170 塊對 150 格。四份原版量到的偏差完全一樣。
    所以**不要**拿「沒有聲音」當「已經被縮短過」的判準,那會把原版誤標成改過的。

本站沒驗的
    · 遊戲跑起來實際的畫面。本站量的是**檔案**:格式合法、影格數對得上、
      區塊組成正確。至於遊戲會不會照播、播完會不會正常進主選單,
      需要真的開一次遊戲看。⚠️ 這一段還沒實測
    · 這台測試機的 movies 資料夾 2008 年就被社群模組換成 1,940 bytes 的樁了(15 個樁的檔案時間是 2008-10-09 / 10)
      (15 個檔共用同一份,SHA-256 全部相同),所以「換完之後遊戲照跑」
      這件事在這台機器上是**別人早就驗過的**,不是本站驗的
    · 這一版新加的三件事(還原前的備份守門、輸出改成 UTF-8、多檔時失敗不整批中止)
      本站只在 macOS 上跑過。cp950 那一條是用 PYTHONIOENCODING=cp950 重現與複驗的,
      **真正的 Windows 主控台還沒實測**
    · 符號連結那一組守門也只在 macOS 上跑過。Windows 沒開開發者模式就建不出
      符號連結,自我測試遇到這種環境會自己跳過那三個餌並印出來說跳過了;
      Windows 的 junction / reparse point 本站**還沒實測**
    · 不可中斷段那一段(把換名跟登記綁在一起)是拿變體檔在 macOS 上重現與複驗的:
      換名之後才中斷會誠實說「已經換掉」並印還原指令、正本 sha256 真的變了;
      換名之前中斷會說「沒動到」、正本 sha256 不變;
      停在換名中間會說「當時正在替換 X」,而且不會斷言換成了沒有。
      三種都回傳 130,三種的 sha256 都對得上它講的話。**Windows 的 Ctrl+C 還沒實測**
    · 「讀不動那個檔」與「還原之後讀不回來」這兩條路是拿權限位元關掉的檔
      在 macOS 上重現的(修之前兩條都噴 traceback,修之後逐檔講清楚並回非 0)。
      Windows 的權限位元跟 POSIX 不一樣,**那邊還沒實測** ——
      不過自我測試裡的那兩個餌不靠權限位元(一個拿資料夾冒充 .vp6,
      一個直接讓那一次讀取失敗),在哪個作業系統上都會跑

授權:MIT(見檔尾完整條款)。本站教學文字另採 CC BY 4.0。
"""
#
# ─────────────────────────────────────────────────────────
#  法律與免責(每一支本站腳本都帶著這一段)
#
#  · 本工具與 Electronic Arts 無任何官方關聯,也未經其授權或背書。
#    MVP Baseball 2005 為 Electronic Arts 之作品與商標。
#  · 本工具為原創程式碼,**不含任何 EA 的程式碼或資產**。
#  · 本工具不提供、不教學、也不包含任何規避技術保護措施的功能。
#  · 使用者應僅對自己合法取得的遊戲副本使用本工具,並自行承擔風險。
#    使用前請自行確認你與遊戲發行商之間的使用者授權合約(EULA)。
#  · 本工具按「現狀」提供,不附任何明示或默示的擔保。
#  · 授權:MIT(見檔尾)。教學文字另採 CC BY 4.0。
#  · 回報與下架:https://toniliumvp.github.io/MVPBaseball/report.html
#    三條管道,其中「直接向 GitHub 提出」不需經過維護者;
#    留言區那條不需要任何帳號。管道有變動只會改那一頁。
# ─────────────────────────────────────────────────────────

import argparse
import io
import os
import shutil
import signal
import struct
import sys
import tempfile

if sys.version_info < (3, 7):
    sys.exit('🔴 需要 Python 3.7 以上,目前是 %d.%d' % sys.version_info[:2])

# Windows 主控台預設編碼(繁中是 cp950)存不下 ✅ 🔴 ⚠️ ⏭ ≥ 這些符號,
# 輸出被重導向到檔案或接管線時會直接 UnicodeEncodeError 中斷 ——
# 檔案其實已經寫好也驗過了,使用者看到的卻是 traceback。先把輸出轉成 UTF-8。
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except (AttributeError, ValueError):                # Python 3.6 以下沒有 reconfigure
    pass

MAGIC = b'MVhd'
HDR_LEN = 32
OFF_W, OFF_H, OFF_FRAMES = 12, 14, 16
BAK_SUFFIX = '.introbak'

# 影像區塊:MV0K 是關鍵影格(自己就能解出一張圖),MV0F 是後續影格(靠前一張推)。
# 所以留下來的第一格**一定要是 MV0K**,不然沒有起點。
CHUNK_KEY = b'MV0K'
CHUNK_FRAME = b'MV0F'
# 音訊區塊:整組丟掉。SCHl 是容器檔頭、SCCl 是設定、SCDl 是資料、SCEl 是結束。
# 這四個標記跟本站語音那幾課(read-voice / make-voice)解開的是同一組,不是三個。
# 四份原版的 15 個有聲檔各有一個 SCEl,creditm.vp6 則一個音訊區塊都沒有。
AUDIO_TAGS = (b'SCHl', b'SCCl', b'SCDl', b'SCEl')

# 哪一支影片對應到哪一個代號。名字是 EA 取的,不是本站編的。
MOVIES = {
    'intro':   ('mvpintro.vp6', '開場動畫(最長的一支)'),
    'credits': ('creditm.vp6',  '工作人員名單'),
    'ea':      ('easports.vp6', 'EA SPORTS 商標'),
}
# cameoNN 是球員特寫短片,數量與編號會因為版本不同,執行時才去數。


class VP6Error(Exception):
    """格式不對就丟這個,不要硬猜。"""


def read_header(data):
    """讀出檔頭。不合格就丟例外,絕不猜。"""
    if len(data) < HDR_LEN:
        raise VP6Error('檔案只有 %d 個位元組,連檔頭(%d)都不夠' % (len(data), HDR_LEN))
    if data[:4] != MAGIC:
        raise VP6Error('開頭四個字元是 %r,不是 %r —— 這不是 .vp6'
                       % (data[:4], MAGIC))
    hdr_len = struct.unpack_from('<I', data, 4)[0]
    if hdr_len != HDR_LEN:
        raise VP6Error('檔頭長度寫著 %d,本站量到的四份原版都是 %d。'
                       '沒見過的變體,不動它' % (hdr_len, HDR_LEN))
    w = struct.unpack_from('<H', data, OFF_W)[0]
    h = struct.unpack_from('<H', data, OFF_H)[0]
    frames = struct.unpack_from('<I', data, OFF_FRAMES)[0]
    return {'w': w, 'h': h, 'frames': frames}


def walk_chunks(data):
    """把區塊一個一個走出來,回傳 [(標記, 起點, 長度), ...]。

    區塊格式是「4 個字元標記 + 4 個位元組長度」,長度**含**標記與長度自己。
    長度不合理就停下來並丟例外 —— 硬走下去只會讀到垃圾。
    """
    out = []
    off = HDR_LEN
    while off + 8 <= len(data):
        tag = data[off:off + 4]
        size = struct.unpack_from('<I', data, off + 4)[0]
        if size < 8 or off + size > len(data):
            raise VP6Error('位移 %d 的區塊 %r 長度寫著 %d,超出檔案範圍'
                           % (off, tag, size))
        out.append((tag, off, size))
        off += size
    return out


def summarise(data):
    """給 --info 用:檔頭 + 區塊統計。"""
    hdr = read_header(data)
    chunks = walk_chunks(data)
    counts = {}
    for tag, _off, _size in chunks:
        counts[tag] = counts.get(tag, 0) + 1
    video = counts.get(CHUNK_KEY, 0) + counts.get(CHUNK_FRAME, 0)
    audio = sum(counts.get(t, 0) for t in AUDIO_TAGS)
    hdr.update({'counts': counts, 'video_frames': video, 'audio_chunks': audio,
                'size': len(data)})
    return hdr


def build_stub(data, keep_frames):
    """從**這一份檔案自己**做出一個短版。

    留下第一個 MV0K 加上後面的 MV0F,湊滿 keep_frames 張;
    所有音訊區塊丟掉;檔頭的影格數改成實際留下的張數。

    ⚠️ 第一格一定要是 MV0K。少了關鍵影格,後面的 MV0F 沒有起點可以推。
    """
    hdr = read_header(data)
    chunks = walk_chunks(data)

    kept = []
    for tag, off, size in chunks:
        if tag in AUDIO_TAGS:
            continue
        if not kept:
            if tag != CHUNK_KEY:
                continue          # 還沒遇到第一個關鍵影格,前面的先跳過
            kept.append((tag, off, size))
        elif tag in (CHUNK_KEY, CHUNK_FRAME):
            kept.append((tag, off, size))
        if len(kept) >= keep_frames:
            break

    if not kept:
        raise VP6Error('這個檔裡找不到任何 %r 關鍵影格,不知道從哪裡開始留'
                       % CHUNK_KEY)

    out = bytearray(data[:HDR_LEN])
    struct.pack_into('<I', out, OFF_FRAMES, len(kept))
    for _tag, off, size in kept:
        out += data[off:off + size]
    return bytes(out), len(kept), hdr


def verify_stub(new_data, want_frames):
    """寫回去之前先自己讀一次。讀不回來就不要寫。"""
    hdr = read_header(new_data)
    chunks = walk_chunks(new_data)
    tags = [t for t, _o, _s in chunks]
    if hdr['frames'] != want_frames:
        raise VP6Error('檔頭寫的影格數 %d ≠ 實際留下的 %d'
                       % (hdr['frames'], want_frames))
    if len(chunks) != want_frames:
        raise VP6Error('區塊數 %d ≠ 影格數 %d' % (len(chunks), want_frames))
    if tags[0] != CHUNK_KEY:
        raise VP6Error('第一個區塊是 %r,不是關鍵影格 %r' % (tags[0], CHUNK_KEY))
    bad = [t for t in tags if t in AUDIO_TAGS]
    if bad:
        raise VP6Error('還留著 %d 個音訊區塊,應該要全部丟掉' % len(bad))
    end = HDR_LEN + sum(s for _t, _o, s in chunks)
    if end != len(new_data):
        raise VP6Error('區塊長度加總 %d ≠ 檔案長度 %d' % (end, len(new_data)))
    return True


def check_vp6_blob(data, label):
    """把一份位元組確認成「一個完整的 .vp6」。空的、半截的、不是這個格式就丟例外。

    ⚠️ 這是還原那條路上唯一的守門。0 bytes 或半截的備份蓋回去,
       讀者的遊戲檔當場報銷,而畫面還會照樣印 ✅。本站 2026-08-29 修好的是
       「產生備份」那一半(見 atomic_backup),「用備份」這一半是這一版才補的。
       腳本自己不會產生壞備份,壞的來源在外面:整包資料夾複製到 USB 中斷、
       雲端同步留下 0 bytes 佔位、防毒截斷。

    驗四件事:
      1. 開頭是 MVhd、檔頭長度寫著 32,而且檔案至少有檔頭那麼長
         (0 bytes 的備份就是在這一關被擋下來的)
      2. 每一個區塊的長度都落在檔案裡
      3. 區塊長度加總 + 檔頭 = 檔案長度  ← 抓「中途被截斷」
      4. 影像區塊數 = 檔頭寫的影格數      ← 抓「剛好截在區塊邊界上」
         第 4 條是量出來的:四份原版的 16 個檔(64 份)加上本站測試機那個
         movies 資料夾的 16 個檔(其中 15 個是別人做的社群短樁),
         80 份全部成立 —— 連別人做的短樁也遵守這一條。

    每一句錯誤訊息都會**指名是哪一份**。少了這個,讀者看到「檔案只有 0 個位元組」
    會以為是自己的遊戲檔空了,而其實空的是備份。
    """
    try:
        hdr = read_header(data)
        chunks = walk_chunks(data)
    except VP6Error as e:
        raise VP6Error('%s:%s' % (label, e))
    end = HDR_LEN + sum(s for _t, _o, s in chunks)
    if end != len(data):
        raise VP6Error('%s 的區塊長度加總 %d ≠ 檔案長度 %d,它是半截的'
                       % (label, end, len(data)))
    video = sum(1 for t, _o, _s in chunks if t in (CHUNK_KEY, CHUNK_FRAME))
    if video != hdr['frames']:
        raise VP6Error('%s 只有 %d 個影像區塊,檔頭卻寫著 %d 格,對不上'
                       % (label, video, hdr['frames']))
    return hdr


def check_backup_usable(bak):
    """讀出備份並確認它是完整的。回傳內容;不完整就丟例外,呼叫端不要寫。"""
    refuse_symlink(bak, '備份 ' + os.path.basename(bak))
    if not os.path.lexists(bak):
        raise VP6Error('備份 %s 不見了' % os.path.basename(bak))
    with io.open(bak, 'rb') as fh:
        data = fh.read()
    check_vp6_blob(data, '備份 ' + os.path.basename(bak))
    return data


# 已經真的被 os.replace 換掉的遊戲檔。Ctrl+C 的訊息要靠它講實話 ——
# 「什麼都沒有動到」這句話只有在這個清單是空的時候才成立。
_MODIFIED = []

# ── 2026-09-06 稽核抓到的:Ctrl-C 落在「換名」與「登記」之間 ────────────────
# os.replace 那一行跟 _MODIFIED.append 那一行是兩個獨立的動作。中斷剛好落在中間,
# 收尾看到的還是舊狀態,於是印出「一個位元組都沒動」—— 而遊戲檔已經換掉了。
# 窗口很窄,但它是真的:本站拿變體檔在修之前的版本上重現過。
#
# 兩道一起上:
#   (a) _NoInterrupt 把「換名 + 登記」包成一段不可中斷的動作。這段期間收到的
#       SIGINT 先記著,離開這段之後再照常丟出 —— 收尾看到的清單一定跟磁碟一致。
#   (b) _INFLIGHT 是保險:進那一段之前先登記「正在換 X」。(a) 失效的時候
#       (例如不在主執行緒,signal.signal 裝不上去)還有這一層,
#       收尾會說「當時正在替換 X」,不會說「沒動到」(見 say_file_state)。
#
# 三態:兩個清單都空 = 還沒動;_INFLIGHT 有 = 正在換;_MODIFIED 有 = 已經換掉。
_INFLIGHT = []


class _NoInterrupt(object):
    """把「os.replace + 登記」包起來:這段期間收到 Ctrl-C 先記著,離開之後再丟。

    裝不上處理器的情況(不在主執行緒等)就退回原本行為 —— 不會比以前更糟,
    而且還有 _INFLIGHT 那一層保險。
    """

    def __enter__(self):
        self._pending = False
        self._old = None
        try:
            self._old = signal.signal(signal.SIGINT, self._remember)
        except (ValueError, OSError):
            self._old = None
        return self

    def _remember(self, signum, frame):
        self._pending = True

    def __exit__(self, exc_type, exc, tb):
        if self._old is not None:
            try:
                signal.signal(signal.SIGINT, self._old)
            except (ValueError, OSError):
                pass
        if self._pending and exc_type is None:
            raise KeyboardInterrupt
        return False


def refuse_symlink(path, what=None):
    """目標是符號連結就不要動它。

    ⚠️ 這裡一定要用 os.path.islink(它走 lstat),不可以用 exists()。
       exists() 對「連結存在、但指到的東西不存在」的懸空連結回 False,
       整個看漏。

    兩種災情:
      · 寫入時跟著連結出去,把**資料夾外面**的檔案蓋掉
      · os.replace 把連結本身搬到遊戲檔頭上 —— 遊戲檔當場消失,
        而且畫面還會照樣印 ✅(本站 2026-09-05 實際重現過)
    """
    if os.path.islink(path):
        raise VP6Error('%s 是一個符號連結,本站沒驗過改連結會怎樣,不動它。'
                       '請直接對它指到的那個檔跑一次'
                       % (what or os.path.basename(path)))


def write_atomic(path, blob, track=True, mode_from=None):
    """原子寫入:同資料夾開一個**佔不到名字**的暫存檔,確認內容才 os.replace。

    ⚠️ 每一個會動到遊戲檔的地方都要走這裡,**回滾那一條也要**。
       直接開檔寫入在中途被中斷就會留下半截遊戲檔,而那正是出錯之後
       最不能再出錯的一步。

    ⚠️ 暫存檔的名字不可以是「路徑 + .tmp」這種猜得到的。
       猜得到就佔得住:誰先在同一個資料夾放一個
       〈檔名〉.tmp → 外面某個檔的符號連結,open(..., 'wb') 就跟著連結出去了。
       tempfile.mkstemp 走的是 O_CREAT|O_EXCL,已經存在的名字它不會用,
       所以連結佔不到。

    順序也是刻意的:寫 → flush → fsync → 比長度 → **整份讀回來逐位元組比對**
    → 照抄正本的權限 → 才 os.replace。
    中間任何一步出事(含 Ctrl+C)都把暫存檔刪掉,正本保持動手之前那一份。
    最後那個 os.replace 跟「把它記下來」綁成一段不可中斷的動作(見 _NoInterrupt),
    所以 Ctrl+C 的收尾看到的清單一定跟磁碟上的狀態一致。
    """
    refuse_symlink(path)
    folder = os.path.dirname(os.path.abspath(path))
    fd, tmp = tempfile.mkstemp(dir=folder,
                               prefix='.' + os.path.basename(path) + '.tmp-')
    done = False
    try:
        with io.open(fd, 'wb') as fh:
            fh.write(blob)
            fh.flush()
            os.fsync(fh.fileno())
        if os.path.getsize(tmp) != len(blob):
            raise VP6Error('寫出來的長度跟預期的 %d 對不上,不敢換上去' % len(blob))
        with io.open(tmp, 'rb') as fh:
            back = fh.read()
        if back != blob:
            raise VP6Error('暫存檔讀回來的內容跟要寫的不一樣(%d vs %d bytes),'
                           '不敢換上去' % (len(back), len(blob)))
        # 權限照抄:優先抄正本,正本還不存在(例如第一次建備份)就抄來源檔。
        # mkstemp 建出來的是 0600,不照抄的話換上去之後權限會變。
        src_mode = path if os.path.exists(path) else mode_from
        if src_mode and os.path.exists(src_mode):
            try:
                shutil.copymode(src_mode, tmp)
            except OSError:
                pass                      # 抄不到權限不是不寫的理由
        # ⚠️ 換名跟登記綁成一段不可中斷的動作,順序也是刻意的:
        #    先登記「正在換」→ 換名 → 登記「已經換掉」。中斷落在哪裡,
        #    收尾都說得出實話(見上面 _INFLIGHT 那一段的三態)。
        if track:
            _INFLIGHT.append(path)
        try:
            with _NoInterrupt():
                os.replace(tmp, path)
                done = True
                # ⚠️ 同一個檔可能被換兩次(縮短失敗之後的回滾就走這條),
                #    登記兩次的話 Ctrl+C 的收尾會說「已經有 2 個檔被換掉了」
                #    再把同一個檔名印兩遍 —— 數字是假的。一個檔只記一次。
                if track and path not in _MODIFIED:
                    _MODIFIED.append(path)
        except Exception:
            # os.replace 要嘛整個成功要嘛完全沒動,走到這裡可以確定沒換成,
            # 把「正在換」撤掉是安全的。
            # ⚠️ 這裡刻意只接 Exception 不接 BaseException:KeyboardInterrupt
            #    走到這裡的時候「換成了沒有」是不確定的,那一筆要留在 _INFLIGHT
            #    裡讓收尾說實話。
            # ⚠️ 用 remove(path) 不用 pop():pop 拿掉的是「最後放進去的那一筆」,
            #    只要哪天有人在這個函式外面再放一筆進去,收掉的就是別人的登記。
            if track and path in _INFLIGHT:
                _INFLIGHT.remove(path)
            raise
        if track and path in _INFLIGHT:
            _INFLIGHT.remove(path)
    finally:
        if not done:
            try:
                os.remove(tmp)
            except OSError:
                pass


def atomic_backup(path):
    """原子備份:走 write_atomic 那一套。已經有備份就不覆蓋。

    ⚠️ 這裡不可以直接 shutil.copy2 到 .introbak。
    2026-08-29 本站在別的腳本上實測過:中途中斷會留下半截備份,
    而站上同時寫著「隨時可以 --restore」—— 那句話會變成假的。

    ⚠️ 判斷「備份已經有了嗎」要用 lexists 不是 exists。
    備份如果是一條指到不存在目標的懸空連結,exists() 回 False,
    腳本就會以為沒備份而去建一個 —— 而那一步會跟著連結寫到外面去。
    """
    bak = path + BAK_SUFFIX
    refuse_symlink(bak, '備份 ' + os.path.basename(bak))
    if os.path.lexists(bak):
        return bak, False
    with io.open(path, 'rb') as fh:
        src = fh.read()
    write_atomic(bak, src, track=False, mode_from=path)
    return bak, True


def restore_hint(game_dir):
    """把「怎麼還原」印成一行可以直接複製的指令。

    ⚠️ 只印「🔴 失敗了」而不告訴讀者下一步做什麼,等於把人丟在半路上。
    """
    me = os.path.basename(sys.argv[0]) or 'mvp_skip_intro.py'
    return '     要回到動手之前,跑這一行:\n       python3 %s "%s" --restore' % (me, game_dir)


def say_file_state(game_dir, lead=''):
    """把「你的檔案現在到底怎麼樣了」講清楚。

    ⚠️ 按 Ctrl+C 跟「發生沒預料到的錯誤」都走這一個函式。
       同一件事如果抄成兩份,早晚只會改到其中一份 —— 本站吃過這個虧。

    三態,跟 _INFLIGHT / _MODIFIED 那一段對齊:
      · 正在換 X:換名開始了、還沒有結論 —— 這時候**不可以**說「沒動到」
      · 已經換掉:把檔名列出來,並把還原指令印給你
      · 兩個清單都空:才可以說「一個位元組都沒動」

    lead 是「為什麼會走到這裡」那一句(例如「你按了 Ctrl+C。」),留白也讀得通。
    """
    inflight = [x for x in _INFLIGHT if x not in _MODIFIED]
    if inflight:
        # 三態的第二態。正常情況走不到這裡(_NoInterrupt 會把中斷壓到登記
        # 做完之後才丟),這是那一層失效時的保險。
        print('  🔴 %s當時正在替換 %s —— 換成了沒有,這裡沒辦法確定。'
              % (lead, '、'.join(os.path.basename(x) for x in inflight)))
        if _MODIFIED:
            print('     在那之前已經換掉的:%s'
                  % '、'.join(os.path.basename(x) for x in _MODIFIED))
        print('     請跑下面這一行還原,或自己拿 %s 備份逐位元組比對。'
              % BAK_SUFFIX)
        print(restore_hint(game_dir))
    elif _MODIFIED:
        # _MODIFIED 記的是「真的走完 os.replace 的那些檔」。
        print('  🔴 %s已經有 %d 個檔被換掉了:%s'
              % (lead, len(_MODIFIED),
                 '、'.join(os.path.basename(x) for x in _MODIFIED)))
        print('     沒寫完的那一個不會留下半截:暫存檔已經刪掉,它還是動手之前那一份。')
        print(restore_hint(game_dir))
    else:
        print('  🔴 %s還沒有任何一個檔被換掉,遊戲檔一個位元組都沒動。' % lead)


def find_movies(game_dir):
    """找出 movies 資料夾與裡面的 .vp6。找不到就講清楚找過哪裡。"""
    cands = [os.path.join(game_dir, 'data', 'frontend', 'movies'),
             os.path.join(game_dir, 'frontend', 'movies'),
             game_dir]
    for d in cands:
        if os.path.isdir(d):
            fs = sorted(f for f in os.listdir(d) if f.lower().endswith('.vp6'))
            if fs:
                return d, fs
    raise VP6Error('找不到任何 .vp6。找過這幾個地方:\n  ' + '\n  '.join(cands))


def cmd_info(game_dir):
    d, files = find_movies(game_dir)
    print('  movies 資料夾:%s' % d)
    print('  %-16s %12s %8s %10s %8s  %s' % ('檔名', 'bytes', '影格', '影像區塊', '音訊區塊', '狀態'))
    total = 0
    for f in files:
        p = os.path.join(d, f)
        with io.open(p, 'rb') as fh:
            data = fh.read()
        total += len(data)
        try:
            s = summarise(data)
        except VP6Error as e:
            print('  %-16s %12s  ⚠️ %s' % (f, format(len(data), ','), e))
            continue
        # ⚠️ 不可以用「音訊區塊 == 0」判斷它是不是已經被縮短過。
        #    本站在四份剛安裝好的安裝上量到:creditm.vp6(工作人員名單)
        #    出廠就是無聲的 —— 只有 MV0K 24 個 + MV0F 5377 個,一個音訊區塊都沒有。
        #    拿「沒有聲音」當短版的判準,會把原版誤標成已經改過。
        #    真正可靠的訊號只有一個:這支腳本自己留下的備份。
        state = '原樣'
        if s['frames'] < 100:
            state = '很短(%d 格)' % s['frames']
        if os.path.lexists(p + BAK_SUFFIX):
            state += ' · 有本工具的備份'
        print('  %-16s %12s %8d %10d %8d  %s'
              % (f, format(len(data), ','), s['frames'],
                 s['video_frames'], s['audio_chunks'], state))
    print('  合計 %s bytes (%.1f MB)' % (format(total, ','), total / 1048576.0))
    return 0


def resolve_targets(files, which):
    """把使用者給的代號換成實際檔名。"""
    if which == 'all':
        return [f for f in files if f.lower() != MOVIES['ea'][0]]
    if which == 'cameo':
        return [f for f in files if f.lower().startswith('cameo')]
    if which in MOVIES:
        name = MOVIES[which][0]
        return [f for f in files if f.lower() == name]
    raise VP6Error('不認得的代號 %r。可用:%s / cameo / all'
                   % (which, ' / '.join(sorted(MOVIES))))


def cmd_skip(game_dir, which, keep, apply_):
    d, files = find_movies(game_dir)
    targets = resolve_targets(files, which)
    if not targets:
        print('  🔴 代號 %r 在這個資料夾裡沒有對應的檔' % which)
        return 1
    print('  movies 資料夾:%s' % d)
    print('  要處理 %d 個檔,每個留 %d 格畫面、音訊整組丟掉' % (len(targets), keep))
    if not apply_:
        print('  (這是預覽,不會寫入。確認沒問題之後同一行後面加 --apply)')
    changed = 0
    failed = []
    for f in targets:
        p = os.path.join(d, f)
        try:
            refuse_symlink(p)
            with io.open(p, 'rb') as fh:
                data = fh.read()
            new, n, hdr = build_stub(data, keep)
            verify_stub(new, n)
        except (VP6Error, OSError) as e:
            # ⚠️ 這裡不可以 return:後面的檔一個都還沒被碰過,
            #    整批中止的話使用者不會知道它們的狀況。記下來繼續跑。
            # ⚠️ OSError 也要收:讀不動這個檔(權限不足、磁碟壞軌、那個名字
            #    其實是一個資料夾)舊版會直接噴 traceback 中止,而前面已經被
            #    換掉的檔一個字都不會被提到,還原指令也印不出來。
            #    本站 2026-09-11 拿一個讀不動的檔重現過。
            print('  🔴 %-16s %s' % (f, e))
            failed.append(f)
            continue
        if len(new) >= len(data):
            print('  ⏭  %-16s 產出 %s ≥ 原本 %s,跳過(它可能已經是短版了)'
                  % (f, format(len(new), ','), format(len(data), ',')))
            continue
        print('  %-16s %12s → %8s bytes · 影格 %d → %d'
              % (f, format(len(data), ','), format(len(new), ','),
                 hdr['frames'], n))
        if apply_:
            # ⚠️ 這兩步會丟 OSError(資料夾唯讀、磁碟滿、權限不足)。
            #    不接住的話整批會噴 traceback 中止,後面那些檔的狀況
            #    使用者一無所知 —— 跟上面那個「不可以 return」是同一件事。
            try:
                bak, made = atomic_backup(p)
            except (VP6Error, OSError) as e:
                print('  🔴 %-16s 備份沒做成:%s。'
                      '遊戲檔一個位元組都沒動,也沒有開始寫' % (f, e))
                failed.append(f)
                continue
            try:
                write_atomic(p, new)
            except (VP6Error, OSError) as e:
                print('  🔴 %-16s 寫入沒成功:%s。'
                      '遊戲檔還是動手之前那一份,暫存檔已經刪掉' % (f, e))
                failed.append(f)
                continue
            # 寫完再讀一次,對不上就把動手之前那一份寫回去。
            # 回滾用的是上面讀進來的 data —— 那就是「動手之前」的內容本身,
            # 不必再去讀備份(備份可能是更早以前那一次留下的)。
            try:
                with io.open(p, 'rb') as fh:
                    verify_stub(fh.read(), n)
            except (VP6Error, OSError) as e:
                # OSError 也走回滾:換上去之後連讀都讀不回來,更沒有理由
                # 讓那一份留在遊戲資料夾裡。
                # ⚠️ 回滾一樣走 write_atomic:它會在換上去之前把內容讀回來比對過,
                #    比對不過就丟例外、暫存檔刪掉、正本維持剛才那一份。
                try:
                    write_atomic(p, data)
                except (VP6Error, OSError) as e2:
                    print('  🔴 %-16s 寫回去之後讀不回來(%s),而且回滾也沒成功'
                          '(%s)。備份還在:%s,請手動把它改名蓋回去'
                          % (f, e, e2, os.path.basename(bak)))
                else:
                    print('  🔴 %-16s 寫回去之後讀不回來(%s),'
                          '已經把動手之前的內容寫回去,逐位元組比對過。請回報' % (f, e))
                failed.append(f)
                continue
            print('       ✅ 已寫入%s' % ('、備份 ' + os.path.basename(bak) if made else '(備份本來就有,沒覆蓋)'))
            changed += 1
    if failed:
        print('  🔴 有 %d 個檔沒有處理成功:%s' % (len(failed), '、'.join(failed)))
        # 只有真的換過檔才印還原指令。一個都沒換到還叫人「回到動手之前」,
        # 會讓讀者以為自己的遊戲被動過了。
        if apply_ and _MODIFIED:
            print(restore_hint(game_dir))
    if apply_ and changed:
        print('  ✅ 複驗通過:%d 個檔都讀得回來,影格數與區塊組成都對得上' % changed)
    elif apply_ and not failed:
        print('  一個檔都沒有改到(全部被跳過),所以沒有東西要複驗。')
    return 1 if failed else 0


def cmd_restore(game_dir):
    d, files = find_movies(game_dir)
    n = 0
    failed = []
    for f in files:
        p = os.path.join(d, f)
        bak = p + BAK_SUFFIX
        # ⚠️ lexists 不是 exists:備份如果是一條懸空的符號連結,exists() 回 False,
        #    這個檔就被無聲跳過了 —— 讀者會以為「沒備份」,而其實是備份壞了。
        if not os.path.lexists(bak):
            continue
        # ⚠️ 先驗備份、再決定要不要寫。順序反過來就是把壞備份蓋上去。
        try:
            refuse_symlink(p)
            src = check_backup_usable(bak)
        except (VP6Error, OSError) as e:
            print('  🔴 %-16s 不還原:%s' % (f, e))
            print('       遊戲檔一個位元組都沒有動,備份檔也原封不動留著。'
                  '請改用你動手之前做的那份整包備份')
            failed.append(f)
            continue
        try:
            write_atomic(p, src)
        except (VP6Error, OSError) as e:
            print('  🔴 %-16s 還原失敗:%s(遊戲檔沒有被換掉)' % (f, e))
            failed.append(f)
            continue
        # 比完整長度。⚠️ 不可以用 zip() 兩兩比 —— 那會在短的那一邊停,
        #    少掉的尾巴永遠比不到,半截檔反而會被判成一樣。
        # ⚠️ 這一次讀取也要收 OSError:檔案**已經被換掉了**,這時候噴 traceback
        #    是最糟的 —— 讀者只看到一段錯誤,不知道這個檔還原了沒有,
        #    後面還有備份的檔也全部沒被處理。本站 2026-09-11 重現過。
        try:
            with io.open(p, 'rb') as fh:
                back = fh.read()
        except OSError as e:
            print('  🔴 %-16s 備份已經寫回去了,但接著要再讀一次確認的時候讀不到'
                  '(%s)。這個檔已經被換成備份那一份了,請自己比對確認' % (f, e))
            failed.append(f)
            continue
        if back != src:
            print('  🔴 %-16s 寫回去了,但讀出來跟備份不一樣'
                  '(%d vs %d bytes)。請回報' % (f, len(back), len(src)))
            failed.append(f)
            continue
        print('  ✅ 還原 %-16s %s bytes' % (f, format(len(src), ',')))
        n += 1
    if failed:
        print('  🔴 有 %d 個檔沒有還原成功:%s' % (len(failed), '、'.join(failed)))
        return 1
    if not n:
        print('  這個資料夾裡沒有 %s 備份,沒有東西要還原。' % BAK_SUFFIX)
    return 0


def _selftest():
    """反向測試:自己造一份假的 .vp6,證明每一道檢查真的會擋。

    ⚠️ 不碰任何遊戲檔。前八個餌只用記憶體;餌 9-18 要驗的是檔案系統上的行為
       (符號連結、換檔失敗、換名與登記的先後、換名之後才被 Ctrl+C 打斷、
       一批檔裡有一個讀不動、還原之後讀不回來、沒預料到的錯誤、同一個檔換兩次),
       所以在系統暫存區用 mkdtemp 現開一個拋棄式資料夾,跑完整個刪掉。
       路徑是當場生出來的,不可能指到你的遊戲。

    在 python3 -O 底下不跑,直接回 2。
    """
    # ⚠️ python3 -O 會把整份程式裡的 assert 拿掉。這一支目前用的是 if/else 不是
    #    assert,所以 -O 還不會讓它假綠;擋掉是為了跟全站的自我測試一致,
    #    而且哪天這裡改寫成 assert,守門已經在了,不必指望那時候有人記得補。
    #    回 2 不回 1:「測試沒跑」跟「測試沒過」是兩回事,混在一起會看不出來。
    if sys.flags.optimize:
        print('  🔴 --selftest 不能在 python3 -O 底下跑:-O 會把 assert 全部拿掉,'
              '測試會變成一片假的綠燈。請拿掉 -O 再跑一次。')
        return 2
    fails = []
    skipped = []

    def mk(frames, chunks):
        h = bytearray(HDR_LEN)
        h[0:4] = MAGIC
        struct.pack_into('<I', h, 4, HDR_LEN)
        struct.pack_into('<H', h, OFF_W, 640)
        struct.pack_into('<H', h, OFF_H, 480)
        struct.pack_into('<I', h, OFF_FRAMES, frames)
        body = b''
        for tag, extra in chunks:
            size = 8 + extra
            body += tag + struct.pack('<I', size) + b'\0' * extra
        return bytes(h) + body

    # 陰性對照:一份長得像原版的檔,要能正常縮短
    good = mk(4, [(b'SCHl', 32), (CHUNK_KEY, 76),
                  (b'SCDl', 20), (CHUNK_FRAME, 68),
                  (b'SCDl', 20), (CHUNK_FRAME, 68),
                  (b'SCDl', 20), (CHUNK_FRAME, 68)])
    try:
        check_vp6_blob(good, '陰性對照')
        new, n, _ = build_stub(good, 3)
        verify_stub(new, n)
        if n != 3:
            fails.append('陰性對照:留 3 格卻得到 %d 格' % n)
        if len(new) >= len(good):
            fails.append('陰性對照:產出沒有變小')
    except VP6Error as e:
        fails.append('陰性對照本身就失敗了:%s' % e)

    # 餌 1:開頭不是 MVhd
    try:
        read_header(b'XXXX' + good[4:])
        fails.append('餌1 沒抓到:開頭不是 MVhd 竟然過了')
    except VP6Error:
        pass

    # 餌 2:區塊長度超出檔案
    bad = bytearray(good)
    struct.pack_into('<I', bad, HDR_LEN + 4, 999999)
    try:
        walk_chunks(bytes(bad))
        fails.append('餌2 沒抓到:區塊長度超出檔案竟然過了')
    except VP6Error:
        pass

    # 餌 3:檔頭影格數跟實際區塊數對不上
    try:
        new, n, _ = build_stub(good, 3)
        tampered = bytearray(new)
        struct.pack_into('<I', tampered, OFF_FRAMES, n + 1)
        verify_stub(bytes(tampered), n + 1)
        fails.append('餌3 沒抓到:影格數對不上竟然過了')
    except VP6Error:
        pass

    # 餌 4:音訊區塊沒丟乾淨
    # ⚠️ 這個餌要讓「音訊殘留」變成**唯一**會擋下來的理由:影格數對得上、
    #    區塊數對得上、第一格也是關鍵影格,只有音訊沒丟乾淨。
    #    舊版的餌拿 pack_into 去改一份當場丟掉的 bytearray 副本,檔頭根本沒被改到,
    #    於是永遠停在前一道檢查 —— 把音訊那一道整個關掉,自我測試照樣印綠燈。
    leftover = mk(2, [(CHUNK_KEY, 76), (b'SCDl', 20)])
    try:
        verify_stub(leftover, 2)
        fails.append('餌4 沒抓到:留著音訊區塊竟然過了')
    except VP6Error as e:
        if '音訊' not in str(e):
            fails.append('餌4 是被別的檢查擋掉的(%s),音訊那一道根本沒被測到' % e)

    # 餌 5:第一格不是關鍵影格
    nokey = mk(2, [(CHUNK_FRAME, 68), (CHUNK_FRAME, 68)])
    try:
        build_stub(nokey, 2)
        fails.append('餌5 沒抓到:沒有關鍵影格竟然過了')
    except VP6Error:
        pass

    # 餌 6:備份是 0 bytes(還原那條路上最致命的一種)
    #      這個餌不只要求「有擋」,還要求擋下來的理由**指名是哪一份** ——
    #      不然讀者看到「檔案只有 0 個位元組」會以為空掉的是自己的遊戲檔。
    try:
        check_vp6_blob(b'', '假備份')
        fails.append('餌6 沒抓到:0 bytes 的備份竟然可以蓋回去')
    except VP6Error as e:
        if '假備份' not in str(e):
            fails.append('餌6 擋下來了,但訊息沒指名是哪一份(%s)' % e)

    # 餌 7:備份剛好被截斷在區塊邊界上 —— 長度加總還是對的,最難抓的那一種。
    #      檔頭寫 4 格,實際只剩 2 個影像區塊。
    half = mk(4, [(CHUNK_KEY, 76), (CHUNK_FRAME, 68)])
    try:
        check_vp6_blob(half, '假備份')
        fails.append('餌7 沒抓到:檔頭說 4 格、實際只剩 2 格的半截備份竟然過了')
    except VP6Error:
        pass

    # 餌 8:備份尾巴多出幾個走不完的位元組(區塊長度加總對不上檔案長度)
    try:
        check_vp6_blob(good + b'\0\0\0', '假備份')
        fails.append('餌8 沒抓到:尾巴多三個位元組的備份竟然過了')
    except VP6Error:
        pass

    # ── 餌 9-18:要真的碰檔案系統。全程在 mkdtemp 開的拋棄式資料夾裡。
    sandbox = tempfile.mkdtemp(prefix='mvp_skip_intro_selftest_')
    try:
        outside = os.path.join(sandbox, 'outside.txt')
        with io.open(outside, 'wb') as fh:
            fh.write(b'DO-NOT-TOUCH')
        work = os.path.join(sandbox, 'movies')
        os.mkdir(work)
        tgt = os.path.join(work, 'movie.vp6')
        with io.open(tgt, 'wb') as fh:
            fh.write(good)

        def link(name, dest=outside):
            """建一條符號連結。Windows 沒開開發者模式就建不出來,那就據實說跳過。"""
            try:
                os.symlink(dest, os.path.join(work, name))
                return True
            except (OSError, NotImplementedError, AttributeError):
                return False

        # 餌 9:先佔住猜得到的暫存檔名字。
        #      舊版寫死 path + '.tmp',誰先放一條 movie.vp6.tmp → 資料夾外的連結,
        #      open(..., 'wb') 就跟著連結出去把外面那個檔蓋掉,而且 os.replace
        #      還會把連結搬到 movie.vp6 頭上 —— 遊戲檔當場消失。
        #      本站 2026-09-05 在改之前的版本上真的重現過:一個 829,172 bytes 的
        #      easports.vp6 變成一條符號連結,畫面照樣印 ✅、回傳 0。
        occupied = [n for n in ('movie.vp6.tmp', 'movie.vp6.part',
                                'movie.vp6' + BAK_SUFFIX + '.tmp') if link(n)]
        if not occupied:
            skipped.append('餌9(這個環境建不出符號連結)')
        stub, _kept, _hdr = build_stub(good, 3)
        atomic_backup(tgt)
        write_atomic(tgt, stub)
        with io.open(outside, 'rb') as fh:
            if fh.read() != b'DO-NOT-TOUCH':
                fails.append('餌9 沒抓到:資料夾外面那個檔被暫存檔的符號連結帶著改掉了')
        if os.path.islink(tgt):
            fails.append('餌9 沒抓到:遊戲檔被換成一條符號連結了')
        with io.open(tgt, 'rb') as fh:
            if fh.read() != stub:
                fails.append('餌9:寫入本身就不對,短版沒有進到檔案裡')
        with io.open(tgt + BAK_SUFFIX, 'rb') as fh:
            if fh.read() != good:
                fails.append('餌9:備份的內容不是動手之前那一份')

        # 餌 10:遊戲檔自己就是符號連結 → 連讀都不讀。
        if link('link.vp6'):
            try:
                write_atomic(os.path.join(work, 'link.vp6'), b'X' * 40)
                fails.append('餌10 沒抓到:對著符號連結寫入竟然過了')
            except VP6Error:
                pass
            with io.open(outside, 'rb') as fh:
                if fh.read() != b'DO-NOT-TOUCH':
                    fails.append('餌10:外面那個檔被改掉了')
        else:
            skipped.append('餌10(這個環境建不出符號連結)')

        # 餌 11:備份是符號連結 → atomic_backup 要拒絕,不可以「當作已經有備份」放行,
        #       --restore 也不可以照著它讀。
        #       ⚠️ 連結的目標刻意放一份**合法的** .vp6:目標如果是垃圾,
        #          check_vp6_blob 自己就會擋下來,那這個餌根本沒測到連結守門
        #          (本站 2026-09-05 第一版的餌就是這樣,反向測試才看出來)。
        elsewhere = os.path.join(sandbox, 'elsewhere.vp6')
        with io.open(elsewhere, 'wb') as fh:
            fh.write(good)
        tgt2 = os.path.join(work, 'movie2.vp6')
        with io.open(tgt2, 'wb') as fh:
            fh.write(good)
        if link('movie2.vp6' + BAK_SUFFIX, elsewhere):
            try:
                atomic_backup(tgt2)
                fails.append('餌11 沒抓到:備份是符號連結竟然過了')
            except VP6Error:
                pass
            try:
                check_backup_usable(tgt2 + BAK_SUFFIX)
                fails.append('餌11 沒抓到:還原時拿符號連結當備份竟然過了')
            except VP6Error:
                pass
        else:
            skipped.append('餌11(這個環境建不出符號連結)')

        # 餌 12:換上去那一步失敗 → 正本原封不動,而且不留半截暫存檔。
        #       這一條就是「還原到一半失敗」那個情境:--restore 走的是同一個
        #       write_atomic,所以擋住這裡等於擋住還原。
        real_replace = os.replace

        def boom(_a, _b):
            raise OSError('餌 12 故意讓 os.replace 失敗')

        os.replace = boom
        try:
            write_atomic(tgt, b'X' * 100)
            fails.append('餌12 沒抓到:os.replace 失敗竟然沒有丟例外')
        except (VP6Error, OSError):
            # 兩種都收:餌 9 要是先壞了(遊戲檔被換成符號連結),這裡會是
            # VP6Error。不收的話整個自我測試會噴 traceback,把前面收集到的
            # 失敗清單一起蓋掉 —— 讀者就看不到真正的原因。
            pass
        finally:
            os.replace = real_replace
        with io.open(tgt, 'rb') as fh:
            if fh.read() != stub:
                fails.append('餌12:換上去失敗之後正本被改掉了')
        left = [x for x in os.listdir(work) if '.tmp-' in x]
        if left:
            fails.append('餌12:失敗之後留下暫存檔 %s' % left)
        if _INFLIGHT:
            fails.append('餌12:換名失敗了,「正在換」的登記卻沒有收掉(%r)'
                         % _INFLIGHT)

        # 餌 13:「正在換 X」一定要在換名**之前**就登記好。
        #       三態的第二態靠的是這個順序。順序反過來的話,萬一 _NoInterrupt
        #       那一層失效(例如不在主執行緒,處理器裝不上去),中斷落在換名中間
        #       就沒有人說得出「正在替換 X」,收尾又會變成「沒動到」。
        tgt3 = os.path.join(work, 'movie3.vp6')
        with io.open(tgt3, 'wb') as fh:
            fh.write(good)
        del _MODIFIED[:]
        del _INFLIGHT[:]
        seen = []

        def watch(a, b):
            seen.append(list(_INFLIGHT))     # 換名當下的登記,拍一張照
            return real_replace(a, b)

        os.replace = watch
        try:
            write_atomic(tgt3, stub)
        finally:
            os.replace = real_replace
        if not seen or tgt3 not in seen[-1]:
            fails.append('餌13 沒抓到:os.replace 執行的當下「正在換」還沒登記,'
                         '三態的第二態是空的')
        if _INFLIGHT:
            fails.append('餌13:換完了,「正在換」的登記卻沒收掉(%r)' % _INFLIGHT)
        if tgt3 not in _MODIFIED:
            fails.append('餌13:換完了卻沒有記進「已經換掉」的清單')

        # 餌 14:換名做完、登記之前收到 Ctrl+C —— 登記不可以漏掉。
        #       這就是 2026-09-06 稽核抓到的那個窗口。本站拿變體檔在修之前的
        #       版本上重現過:easports.vp6 的 sha256 真的變了,畫面卻說
        #       「一個位元組都沒動」。
        #       模擬 Ctrl+C 要靠 signal.raise_signal(Python 3.8 才有);
        #       沒有它、或不在主執行緒(處理器裝不上去)就據實說跳過。
        raiser = getattr(signal, 'raise_signal', None)
        if raiser is None and os.name != 'nt':
            def raiser(sig):
                os.kill(os.getpid(), sig)
        cur = signal.getsignal(signal.SIGINT)
        try:
            # 把現在的處理器原封不動再裝一次:裝得上去就代表在主執行緒。
            # ⚠️ 不可以寫成「getsignal(...) or 預設處理器」—— SIG_DFL 的值是 0,
            #    是假值,那樣寫會把 SIG_DFL 悄悄換成別的東西。
            if cur is None:                 # 處理器不是 Python 裝的,不要碰
                raise ValueError('處理器不是 Python 裝的')
            signal.signal(signal.SIGINT, cur)
            can_sim = True
        except (ValueError, OSError, TypeError):
            can_sim = False
        if raiser is None or not can_sim:
            skipped.append('餌14(這個環境沒辦法在自己身上模擬 Ctrl+C)')
        else:
            tgt4 = os.path.join(work, 'movie4.vp6')
            with io.open(tgt4, 'wb') as fh:
                fh.write(good)
            del _MODIFIED[:]
            del _INFLIGHT[:]

            def replace_then_interrupt(a, b):
                r = real_replace(a, b)
                raiser(signal.SIGINT)        # 換名剛做完就中斷
                return r

            os.replace = replace_then_interrupt
            interrupted = False
            try:
                try:
                    write_atomic(tgt4, stub)
                except KeyboardInterrupt:
                    interrupted = True
                finally:
                    os.replace = real_replace
            except KeyboardInterrupt:
                # 訊號晚一點才送到的情況(它是在下一個位元組碼邊界才處理的),
                # 一樣收下來,不要讓自我測試噴 traceback 把失敗清單蓋掉。
                interrupted = True
            if not interrupted:
                fails.append('餌14 沒抓到:被壓住的 Ctrl+C 應該在不可中斷段'
                             '結束的時候丟出來')
            with io.open(tgt4, 'rb') as fh:
                really_swapped = fh.read() == stub
            if not really_swapped:
                fails.append('餌14 的前提不成立:換名根本沒做完,這個餌沒測到東西')
            elif tgt4 not in _MODIFIED:
                fails.append('餌14 沒抓到:檔案已經換掉了,清單卻說沒動到 —— '
                             'Ctrl+C 的收尾會說謊')
            if [x for x in _INFLIGHT if x not in _MODIFIED]:
                fails.append('餌14:已經換完了,「正在替換」的登記還掛著')

        # 餌 15:一批檔裡有一個**讀不動**(權限、磁碟壞軌,或那個名字其實是一個
        #       資料夾)。舊版在這裡直接噴 traceback 中止:前面已經換掉的檔
        #       一個字都不會被提到,還原指令也印不出來,後面的檔則完全沒被碰過
        #       而使用者不知道。本站 2026-09-11 拿一個讀不動的檔重現過。
        #       這個餌用「資料夾冒充 .vp6」來製造 OSError —— 不必動權限位元,
        #       所以在哪個作業系統、用哪個帳號跑都一樣會觸發。
        g15 = os.path.join(sandbox, 'g15', 'data', 'frontend', 'movies')
        os.makedirs(g15)
        for nm in ('cameo01.vp6', 'cameo03.vp6'):
            with io.open(os.path.join(g15, nm), 'wb') as fh:
                fh.write(good)
        os.mkdir(os.path.join(g15, 'cameo02.vp6'))
        del _MODIFIED[:]
        del _INFLIGHT[:]
        rc15, e15, out15 = None, None, ''
        buf = io.StringIO()
        real_stdout = sys.stdout
        sys.stdout = buf
        try:
            rc15 = cmd_skip(os.path.join(sandbox, 'g15'), 'cameo', 3, True)
        except OSError as e:
            e15 = e
        finally:
            sys.stdout = real_stdout
            out15 = buf.getvalue()
        if e15 is not None:
            fails.append('餌15 沒抓到:一個讀不動的檔就讓整批噴出例外(%s)' % e15)
        else:
            if rc15 == 0:
                fails.append('餌15 沒抓到:有檔沒處理成功,結束碼卻是 0')
            if 'cameo02.vp6' not in out15:
                fails.append('餌15:讀不動的那個檔沒有被列出來,使用者不知道是哪一個')
            if '--restore' not in out15:
                fails.append('餌15:已經換掉檔了,卻沒有把還原指令印出來')
            for nm in ('cameo01.vp6', 'cameo03.vp6'):
                if os.path.getsize(os.path.join(g15, nm)) >= len(good):
                    fails.append('餌15:%s 沒有被縮短 —— 讀不動的那一個不應該'
                                 '拖累前後兩個檔' % nm)

        # 餌 16:還原**已經寫回去了**,接著要再讀一次確認的時候讀不到。
        #       這是最不能噴 traceback 的一個位置:檔案已經被換掉,而讀者
        #       只會看到一段錯誤,不知道這個檔還原了沒有,後面有備份的檔
        #       也全部沒被處理。
        g16 = os.path.join(sandbox, 'g16', 'data', 'frontend', 'movies')
        os.makedirs(g16)
        v16 = os.path.join(g16, 'cameo05.vp6')
        with io.open(v16, 'wb') as fh:
            fh.write(stub)                       # 現在是短版
        with io.open(v16 + BAK_SUFFIX, 'wb') as fh:
            fh.write(good)                       # 備份是動手之前那一份
        del _MODIFIED[:]
        del _INFLIGHT[:]
        real_io_open = io.open

        def open_fail_readback(path, mode='r', *args, **kw):
            # 只擋「還原之後再讀一次確認」那一次:在那之前 cmd_restore
            # 沒有用讀取模式開過正本(備份與暫存檔都是別的路徑)。
            if 'r' in mode and 'b' in mode and isinstance(path, str) \
                    and os.path.abspath(path) == os.path.abspath(v16):
                raise OSError('餌 16 故意讓還原之後那一次讀取失敗')
            return real_io_open(path, mode, *args, **kw)

        rc16, e16, out16 = None, None, ''
        buf = io.StringIO()
        real_stdout = sys.stdout
        io.open = open_fail_readback
        sys.stdout = buf
        try:
            rc16 = cmd_restore(os.path.join(sandbox, 'g16'))
        except OSError as e:
            e16 = e
        finally:
            sys.stdout = real_stdout
            io.open = real_io_open
            out16 = buf.getvalue()
        if e16 is not None:
            fails.append('餌16 沒抓到:還原之後那一次讀取失敗竟然噴出例外(%s)' % e16)
        else:
            if rc16 == 0:
                fails.append('餌16 沒抓到:還原沒確認成功,結束碼卻是 0')
            if 'cameo05.vp6' not in out16:
                fails.append('餌16:沒有講是哪一個檔')
            with io.open(v16, 'rb') as fh:
                if fh.read() != good:
                    fails.append('餌16 的前提不成立:備份根本沒有寫回去,'
                                 '這個餌沒測到東西')

        # 餌 17:發生本站沒有預料到的作業系統錯誤。收尾不可以只丟一段 traceback ——
        #       要先講清楚「哪些檔已經被換掉了」再回非 0。
        g17 = os.path.join(sandbox, 'g17')
        os.makedirs(g17)
        del _MODIFIED[:]
        del _INFLIGHT[:]
        _MODIFIED.append(os.path.join(g17, 'cameo07.vp6'))   # 假裝前面換過一個
        real_find = find_movies

        def find_boom(_d):
            raise OSError('餌 17 故意丟一個沒預料到的作業系統錯誤')

        rc17, e17, out17 = None, None, ''
        buf = io.StringIO()
        real_stdout = sys.stdout
        globals()['find_movies'] = find_boom
        sys.stdout = buf
        try:
            rc17 = main(['mvp_skip_intro.py', g17, '--info'])
        except OSError as e:
            e17 = e
        finally:
            sys.stdout = real_stdout
            globals()['find_movies'] = real_find
            out17 = buf.getvalue()
        if e17 is not None:
            fails.append('餌17 沒抓到:沒預料到的錯誤直接噴成 traceback(%s)' % e17)
        else:
            if rc17 == 0:
                fails.append('餌17 沒抓到:出錯了,結束碼卻是 0')
            if 'cameo07.vp6' not in out17:
                fails.append('餌17 沒抓到:已經被換掉的檔沒有被講出來 —— '
                             '讀者不知道自己的遊戲現在是什麼狀態')
            if '--restore' not in out17:
                fails.append('餌17:換過檔了卻沒有把還原指令印出來')
        del _MODIFIED[:]

        # 餌 18:同一個檔被換兩次(縮短失敗之後的回滾就走這條),只可以登記一次。
        #       登記兩次的話,Ctrl+C 的收尾會說「已經有 2 個檔被換掉了」
        #       再把同一個檔名印兩遍 —— 那個數字是假的。
        tgt6 = os.path.join(work, 'movie6.vp6')
        with io.open(tgt6, 'wb') as fh:
            fh.write(good)
        del _MODIFIED[:]
        del _INFLIGHT[:]
        write_atomic(tgt6, stub)
        write_atomic(tgt6, good)                 # 回滾:把動手之前那一份寫回去
        if _MODIFIED.count(tgt6) != 1:
            fails.append('餌18 沒抓到:同一個檔換兩次就登記了 %d 次,'
                         '收尾報的數字會是假的' % _MODIFIED.count(tgt6))
        if _INFLIGHT:
            fails.append('餌18:換完了,「正在換」的登記卻沒收掉(%r)' % _INFLIGHT)
    finally:
        shutil.rmtree(sandbox, ignore_errors=True)
        # 自我測試動的是拋棄式檔案,不要混進 Ctrl+C 的清單
        del _MODIFIED[:]
        del _INFLIGHT[:]

    if fails:
        for x in fails:
            print('  🔴 %s' % x)
        print('  總判定: ❌ 自我測試沒過')
        return 1
    print('  ✅ 自我測試通過(1 個陰性對照 + %d 個反向餌全部抓到)' % (18 - len(skipped)))
    if skipped:
        print('  ⚠️ 這個環境跳過了:%s' % '、'.join(skipped))
    return 0


def main(argv):
    ap = argparse.ArgumentParser(
        description='關掉 MVP Baseball 2005 的開場動畫(用你自己那一份改短,不刪檔)')
    ap.add_argument('game_dir', nargs='?', help='遊戲資料夾')
    ap.add_argument('--info', action='store_true', help='只看,不動任何檔案')
    ap.add_argument('--skip', metavar='代號',
                    help='要縮短哪一支:intro / credits / ea / cameo / all')
    ap.add_argument('--keep', type=int, default=25,
                    help='留幾格畫面(預設 25,跟本站測試機那份社群樁一樣)')
    ap.add_argument('--apply', action='store_true', help='真的寫入(不加就只是預覽)')
    ap.add_argument('--restore', action='store_true', help='把備份蓋回去')
    ap.add_argument('--selftest', action='store_true', help='跑自我測試,不碰遊戲檔')
    a = ap.parse_args(argv[1:])

    if a.selftest:
        return _selftest()
    if not a.game_dir:
        ap.print_help()
        return 2
    if a.keep < 1:
        print('  🔴 --keep 至少要 1'); return 2
    try:
        if a.restore:
            return cmd_restore(a.game_dir)
        if a.skip:
            return cmd_skip(a.game_dir, a.skip, a.keep, a.apply)
        return cmd_info(a.game_dir)
    except VP6Error as e:
        print('  🔴 %s' % e)
        return 1
    except KeyboardInterrupt:
        # ⚠️ 這裡的重點是**講實話**。舊版按 Ctrl+C 會噴一整段 traceback,
        #    讀者完全不知道自己的遊戲檔到底被換掉了沒有。
        print('')
        say_file_state(a.game_dir, '你按了 Ctrl+C。')
        return 130
    except OSError as e:
        # ⚠️ 沒有預料到的作業系統錯誤(磁碟滿、磁碟拔掉、資料夾中途被搬走)。
        #    舊版走到這裡是一段 traceback,而前面可能已經換掉幾個檔了 ——
        #    讀者看不出自己的遊戲現在是什麼狀態。錯誤照印,但先講檔案的下場。
        print('')
        print('  🔴 作業系統回報了一個錯誤:%s' % e)
        say_file_state(a.game_dir, '')
        print('     請把整段輸出帶到回報頁。')
        return 1


if __name__ == '__main__':
    sys.exit(main(sys.argv))


# ─────────────────────────────────────────────────────────
#  MIT License
#
#  Copyright (c) 2026 toni
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in
#  all copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
#  THE SOFTWARE.
# ─────────────────────────────────────────────────────────
