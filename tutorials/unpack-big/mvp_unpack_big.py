#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
mvp_unpack_big.py — 把封裝檔解成資料夾(實驗性)

⚠️ **這支是給實驗用的,不是給一般玩家的。**先讀下面「這是在驗什麼」。

這是在驗什麼
-----------
官方中文版有一件很特別的事:它**沒有** data/datafile/datafile.big
與 data/anims/anims.big 這兩個封裝檔,而是把它們的內容
**整個拆成散裝檔**放在同名資料夾裡(466 個 .txt 與 730 個 .ord/.orl/.txt)。
而那是 EA 出貨的零售版,遊戲照跑。

兩份執行檔(英文版與中文版)裡也都同時找得到:
  datafile/datafile.big   anims/anims.big     ← 封裝檔的路徑
  %s/%s.ord  %s/%s.orl  %s/%s.txt             ← 「資料夾 + 單檔」的路徑樣板
而中文版散裝的 anims/ 裡剛好就是 243 個 .ord + 243 個 .orl + 244 個 .txt ——
三個樣板對上三種副檔名,一個不多一個不少。

**推論**(還沒證實):引擎在找不到封裝檔時,會去讀同名資料夾裡的散裝檔。
如果成立,模組的做法可以整個簡化:不必再對封裝檔動手術
(接檔尾、改目錄、算校驗、避開孤兒資料),直接改散裝檔就好。

**怎麼確認**:用這支腳本把某個封裝檔解成資料夾,然後開遊戲。
進得去、東西正常 = 這條路通。不行就用 --restore 還原。

解出來的是**解壓縮後的內容**,因為官方中文版的散裝檔就是那樣
(本站拿 460 個同名檔比對過,341 個與封裝內容解壓後位元組完全相同)。

你給它什麼、它產出什麼
--------------------
輸入:一個 .big 封裝檔的完整路徑(例如 <遊戲資料夾>/data/datafile/datafile.big)。
      名單、設定檔都不需要,它只讀你指定的那一個檔。

輸出(只有加了 --apply 才會發生,而且全部落在封裝檔自己所在的那個資料夾):
  · 每一個目錄項目解壓後,寫成一個同名的散裝檔;
  · 封裝檔本身改名成「原名 + .unpackbak」,讓遊戲找不到它。
    這一步正是實驗的重點:遊戲找不到封裝檔的時候會不會改讀散裝檔;
  · 一份清單 .mvp_unpack_manifest.txt,記著寫出去的每個檔名、大小,與**內容的 sha256**。
    它在動手**之前**就先寫好(那一份的大小是 0、指紋是一個減號),
    整批解完再用實際的大小與指紋覆寫一次;中途被打斷或出錯,
    也會把「已經真的寫出去的那幾個」的指紋補進去 ——
    所以任何一種收場都留得下一份可以照著收拾的清單。
    --restore 靠它認出哪些散裝檔是自己寫的,
    --clean 再靠指紋確認那些檔現在**還是**自己寫的那一份。

安全網在哪
---------
· 預設只預覽。沒加 --apply 一個位元組都不寫,先讓你看清楚會發生什麼事。
· 目標資料夾裡只要有一個同名檔就整個停下來,不覆蓋任何既有的檔。
  那個名字是一條**符號連結**的話會點名說出來(那跟「你上次解過一次」是兩件事),
  一律不跟著連結寫到資料夾外面去。要寫的每一個目的檔都過這一關:
  散裝檔、清單、封裝檔要改成的備份名,還原時封裝檔要改回的正本名。
· 每一個散裝檔都是:先寫進一個暫存檔 → flush + fsync → **讀回來比對 sha256**
  → 再原子改名換上去。暫存檔的名字交給 mkstemp 決定(它內部用 O_EXCL,
  撞名就自己換一個),所以既不覆蓋任何東西,也不可能開到一個事先擺在那裡的符號連結。
  中途失敗一定把暫存檔清掉,那個檔名底下不會留下半截的東西。
· 上一次留下的清單 .mvp_unpack_manifest.txt 還在的話也停下來,不覆蓋它 ——
  蓋掉了就沒有東西認得出上一次解出來的是哪些檔。
  要寫的時候也是先寫進同一個資料夾裡的唯一暫存檔、fsync 之後才 os.replace 換上去,
  所以它不會留下寫到一半的版本,也不會跟著一個同名的符號連結跑到資料夾外面去寫。
· 「這個名字已經被佔住了嗎」一律用 os.path.lexists 問,不用 os.path.exists ——
  後者對「指到別處、而那邊還不存在」的符號連結會回答「沒有」,
  接著就會有人跟著那條連結寫到遊戲資料夾外面去。
· 封裝檔要改成的那個備份名 <原名>.unpackbak 已經被佔住就停手。
  直接改名過去會把上一次留下的那份原檔無聲蓋掉,而那可能是唯一的一份。
· 項目名稱含斜線、反斜線、冒號、控制字元,以點開頭、以點或空白結尾,
  或是 Windows 的保留裝置名(NUL、CON、PRN、AUX、COM1-9、LPT1-9)的一律拒絕,
  寫不到目標資料夾以外的地方去。
· 目錄裡有兩項同名就停手:解出來會互相蓋掉,而檔數與複驗都還是照兩項算。
  **名字只差在大小寫也算**:Windows 與 macOS 預設都不分大小寫,
  A.FSH 與 a.fsh 在那裡是同一個落點。
· 清單是**動手之前**先寫好的,整批做完再用實際大小與指紋覆寫一次;
  解到一半被 Ctrl-C 打斷或出錯,也會先把已經寫出去的那幾個的指紋補進清單再收尾。
  所以 --restore --clean 照樣收拾得掉 —— 不補的話那些檔在清單裡沒有指紋,
  而沒有指紋的檔 --clean 是不敢刪的。
· 封裝檔是**改名**,不是刪除。原檔完整躺在旁邊,--restore 一行就改回來。
  還原之前會先驗那個備份還是不是一個完整的封裝檔(開頭是 BIGF,而且檔頭 +0x04
  那個「檔案總大小」對得上實際檔案大小),對不上就停手,
  不把一個壞掉的檔擺回遊戲要讀的位置。停手也不會弄丟東西:備份還躺在原地。
· 解完立刻複驗每個檔「在不在、是不是一般檔案、大小對不對、內容的指紋對不對」。
  有一個不對就**自動**把封裝檔改回原名
  (那是遊戲會去讀的位置),然後用非 0 的結束碼停下來,並把清掉散裝檔的指令印給你。
· 按 Ctrl-C 中斷時會照實說到底做到哪一步:封裝檔還沒改名就說沒改名
  (清單與已經解出來的那幾個檔照樣講給你聽),已經改名就叫你跑 --restore,
  還原做到一半就說還原還沒做完,--clean 刪到一半就說已經刪掉幾個。
  結束碼一律 130。這幾句話是照**相位**分的,而「還沒開始動」以外的每一種相位
  都不准說「什麼都還沒有動到」(2026-09-11 訂正:在那之前,改名那一步與 --clean
  刪檔那一段都會掉回那句話,而清單、散裝檔都已經在資料夾裡了)。
  「換名」跟「登記換過了」被包成**不可中斷的一段**(收到 Ctrl-C 先記著、
  離開那一段再丟出來),所以收尾看到的登記跟磁碟上的狀態一定一致;
  真的落在縫裡(那個保險裝不上的時候)它會說「換好了沒有無法確定」,
  不會說「什麼都沒有動到」。
· 散裝檔預設留著不動。要一起清掉是另一個開關 --clean,
  而且只刪「清單裡有、**而且現在的 sha256 還跟清單記的一樣**」的那些。
  你自己改過的、指紋還沒補上去的、名字現在變成符號連結的,一律保留並逐一列給你看;
  只要還有東西留著,清單也留著不刪 —— 它是唯一認得出那些檔的東西。
  舊版(2026-09-06 之前)解出來的清單沒有指紋那一欄,那種清單**一個檔都不刪**。

做不到的事
---------
· 不會把散裝檔打包回封裝檔。這支只有「拆開」一個方向。
· 不會處理巢狀路徑。封裝檔裡的項目名稱一律當成單一檔名,看到路徑分隔符號就拒絕。
· 解出來的是**解壓後**的內容,不是封裝檔裡原本那串位元組,
  所以「解開再照樣塞回去」拿不回位元組相同的封裝檔。
· 驗不到「遊戲會不會真的去讀這些散裝檔」。那一步只能你自己開遊戲看,
  而那正是這支腳本存在的理由。

寫回封裝檔一律用「接到檔尾」的方式:新資料接在檔案最後面,
只改目錄裡那一項的 8 個位元組 + 檔頭的 4 個位元組。
原本的資料一個位元組都不動,所以出錯了也還原得回來。
(上面這一段是本站每一支會動封裝檔的腳本共用的紀律。**這一支不寫回封裝檔**:
 它只把內容讀出來、再把封裝檔改名。所以下面 append_entry()、read_entry()、
 qfs_compress_literal() 與那兩個 fsh_ 開頭的函式,
 在本支從頭到尾沒有被叫到,留著是為了跟其他課的腳本長得一樣,
 你要對照的時候比較好認。
 上面這五個是在本檔上用 Python 的語法樹從 main() 一路追呼叫追出來的:
 真的走得到的函式是 big_entries / cleanup_hint / cmd_plan / cmd_restore / main /
 manifest_text / plan_unpack / qfs_decompress / read_manifest / refuse_symlink /
 safe_name / sha256_file / size_field_order / taken / write_text_atomic 十五個,
 另外還有 DataError 與 _NoInterrupt 兩個類別(上面那個數字只數函式)。
 (2026-09-05 這個數字從八變成十一:cleanup_hint / taken / write_text_atomic
  是那一天新加的三個小工具 —— 分別是「中斷時照實說做到哪一步」、
  「問名字被佔住了沒、而且不跟著符號連結走」、「原子寫清單」。
  2026-09-06 再從十一變成十五:manifest_text / read_manifest 是清單多了指紋那一欄
  之後,把「怎麼寫」跟「怎麼讀回來」收成同一個地方;refuse_symlink 是
  「要寫的目的檔是符號連結就停手」;sha256_file 是算指紋的。)
 2026-09-05 訂正:size_field_order() 原本也在「走不到」那一份名單裡,說明也寫著
 「這一支跑起來從來不去讀檔頭 +0x04 那個檔案總大小欄位」。現在 --restore 會先叫它
 驗那個備份還是不是一個完整的封裝檔,所以它走得到了,+0x04 也會被讀 —— 只讀,不寫。)

自包含:整支腳本就是這一個檔,只用 Python 內建模組,不需要安裝任何套件。
⚠️ 2026-09-04 訂正:上面這句原本掛著「連讀寫 PNG 都是自己做的」,那在**這一支**上不成立,已經拿掉。
   這個檔從頭到尾沒有一行 PNG 的程式碼:拿 png 不分大小寫去搜 mvp_unpack_big.py,
   整個檔就只有這一段訂正會命中。它也不需要,因為這一支不讀也不寫圖,
   只把封裝檔目錄裡的每一項解出來寫成散裝檔。
   (前面提到的那兩個 fsh_ 開頭的函式碰的是 EA 自己的 SHPI/FSH 圖片格式,不是 PNG。)
   「自包含、不需要安裝套件」那半句是對的:在本檔上用 Python 語法樹掃到 10 個 import,
   argparse / hashlib / os / re / shutil / signal / struct / sys / tempfile / zlib,
   全是 Python 自己就附的模組。
   其中 re、shutil、zlib 被當成模組屬性使用的次數都是 0,跟上面那五個走不到的函式一樣,
   留著是為了跟其他課的腳本長得一樣;tempfile 是 2026-09-05 加的,
   清單那個檔就是靠它的 mkstemp() 拿到一個「同資料夾、名字不會撞、也不可能是既有符號連結」
   的暫存檔,寫完再原子換上去 —— 2026-09-06 起每一個散裝檔也是這樣寫的。
   hashlib 與 signal 是 2026-09-06 加的:前者算清單裡那一欄指紋,
   後者讓「換名 + 登記」變成一段不可中斷的動作。
   真正自己讀寫 PNG 的是「換球員大頭照」「做一張新的球員臉皮」「換掉開機畫面」
   「換球隊隊徽」這四課的腳本:在 site/tutorials 底下的 29 支腳本上量,
   只有那四個檔找得到 png_read 與 png_write。

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

import os
import re
import sys
import zlib
import signal
import struct
import shutil
import hashlib
import argparse
import tempfile

try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass


class DataError(Exception):
    """檔案內容跟預期不符。一律當成「停下來問人」,不要猜。"""


class _NoInterrupt(object):
    """把「os.replace + 登記」包起來,這段期間不讓 Ctrl-C 插隊。

    收到 SIGINT 先記著,離開這一段之後再照常丟出 KeyboardInterrupt。
    這樣收尾看到的登記一定跟磁碟上的狀態一致,不會出現「檔案已經換掉了、
    程式卻還以為沒換」的那一瞬間。

    ⚠️ signal.signal 只有主執行緒裝得上;裝不上就退回原本的行為 ——
       不會比以前更糟,而且外面那個「正在換」的狀態就是為這種情形留的:
       真的落在縫裡,收尾會誠實說「換好了沒有無法確定」,不會說「沒動到」。
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


def refuse_symlink(path, what):
    """要「寫」的那個名字是符號連結就停下來,不跟著它寫過去。

    ⚠️ 判斷用 os.path.islink,不用 os.path.exists:一條指到別處、
       而那邊還不存在的符號連結,exists() 回答「沒有」—— 名字明明被佔著,
       看起來卻是空的,接著就會有人沿著它在遊戲資料夾**外面**憑空生一個檔出來
       (指到既有的檔就是把那個檔整個寫掉)。islink() 看的是連結本身。

    路徑中間的**資料夾**是連結不管(有人把遊戲目錄放在別顆碟,那很正常),
    這裡只看最後那一個名字。讀取也不限制,只有要寫的目的檔才過這一關。
    """
    if os.path.islink(path):
        raise DataError('%s 是符號連結,本工具不跟著連結寫,請把它換成真正的檔案。\n'
                        '  (%s)目前沒有動到任何檔案。' % (path, what))


def sha256_file(path):
    """算一個檔案內容的 sha256。分塊讀,大檔也不會把記憶體吃光。"""
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        while True:
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


# 上限與固定名稱。前兩個是壞檔防護:封裝檔的檔頭是**檔案自己說的**,
# 一個壞掉或被亂改的檔可以宣稱「我解開有 4 GB」或「我有兩億個項目」,
# 照著它去配置記憶體就當場把機器吃光。所以先擋在合理範圍外面。
MAX_UNCOMPRESSED = 64 * 1024 * 1024    # 單一項目解壓後的上限(64 MB)
MAX_BIG_ENTRIES = 200000               # 目錄項目數上限
MAX_NAME = 255                         # 單一項目名稱的位元組上限(檔案系統的常見上限)
BACKUP_SUFFIX = '.unpackbak'           # 封裝檔改名後的後綴,--restore 認這個
MANIFEST = '.mvp_unpack_manifest.txt'  # 解出來的檔案清單,--clean 只敢刪這裡面有的

# Windows 的保留裝置名。這些名字在那邊指的是**裝置**不是檔案:寫給 NUL 的內容
# 直接消失,寫給 CON 會跑到主控台去,而且加副檔名也沒用(CON.txt 一樣是裝置)。
# 本站在這台機器上 1,879 個真的封裝檔、共 282,996 個項目名稱上跑過 safe_name,
# 被擋下來的是 0 個(不只保留裝置名這一條,整組規則加起來都是 0),
# 所以擋這些不會擋到真的遊戲資料。
WIN_RESERVED = frozenset(['CON', 'PRN', 'AUX', 'NUL'] +
                         ['COM%d' % i for i in range(1, 10)] +
                         ['LPT%d' % i for i in range(1, 10)])


# ─────────────────────────────────────────────────────────
#  QFS(EA 的壓縮格式,檔頭是 10 FB)
# ─────────────────────────────────────────────────────────
def qfs_decompress(data):
    """把 QFS 壓縮過的一段資料解開;不是 QFS 就原樣回傳。

    QFS(社群也叫它 RefPack)是 EA 自家的壓縮法,做的事跟 zip 同一類:
    一邊照抄新的位元組,一邊叫「往回 N 個位元組、把 L 個抄過來」。

    檔頭有兩種長度,靠第 1 個位元組的最低位元分辨:
      · bit0 = 1 → 檔頭 10 個位元組,解壓後大小放在 +6..+9,四個位元組**大端序**
      · bit0 = 0 → 檔頭 5 個位元組,解壓後大小放在 +2..+4,三個位元組**大端序**
    第 2 個位元組固定是 0xFB,那就是「這是 QFS」的招牌。
    大端序這件事讀者看不出來,而且跟同一個檔案裡其他欄位不一致,所以特別寫下來。
    """
    # 封裝檔裡的東西**不一定壓縮過**。所以先看招牌,沒有就當它本來就是原始資料。
    if len(data) < 2 or data[1] != 0xFB:
        return data
    # 兩種檔頭長度擇一,順便把「檔案自己宣稱的解壓後大小」讀出來,後面拿它當上限。
    if data[0] & 0x01:
        if len(data) < 10:
            raise DataError('QFS 檔頭不完整')
        size = int.from_bytes(data[6:10], 'big'); pos = 10
    else:
        if len(data) < 5:
            raise DataError('QFS 檔頭不完整')
        size = int.from_bytes(data[2:5], 'big'); pos = 5
    # 這個數字是壞檔可以隨手改的。照著它去配置記憶體會被吃光,所以先擋。
    if not 0 <= size <= MAX_UNCOMPRESSED:
        raise DataError('QFS 宣稱解壓尺寸異常:%d' % size)

    out = bytearray()
    end = len(data)

    def copy_back(offset, length):
        """往回 offset 個位元組,一個一個抄 length 個到輸出的尾巴。

        **必須一個一個抄,不可以整段切片。** 來源區間允許跟目的區間重疊
        (offset 比 length 小的時候就會),那時候後抄的位元組要看到前面剛抄好的結果,
        這正是 QFS 表達「同一小段重複很多次」的方式。整段切片會拿到舊內容。
        """
        # 這一行擋的是「往回的距離」:至少要往回 1 個位元組,而且不能往回到
        # 還沒解出來的地方。它管的不是輸出總長度,總長度由下面那道擋。
        if not 0 < offset <= len(out):
            raise DataError('QFS 反向參照越界 offset=%d' % offset)
        src = len(out) - offset
        for _ in range(length):
            out.append(out[src]); src += 1
        # ⚠️ 只檢查檔頭宣稱的大小是不夠的:那是「檔案自己說的」。
        #    一個惡意檔可以宣稱很小(通過上面那道),再用反向參照無限吐資料,
        #    把記憶體吃光。實際輸出也必須有上限,而且上限就是它自己宣稱的大小。
        if len(out) > size:
            raise DataError('QFS 解出來的資料超過檔頭宣稱的 %d 位元組' % size)

    # 主迴圈:每一輪先讀一個控制碼,由它的數值範圍決定「這是哪一種指令、
    # 後面還要再讀幾個位元組」。控制碼本身依序是 1、1、4、3、2 個位元組長,
    # 之後才是那 n 個要照抄的位元組。
    while pos < end:
        b0 = data[pos]
        # 0xFC-0xFF:結束。最低 2 個位元是「還剩幾個位元組照抄」(0 到 3)。
        if b0 >= 0xFC:
            n = b0 & 0x03; pos += 1
            out += data[pos:pos + n]; break
        # 0xE0-0xFB:純照抄一段,沒有往回參照。長度 = (低 5 位 << 2) + 4,
        # 也就是 4 到 112 個位元組,而且一定是 4 的倍數。
        # 上限是 112 不是 128:0xFC-0xFF 在上面那一支已經先被攔掉,能走到這裡的
        # b0 最大只到 0xFB,(0xFB & 0x1F) = 27,(27 << 2) + 4 = 112。
        # 把 0xE0 到 0xFB 這 28 個控制碼整族代進上面那條公式算過一遍,
        # 得到的就是 4、8、12 一直到 112,沒有一個超過 112。
        # 底下 qfs_compress_literal() 一次最多切 112 個位元組,講的是同一件事。
        if b0 >= 0xE0:
            n = ((b0 & 0x1F) << 2) + 4; pos += 1
            out += data[pos:pos + n]; pos += n; continue
        # 以下三種都是「先照抄 n 個,再往回抄 length 個」,
        # 差別在能表達多遠的 offset 與多長的 length,所以用掉的位元組數不同。
        # 0xC0-0xDF:4 個位元組,指得最遠也抄得最長。
        # 把下面那三行的位元運算算到底:offset 最多 131,072,length 最多 1,028。
        if b0 >= 0xC0:
            b1, b2, b3 = data[pos + 1], data[pos + 2], data[pos + 3]; pos += 4
            n = b0 & 0x03
            length = ((b0 & 0x0C) << 6) + b3 + 5
            offset = ((b0 & 0x10) << 12) + (b1 << 8) + b2 + 1
        # 0x80-0xBF:3 個位元組,中距離(offset 最多 16,384,length 最多 67)。
        # 要先照抄幾個藏在 b1 的最高 2 位,不在 b0 裡,這一點跟另外兩種不一樣。
        elif b0 >= 0x80:
            b1, b2 = data[pos + 1], data[pos + 2]; pos += 3
            n = (b1 >> 6) & 0x03
            length = (b0 & 0x3F) + 4
            offset = ((b1 & 0x3F) << 8) + b2 + 1
        # 0x00-0x7F:2 個位元組,短距離(offset 最多 1,024,length 最多 10)。
        # 短距離最常出現,所以給它最省的編碼。
        else:
            b1 = data[pos + 1]; pos += 2
            n = b0 & 0x03
            length = ((b0 & 0x1C) >> 2) + 3
            offset = ((b0 & 0x60) << 3) + b1 + 1
        # 順序不能反:先把控制碼後面那 n 個位元組照抄過去,再做往回參照。
        # 往回參照可能指到剛剛才抄進去的那幾個位元組。
        out += data[pos:pos + n]; pos += n
        copy_back(offset, length)
    # 切到檔頭宣稱的大小為止。最後一輪照抄有可能多帶幾個位元組進來。
    return bytes(out[:size])


def qfs_compress_literal(data):
    """純 literal 編碼:不做字串比對,瞬間完成,格式一樣合法。

    壓出來比 EA 原本的大(大約等於原始大小),但因為我們是接到檔尾,
    大一點沒有影響。換來的是速度快上千倍,而且不可能壓錯。
    """
    # 5 個位元組的短檔頭:0x10 0xFB 之後是三個位元組的原始大小,**大端序**。
    # 0x10 的最低位元是 0,所以解壓那邊會走「短檔頭」那一支。
    n = len(data)
    out = bytearray([0x10, 0xFB, (n >> 16) & 0xFF, (n >> 8) & 0xFF, n & 0xFF])
    # 0xE0 那一類指令一次只能照抄 4 的倍數,所以先把尾巴那幾個位元組切出來,
    # 留給結束指令(0xFC | 餘數)帶走。
    tail = n % 4
    body = n - tail
    pos = 0
    # 整段切成一塊最多 112 個位元組的照抄指令。
    # 為什麼是 112 不是 128:控制碼是 0xE0 | ((chunk-4)//4),
    # chunk 一到 128 就變成 0xE0|31 = 0xFF,那已經踩進「結束」那一段(0xFC-0xFF),
    # 解壓端會當場停下來。能用的最大值是 0xFB,也就是 27,對應 chunk = 112。
    while pos < body:
        chunk = min(112, body - pos)
        out.append(0xE0 | ((chunk - 4) // 4))
        out += data[pos:pos + chunk]
        pos += chunk
    # 結束指令 + 最後那 0 到 3 個位元組。少了它解壓端不知道到哪裡停。
    out.append(0xFC | tail)
    out += data[pos:]
    return bytes(out)


# ─────────────────────────────────────────────────────────
#  BIGF 封裝檔:讀目錄、接到檔尾
#
#  檔頭 16 個位元組:
#    +0x00  4  'BIGF' 這四個字,認不出來就不是封裝檔
#    +0x04  4  整個檔案的總大小。**位元組順序不固定**,見 size_field_order()
#              (這一支**不寫**這一欄,但會**讀**:--restore 之前要先確認那個備份
#               還是不是一個完整的封裝檔,靠的就是 size_field_order() 拿它跟
#               實際檔案大小對一次。檔頭 docstring 那邊 2026-09-05 已經訂正過,
#               這張表當時漏改,2026-09-06 補上)
#    +0x08  4  目錄有幾個項目,**大端序**
#    +0x0C  4  這支腳本沒有用到
#  +0x10 起是目錄,一項接一項,每一項:
#    4 個位元組  這一項的資料在檔案裡的位移,**大端序**
#    4 個位元組  這一項的資料有多長,**大端序**
#    N 個位元組  項目名稱,以一個 0x00 結尾,長度不固定
#  名稱長度不固定,所以「目錄一共多長」要邊讀邊算,沒辦法先乘出來。
# ─────────────────────────────────────────────────────────
def size_field_order(path):
    """檔頭 +0x04 的「檔案總大小」是 little 還是 big endian。

    ⚠️ 這一欄兩種順序都遇得到,不能寫死,也不能照檔名或檔案大小猜。
       「哪個檔是哪一種」不是這個格式天生的性質,是看你手上這一份被誰重新打包過。
       本站用 BIGF 檔頭(不是副檔名)認過三份剛安裝好的原版 data 資料夾:
       英文版 207 個封裝檔、繁體中文版 205 個、PK 版 205 個,三份全部是 little-endian,
       連原版裡 172,992,803 個位元組的 models.big 與 109,291,217 個位元組的
       portrait.big 都是。
       big-endian 只出現在本站測試機那份疊過模組的 data 資料夾(384 個封裝檔裡有 10 個),
       而且全部落在這 7 個檔名上:models.big、frontend/portrait.big、
       audio/spch_pbp/pnamehdr.big、audio/cd/spch_pbp/pnamedat.big,以及球場夜間檔
       coornite.big、dodgnite.big、wrignite.big(球場那三個在測試機上另有一份
       備份資料夾的副本,所以檔數是 10 個而不是 7 個)。
       這 7 個檔名在上面三份原版裡全都是 little-endian,所以 big-endian 是這個檔
       被別的工具重新打包過之後才有的,不是這幾個檔名或檔案大小的性質。
       讀出來是哪一種,寫回去就照哪一種。
    """
    # 判法很直接:實際檔案大小只有一個,拿兩種順序各解一次,哪一種對得上就是哪一種。
    # 這比「照檔名猜」可靠,而且不必維護一份例外清單。
    n = os.path.getsize(path)
    with open(path, 'rb') as f:
        raw = f.read(8)
    if len(raw) < 8:
        raise DataError('%s 太小,不像封裝檔' % os.path.basename(path))
    if struct.unpack('<I', raw[4:8])[0] == n:
        return '<'
    if struct.unpack('>I', raw[4:8])[0] == n:
        return '>'
    # 兩種都對不上代表這個檔已經被改壞(或根本不是封裝檔)。這時候硬寫回去會壞得更徹底。
    raise DataError('%s 的檔頭大小欄位跟實際檔案大小對不上 —— 這個檔可能已經損毀'
                    % os.path.basename(path))


def big_entries(path):
    """回傳 [(名稱, 目錄欄位位置, 資料 offset, 資料長度)]。

    目錄欄位位置留著,是為了之後只改那 8 個位元組,不必重寫整個目錄。

    位移與長度兩個欄位都是**大端序**,跟檔頭那個「總大小」不一樣
    (那一個兩種順序都遇得到)。同一個檔裡混用兩種順序,是這個格式最容易踩的地方。
    """
    items = []
    try:
        with open(path, 'rb') as f:
            head = f.read(16)
            if len(head) < 16 or head[:4] != b'BIGF':
                raise DataError('%s 的開頭不是 BIGF,這不是封裝檔' % os.path.basename(path))
            count = int.from_bytes(head[8:12], 'big')
            if not 0 < count < MAX_BIG_ENTRIES:
                raise DataError('%s 的目錄項目數異常(%d)' % (os.path.basename(path), count))
            # 項目名稱長度不固定,所以目錄總長度事先算不出來。
            # 這裡用「每項抓 80 個位元組再多給 8 KB」當寬鬆估計一次讀進來,
            # 免得為了幾個位元組跟磁碟來回幾千次。
            blob = head + f.read(count * 80 + 8192)
            # ⚠️ 估太少的時候要**再去拿**,不可以就停在讀到的地方。
            #    2026-09-05 訂正:舊版那兩個 break 的註解寫著「已讀到的就夠用」——
            #    那對「只是列個目錄」成立,對這一支不成立:它解完會把封裝檔改名藏起來,
            #    少讀的那幾項就等於從遊戲裡消失,而畫面上還是印一個綠色的勾。
            #    實測 200 項、名稱各 124 個位元組的合成封裝檔,舊寫法只解出 181 個檔,
            #    全程沒有一句警告。(這台機器上 1,879 個真的封裝檔最長的名稱是
            #    42 個位元組,一個都沒踩到 —— 所以這是耐用性缺口,不是現有教學路徑上的活錯誤。)
            # 上限:一個名稱長不過 MAX_NAME,所以目錄再長也長不過這個數,
            # 免得一個亂改過的檔頭害我們把整個檔讀進記憶體。
            limit = 16 + count * (8 + MAX_NAME + 1) + 8192

            def more(upto):
                """要讀到 blob 的第 upto 個位元組;不夠就再從檔案多拿一塊回來。

                回傳 False 代表檔案已經到底、再拿不到東西了(blob 仍可能長大了一些,
                所以呼叫的人要先再找一次,再決定要不要當成「檔案被截斷」)。
                """
                nonlocal blob
                while len(blob) < upto:
                    if len(blob) >= limit:
                        raise DataError('%s 的目錄長得離譜(讀了 %d 個位元組還沒走完,'
                                        '項目名稱可能沒有結尾的 0x00),不敢再讀下去。'
                                        % (os.path.basename(path), len(blob)))
                    chunk = f.read(65536)
                    if not chunk:
                        return False
                    blob += chunk
                return True

            # 從 +0x10 開始一項一項走。field 記的是「這一項的 8 個位元組在檔案裡的位置」,
            # 之後要改目錄時只寫那 8 個位元組,不必把整份目錄重排一次。
            pos = 16
            for _ in range(count):
                if not more(pos + 8):
                    raise DataError('%s 的目錄說有 %d 項,讀到第 %d 項就沒有了 —— 這個檔可能被截斷過。'
                                    % (os.path.basename(path), count, len(items) + 1))
                field = pos
                off = int.from_bytes(blob[pos:pos + 4], 'big')
                size = int.from_bytes(blob[pos + 4:pos + 8], 'big')
                pos += 8
                # 名稱到下一個 0x00 為止。找不到 0x00 代表讀進來的那一塊剛好切在名稱中間,
                # 再多拿一塊回來接著找。
                end = blob.find(b'\x00', pos)
                while end < 0:
                    # more() 回 False 只代表「檔案沒東西了」,不代表找不到 ——
                    # 它可能在到底之前又補了一段進來,那一段裡就有那個 0x00。
                    # 所以先再找一次,找不到才當成截斷。
                    grew = more(len(blob) + 65536)
                    end = blob.find(b'\x00', pos)
                    if end < 0 and not grew:
                        raise DataError('%s 第 %d 項的名稱沒有結尾的 0x00 —— 這個檔可能被截斷過。'
                                        % (os.path.basename(path), len(items) + 1))
                # 用 latin-1 解:一個位元組換一個字元,不會因為遇到不是 UTF-8 的位元組就爆掉,
                # 而且原樣編碼回去拿得回同一串位元組。這裡只是要一個檔名,不是要正確的文字。
                items.append((blob[pos:end].decode('latin-1', 'replace'), field, off, size))
                pos = end + 1
    except OSError as e:
        raise DataError('讀不到 %s:%s' % (path, e))
    return items


def read_entry(path, off, size):
    """照目錄給的位移與長度,把一個項目的原始位元組讀出來(還沒解壓)。

    短讀一定要當成錯誤:目錄說有這麼多而檔案給不出來,代表檔案被截斷過,
    後面每一項的位移也就都不能信了。
    """
    with open(path, 'rb') as f:
        f.seek(off)
        data = f.read(size)
    if len(data) != size:
        raise DataError('目錄說這一項有 %d 個位元組,實際只讀到 %d' % (size, len(data)))
    return data


def append_entry(path, field_pos, blob):
    """把 blob 接到檔尾,只改該項目的目錄 8 bytes 與檔頭的 4 bytes。

    原本的資料一個位元組都不動 —— 所以就算新資料是壞的,舊資料還在檔案裡。
    """
    # 順序有講究:
    # 1) 先量位元組順序。開始往檔尾寫之後,檔案大小就跟檔頭那個數字對不上了,
    #    那時候再量會兩種都不符,量不出來。
    # 2) 新資料的位移就是「還沒寫之前的檔案大小」。
    order = size_field_order(path)          # 一定要在改檔案之前先量
    new_off = os.path.getsize(path)
    with open(path, 'r+b') as f:
        f.seek(0, os.SEEK_END)
        f.write(blob)
        total = f.tell()
        # 只改這一項的 8 個位元組:新位移 + 新長度,兩個都是大端序。
        f.seek(field_pos)
        f.write(struct.pack('>II', new_off, len(blob)))     # 目錄一律 big-endian
        # 再改檔頭 +0x04 的總大小,用剛才量到的那一種順序寫回去。
        f.seek(4)
        f.write(struct.pack(order + 'I', total))
        # fsync 是要求作業系統真的落到磁碟。中途斷電時,
        # 「舊資料還在 + 目錄沒改到」比「目錄改了但資料沒寫進去」好收拾。
        f.flush()
        os.fsync(f.fileno())
    return new_off


# ─────────────────────────────────────────────────────────
#  FSH(SHPI 容器):找到那張圖、換掉像素
#
#  ⚠️ **這一整塊在本支腳本裡沒有被用到。** 它是本站處理圖檔那幾課共用的部分
#     (隊徽、大頭照、開場圖),留在這裡是為了讓每一支腳本長得一樣好對照。
#     這一課從頭到尾只做「把封裝檔拆成散裝檔」,不碰圖片內容。
#
#  SHPI 容器的位元組配置(全部**小端序**,跟外面 BIGF 目錄的大端序相反):
#    +0x00  4  'SHPI'
#    +0x04  4  整個 SHPI 的大小
#    +0x08  4  裡面有幾筆記錄
#    +0x0C  4  目錄識別字
#  +0x10 起是每筆記錄的索引,一筆 8 個位元組:4 個位元組的標籤 + 4 個位元組的位移。
#  記錄本身的前 16 個位元組是:格式代號 1 個、區塊大小 3 個、寬 2 個、高 2 個,
#  剩下 8 個是位置資訊;像素從記錄開頭 +16 開始。
# ─────────────────────────────────────────────────────────
# 名字後面那個數字是「一個像素幾個位元組」,全部是本站在剛安裝好的原版上量出來的。
# 2026-08-28 訂正:原本這張表有四格名字跟量到的位元組數對不上(0x6D 寫成 4 位元組、
# 0x7B 寫成 2 位元組、0x7D 寫成 3 位元組、RGB24 這個名字掛錯代號),
# 而且漏了 0x79 與 0x7F 兩個代號 —— 漏掉會讓下面的守門員把真實的圖擋掉。
# 2026-08-28 再訂正:0x79 原本叫 EMPTY_1x1,那是把「用途」寫成了「格式」。
FSH_FORMATS = {
    0x60: 'DXT1',        # 0.5  每 4x4 像素一個 8 位元組區塊
    0x61: 'DXT3',        # 1.0  每 4x4 像素一個 16 位元組區塊,前 8 個是透明度
    0x6D: 'ARGB16_4444', # 2.0  models.big 裡 18,287 張
    0x78: 'RGB16_565',   # 2.0  models.big 裡 10,512 張
    0x79: 'PAL4',        # 0.5  4 位元索引色,調色盤在緊接的 0x2A 區塊裡
                         #      2026-08-28 訂正:原本寫 EMPTY_1x1「永遠 1×1」。
                         #      uniforms.big 的 431 個空槽確實都是 1×1,但那是用途不是格式:
                         #      中文字型的字圖集就是 0x79,1024x512、正好 0.500 bytes/像素,
                         #      而 au20b_en.ffn 後面的 0x2A 調色盤正好 16 個項目(2的4次方)。
    0x7B: 'PAL8',        # 1.0  一個位元組是索引,調色盤在緊接的 0x2A 區塊裡
    0x7D: 'ARGB32',      # 4.0  剛安裝好的原版 portrait.big 2,391 張圖全部是這個
    0x7E: 'ARGB16_1555', # 外部文件說的,本站至今找不到樣本,無從實測
    0x7F: 'RGB24',       # 3.0  models.big 裡 45 張(g001-g045.fsh)
}
# 名字對齊 FSHTOOL 1.22(Denis Auroux, 2002)說明書列的格式表;
# 每像素位元組數是本站在剛安裝好的原版上自己量的,兩邊完全吻合。
# 那份說明書還有一條本站沒用到的規則:代號 +0x80 代表「這張圖本身是壓縮過的」。


def fsh_first_image(data):
    """回傳 (格式代號, 寬, 高, 像素起點, 像素終點)。只看第一筆記錄。

    只看第一筆是刻意的:後面那些通常是縮圖層或調色盤,不是要換的那張圖。

    ⚠️ 本支腳本沒有叫這個函式,見上面那一段說明。
    """
    if len(data) < 16 or data[:4] != b'SHPI':
        raise DataError('不是 SHPI 檔(開頭是 %r)' % data[:4])
    num = struct.unpack_from('<I', data, 8)[0]
    if num < 1:
        raise DataError('這個 SHPI 裡一張圖都沒有')
    # 第一筆索引在 +0x10,前 4 個位元組是標籤,位移在它後面,所以是 +20。
    off = struct.unpack_from('<I', data, 20)[0]         # 16 + 0*8 + 4
    if off + 16 > len(data):
        raise DataError('圖片記錄的檔頭不完整')
    # 格式代號不在上面那張表裡就停手。硬猜等於拿錯的每像素位元組數去算像素範圍,
    # 而算錯範圍寫回去的檔案是壞的。
    code = data[off]
    if code not in FSH_FORMATS:
        raise DataError('沒見過的格式代號 0x%02X' % code)
    # 區塊大小是 3 個位元組的小端序,沒有現成的格式字串可用,只能自己拼。
    block_size = data[off + 1] | (data[off + 2] << 8) | (data[off + 3] << 16)
    width = struct.unpack_from('<H', data, off + 4)[0]
    height = struct.unpack_from('<H', data, off + 6)[0]
    if not (0 < width <= 4096 and 0 < height <= 4096):
        raise DataError('圖片尺寸異常 %dx%d' % (width, height))
    # 像素從記錄開頭數過去第 16 個位元組開始。
    # 終點有三條路,按可信度排:
    #   1. 這筆記錄自己寫了區塊大小 → 用它
    #   2. 沒寫但後面還有記錄 → 用下一筆記錄的起點當這一筆的終點
    #   3. 都沒有 → 只好用到檔尾
    start = off + 16
    if block_size > 16:
        end = min(off + block_size, len(data))
    elif num > 1:
        end = min(struct.unpack_from('<I', data, 16 + 8 + 4)[0], len(data))
    else:
        end = len(data)
    return code, width, height, start, end


def fsh_replace_pixels(data, start, end, new_pixels):
    """把像素那一段換掉,前後的位元組原封不動接回去。長度不同就拒絕。

    為什麼長度一定要一樣:FSH 的檔頭與各筆記錄之間是用**絕對位移**互相指的。
    中間長度一變,後面每一個位移就全部指錯地方,整個容器當場壞掉。

    ⚠️ 本支腳本沒有叫這個函式,見上面那一段說明。
    """
    if len(new_pixels) != end - start:
        raise DataError('新像素有 %d 個位元組,原本是 %d —— 尺寸或格式不一致,拒絕寫入'
                        % (len(new_pixels), end - start))
    return data[:start] + new_pixels + data[end:]




# ─────────────────────────────────────────────────────────
#  解成資料夾
# ─────────────────────────────────────────────────────────
# 動手的時候記下「做到哪一步」。cmd_plan() 與 cmd_restore() 會寫它,
# main() 收尾那三個分支會讀它 —— 讀者按 Ctrl-C 或撞到錯誤的時候,
# 要能照實說出「封裝檔改名了沒有、散裝檔寫出去幾個」,不能一律說「什麼都沒動」。
#
# ⚠️ 2026-09-06 第三輪訂正:phase 與 inflight 是這一輪加的**三態**。
#    原本只有「寫了幾個」這種事後才更新的數字,而 os.replace 跟「登記」是兩行:
#    Ctrl-C 剛好落在那兩行中間的話,收尾照著登記講話就會少講一個檔。
#    現在那兩行被 _NoInterrupt 包成不可中斷的一段(那是主要的一道),
#    phase / inflight 則是保險 —— signal.signal 裝不上的時候(非主執行緒)
#    還是有人說得出「中斷時正在換 X,換好了沒有無法確定」。
#      phase: idle 還沒動 / unpacking 正在解 / renaming 正在改名 / renamed 已改名
#             / restoring 正在還原 / restored 已還原 / cleaning 正在刪散裝檔
#      inflight: 正在換名的那個散裝檔名(換完就清掉)
#      deleted: --clean 已經刪掉幾個散裝檔
#
# ⚠️ 2026-09-11 第四輪訂正:cleaning 與 deleted 是這一輪補的。
#    在此之前 --clean 那個刪檔迴圈從頭到尾不改 phase,於是刪到一半出事
#    (Ctrl-C,或 Windows 上遊戲/防毒握著某個散裝檔讓 os.remove 丟 PermissionError)時,
#    收尾看到的還是進迴圈之前那個相位 —— 「已經在原位了」那條路上它是 idle,
#    畫面就印「什麼都還沒有動到」,而檔案已經刪掉一批了。
#    (實測見下面 cleanup_hint() 那一段的訂正說明。)
PROGRESS = {'wrote': 0, 'manifest': None, 'target': None,
            'phase': 'idle', 'inflight': None, 'deleted': 0}


def taken(path):
    """這個名字被佔住了嗎?

    ⚠️ 用 os.path.lexists,不用 os.path.exists。後者會**跟著符號連結走**:
       一個指到別處、而那邊還不存在的符號連結,exists() 回答「沒有」,
       接下來 open() 就會沿著那條連結,在遊戲資料夾**外面**憑空生一個檔出來
       (指到既有的檔就是把那個檔整個寫掉)。
       lexists() 問的是「這個名字本身在不在」,符號連結自己就算佔住了。
    """
    return os.path.lexists(path)


def write_text_atomic(path, text):
    """把一段文字原子寫進 path,而且不跟著符號連結走。

    步驟:同一個資料夾裡開一個唯一暫存檔(mkstemp 內部用 O_EXCL,撞名會失敗,
    也不可能開到一個事先擺在那裡的符號連結)→ 寫 → flush → os.fsync
    → 補上一般檔案的權限(mkstemp 給的是 0600,只有自己讀得到)
    → os.replace 換上去(同一個檔案系統內的改名是原子的)。
    中途任何一步失敗就把暫存檔刪掉,原來那個名字維持原狀 ——
    所以不會留下一份寫到一半的清單,而 --clean 正是照著清單刪檔的。
    """
    refuse_symlink(path, '要寫的是這份清單')
    d = os.path.dirname(os.path.abspath(path))
    fd, tmp = tempfile.mkstemp(dir=d, prefix=os.path.basename(path) + '.tmp-')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as g:
            g.write(text)
            g.flush()
            os.fsync(g.fileno())
        os.chmod(tmp, 0o644)
        # 換名這一下不讓 Ctrl-C 插隊:中斷落在 os.replace 前後,
        # 磁碟上是舊清單還是新清單,呼叫的人要說得準。
        with _NoInterrupt():
            os.replace(tmp, path)
    except BaseException:
        try:
            os.remove(tmp)
        except OSError:
            pass
        raise


def manifest_text(bigpath, rows, done):
    """把清單的內容組出來。動手之前先寫的那一份與整批解完覆寫的那一份**同一個格式**。

    一行一個檔,用 tab 隔成三欄:檔名、寫出去的位元組數、內容的 sha256。
    還沒寫出去的那幾行,後兩欄是 0 與一個減號。

    ⚠️ 指紋這一欄是 2026-09-06 加的,而且 --clean 的整個安全性都靠它:
       沒有它的話「刪掉清單裡有的」只證明得了「這個名字當初是我寫的」,
       證明不了「現在躺在這個名字底下的還是我寫的那份東西」——
       讀者解出來之後自己改過的檔會被一起刪掉,而畫面上還印著
       「不是這支腳本寫的檔一個都沒動」。
    """
    head = ('# 這份清單由 mvp_unpack_big.py 產生,--restore 會用它認出自己寫過哪些檔。\n'
            '# 封裝檔: %s\n'
            '# 欄位(用 tab 隔開):檔名、寫出去的位元組數、內容的 sha256。\n'
            '# 指紋是 - 的那幾行代表「還沒寫出去,或那一次沒跑完」。\n'
            '# --clean 只刪指紋對得上的檔:沒有指紋的、對不上的(你自己改過的)一律保留。\n'
            % os.path.basename(bigpath))
    out = [head]
    for name, _off, _size, _dst in rows:
        n, sha = done.get(name, (0, '-'))
        out.append('%s\t%d\t%s\n' % (name, n, sha))
    return ''.join(out)


def read_manifest(path):
    """把清單讀回來,回傳 (項目, 這份是不是舊版的)。

    項目是 [(檔名, 大小, 指紋或 None)]。指紋那一欄整個不存在(只有兩欄)的話,
    這份清單就是 2026-09-06 之前的版本寫的 —— 回傳的第二個值為真,
    呼叫的人要據此拒絕刪任何東西。

    清單是一個檔案,而檔案是可以被改的,下面 --clean 會照著它刪檔。
    所以每個名字都要再過一次 safe_name(),跟寫出去的時候同一道關卡。
    """
    entries = []
    legacy = False
    with open(path, encoding='utf-8') as f:
        for line in f:
            if line.startswith('#') or not line.strip():
                continue
            cols = line.rstrip('\r\n').split('\t')
            try:
                name = safe_name(cols[0])
            except DataError as e:
                raise DataError('清單 %s 裡有一個不像單純檔名的項目,不敢照著刪任何東西:\n'
                                '  %s' % (MANIFEST, e))
            if len(cols) == 2:
                # 舊版寫出來的剛好是「檔名 + 大小」兩欄。名字照收(--restore 要數給你聽),
                # 但整份標成舊版,--clean 一個都不刪。
                legacy = True
                entries.append((name, None, None))
                continue
            if len(cols) != 3:
                # ⚠️ 舊版剛好兩欄、新版剛好三欄。一欄或四欄以上都不是這支寫得出來的,
                #    代表這份清單被改過(或根本不是它)。--clean 會照著它刪檔,所以拒絕。
                #    實測那個餌:把清單裡的檔名中間塞一個換行,那一行就變成一欄 ——
                #    只當成「舊版」放過去的話,畫面上會印「這份清單沒有指紋(舊版解出的)」,
                #    那句話是假的:它不是舊版,是被動過手腳。
                raise DataError('清單 %s 裡有一行不是這支腳本寫得出來的格式'
                                '(讀到 %d 欄,舊版是 2 欄、現在是 3 欄):\n'
                                '  %r\n'
                                '  這份清單被改過,不敢照著它刪任何東西。'
                                % (MANIFEST, len(cols), line.rstrip('\r\n')[:60]))
            try:
                size = int(cols[1])
            except ValueError:
                size = None
            sha = cols[2].strip().lower()
            entries.append((name, size, sha if len(sha) == 64 else None))
    return entries, legacy


def cleanup_hint():
    """照磁碟上的實況(加上 PROGRESS 當保險)說出「現在是什麼狀態、下一步該做什麼」。

    ⚠️ 不可以無條件說「什麼都沒有動到」。中斷會落在好幾個位置:
       還沒寫任何東西、寫了清單與一部分散裝檔、連封裝檔都已經改名藏起來了,
       或是正在 --restore 把它改回來的半路上。
       每一種要說不一樣的話 —— 說錯的那一句會讓讀者直接去開遊戲,
       而那時候封裝檔可能正躺在一個遊戲找不到的名字底下。

    ⚠️ 「封裝檔改名了沒有」一律去問磁碟,不看旗標。
       旗標是在 os.replace **之後**那一行才設的,而 Ctrl-C 可以剛好落在那個縫裡
       (實測:在那兩行中間丟 KeyboardInterrupt,看旗標的寫法印的是
        「封裝檔還在原位」,而它其實已經改名藏起來了 —— 讀者照著那句話去開遊戲,
        遊戲就少一個封裝檔)。磁碟上的狀態沒有這個縫。
       2026-09-06 加了 _NoInterrupt 把那兩行包成不可中斷的一段之後,
       這個縫幾乎不會被踩到;但這裡照樣以磁碟為準,因為「幾乎」不是「不會」。
    """
    me = os.path.basename(sys.argv[0])
    target = PROGRESS['target']
    if not target:
        return '  什麼都還沒有動到。\n'
    backup = target + BACKUP_SUFFIX
    here, there = taken(target), taken(backup)

    # 兩個名字同時不見 —— 換名那一步結果不明時才這樣說。不猜。
    # ⚠️ 2026-09-11 訂正:這一道原本沒有問相位,而 cmd_restore() 是在
    #    「跟它的備份都找不到」那道檢查**之前**就先登記 target 的,
    #    於是最常見的使用者失誤(--restore 指到不存在的檔、或在錯的資料夾裡跑)
    #    也會亮起,畫面上捏造出一段根本沒發生過的中斷情節
    #    (實測 --restore nosuch.big:舊寫法印「中斷剛好落在換名那一步,
    #     東西換到哪一邊無法確定」,而那個資料夾裡本來就沒有這個檔,也沒有中斷)。
    #    真的落在換名那一步時,相位一定已經不是 idle 了。
    if PROGRESS['phase'] != 'idle' and not here and not there:
        return ('  ⚠️ %s 跟 %s 現在兩個都找不到 —— 中斷剛好落在換名那一步,\n'
                '     東西換到哪一邊無法確定。請先自己看一眼那個資料夾,\n'
                '     再決定要不要把其中一個改回原名。\n'
                % (os.path.basename(target), os.path.basename(backup)))

    # --restore 走到一半:方向跟 --apply 相反,話也要反過來說。
    if PROGRESS['phase'] in ('restoring', 'restored'):
        if here and not there:
            return ('  還原已經做完了:%s 回到原位,遊戲讀得到它。\n'
                    '  (散裝檔要不要一起清掉是另一個開關:再跑一次加 --clean。)\n'
                    % os.path.basename(target))
        return ('  還原還沒做完 —— %s 還躺在備份的名字底下,遊戲現在找不到封裝檔。\n'
                '  請再跑一次:\n'
                '    python3 %s "%s" --restore\n'
                % (os.path.basename(target), me, target))

    # --clean 的刪檔迴圈走到一半。封裝檔這時已經在原位了(還原過或本來就在),
    # 剩下的是「刪掉幾個、清單還在不在」。
    if PROGRESS['phase'] == 'cleaning':
        return ('  中斷時正在刪散裝檔 —— 已經刪掉 %d 個,沒刪到的還在原地。\n'
                '  清單沒有被刪掉,它是唯一認得出那些檔的東西。要接著清就再跑一次:\n'
                '    python3 %s "%s" --restore --clean\n'
                % (PROGRESS['deleted'], me, target))

    # 備份在、正本不在 = 封裝檔確實已經改名藏起來了。
    if there and not here:
        return ('  封裝檔已經改名成 %s —— 遊戲現在找不到它。要回到原狀請跑:\n'
                '    python3 %s "%s" --restore --clean\n'
                % (os.path.basename(backup), me, target))

    # 走到這裡,封裝檔一定還在原位。剩下的是「這個資料夾裡留了什麼」。
    # 清單在不在也問磁碟:PROGRESS['manifest'] 是在 write_text_atomic 回來之後
    # 才設的,同樣有那個縫。
    extra = ''
    if PROGRESS['inflight']:
        # 只有 _NoInterrupt 裝不上的時候才走得到。不確定就說不確定。
        extra = ('  ⚠️ 中斷時正在把「%s」換上去,換好了沒有無法確定 ——\n'
                 '     下面那份清單裡它的指紋可能是空的,--clean 會保留它並告訴你。\n'
                 % PROGRESS['inflight'])
    # ⚠️ 下面這句只有 --apply 那條路說得出口。--restore 在第一道關卡就停下來時,
    #    資料夾裡的清單與散裝檔是**上一次**留下的,不是這一次弄出來的 ——
    #    講成「這一次」會害讀者以為剛才那個指令做了什麼(實測:還原時正本名被一條
    #    符號連結佔住,舊寫法印「已經留下一份清單與 0 個散裝檔」,而這一次一個位元組
    #    都沒有寫)。
    # ⚠️ 2026-09-11 訂正:這一道原本問的是「相位是不是 unpacking」,於是換名那一步
    #    (phase='renaming',也就是 os.replace(bigpath, backup) 前後)一出事就掉進來
    #    說「什麼都還沒有動到」—— 而那時候清單與整批散裝檔早就躺在讀者的遊戲資料夾裡了。
    #    那不只是 Ctrl-C 剛好落在縫裡:Windows 上遊戲或防毒程式握著封裝檔的 handle 時,
    #    改名就是 PermissionError,那是一條必定走得到的路
    #    (實測把那一行換成 raise OSError(13):舊寫法 exit 2、畫面說沒動到,
    #     而資料夾裡清單與散裝檔都在)。
    #    現在只有 idle 這一個相位說得出這句話 —— 「還沒開始動」以外的每一種,
    #    都往下走去問磁碟。日後再加新的相位也不會默默掉回這句謊話。
    if PROGRESS['phase'] == 'idle':
        return extra + '  什麼都還沒有動到。\n'
    man = PROGRESS['manifest'] or os.path.join(
        os.path.dirname(os.path.abspath(target)), MANIFEST)
    if taken(man) or PROGRESS['wrote']:
        return (extra +
                '  封裝檔還在原位、沒有改名 —— 遊戲照樣讀得到它。\n'
                '  但這個資料夾裡已經留下一份清單與 %d 個散裝檔。要清掉請跑:\n'
                '    python3 %s "%s" --restore --clean\n'
                % (PROGRESS['wrote'], me, target))
    return extra + '  什麼都還沒有動到。\n'


def safe_name(name):
    """項目名稱要拿來當檔名,先擋掉任何會跳出目標資料夾的寫法。

    封裝檔是別人給的檔案,裡面的名稱一律當成**不可信的輸入**。
    名稱裡塞路徑分隔符號就能讓解出來的檔落到別的資料夾去,
    所以只認單純的檔名,看到別的一律停手,不做「清洗後照用」。

    2026-09-05 訂正:這段說明原本寫「這裡是白名單心態」,那不準確 ——
    它列舉的是**要擋的東西**,其餘一律放行,那是黑名單。而且當時的名單漏了好幾種:
    實測 'C:evil.txt'、'foo.txt:ads'、'NUL'、'CON.txt' 與名稱裡帶換行的全部通過。
    下面是現在真的擋的每一種,每一種都在本檔上實際餵過:

      · 空的、'.'、'..'
      · 斜線與反斜線 —— 跳到別的資料夾
      · 冒號 —— Windows 上 os.path.join(r'D:\game\data', 'C:evil.txt') 的結果是
        'C:evil.txt',前面整段被丟掉,檔案落到 C: 的目前工作目錄去;
        'foo.txt:ads' 則會寫成 NTFS 的交替資料流,在檔案總管完全看不到
      · 以點開頭 —— 藏起來的檔;也擋掉本支自己那份清單 .mvp_unpack_manifest.txt
      · 控制字元 —— 名稱裡的換行會在清單裡多寫一行,而 --clean 是照那份清單刪檔的。
        實測可以讓它刪掉玩家自己放在同一個資料夾裡的存檔,
        而同一時間畫面上還印著「不是這支腳本寫的檔一個都沒動」
      · 結尾是點或空白 —— Windows 會把結尾的點與空白吃掉,寫出來的是另一個檔名,
        之後複驗與 --clean 都找不到它
      · Windows 的保留裝置名(見 WIN_RESERVED)—— 那些名字指的是裝置不是檔案
    """
    if not name or name in ('.', '..'):
        raise DataError('封裝檔裡有一個空的或可疑的項目名稱,中止。')
    if '/' in name or '\\' in name or ':' in name or name.startswith('.'):
        raise DataError('項目名稱「%s」含路徑分隔符號、磁碟代號或以點開頭,不敢寫出去。' % name)
    if any(ord(c) < 0x20 or ord(c) == 0x7F for c in name):
        raise DataError('項目名稱 %r 含控制字元,不是單純的檔名,不敢寫出去。' % name)
    if name[-1] in ' .':
        raise DataError('項目名稱「%s」結尾是點或空白 —— Windows 會把它吃掉,不敢寫出去。' % name)
    if name.split('.')[0].upper() in WIN_RESERVED:
        raise DataError('項目名稱「%s」是 Windows 的保留裝置名,不敢寫出去。' % name)
    return name


def plan_unpack(bigpath):
    """先把「會寫哪些檔、寫到哪裡」整份算完,還沒有動到任何檔案。

    要有這一步,是因為預覽跟實作必須走**同一份計算**。
    分開寫兩套的話,預覽給你看的跟真的做的會慢慢長歪,而你是照預覽做決定的。

    ⚠️ 但這裡算得準的只有**檔名與路徑**,算不出「會寫多大」。
    rows 裡那個 size 是封裝檔目錄登記的長度,也就是**壓縮後**的大小;
    --apply 真正寫出去的是 qfs_decompress() 解開之後的內容,兩者可以差好幾倍。
    在剛安裝好的英文版 data/datafile/datafile.big 上量:460 個項目沒有一個相同,
    01day.txt 目錄登記 4,470、解出來 11,934,
    目錄登記的長度加總 2,839,757(檔案本身 2,857,593)變成 14,095,446(4.96 倍)。
    未壓縮的封裝檔兩者才會相同(同一份安裝的 data/anims/anims.big,
    730 個項目全部一致),所以只挑那種檔測是測不出來的。

    解出來的散裝檔就放在封裝檔自己那個資料夾裡,不另外開目錄:
    這個實驗要驗的正是「同名資料夾 + 散裝檔」那個擺法。
    """
    items = big_entries(bigpath)
    outdir = os.path.dirname(os.path.abspath(bigpath))
    rows = []
    seen = {}
    for name, field, off, size in items:
        n = safe_name(name)
        # 同一個名字出現兩次的話,後面那一項會蓋掉前面那一項寫出去的檔,
        # 而「已解出 N 個檔」跟複驗都還是照 N 算 —— 資料夾裡其實少一個。
        # 兩項大小剛好一樣時連複驗都抓不到(實測:兩項各 4 個位元組,
        # 印「已解出 3 個檔 / 複驗:3 個檔全部在…✅」,而資料夾裡只有 2 個)。
        # (那一次實測是在複驗還只看大小的時候做的。現在複驗連內容的指紋一起比,
        #  但這一種還是抓不到 —— 少掉的那個檔根本沒被走訪到。)
        # 所以在還沒寫任何一個位元組之前就擋掉。
        # 這不是理論狀況:四份剛安裝好的原版(英文版、中文版、PK 版、TC PATCH123)
        # 底下 data/frontend/ 各有 17 個封裝檔帶著一個重複的名稱
        # (例如 portrait.big 的 a2653.fsh,兩項位移不同、各 1 個位元組,
        #  是兩項不同的資料,不是同一項登記兩次)。
        # 本課教的 datafile.big 與 anims.big 沒有這種項目。
        # ⚠️ 查重的鍵**不是**名稱本身,是「Windows 會把哪些名字當成同一個檔」:
        #    那邊不分大小寫(A.FSH 與 a.fsh 是同一個落點),而且會把結尾的點與空白吃掉。
        #    macOS 預設的檔案系統同樣不分大小寫。拿原字串當鍵的話,
        #    A.FSH 與 a.fsh 會被當成兩項各寫一次,最後資料夾裡只有一個檔,
        #    而兩項大小剛好一樣時連下面的複驗都會印綠色的勾。
        #    (結尾的點與空白、保留裝置名在上面 safe_name() 已經整個擋掉了;
        #     這裡照樣正規化一次,是不想讓這個鍵的正確性掛在另一個函式的實作細節上。)
        #    2026-09-05 在這台機器上量:1,881 個真的封裝檔、283,014 個項目名稱,
        #    「只差在大小寫」的碰撞是 0 個 —— 所以這一道不會擋到真的遊戲資料。
        key = n.casefold().rstrip(' .')
        if key in seen:
            if seen[key] == n:
                raise DataError('封裝檔的目錄裡有兩項都叫「%s」,解出來會互相蓋掉,不敢做。' % n)
            raise DataError('封裝檔的目錄裡有兩項只差在大小寫(「%s」與「%s」)——\n'
                            '  Windows 與 macOS 預設不分大小寫,解出來會互相蓋掉,不敢做。'
                            % (seen[key], n))
        seen[key] = n
        rows.append((n, off, size, os.path.join(outdir, n)))
    return outdir, rows


def cmd_plan(bigpath, apply_it):
    """預覽(apply_it 為假)與實作(為真)共用的主流程。

    同一個函式做兩件事是刻意的:預覽印出來的**那些檔名**,
    就是待會兒真的要寫出去的那一份,不會有第二套邏輯偷偷不一樣。
    但那一欄的數字不是「會寫出來的大小」:它是封裝檔目錄登記的**壓縮後**長度,
    真正寫出去的是解壓後的內容。所以印的時候欄位要寫明「壓縮後」,
    只寫「位元組」會讓人照著一個小好幾倍的數字去估硬碟空間。
    """
    outdir, rows = plan_unpack(bigpath)
    # 先問一句「這些檔名已經被佔住了嗎」。被佔住就整個停下來,
    # 一個都不覆蓋。那些檔可能是你上次解出來的,也可能是遊戲本來就有的。
    # 用 taken()(os.path.lexists)不用 os.path.exists:見 taken() 的說明,
    # 一個指到資料夾外面、而那邊還不存在的符號連結,exists() 會回答「沒有」。
    exists = [r for r in rows if taken(r[3])]
    print('  封裝檔 %s(%d 個項目,%d 位元組)'
          % (os.path.basename(bigpath), len(rows), os.path.getsize(bigpath)))
    print('  會解到 %s' % outdir)
    print()
    print('  前 8 個項目(大小是目錄登記的壓縮後長度,壓縮過的項目解出來會大好幾倍):')
    for name, off, size, dst in rows[:8]:
        print('    %-26s %10d 位元組(壓縮後)' % (name, size))
    if len(rows) > 8:
        print('    ...(還有 %d 個)' % (len(rows) - 8))
    if exists:
        print()
        print('  ⚠️ 這 %d 個檔名在資料夾裡已經存在:' % len(exists))
        for r in exists[:8]:
            print('     %s' % r[0])
        # 是符號連結的話要點名說出來:那跟「你上次解過一次」是完全不同的一件事,
        # 而讀者要採取的行動也不一樣(前者是把連結移走,後者是先確認舊檔)。
        for r in exists:
            refuse_symlink(r[3], '那是要寫出去的散裝檔')
        raise DataError('資料夾裡已經有同名的檔,不敢覆蓋。\n'
                        '  先確認那些檔是什麼(可能你已經解過一次了)。')
    # 清單也是一個既有的檔,一樣不覆蓋。同一個資料夾裡可能不只一個封裝檔
    # (data/frontend/ 就是一堆),蓋掉上一次那份清單,上一次解出來的散裝檔
    # 就再也沒有東西認得出是哪些,--clean 只能什麼都不刪。
    man = os.path.join(outdir, MANIFEST)
    if taken(man):
        refuse_symlink(man, '要寫的是這份清單')
        raise DataError('這個資料夾裡已經有一份 %s —— 那是上一次解封裝檔留下的紀錄。\n'
                        '  先把上一次那個封裝檔還原掉(--restore --clean),再回來解這一個。'
                        % MANIFEST)
    # 封裝檔要改成的那個備份名也一樣:被佔住就停手。
    # ⚠️ 底下那一行 os.replace(bigpath, backup) 是**無聲覆蓋**的:
    #    備份名已經有東西時,它會直接把那個東西換掉、一句話都不說。
    #    那個東西極可能就是上一次解封裝檔留下的原檔 —— 而且是唯一的一份,
    #    蓋掉之後這個封裝檔就再也回不來了(實測:事先放一份非空的 .unpackbak,
    #    舊版跑完之後那份內容整個消失,畫面上還是印綠色的勾)。
    backup = bigpath + BACKUP_SUFFIX
    if taken(backup):
        refuse_symlink(backup, '封裝檔要改成的就是這個名字')
        raise DataError('%s 已經存在 —— 那多半是上一次解這個封裝檔留下的原檔。\n'
                        '  蓋掉它就等於把原檔弄丟,不敢做。\n'
                        '  先還原上一次那次(--restore --clean),或自己確認那個檔是什麼。'
                        % os.path.basename(backup))
    print()
    print('  解完之後會把 %s 改名成 %s%s，'
          % (os.path.basename(bigpath), os.path.basename(bigpath), BACKUP_SUFFIX))
    print('  這樣遊戲就找不到封裝檔,只能去讀散裝檔 —— 那正是這個實驗要驗的事。')
    if not apply_it:
        print()
        print('  以上是預覽,還沒有動到任何檔案。')
        print('  確定要做的話,在剛才那一行最後面加上 --apply')
        return

    # ⚠️ 動手**之前**先把「打算要寫哪些檔」寫成清單。
    #    2026-09-05 訂正:舊版是整批做完才寫清單,結果解到一半被 Ctrl-C 或出錯時,
    #    已經寫好的那幾百個散裝檔留在遊戲資料夾裡而清單還沒出去 ——
    #    --restore --clean 說「找不到清單,不動它們」什麼都不刪,
    #    --apply 重跑又被「資料夾裡已經有同名的檔」擋住,讀者被卡在一個
    #    工具自己走不出來的狀態(實測:剛寫出三百多個檔的時候送中斷訊號,結束碼 130,
    #    留下 312 個散裝檔、0 份清單,兩條退路都走不通)。
    #    (整批做完下面那一段會用實際大小再覆寫一次。)
    #    寫法用 write_text_atomic():同資料夾唯一暫存檔 → fsync → os.replace。
    #    直接 open(man, 'w') 有兩個問題:一是它會跟著一個同名的符號連結跑到資料夾外面去,
    #    二是它會先把既有內容截成 0 —— 而 --clean 是照這份清單刪檔的,
    #    一份被截半的清單等於「有些解出來的檔從此沒有人認得」。
    # ⚠️ 登記要在**寫之前**。反過來的話,Ctrl-C 落在「清單已經落到磁碟上」與
    #    「程式登記了它」這兩件事中間,收尾就會說「什麼都還沒有動到」,
    #    而資料夾裡明明多了一份清單。cleanup_hint() 那邊還會再去問一次磁碟。
    PROGRESS['target'] = bigpath
    PROGRESS['manifest'] = man
    PROGRESS['phase'] = 'unpacking'
    write_text_atomic(man, manifest_text(bigpath, rows, {}))

    # 封裝檔只開一次,靠 seek 跳著讀每一項。幾百個項目各開一次檔會慢很多。
    written = []
    # 「有沒有一路走到把最終清單寫出去」。下面的 finally 靠它決定要不要補寫清單。
    # ⚠️ 不可以拿「寫出去的數量對不對得上」當條件(2026-09-06 被自己種的餌抓到):
    #    Ctrl-C 落在 _NoInterrupt 區塊**裡面**的時候,那個檔已經換上去、也已經
    #    登記進 written 了,數量剛好對得上 —— 條件不成立,清單就沒補,
    #    留在每一行指紋都是「-」的狀態,而 --clean 不敢刪沒有指紋的檔。
    #    實測那一次:title.ico 躺在資料夾裡,清單寫著「title.ico 0 -」,
    #    --restore --clean 印「1 個檔清單裡沒有指紋,保留」,讀者兩條路都走不通。
    manifest_final = False
    try:
        with open(bigpath, 'rb') as f:
            for name, off, size, dst in rows:
                f.seek(off)
                blob = f.read(size)
                if len(blob) != size:
                    raise DataError('讀 %s 時只讀到 %d 個位元組(應該 %d),中止。'
                                    % (name, len(blob), size))
                # 官方中文版的散裝檔是**解壓縮後**的內容,所以這裡也解開。
                plain = qfs_decompress(blob)
                want = hashlib.sha256(plain).hexdigest()
                # 先寫一個暫存檔再改名。os.replace 是原子的:
                # 寫到一半被中斷時,留下來的是那個暫存檔,
                # 不會是一個「看起來寫好了」的半截檔。
                # ⚠️ 暫存檔的名字交給 mkstemp 決定,不用「<名稱>.tmp」這種猜得到的名字。
                #    mkstemp 內部是 O_EXCL:撞到既有的名字就自己換一個再開,
                #    所以既不可能覆蓋別人的檔,也不可能開到一個事先擺在那裡的符號連結
                #    (前面那道「這些檔名已經在了嗎」只看最終檔名,看不到暫存檔那個名字;
                #     用 open(tmp, 'wb') 的話,一個指向遊戲資料夾**外面**的暫存檔連結
                #     會讓這一行把外面那個檔整個寫掉,而複驗透過同一個連結讀回來
                #     還是會印綠色的勾 —— 實測:資料夾外的 precious.sav
                #     被寫成解出來的內容,畫面照樣印綠色的勾)。
                try:
                    fd, tmp = tempfile.mkstemp(dir=outdir, prefix=name + '.tmp-')
                except OSError as e:
                    raise DataError('在 %s 裡開不了暫存檔:%s\n'
                                    '  資料夾可能沒有寫入權限,或磁碟滿了。' % (outdir, e))
                try:
                    with os.fdopen(fd, 'wb') as g:
                        g.write(plain)
                        g.flush()
                        # fsync 是要求作業系統真的把它落到磁碟。
                        # 下一行要「讀回來比對」,不 fsync 的話讀到的可能只是
                        # 作業系統的快取,那等於拿自己剛寫的東西跟自己比。
                        os.fsync(g.fileno())
                    # mkstemp 給的權限是 0600(只有自己讀得到)。解出來的散裝檔
                    # 是要給遊戲讀的,補成一般檔案的權限。
                    os.chmod(tmp, 0o644)
                    # 讀回來比指紋:確認磁碟上真的是我們要寫的那一串位元組。
                    # 磁碟滿了而 write() 沒報錯、或檔案系統出問題,都在這裡被抓住。
                    got = sha256_file(tmp)
                    if got != want:
                        raise DataError('%s 寫出去之後讀回來對不上(想寫 %s,讀到 %s)——\n'
                                        '  磁碟可能滿了或有問題。暫存檔已經清掉,\n'
                                        '  這個檔名底下什麼都沒有寫進去。'
                                        % (name, want[:16], got[:16]))
                    # 換名與登記中間不可以有縫:檔案換上去之後 Ctrl-C 才到的話,
                    # 收尾要把這個檔算進去,不可以少講一個。
                    PROGRESS['inflight'] = name
                    with _NoInterrupt():
                        os.replace(tmp, dst)
                        written.append((name, len(plain), want))
                        PROGRESS['wrote'] = len(written)
                        PROGRESS['inflight'] = None
                except BaseException:
                    # 換名沒做成才可以清暫存檔並把「正在換」收回來。
                    # 做成了的話 tmp 這個名字已經不存在,os.remove 會失敗,正好。
                    if not taken(dst):
                        PROGRESS['inflight'] = None
                    try:
                        os.remove(tmp)
                    except OSError:
                        pass
                    raise
        print()
        print('  已解出 %d 個檔。' % len(written))
        # 清單再寫一次,這次帶實際大小與內容的指紋(man 在上面已經算過路徑了)。
        # 還原時才知道哪些檔是這支腳本寫出來的、而且現在還是原樣:
        # 沒有它的話 --clean 只能靠猜,而猜錯就是刪掉玩家自己的檔。
        write_text_atomic(man, manifest_text(
            bigpath, rows, dict((w[0], (w[1], w[2])) for w in written)))
        manifest_final = True
    finally:
        # 沒走到上面那一行的話,把「已經真的寫出去的那幾個」的指紋補進清單。
        # ⚠️ 這一段是 --restore --clean 收拾得掉半途而廢那一次的唯一依據:
        #    先寫的那一份清單每一行的指紋都是「-」,而 --clean 不敢刪沒有指紋的檔。
        #    不補的話讀者會卡在「--apply 說資料夾裡已經有同名的檔」與
        #    「--clean 說沒有指紋不敢刪」兩條都走不通的中間。
        #    只吞 Exception 不吞 BaseException:第二次 Ctrl-C 要照樣穿出去,
        #    也不可以讓補清單失敗蓋掉原本那個更重要的例外。
        if not manifest_final:
            try:
                write_text_atomic(man, manifest_text(
                    bigpath, rows, dict((w[0], (w[1], w[2])) for w in written)))
            except Exception:
                pass
    print('  已記錄清單 → %s' % MANIFEST)

    # 改名不是刪除。遊戲從此找不到封裝檔(這正是要製造的情境),
    # 而原檔一個位元組都沒少,就躺在旁邊等 --restore 把名字換回來。
    # (backup 這個名字在上面已經先確認過沒有被佔住了 —— os.replace 會無聲覆蓋。)
    # 換名與登記中間不可以有縫(2026-09-06)。封裝檔藏起來之後 Ctrl-C 才到,
    # 收尾要說「已經改名了,請 --restore」,不可以說「還在原位」。
    PROGRESS['phase'] = 'renaming'
    with _NoInterrupt():
        os.replace(bigpath, backup)
        PROGRESS['phase'] = 'renamed'
    print('  已把 %s 改名成 %s' % (os.path.basename(bigpath), os.path.basename(backup)))

    # 複驗:重新去磁碟上看一次,不是相信剛才那幾行「我寫過了」。
    # 「檔在不在、是不是一般檔案、大小對不對、內容的指紋對不對」四項都驗
    # (2026-09-06 清單多了指紋那一欄之後才有第四項;這一句在那之前寫的是
    #  「只驗得到檔在、大小對,驗不到內容」,現在不成立了)。
    # 真正驗不到的是「遊戲會不會去讀這些散裝檔」—— 那要你自己開遊戲才知道。
    bad = 0
    for name, n, sha in written:
        p = os.path.join(outdir, name)
        if os.path.islink(p) or not os.path.isfile(p) or os.path.getsize(p) != n:
            print('  ❌ %s 複驗失敗(檔不在、是一條符號連結,或大小不對)' % name)
            bad += 1
        elif sha256_file(p) != sha:
            # 大小對得上、內容卻不是我們寫的那一份。抓得到這種的只有指紋。
            print('  ❌ %s 複驗失敗(大小對得上,但內容的指紋對不上)' % name)
            bad += 1
    if bad:
        # 複驗沒過就**自動**把封裝檔改回原名。那一步是安全的:
        # 原檔從頭到尾一個位元組都沒被動過,只是換了個名字,改回去就是放回遊戲要讀的位置。
        # 散裝檔不自動刪 —— 刪檔這件事永遠留給讀者自己下 --clean,
        # 下面把那一行指令印出來。
        back = '想自動把封裝檔改回原名,但沒有做成'
        try:
            if taken(backup) and not taken(bigpath):
                PROGRESS['phase'] = 'restoring'
                with _NoInterrupt():
                    os.replace(backup, bigpath)
                    PROGRESS['phase'] = 'restored'
                back = ('已自動把 %s 改回 %s(原檔一個位元組都沒動過,遊戲讀得到它)'
                        % (os.path.basename(backup), os.path.basename(bigpath)))
        except OSError as e:
            back = '想自動把封裝檔改回原名卻失敗了(%s)' % e
        raise DataError('有 %d 個檔複驗沒過 —— %s。' % (bad, back))
    print('  複驗:%d 個檔全部在,大小與內容的指紋都對得上 ✅' % len(written))
    print()
    print('  現在開遊戲試試看。')
    print('  進得去而且一切正常 → 這條路通,模組可以不必再動封裝檔。')
    print('  進不去或有東西不見 → 用下面這行還原,然後回報:')
    print('    python3 %s "%s" --restore' % (os.path.basename(sys.argv[0]), backup))


def cmd_restore(path, clean):
    """path 可以給原本的 .big 或改名後的備份,兩種都認。"""
    if path.endswith(BACKUP_SUFFIX):
        backup, target = path, path[:-len(BACKUP_SUFFIX)]
    else:
        backup, target = path + BACKUP_SUFFIX, path
    # ⚠️ 還原跟清理是兩件獨立的事。
    #    第一版把它們綁在一起,結果「已經還原過、只想清散裝檔」時
    #    會卡在「找不到備份」而中止 —— 跑一次就看到了。
    # 兩個都在的時候不猜。那代表有人手動放了一個同名的封裝檔回來,
    # 這時候改名過去會蓋掉其中一個,而蓋掉哪一個都可能是錯的。
    # 這三道「在不在」一律用 taken()(os.path.lexists),不用 os.path.exists:
    # 一個指到別處、而那邊還不存在的符號連結,exists() 會回答「沒有」,
    # 於是「備份跟正本同時存在」那一道就形同虛設,os.replace 直接蓋過去。
    # 從這裡開始就要說得出「還原做到哪一步」了(見 cleanup_hint())。
    PROGRESS['target'] = target
    if taken(backup):
        # ⚠️ 這一道要問在「同時存在」**之前**。
        #    符號連結(連懸空的都算)在 taken() 眼裡就是「這個名字被佔住了」,
        #    擺在後面的話永遠是「同時存在」先講話,這一道一次都不會亮
        #    (實測:正本名擺一條指到資料夾外面的連結,舊的順序印的是
        #     「misc.big 跟它的備份同時存在」—— 擋是擋住了,但讀者照著那句話
        #     去找「另一個 misc.big」根本找不到,真正的問題是那是一條連結)。
        refuse_symlink(target, '封裝檔要改回的就是這個名字')
        if taken(target):
            raise DataError('%s 跟它的備份同時存在。先確認哪一個是你要的,不敢覆蓋。'
                            % os.path.basename(target))
        # 備份本身是一條符號連結的話,下面驗的是它指到的那個檔,
        # 而 os.replace 搬回去的是那條連結 —— 驗過的東西跟放回去的東西不是同一個。
        # 遊戲之後讀到的會是連結另一頭的內容,那可能在遊戲資料夾外面。
        if os.path.islink(backup):
            raise DataError('%s 是一條符號連結,不是備份出來的封裝檔本體。\n'
                            '  驗的是它指到的檔、搬回去的卻是連結本身,兩者不是同一個東西,不敢做。'
                            % os.path.basename(backup))
        # 還原之前先驗那個備份還是不是一個完整的封裝檔。
        # 它應該就是原檔、只是換了個名字,所以開頭四個位元組要是 BIGF,
        # 而檔頭 +0x04 那個「檔案總大小」要對得上實際檔案大小。
        # 0 個位元組、被截斷過、或根本被換成了別的東西,都會在這裡停下來 ——
        # 把一個壞掉的檔擺回遊戲要讀的位置,比不還原糟得多。
        # 停下來也不會弄丟任何東西:備份還躺在原地,名字沒動,你可以自己看一眼再決定。
        # 本站拿這道檢查掃過 1,879 個真的封裝檔(含四份剛安裝好的原版),
        # 沒有一個被擋下來。
        with open(backup, 'rb') as f:
            magic = f.read(4)
        if magic != b'BIGF':
            raise DataError('備份 %s 的開頭不是 BIGF(讀到 %r,整個檔 %d 個位元組)——\n'
                            '  那不是原本的封裝檔,不敢拿它去還原。它還躺在原地,名字沒動。'
                            % (os.path.basename(backup), magic, os.path.getsize(backup)))
        size_field_order(backup)     # 大小欄位對不上就在這裡丟 DataError
        # 這裡是**改名**不是複製:備份本來就是原檔,只是換過名字,
        # 改名回去是原子的 —— 不可能留下一個寫到一半的封裝檔給遊戲讀。
        # (先複製成暫存檔再換上去反而更糟:備份會留在原地,
        #  下一次 --restore 就撞上「正本跟備份同時存在」那一道而停手。)
        # 換名與登記中間一樣不留縫。
        PROGRESS['phase'] = 'restoring'
        with _NoInterrupt():
            os.replace(backup, target)
            PROGRESS['phase'] = 'restored'
        print('  已把 %s 改回 %s' % (os.path.basename(backup), os.path.basename(target)))
    elif taken(target):
        print('  %s 已經在原位了(可能你還原過一次)。' % os.path.basename(target))
    else:
        raise DataError('%s 跟它的備份都找不到 —— 沒有東西可以還原。'
                        % os.path.basename(target))

    # 封裝檔回來了,接下來處理散裝檔。沒有清單就不知道哪些是自己寫的,
    # 那就什麼都不刪。少刪只是留下垃圾,多刪是刪掉玩家的東西。
    outdir = os.path.dirname(os.path.abspath(target))
    man = os.path.join(outdir, MANIFEST)
    if not taken(man):
        print('  (找不到清單,所以不知道哪些散裝檔是解出來的 —— 不動它們)')
        return
    # 清單是一份「等一下要照著刪的名單」。它自己是一條符號連結的話,
    # 讀到的就是連結另一頭那個檔的內容 —— 那可能是任何人擺的任何一份名單。
    if os.path.islink(man):
        raise DataError('%s 是一條符號連結,不是這支腳本寫出來的那份清單。\n'
                        '  照著它刪檔等於讓別人決定要刪什麼,不敢做。' % MANIFEST)
    entries, legacy = read_manifest(man)
    print('  清單裡有 %d 個當初解出來的散裝檔。' % len(entries))
    if not clean:
        print('  它們還留在資料夾裡。封裝檔已經回來了,遊戲會用封裝檔。')
        print('  想一起清掉的話,加 --clean 再跑一次:')
        print('    python3 %s "%s" --restore --clean' % (os.path.basename(sys.argv[0]), target))
        return
    # ⚠️ 沒有指紋那一欄的清單是 2026-09-06 之前的版本寫的。
    #    那種清單只證明得了「這些名字當初是我寫的」,證明不了
    #    「現在躺在這些名字底下的還是我寫的那份東西」——
    #    你解出來之後自己改過的檔會被一起刪掉。所以一個都不刪。
    if legacy:
        print()
        print('  這份清單沒有指紋(舊版解出的),分不出哪些檔你後來改過 ——')
        print('  所以一個都不敢刪。請自己清,或重新解一次再 --restore --clean。')
        print('  (封裝檔已經回到原位了,遊戲會用封裝檔,散裝檔留著不影響它。)')
        return
    # 從這裡開始就會真的刪檔了,先把相位登記起來:刪到一半被 Ctrl-C 打斷、
    # 或某個檔被別的程式握著讓 os.remove 丟 PermissionError 的時候,
    # 收尾要說得出「已經刪掉幾個」,不可以說「什麼都還沒有動到」。
    PROGRESS['phase'] = 'cleaning'
    gone = 0
    links = []
    changed = []
    nofp = []
    for n, _size, sha in entries:
        p = os.path.join(outdir, n)
        # 符號連結跳過。這支腳本寫出來的一定是一般檔案,所以名字對得上卻是一條連結,
        # 就代表那不是我們寫的那個檔 —— 別人擺的東西一個都不動。
        if os.path.islink(p):
            links.append(n)
        elif not os.path.isfile(p):
            continue                     # 已經不在了,沒什麼好刪的
        elif sha is None:
            # 那一次沒跑完,這個名字的指紋還沒補上去。不確定就不刪。
            nofp.append(n)
        elif sha256_file(p) != sha:
            changed.append(n)
        else:
            # 計數要跟 os.remove 貼在一起:中間隔著別的事情的話,
            # 中斷落在那個縫裡收尾就會少講一個。
            os.remove(p); gone += 1; PROGRESS['deleted'] = gone
    kept = links + changed + nofp
    if kept:
        # 還有東西留著,清單就不能刪 —— 它是唯一認得出那些檔的東西。
        print('  已刪掉 %d 個當初解出來的散裝檔。' % gone)
        print('  清單留著沒刪:下面這些檔還在,而清單是唯一認得出它們的東西。')
    else:
        os.remove(man)
        print('  已刪掉 %d 個當初解出來的散裝檔,以及那份清單。' % gone)
    if changed:
        print('  %d 個檔你改過,保留:' % len(changed))
        for n in changed[:8]:
            print('     %s' % n)
        if len(changed) > 8:
            print('     ...(還有 %d 個)' % (len(changed) - 8))
    if nofp:
        print('  %d 個檔清單裡沒有指紋(那一次沒跑完),保留:' % len(nofp))
        for n in nofp[:8]:
            print('     %s' % n)
        if len(nofp) > 8:
            print('     ...(還有 %d 個)' % (len(nofp) - 8))
    if links:
        print('  %d 個名字現在是符號連結,不是這支腳本寫的檔,保留:' % len(links))
        for n in links[:8]:
            print('     %s' % n)
        if len(links) > 8:
            print('     ...(還有 %d 個)' % (len(links) - 8))
    print('  ⚠️ 只刪清單裡有、而且內容的指紋還對得上的 ——')
    print('     不是這支腳本寫的、以及你自己改過的,一個都沒動。')


def main():
    """讀參數、分派到 --restore 或預覽/實作,並把結束碼收成一致的三種。

    結束碼:0 正常、2 自己停下來、130 你按了 Ctrl-C。
    三種收尾都會再印一次 cleanup_hint():檔案現在是什麼狀態、下一步該做什麼。
    「什麼都還沒有動到」這句話只有在真的一個檔都還沒寫、也還沒刪的時候才印得出來
    (2026-09-11 訂正:這句話一度是假的 —— cleanup_hint() 那道相位閘只認得 unpacking,
     於是換名那一步與 --clean 刪檔那一段出事時都掉回這句話。現在只有 idle
     這一個相位說得出口,而 idle 的意思就是「還沒寫、也還沒刪」)。
    「自己停下來」一律印成「停下來了:…」,不噴一長串堆疊訊息,
    因為這支是給人看的工具,不是給程式接的。
    2026-09-05 訂正:舊版只接 DataError 與 KeyboardInterrupt,所以上面這兩句
    在壞檔上並不成立 —— 一個被截斷的 QFS 串流會讓 qfs_decompress() 丟 IndexError,
    當場噴一整串堆疊訊息、結束碼是 1(實測)。下面補了一段把那一族收進結束碼 2。
    """
    EPILOG = (
        "\n這是實驗用的工具。順序:\n\n"
        "  1. 先預覽(不會動到任何東西)\n"
        "     python3 mvp_unpack_big.py \"<遊戲資料夾>/data/datafile/datafile.big\"\n\n"
        "  2. 真的解開,並把封裝檔改名藏起來\n"
        "     python3 mvp_unpack_big.py \"<...>/datafile.big\" --apply\n\n"
        "  3. 開遊戲。進得去 = 引擎真的會讀散裝檔。\n\n"
        "  4. 還原(封裝檔改回來)\n"
        "     python3 mvp_unpack_big.py \"<...>/datafile.big\" --restore\n"
        "     想連解出來的散裝檔一起清掉再加 --clean\n"
    )
    ap = argparse.ArgumentParser(
        description='把封裝檔解成資料夾(實驗性:驗證引擎會不會讀散裝檔)',
        formatter_class=argparse.RawDescriptionHelpFormatter, epilog=EPILOG)
    ap.add_argument('bigfile', help='要解開的 .big(或還原時給它的備份檔)')
    ap.add_argument('--apply', action='store_true', help='真的解開(沒加就只是預覽)')
    ap.add_argument('--restore', action='store_true', help='把封裝檔改回來')
    ap.add_argument('--clean', action='store_true', help='還原時一併刪掉當初解出來的散裝檔')
    args = ap.parse_args()

    try:
        if args.restore:
            cmd_restore(args.bigfile, args.clean)
        else:
            cmd_plan(args.bigfile, args.apply)
    except DataError as e:
        print('\n  停下來了:%s\n' % e)
        print(cleanup_hint(), end='')
        return 2
    except KeyboardInterrupt:
        # ⚠️ 這裡以前只印「已中斷。」四個字,那等於沒說 ——
        #    中斷可能落在「還沒動任何東西」,也可能落在「封裝檔已經改名藏起來了」,
        #    而後者不還原的話遊戲就少了一個封裝檔。cleanup_hint() 照實說是哪一種。
        print('\n  已中斷(你按了 Ctrl-C)。')
        print(cleanup_hint(), end='')
        return 130
    except (IndexError, struct.error, OSError) as e:
        # 壞掉或被截斷的 QFS 串流,會在 qfs_decompress() 去讀控制碼後面那幾個位元組時
        # 丟 IndexError(實測:短檔頭 + 一個 0x00 控制碼就重現得出來);
        # 磁碟寫滿或資料夾沒有寫入權限,則會在寫散裝檔的時候丟 OSError
        # (本課的 datafile.big 解出來會膨脹將近五倍,寫滿不是罕見狀況)。
        # struct.error 是同一族的「資料長度不夠」,一併收在這裡。
        # 沒有這一段的話,讀者看到的是一長串堆疊訊息,結束碼還是 1,
        # 跟上面說好的三種對不上。
        print('\n  停下來了:讀寫或解壓時出錯(%s:%s)。\n'
              '  這個封裝檔可能已經損毀,或磁碟空間不足、資料夾沒有寫入權限。\n'
              % (type(e).__name__, e))
        print(cleanup_hint(), end='')
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())

#
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
