#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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

"""
mvp_read_voice.py —— 讀懂 MVP Baseball 2005 的語音檔（唯讀，不會改任何東西）

    列出遊戲裡的語音   python3 mvp_read_voice.py "<遊戲資料夾>" --list
    看單一語音檔       python3 mvp_read_voice.py "<某個 .dat>"
    看內部區塊切法     python3 mvp_read_voice.py "<某個 .dat>" --blocks

⚠️ 這支腳本**不會**把語音變成 WAV —— 這一課只負責讀懂結構。
   要匯出 WAV 或把你自己的聲音寫回去，用 make-voice 那一課的 mvp_audio.py。

─────────────────────────────────────────────────────────
 這支在做什麼
─────────────────────────────────────────────────────────
一句話：把遊戲的語音檔拆開，把外殼裡量得出來的東西印給你看，全程唯讀。

吃什麼（輸入）
  · 遊戲資料夾 ＋ --list：往下找 data/audio，把每個 **BIGF** 封裝檔裡有幾段語音、
    分別用哪種編碼列出來。找不到 data/audio 就直接掃你給的那一層，
    所以散裝資料夾或單獨一個封裝檔也吃得下去。
    ⚠️ 只認 BIGF 開頭的封裝檔。cd/ 底下那 8 個「本身就是一長串 SCHl」的 .big
    （pbpdat / chantdat / padat / rallydat / plchtdat / hsfxdat / stdmdat /
    bdcstdat）不會出現在 --list 的清單裡 —— 播報語音就在其中最大的那個
    pbpdat.big。要看它們就把檔案本身指給這支腳本。
  · 單一語音檔（.dat，或你從封裝檔裡撈出來的一段）：印那一個檔的檔頭。
    ⚠️ 剛安裝好的原版**沒有散裝的 .dat**（本站數過原版 data/audio 底下 82 個
    非 .big 的檔，.dat 是 0 個），語音全部包在 .big 裡；散裝的 .dat 多半來自
    社群語音包。這支沒有取出功能，要把某一段撈成 WAV 是 make-voice 那一課的
    mvp_audio.py --export；上面說的那 8 個 .big 則可以直接指給這支腳本。
  · 再加 --blocks：連聲音資料內部怎麼切成聲道、怎麼切成 15 個位元組一組都印出來。

吐什麼（輸出）
  · 只有畫面上的文字。它不寫檔、不建資料夾、不產生 WAV。
    整支腳本開檔一律是 'rb'，沒有任何 open(..., 'w')，你可以自己搜一次確認。
  · 回傳值：讀得懂是 0；讀不懂、找不到檔案、或路徑給的是資料夾卻沒加 --list，
    這三種都印一句人話然後回 2（不丟 traceback）。

安全網
  · 唯讀是它的預設，也是它唯一的模式：沒有 --apply、沒有備份、也沒有還原功能，
    因為它從頭到尾沒有任何東西可以被改壞。
  · 讀不懂就停下來（丟 DataError），不硬解：開頭不是 SCHl、區塊長度不合理，
    這兩種會印一句人話然後結束（回傳 2）。--list 掃整包時則是跳過讀不懂的那一項，
    --blocks 遇到某一段切不開也只會說那一段切不開，其餘照樣走完。
  · 印出來的東西分「量到的」與「推論」：取樣率 48,000 Hz 是推論，
    而且只涵蓋 GSTR 容器的編碼 3（社群做的那批裡的一種）。EA 原版、以及
    PT 容器的編碼 3，本站都測不出來，所以不替它們換算秒數。
    而且那個推論**本身也還沒定案**，第三節那個 ⚠️ 寫了矛盾在哪。

做不到的事
  · 不會把語音變成 WAV，也不會把你的聲音寫回去（那兩件事在 make-voice 那一課）。
  · 只認 SCHl 開頭的語音檔。BIGF 封裝檔只列目錄，不解裡面的圖或別的資料。
  · 聲音資料的切法只在 **GSTR 容器的編碼 3** 上驗過。遇到別的（編碼 1、編碼 2、
    以及 PT 容器的編碼 3）只印外殼，--blocks 會直接說本站沒解開然後停手，
    而不是套一套印出看起來像真的數字。

─────────────────────────────────────────────────────────
 為什麼會有這一課
─────────────────────────────────────────────────────────
本站原本把「換播報語音」整條路標成做不到，理由是「音訊編碼沒解開」。
**那是把「未解」貼在錯的格子。**社群二十年前就換成功了 ——
他們需要的是「產生一個遊戲吃得下去的檔」，不是「把 EA 的解碼出來」。

這一課是往那個方向的第一步：先確認我們真的讀得懂外殼。
結果是外殼讀懂了，最後一格當時還沒 —— 那一格 2026-08-29 也解開了，見下面第四節。
下面每個數字都可以自己重跑。

─────────────────────────────────────────────────────────
 一、外殼（完全解開）
─────────────────────────────────────────────────────────
語音檔是 EA 的區塊鏈：

    SCHl  檔頭 + 一串標籤
    SCCl  計數
    SCDl  聲音資料（可以有很多個）
    SCEl  結束

每個區塊 = 4 bytes 標記 + 4 bytes 長度（小端序）。
剛安裝好的原版 6,995 個語音檔，區塊鏈 100% 完整。

檔頭標籤是「標籤(1) + 長度(1) + 值」，但 0xFC/0xFD/0xFE 沒有長度也沒有值：

  0x06  恆為 101（6,995 個全部一樣）
  0x80  編碼方式    EA 原版 = 2 · 社群做的 = 3
  0x82  聲道數（本站這台機器上，編碼 3 的 8,767 個裡 8,446 個是 1、321 個是 2；
        下面第二節那套雙聲道擺法講的是那 321 個。編碼 1 與 2 全部是 1）
  0x84  取樣率（分編碼差很多：剛安裝好的原版 6,995 個一個都沒標；本站這台機器上
        編碼 2 的 7,271 個裡 207 個有標，編碼 3 的 8,767 個裡 8,230 個有標，
        其中 7,841 個標 22,050 Hz）
  0x85  取樣數
  0xa0  恆為 4。但「只有 EA 原版有」是錯的：本站兩份安裝上量到 PT 容器的
        15,283 個項目**全部**有這個標籤，GSTR 容器的 8,203 個裡只有 11 個有
        —— 它比較像「PT 容器的記號」，不是「EA 原版的記號」。

驗證方式很硬：**標籤解析消耗的長度必須等於檔頭宣告的長度** ——
原版 6,995 個檔全部落在檔頭宣告長度的 1 個位元組容差內（程式第 459 行就是這樣判的：2,556 個剛好相等、4,439 個差 1）。

─────────────────────────────────────────────────────────
 二、聲音資料怎麼擺（完全解開）
─────────────────────────────────────────────────────────
每個 SCDl 的內容是：

    [4 bytes] 這一段的取樣數（位元組序看容器：PT 小端、GSTR 大端）
    [4 bytes] 左聲道起點（永遠 0）
    [4 bytes] 右聲道起點
    [......]  左聲道一整段
    [......]  右聲道一整段

**兩個聲道不是交錯的，是各自連續一整段。**
驗證：右聲道起點必須正好等於「剩下資料的一半」——
社群檔在這台機器上 321 個雙聲道檔、2,382 段全部吻合（可以自己重跑）。

（本站原本按「左 15 右 15 交錯」解，等於把兩邊剪碎後交叉黏起來。
  這是這一課走過最大的一段冤枉路。）

每個聲道裡面是 **15 個位元組一組**：1 個表頭 + 14 個資料位元組（= 28 個半位元組）。
表頭的高半位元組是 0–3（四組係數之一）。驗證方式是**掃相位**：
切在對的位置時「高半位元組 ≤ 3」占 **97.7%**，切錯位置時只有約 50%
（= 亂猜的水準）。差距這麼大，切法就不可能是猜的。

⚠️ **這一整節只在「GSTR 容器」的編碼 3 檔上成立**（2026-09-05 量到的分界）。
   編碼 3 有兩種容器，行為完全相反：
     · GSTR（本站這台機器 8,203 個）：掃相位中位數 1.000、98.0% 的聲道 >0.9，
       會印「⚠️ 切法可能不對」的只有 2.2% 的檔。上面那些數字講的就是這一批。
     · PT（564 個）：掃相位中位數 0.478 —— 就是亂猜的水準，**100% 的檔都會印
       「⚠️ 切法可能不對」**。而且算得出來根本擺不下：某一段宣告 1,728 個取樣，
       照 15/28 需要 915 個位元組，那一段只有 668 個。
   所以 PT 容器的編碼 3 是**另一種東西，本站沒有解開**，--blocks 對它直接說
   自己沒解開，不套一套印出看起來像真的數字。

資料半位元組的分佈也對得上 4-bit 差分編碼：對稱、峰在 0/1/2/E/F、
谷在 7/8、位元組熵 6.5 bits（隨機資料會是 8）。

段落長度的迴歸：**位元組 = 1.0697 × 取樣數 + 每段固定開銷**，
而每聲道 15 bytes / 28 取樣 × 2 聲道 = 1.0714。差 0.16%。

─────────────────────────────────────────────────────────
 三、取樣率 48,000 Hz（推論，證據夠強但不是直接量到）
─────────────────────────────────────────────────────────
大部分檔沒有標 0x84。舊資料裡有 681 個來源 WAV（當年錄語音的素材），
其中 **680 個是 48,000 Hz**（剩下那一個是 24 kHz 的 MP3，不是 PCM）。
這批裡有一部分的**取樣數跟語音檔精確相同**，
名字也對得上（`Tien.wav` ↔ 田家安的 4518）。

**做過隨機對照**：把語音檔的取樣數整體平移一個隨機量、跑 200 次，
最多只吻合 60 個。實際 188 個高於 200 次對照的最大值 —— 配對是真的。

取樣數完全相同 = 沒有重新取樣 → 語音檔也是 48,000 Hz。
⚠️ 這一步是**推論**：直接的證據是「長度一樣」，不是「內容一樣」。

⚠️ 這個結論只涵蓋**那一批社群檔**。EA 原版（編碼 2）沒有標 0x84，本站測不出來。

⚠️ **這一格本站還沒定案（2026-09-05 重跑時抓到的矛盾）**：拿 680 個 48 kHz 來源
   WAV 的每聲道取樣數去配語音檔，161 個 WAV 配到 195 個語音檔，而那 195 個裡
   有 **96 個是編碼 3、而且自己標著 22,050 Hz**，只有 10 個沒有標。
   「語音檔也是 48,000 Hz」跟「檔案自己標的取樣率」最多只能對一個。
   本站沒有量出哪一個對（試過拿解出來的取樣跟來源 WAV 比包絡：真配對 6 個
   平均 0.27、隨機對照平均 0.14 但最大值 0.54 —— 那個指標分不開兩者），
   所以兩邊都照原樣印給你看，不替你選一邊。
   另外，「大部分檔沒有標 0x84」這句話在編碼 3 上其實反過來：本站這台機器上
   編碼 3 的 8,767 個裡 8,230 個有標，沒標的 537 個裡有 534 個是 **PT 容器**
   —— 也就是第二節那個 ⚠️ 說「本站沒解開」的那一批。所以這支腳本現在只對
   GSTR 容器的編碼 3 印那句「若是 48000 Hz 則為 X 秒」。

─────────────────────────────────────────────────────────
 四、這一格後來解開了（2026-08-29 訂正）
────────────────────────────────────
**15 個位元組怎麼變回 28 個取樣的還原公式 —— 已經解開。**

這一節原本寫「本站沒有解開的（就這一格）」：試過 1,000 種以上的參數組合
（位移基準、半位元組順序、係數表、濾波器變體、前置長度），
最好的相關係數只有 0.16。那段經過是真的，結論已經過期。

解開它的不是更聰明的組合，是**找到一份標準答案** —— 免費的 ffmpeg
解得開遊戲的選單音樂，於是「你錯了」終於有東西說得出口。
對照驗證 21,678,328 個取樣 0 個不同，編碼寫回去再讀出來 98.1 dB。

**這支腳本仍然只讀不寫、不產生 WAV**，那是分工不是做不到。
要匯出 WAV 或把自己的聲音寫回去，用「換掉遊戲的聲音」那一課的
mvp_audio.py（--export / --import）。

MIT License · Copyright (c) 2026 toni · 無外部相依，Python 3.7 以上
"""

import argparse
import os
import struct
import sys

# 編碼 3 的一組 = 1 個表頭位元組 + 14 個資料位元組(= 28 個半位元組),
# 還原出來是 28 個取樣。這兩個數字撐起後面的相位掃描與長度換算,
# 改動它們等於改掉本站對這個格式的整套理解。
BLOCK = 15          # 一組 15 個位元組
PER_BLOCK = 28      # 還原成 28 個取樣


class DataError(Exception):
    """看不懂這個檔就丟這個。

    單獨看一個檔時,main() 會把它印成一句人話(不丟一整片 traceback)。
    --list 掃整包時反過來:讀不懂的那一項跳過就好,不要讓整份清單停下來。
    """
    pass


# ─────────────────────────────────────────────────────────
#  BIGF 封裝檔（只列目錄，不寫回）
# ─────────────────────────────────────────────────────────

def big_entries(raw):
    """列出 BIGF 封裝檔的目錄,回傳 [(名稱, 位移, 大小)]。不是 BIGF 就回 None。

    檔頭固定 16 個位元組:BIGF(4) + 檔案總大小(4) + 項目數(4) + 目錄大小(4),
    ⚠️ **不是每一欄都同一個方向**,別照抄「數字全是大端序」那句話(舊版寫錯了):
      · 項目數(raw[8:12])是**大端序** —— 這支只用這一欄,本站兩份安裝的 24 個
        BIGF 檔照大端讀都走得完整份目錄。它跟裡面語音區塊的長度(小端序)方向相反,
        這一格搞反不會當掉,只會安靜地讀出一堆天文數字。
      · 檔案總大小(raw[4:8])多數是**小端序**:24 個裡 22 個照小端讀才等於
        真正的檔案大小,只有 2 個是大端。
      · 目錄大小(raw[12:16])本站沒有定案 —— 拿它跟「目錄實際結束的位置」比,
        大端只對上 3 個、小端 0 個,所以這裡不替它下結論。
    """
    if raw[:4] != b'BIGF':
        return None
    count = struct.unpack('>I', raw[8:12])[0]
    # 目錄從第 16 個位元組開始,一項是「位移(4) + 大小(4) + 名稱」。
    # 名稱沒有長度欄,是用一個 0x00 收尾,所以要往前找那個 0 才知道下一項在哪。
    out, p = [], 16
    for _ in range(count):
        # 目錄被截斷時就停在這裡。項目數是檔案自己宣告的,不可以無條件相信。
        if p + 8 > len(raw):
            break
        off, size = struct.unpack('>II', raw[p:p + 8])
        p += 8
        # 名稱是 0x00 收尾。找不到那個 0 就代表目錄在這裡被截斷了 —— 用 find 不用
        # index:index 會丟 ValueError,而這裡在呼叫端的 try 之外,整份清單會當場停掉
        # (檔頭那句「跳過讀不懂的那一項」就變成假的)。
        e = raw.find(b'\x00', p)
        if e < 0:
            break
        # 名稱按 latin-1 解:這一層要的是「位元組原樣對上字元」,不是正確的文字,
        # 用它才不會有任何位元組解不開而中途炸掉。
        out.append((raw[p:e].decode('latin-1'), off, size))
        p = e + 1
    return out


# ─────────────────────────────────────────────────────────
#  SCHl 容器
# ─────────────────────────────────────────────────────────

# 這三個標籤只有標籤本身,後面沒有長度也沒有值。
# 把它們當成「標籤 + 長度 + 值」去讀,會吃掉後面的位元組,整串標籤從這裡開始錯位。
NOVALUE = (0xFC, 0xFD, 0xFE)
# 0x80 這個標籤標的是編碼方式。三個值本站都遇得到,括號裡寫的是各自的解開進度。
CODEC = {1: '音樂那種，每塊自帶起始狀態 —— 已解開，見 make-voice',
         2: 'EA 原版用的 —— 已解開，見 make-voice 那一課',
         3: '社群做的用的 —— GSTR 容器的那種已解開，見 make-voice 那一課'}


def walk_blocks(b):
    """沿著區塊鏈走一遍,回傳 [(位移, 標記, 長度)] 與「走到第幾個位元組」。

    一個區塊 = 4 個位元組的標記(SCHl / SCCl / SCDl / SCEl)+ 4 個位元組的長度,
    長度是**小端序**,而且**含這 8 個位元組自己**,所以下一塊的位移就是 i + n。
    """
    out, i = [], 0
    while i + 8 <= len(b):
        tag = b[i:i + 4]
        # 標記不是 SC 開頭就代表區塊鏈到此為止。這裡用 break 而不是丟錯,
        # 因為呼叫端要靠回傳的位置去算「後面還剩多少不屬於區塊鏈的位元組」。
        if tag[:2] != b'SC':
            break
        n = struct.unpack('<I', b[i + 4:i + 8])[0]
        # 兩種壞法一起擋:長度小於 8 會讓 i 停在原地變成無窮迴圈,
        # 超過檔案尾則是壞檔或位元組序讀反了。硬走下去會讀到別人的資料。
        if n < 8 or i + n > len(b):
            raise DataError('第 %d 個位元組的區塊長度 %d 不合理' % (i, n))
        out.append((i, tag.decode('latin-1'), n))
        i += n
        # SCEl 是結束標記。它後面**可能**是封裝檔的補齊,也可能是下一段語音:
        # 原版 cd/spch_pbp/pbpdat.big 就是 15,391 段 SCHl 直接接在一起(本站走過
        # 每一段,15,391 段都以 SCEl 收尾)。這支走到這裡就收手,只讀第一段 ——
        # 所以呼叫端要拿回傳的位置去看「後面還剩什麼」,不要預設那是補齊。
        if tag == b'SCEl':
            break
    return out, i


def parse_tags(b, start, end):
    """把檔頭裡那串標籤讀成 {標籤: 值},並回傳讀到第幾個位元組。

    一筆是「標籤(1) + 長度(1) + 值(長度個位元組)」,值是**大端序**
    (跟區塊長度的小端序相反)。0xFF 是整串的結束記號。
    end 是檔頭自己宣告的長度:讀到那裡就停,不要越界讀進聲音資料。
    回傳的位置是硬驗證用的,呼叫端會拿它跟宣告長度比對。
    """
    out, i = {}, start
    while i < end:
        t = b[i]
        if t == 0xFF:
            i += 1
            break
        # 0xFC/0xFD/0xFE 沒有長度也沒有值,只往前走一格。
        # 用 setdefault 是為了同一個標籤出現兩次時不覆蓋先讀到的那筆。
        if t in NOVALUE:
            out.setdefault(t, None)
            i += 1
            continue
        # 長度欄或值被宣告的長度切掉 = 這個檔頭沒讀完就到底了。
        # 這裡安靜停手,呼叫端會發現 tag_end 對不上 hdr_len,在畫面上打 ❌。
        if i + 1 >= end:
            break
        n = b[i + 1]
        if i + 2 + n > end:
            break
        out[t] = int.from_bytes(b[i + 2:i + 2 + n], 'big')
        i += 2 + n
    return out, i


def parse_voice(b):
    """回傳一個 dict 描述這個語音檔。看不懂就丟 DataError。

    走法:先確認開頭是 SCHl,沿區塊鏈走一遍,再回頭讀第一塊(檔頭)裡的標籤。
    ⚠️ 標籤從第幾個位元組開始要看子格式:第 8 到 11 個位元組是子格式標記,
       PT 開頭的從第 12 個開始,其餘從第 16 個開始。這一格算錯,整串標籤全歪。
    """
    if b[:4] != b'SCHl':
        raise DataError('開頭不是 SCHl，這不是語音檔')
    blocks, consumed = walk_blocks(b)
    # 第一塊一定是檔頭,它宣告的長度就是標籤那串可以讀到哪裡為止。
    # 開頭是 SCHl 卻一個區塊都走不出來 = 檔案短到連 8 個位元組的區塊頭都放不下。
    # 不擋的話下一行 blocks[0] 會丟 IndexError,使用者拿到的是一整片 traceback。
    if not blocks:
        raise DataError('只有 %d 個位元組，連一個完整的區塊都放不下' % len(b))
    hdr_len = blocks[0][2]
    sub = b[8:12]
    tags, tag_end = parse_tags(b, 12 if sub[:2] == b'PT' else 16, hdr_len)

    # 聲音資料可以拆成很多個 SCDl,一段接一段。
    # 每個 SCDl 的 pos+8 到 pos+12 是這一段的取樣數,pos+12 之後才是內容。
    # ⚠️ **那個取樣數的位元組序跟容器綁在一起**,不是固定的(這一格本站 2026-09-05
    #    才補上,在那之前一律當大端讀,所以每一個 PT 容器的檔都讀出天文數字):
    #      PT   容器 → 小端序
    #      GSTR 容器 → 大端序
    #    驗證法很硬:把一個檔每一段的取樣數加起來,應該等於檔頭 0x85 標的總數。
    #    本站在兩份安裝上量了 23,486 個項目 —— 照容器選位元組序時全部相符,
    #    照舊的「一律大端」則 PT 那 8,288 個沒有一個對得上。
    #    (這條規則跟 make-voice 那一課 2026-08-30 量到的是同一條。)
    # 這裡只收「取樣數 + 原始位元組」,怎麼切成聲道交給 split_channels,
    # 因為那件事只在 GSTR 容器的編碼 3 上驗過,不該在這一層先套上去。
    endian = '>' if sub[:4] == b'GSTR' else '<'
    chunks = []
    for pos, tag, n in blocks:
        if tag == 'SCDl':
            chunks.append((struct.unpack(endian + 'I', b[pos + 8:pos + 12])[0],
                           b[pos + 12:pos + n]))

    return {'sub': sub.decode('latin-1').rstrip('\x00'),
            # 容器種類要一路帶到輸出:它決定位元組序,也決定下面那套
            # 「15 個位元組一組」的擺法適不適用(只有 GSTR 適用)。
            'gstr': sub[:4] == b'GSTR', 'endian': endian,
            'hdr_len': hdr_len, 'tag_end': tag_end, 'tags': tags,
            'blocks': [(t, n) for _, t, n in blocks], 'chunks': chunks,
            'consumed': consumed, 'total': len(b),
            'codec': tags.get(0x80), 'channels': tags.get(0x82, 1),
            'samples': tags.get(0x85), 'rate': tags.get(0x84)}


def split_channels(data, channels):
    """用聲道起點表把一段切成每個聲道。回傳 [(起點, 位元組)]。

    傳進來的 data 是 SCDl 扣掉開頭那 4 個位元組(取樣數)之後的部分。
    它的開頭是每個聲道各 4 個位元組的起點(大端序),第一個永遠是 0,
    而且起點是從「起點表之後」算起,所以真正的位置要再加上 4 × 聲道數。
    ⚠️ 「大端序」這一格只在 **GSTR 容器**上驗過,而本站兩份安裝裡的多聲道項目
       (321 個)剛好全部都是 GSTR 的編碼 3,所以另一種容器的多聲道長什麼樣子
       本站沒有樣本可以說。呼叫端(show_blocks)也只讓 GSTR 的編碼 3 走到這裡。
    **兩個聲道各自連續一整段,不是交錯的**。
    按交錯解等於把兩個人的話剪碎再交叉黏起來,那是本站走過最長的一段冤枉路。
    """
    if channels < 1:
        raise DataError('聲道數 %s 不合理' % channels)
    offs = [struct.unpack('>I', data[4 * i:4 * i + 4])[0] for i in range(channels)]
    base = 4 * channels
    out = []
    for c in range(channels):
        # 下一個聲道的起點就是這個聲道的結尾;最後一個聲道沒有下一個,吃到資料尾。
        s = base + offs[c]
        e = base + offs[c + 1] if c + 1 < channels else len(data)
        out.append((s, data[s:e]))
    return out


def find_phase(body):
    """掃相位：切在對的位置時，表頭高半位元組應該幾乎都 ≤ 3。

    為什麼要掃:同一個檔裡不是每一段都從第 0 個位元組開始
    (本站量到同一個檔第 1 段前面有 3 個位元組前置、第 2 段沒有),
    所以每一段都要重新找 15 個位元組那一組的起點,不能沿用上一段的。
    判準:表頭的高半位元組是 0 到 3(四組係數之一)。切對的位置本站量到 97.7%,
    切錯只有大約 50%(= 亂猜的水準)。差距這麼大,就不會是碰巧對上的。
    ⚠️ 那個 97.7% 只在 **GSTR 容器**的編碼 3 上成立(本站量到中位數 1.000);
       PT 容器的編碼 3 中位數 0.478,就是亂猜的水準,所以 show_blocks 根本
       不讓它走到這裡(見腳本開頭第二節那個 ⚠️)。
    ⚠️ 回傳的分數是 **-1.0** 時代表「這個聲道連一組都放不下,量不出來」,
       不是 -100%。呼叫端要先判 sc < 0,直接乘 100 去印會出現負的百分比。
    """
    best, score = 0, -1.0
    # 15 個位元組一組,所以起點只有 0 到 14 這 15 種可能,全部試一遍就是窮舉。
    for ph in range(BLOCK):
        # 終點是 len(body) - BLOCK + 1:最後一個**完整**的一組起點就是 len - 15,
        # 而 range 的終點不含,所以要 +1。少了那個 +1 會漏掉最後一組 ——
        # 本站量到 68,525 個編碼 3 聲道裡,有 8,497 個的百分比因此算錯、
        # 545 個連相位都選錯,而且 show_blocks 印的「N 組」數的是含最後一組的,
        # 兩個數字本來就對不起來。
        idx = range(ph, len(body) - BLOCK + 1, BLOCK)
        n = 0
        ok = 0
        for i in idx:
            n += 1
            if (body[i] >> 4) <= 3:
                ok += 1
        if n and ok / float(n) > score:
            best, score = ph, ok / float(n)
    return best, score


# ─────────────────────────────────────────────────────────
#  輸出
# ─────────────────────────────────────────────────────────

def describe(b, name):
    """把一個語音檔的檔頭印成人看得懂的樣子,順便把解析結果回傳給 --blocks 用。"""
    v = parse_voice(b)
    # 硬驗證:標籤一路讀下來停的位置,要等於檔頭自己宣告的長度(留 1 個位元組容差)。
    # 差得更多就打 ❌,代表這個檔的標籤沒有照本站理解的方式排。
    # ⚠️ ❌ 不等於壞檔:本站在自己這台機器的安裝上,把 data/audio 底下每一個語音都量
    #    過一次,編碼 1 與 2 的 7,724 個全部吻合,編碼 3(社群做的)的 8,767 個裡
    #    有 2,586 個對不上。上面第一節那個「原版 6,995 個零例外」講的是原版,不含這批。
    fit = '✅' if v['tag_end'] in (v['hdr_len'], v['hdr_len'] - 1) else '❌'
    print('  %s' % name)
    print('    子格式      %s' % v['sub'])
    print('    檔頭        宣告 %d · 標籤解析到 %d  %s' % (v['hdr_len'], v['tag_end'], fit))
    print('    編碼方式    %s → %s' % (v['codec'], CODEC.get(v['codec'], '本站沒見過這個值')))
    # 編碼 3 有兩種容器,只有 GSTR 那種解開了。上面那句話對 PT 容器的檔會誤導,
    # 所以這裡補一行說清楚 —— 「子格式」那一行印的就是它是哪一種。
    if v['codec'] == 3 and not v['gstr']:
        print('                ⚠️ 但你這個是 %s 容器，本站沒解開這一種'
              % (v['sub'] or '（沒有標記）'))
    print('    聲道        %d' % v['channels'])
    print('    取樣數      %s' % (v['samples'] if v['samples'] else '（沒有標）'))
    if v['rate']:
        print('    取樣率      %d Hz（檔案自己標的）' % v['rate'])
        if v['samples']:
            print('    時長        %.2f 秒' % (v['samples'] / float(v['rate'])))
    else:
        print('    取樣率      （沒有標）')
        # 48000 這個推論的來源是「社群做的那批(編碼 3)裡有一部分的取樣數跟
        # 48 kHz 來源 WAV 精確相同」,而那一批是 **GSTR 容器**的。
        # ⚠️ 2026-09-05 加的兩道限制:
        #    (1) 只對 GSTR 的編碼 3 印 —— 沒標 0x84 的編碼 3 檔本站量到 537 個,
        #        其中 534 個是 PT 容器,而 PT 容器的編碼 3 本站根本沒解開,
        #        對它套 48 kHz 等於把一個沒驗過的假設套到別的東西上。
        #    (2) 就算是 GSTR,這個推論本身也還沒定案(見開頭第三節那個 ⚠️:
        #        配對到的檔多數自己標著 22,050 Hz),所以句子裡要寫明白。
        if v['samples'] and v['codec'] == 3 and v['gstr']:
            print('                若是 48000 Hz 則為 %.2f 秒'
                  '（推論，尚未定案 —— 見腳本開頭第三節那個 ⚠️）'
                  % (v['samples'] / 48000.0))
        elif v['samples'] and v['codec'] == 3:
            print('                本站沒解開 %s 容器的編碼 3，所以不換算秒數'
                  % (v['sub'] or '（沒有標記）'))
        elif v['samples']:
            print('                本站測不出編碼 %s 的取樣率，所以不換算秒數' % v['codec'])
    # 區塊多的時候不要整串印出來(本站在自己的安裝上遇過一個檔 54 塊),只給頭尾與總數,
    # 但「其中幾塊是聲音資料」要留著:那個數字決定 --blocks 會印出幾段。
    bl = v['blocks']
    if len(bl) <= 8:
        print('    區塊        %s' % ', '.join('%s(%d)' % x for x in bl))
    else:
        nd = sum(1 for t, _ in bl if t == 'SCDl')
        print('    區塊        %s, …, %s（共 %d 塊，其中 %d 塊是聲音資料）'
              % (', '.join('%s(%d)' % x for x in bl[:3]),
                 '%s(%d)' % bl[-1], len(bl), nd))
    # 各段開頭那 4 個位元組 = 取樣數。位元組序照容器選(見 parse_voice 那一段)之後,
    # 這個加總本站在兩份安裝的 23,486 個項目上都等於檔頭 0x85 標的總數 ——
    # 所以現在每一種編碼都比得了,不再只比編碼 3。
    # (舊版一律用大端讀,PT 容器的那 8,288 個會加出天文數字,所以當時只好不比。)
    tot = sum(c for c, _ in v['chunks'])
    if v['samples']:
        print('    各段取樣加總 %d %s 標籤說的 %d'
              % (tot, '=' if tot == v['samples'] else '≠', v['samples']))
    if v['consumed'] != v['total']:
        # ⚠️ 這段尾巴**不一定是補齊**,所以先數一下再下結論:
        #    剛安裝好的原版 stdnmdat.big 的 94 項全部有尾巴,其中 85 項的尾巴裡
        #    還接著完整的 SCHl 語音串(那 94 項的位移互不重疊,所以確實屬於同一項);
        #    cd/spch_pbp/pbpdat.big 更極端 —— 15,391 段語音接在一起,這支只讀第一段,
        #    剩下的 212,216,048 個位元組全落在這個「尾巴」裡。
        tail = b[v['consumed']:v['total']]
        more = tail.count(b'SCHl')
        if more:
            print('    區塊鏈之後還有 %d 個位元組，裡面還有 %d 個 SCHl 開頭'
                  '（那是後面還沒讀的語音，不是補齊；這支只讀第一段）'
                  % (len(tail), more))
        else:
            print('    區塊鏈之後還有 %d 個位元組（找不到別的 SCHl，'
                  '看起來是封裝檔的補齊）' % len(tail))
    return v


def show_blocks(v):
    """--blocks:把每一段切成聲道、再切成 15 個位元組一組,把量到的數字攤開。"""
    print()
    print('  ── 聲音資料怎麼擺 ──')
    # 只有 **GSTR 容器的編碼 3** 這一套擺法本站驗過(社群語音包 1,945 段零例外;
    # 2026-09-05 用這台機器全部 321 個雙聲道檔的 2,382 段重跑,也全部吻合)。
    # 別的硬套同一套切法,印出來的數字會看起來很像真的,但沒有東西支持它。
    if v['codec'] != 3:
        print('  這個檔是編碼 %s，本站只解開了 GSTR 容器的編碼 3 的擺法。' % v['codec'])
        return
    # 編碼 3 有兩種容器,只有 GSTR 那種本站解開了。PT 容器的編碼 3(本站這台機器
    # 564 個)掃相位中位數 0.478 = 亂猜的水準,100% 的檔都會印「⚠️ 切法可能不對」,
    # 而且照 15/28 算出來的位元組數比實際有的還多(1,728 取樣要 915 bytes,只有 668)。
    # 硬印出來的數字看起來很像真的,但沒有東西支持它 —— 跟上面擋掉別的編碼同一個理由。
    if not v['gstr']:
        print('  這個檔是編碼 3，但裝在 %s 容器裡（不是 GSTR）。' % (v['sub'] or '（沒有標記）'))
        print('  本站解開的擺法只涵蓋 GSTR 那一種，所以這裡不套上去。')
        print('  （量到的分界：本站這台機器 GSTR 8,203 個、掃相位中位數 1.000；')
        print('    PT 564 個、中位數 0.478 —— 那就是亂猜的水準。）')
        return
    for n, (cnt, d) in enumerate(v['chunks'], 1):
        try:
            chans = split_channels(d, v['channels'])
        except Exception as e:
            print('  第 %d 段：切不開（%s）' % (n, e))
            continue
        # 這是這一格的硬驗證:扣掉起點表之後,每個聲道應該一樣長
        # (兩聲道時就是「右聲道起點 = 剩下資料的一半」)。
        # 對不上代表切法或聲道數讀錯了,所以印 ⚠️ 而不是安靜地繼續。
        half = (len(d) - 4 * v['channels']) // v['channels']
        mark = '✅' if all(len(x[1]) == half for x in chans) else '⚠️'
        print('  第 %d 段  宣告 %d 取樣 · %d bytes · 每聲道 %d bytes  %s'
              % (n, cnt, len(d), half, mark))
        for c, (start, body) in enumerate(chans):
            ph, sc = find_phase(body)
            nb = max(0, (len(body) - ph) // BLOCK)
            print('     聲道 %d  起點 %-6d 長度 %-6d 前置 %d bytes · %d 組 × 15 bytes'
                  % (c, start, len(body), ph, nb))
            # find_phase 用 -1.0 當「一組都放不下」的記號,直接乘 100 會印 -100.0%,
            # 看起來像程式壞掉。真實資料碰不到(本站量到最短的聲道是 16 bytes),
            # 但壞檔或別人的模組包會。
            if sc < 0:
                print('             表頭高半位元組 ≤3   這個聲道只有 %d bytes，'
                      '不到一組（15 bytes），量不出來' % len(body))
            else:
                print('             表頭高半位元組 ≤3 占 %.1f%%   %s'
                      % (sc * 100, '切法正確' if sc > 0.9 else
                         ('大致正確' if sc > 0.7 else '⚠️ 切法可能不對')))
            # 把「照 15 → 28 換算出來的取樣數」跟「檔案自己宣告的」並排印,
            # 兩個數字對不上就代表前置位元組或切法還有東西沒算進去。
            print('             可還原 %d 取樣（宣告 %d）' % (nb * PER_BLOCK, cnt))
    print()
    print('  ⚠️ 到這裡為止都量得出來。15 bytes 還原成 28 個取樣的公式已於 2026-08-29 解開，\n        在「換掉遊戲的聲音」那一課；這支只讀不寫，不產生 WAV。')


def cmd_list(root):
    """--list:掃資料夾底下的 .big 封裝檔,列出每一個裡面有幾段語音、用哪種編碼。"""
    # 語音住在 data/audio 底下。給錯一層不強迫你重打:找不到那一層就直接掃你給的
    # 那一層,所以散裝資料夾、或已經拆出來的一堆檔,同樣列得出來。
    base = os.path.join(root, 'data', 'audio')
    if not os.path.isdir(base):
        base = root
    found = 0
    for r, _, fs in os.walk(base):
        for f in sorted(fs):
            if not f.lower().endswith('.big'):
                continue
            p = os.path.join(r, f)
            # 一次把整個封裝檔讀進記憶體:後面每一項就能拿目錄裡的位移直接切,
            # 不必為了成千上萬項反覆 seek(本站量到一個封裝檔裡有 12,527 段語音)。
            # 開檔是 'rb',全程唯讀。
            with open(p, 'rb') as fh:
                raw = fh.read()
            items = big_entries(raw)
            if not items:
                continue
            codecs = {}
            n = 0
            for _, o, s in items:
                # 封裝檔裡不是每一項都是語音,所以逐項看開頭那 4 個位元組是不是 SCHl。
                if raw[o:o + 4] != b'SCHl':
                    continue
                n += 1
                try:
                    v = parse_voice(raw[o:o + s])
                except DataError:
                    # 個別項目讀不懂不要讓整份清單停下來。這裡是概觀,
                    # 想知道某一個檔為什麼讀不懂,單獨拿那個檔跑一次會印出原因。
                    continue
                codecs[v['codec']] = codecs.get(v['codec'], 0) + 1
            if not n:
                continue
            found += 1
            print('  %-40s %5d 個語音 · 編碼 %s'
                  % (os.path.relpath(p, root), n,
                     ', '.join('%s×%d' % (k, x) for k, x in sorted(codecs.items()))))
    if not found:
        print('  在這個資料夾底下沒有找到語音封裝檔。')
        print('  請確認你指的是**遊戲安裝資料夾**（它的下一層才是 data）。')


def main():
    """命令列入口:決定要跑 --list 還是看單一檔案,並把讀不懂的狀況印成一句人話。"""
    # Windows 上把輸出導到檔案或接管線(> out.txt、| more、PowerShell 的 |)時,
    # Python 會用系統語系(繁體中文是 cp950)寫 stdout,而 ✅ ❌ ⚠️ ─ 這些字元
    # cp950 沒有 —— 不處理的話會在印到第三行時丟 UnicodeEncodeError、以 1 結束,
    # 只留下半截檔案(本站用 PYTHONIOENCODING=cp950 重現過:31 bytes 就斷了)。
    # 這裡不換編碼,只把「編不出來的那個字」換成問號,中文照舊。
    # 直接看主控台的人不受影響(Python 3.6+ 在 Windows 主控台走 UTF-16 API)。
    try:
        sys.stdout.reconfigure(errors='replace')
    except (AttributeError, ValueError):
        pass
    ap = argparse.ArgumentParser(
        description='讀懂 MVP Baseball 2005 的語音檔（唯讀，不產生音訊）',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='\n這支腳本不會改你的遊戲，也不會產生任何檔案。\n')
    ap.add_argument('path', help='遊戲資料夾（配 --list）或單一 .dat')
    ap.add_argument('--list', action='store_true',
                    help='列出 BIGF 封裝檔裡的語音（cd/ 底下那 8 個本身就是一長串 '
                         'SCHl 的 .big 不在內，例如 pbpdat.big，那種要直接指檔案）')
    ap.add_argument('--blocks', action='store_true', help='顯示聲音資料的內部切法')
    args = ap.parse_args()

    try:
        if args.list:
            cmd_list(args.path)
            return 0
        with open(args.path, 'rb') as f:
            b = f.read()
        v = describe(b, os.path.basename(args.path))
        if args.blocks:
            show_blocks(v)
        return 0
    # 兩種預期得到的失敗各印一句人話就好:一整片 traceback 對「只是想看看自己
    # 遊戲檔」的人沒有任何用處。回傳 2 代表沒讀成功,別的錯誤仍然照常拋出來。
    except DataError as e:
        print('\n  停下來了：%s\n' % e)
        return 2
    except FileNotFoundError:
        print('\n  找不到檔案：%s\n' % args.path)
        return 2
    # 路徑給了資料夾卻忘記加 --list 是很自然的失誤(頁面步驟 2 給資料夾、
    # 步驟 3 給檔案)。不擋的話讀者拿到的是 IsADirectoryError 一整片 traceback。
    except IsADirectoryError:
        print('\n  這是一個資料夾，不是單一語音檔。要列出整包語音請加 --list：')
        print('      python3 mvp_read_voice.py "%s" --list\n' % args.path)
        return 2


if __name__ == '__main__':
    sys.exit(main())


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
