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
#    各管道要不要帳號寫在那一頁。管道有變動只會改那一頁。
# ─────────────────────────────────────────────────────────

"""mvp_fingerprint.py — 幫一份遊戲資料夾算「指紋」,用來確認你我量的是同一份東西

本站每一個數字都寫著「量到的」。但「量到的」有一個前提:
**你要知道我量的是哪一份檔案。**同一個檔名在不同的模組包裡可以差 2,200 倍(測試機 ingame.big 孤兒 92.590% 對原版 0.04234%,比值 2,187)。

這支腳本產生一份可以貼出來比對的指紋:

    · 檔數與總位元組數
    · 清單雜湊 —— 把「相對路徑 + 大小」排序後整串算一次 SHA-256
      (只看結構與大小,不讀內容,所以幾 GB 也很快)
    · 錨點檔的 SHA-256 —— 幾個關鍵檔案逐位元組的雜湊

清單雜湊一樣 = 檔案結構與大小完全相同。
錨點雜湊也一樣 = 那幾個檔的內容也逐位元組相同。

用法:
    python mvp_fingerprint.py "<遊戲資料夾>"
    python mvp_fingerprint.py "<資料夾>" --all      # 每個檔都算 SHA-256(慢)
    python mvp_fingerprint.py "<資料夾>" --show-full-paths   # 連完整路徑一起印
    python mvp_fingerprint.py --selftest            # 自我測試,不需要遊戲

量指紋的時候不會修改任何檔案。唯一會寫檔的是 --selftest:
它在系統的暫存資料夾裡造一份自己的假資料來測,跑完就刪掉,不會碰到你的遊戲。

── 輸入 ─────────────────────────────────────────────
  一個路徑,指到「裡面有 data 資料夾」的那一層。
  指錯層不會報錯,但六個錨點會一個都找不到,腳本會提醒你這件事。
  加 --all 就每個檔都算一次 SHA-256,幾 GB 的資料夾要跑很久。
  加 --show-full-paths 才會印出完整路徑;預設不印,理由見下面「輸出」。

── 輸出 ─────────────────────────────────────────────
  只印到畫面,不產生任何檔案:
    · 資料夾的**名稱**、檔數、總位元組數(順便換算成 GB)
    · 清單雜湊,完整 64 個十六進位字元
    · 六個錨點檔各自的 SHA-256 前 32 碼與大小
    · 加了 --all 才有的逐檔清單(每個檔印雜湊前 16 碼)
    · 有東西讀不到時,會印出一段警告與那些路徑(見下面的結束碼 1)
  這份輸出是拿來貼給別人比對的,所以預設**不印完整路徑**:
  完整路徑裡常常有你的 Windows 使用者名稱、Mac 帳號名稱或磁碟布局。
  資料夾只印最後一層的名稱,讀不到的項目只印相對於它的路徑;
  給錯路徑時的錯誤訊息也一樣:只說找不到、或說那是一個檔案,不把你給的路徑印回來。
  路徑有空白卻沒用雙引號包起來、被拆成好幾段時,多出來的那幾段同樣不印。
  選項後面多接了東西(例如把路徑接在 --all= 後面)、選項名稱只打一半這類
  參數錯誤,也只印用法與一段中文說明,你打的那一串一樣不印回來。
  真的要完整路徑再加 --show-full-paths —— 那份輸出就不要直接公開。
  把輸出導到檔案(例如 > 指紋.txt)時,Python 在 Windows 繁體中文版上用的是 cp950,
  而 cp950 存不下 ⚠️ 這類符號:存不下的字會換成問號,不會印到一半就中斷。
  (本站是在 Mac 上用 PYTHONIOENCODING=cp950 模擬的,還沒在 Windows 上實測。)
  結束碼:0 = 跑完了,
         1 = 跑完了,但有檔案或資料夾讀不到,這份指紋不完整,不要拿去比對,
         2 = 給的路徑不是資料夾(參數本身給錯、或是根本沒給,也是 2;
             路徑被空白拆成好幾段、多出參數、選項後面多接了東西,也是 2;
             在 python3 -O 底下跑 --selftest 也是 2 —— 見下面「安全網在哪」),
       130 = 你自己按了 Ctrl-C。它只讀不寫,所以中途停掉什麼都不會少。

── 安全網在哪 ───────────────────────────────────────
  量指紋的那條路上只開檔案來讀,而且是唯讀的二進位模式('rb'):
  沒有寫入、沒有刪除、沒有搬移,也不連網。
  整支腳本裡唯一寫檔的地方在 selftest() 裡面,那是 --selftest 專用的:
  它用 tempfile 在系統暫存資料夾造一份自己的假遊戲資料夾,測完自己刪掉。
  --selftest 在 python3 -O 底下會直接拒跑(結束碼 2):那個旗標會把 assert
  整段拿掉,而且不會傳給自我測試另開的那幾個程序,所以在 -O 底下看到的綠燈,
  量的不是你這一次跑的條件。
  你給的那個路徑,不管加什麼旗標都只會被讀。
  錨點檔如果是符號連結會直接跳過不讀:它可能指到這個資料夾外面的東西,
  把外面那個檔的雜湊印出來既沒有意義,也可能洩漏不相干的資訊。
  這跟上面清單雜湊跳過所有符號連結是同一個理由。
  它的用途正是「動手之前留下一份可以回頭比對的紀錄」,所以本身不動任何東西。

── 做不到的事 ───────────────────────────────────────
  · 清單雜湊看不出「內容改了而大小沒變」。那正是還要算錨點檔逐位元組雜湊的原因。
  · 錨點雜湊只涵蓋那六個檔,其他檔一樣不一樣它不知道。要全部就得加 --all。
  · 兩份指紋不一樣時,它自己不會告訴你差在哪一個檔。要找出那一個,
    得兩邊都加 --all 各存一份輸出,再自己拿去比對。
  · 印出來的錨點雜湊只有前 32 個十六進位字元(前 16 個位元組)。
    那足夠拿來比對兩份安裝,不足以拿去做任何安全性主張。
  · 遮蔽只管本站這一支印出來的東西。你自己在終端機裡打的那一行指令
    仍然含完整路徑,截圖或複製整個視窗時會一起帶出去,那不是它擋得掉的。

MIT License · Copyright (c) 2026 toni · 無外部相依,Python 3.7 以上
"""
TOOL_DATE = '2026-09-24'  # 這一版工具的日期

import argparse
import hashlib
import os
import sys

# 錨點:挑「幾乎每一份都有、而且模組會動到」的檔。
# 少一個不算錯,腳本會標「沒有這個檔」。
ANCHORS = [
    'mvp2005.exe',
    'data/frontend/ingame.big',
    'data/frontend/frontend.big',
    'data/database/attrib.dat',
    'data/fonts/fonts.big',
    'data/models.big',
]

# 作業系統自己產生的檔。它們有沒有出現跟遊戲無關,
# 算進去會讓兩份其實一模一樣的安裝算出不同的指紋。
SKIP_NAMES = {'.DS_Store', 'Thumbs.db', 'desktop.ini'}

# --selftest 的餌 6 會自己再開一個程序來驗「-O 底下要拒跑」。
# 這個環境變數是那個子程序身上的記號,用途只有一個:別再往下開一層。
# 平常跑的時候不會有人設它,所以對讀者完全沒有影響。
NESTED_ENV = 'MVP_FINGERPRINT_NESTED_SELFTEST'


def walk(root):
    """回傳 (清單, 讀不到的路徑)。清單是 [(相對路徑, 大小), ...],已排序。

    跳過三類東西:作業系統自己產生的垃圾檔、所有以點開頭的檔案與資料夾、
    以及所有符號連結。這三類都不進雜湊,所以兩份只差在這些東西的資料夾,
    算出來的指紋會完全相同。

    第二個回傳值是「想看卻看不到」的路徑(權限不足,或是掃描途中檔案不見了)。
    這種東西不可以默默丟掉:少算一個檔,清單雜湊就整個不一樣,
    而這支腳本唯一的用途正是拿那個雜湊來比對。呼叫端負責把它印出來。

    底下每一道處理都是為了同一件事:讓兩台不同的電腦掃同一份資料夾時,
    產生的清單要逐字相同。差一個字,雜湊就完全不一樣,比對就失去意義。
    """
    out = []
    bad = []

    def note(err):
        # os.walk 預設把「進不去這個資料夾」整個吞掉,連錯誤都不丟出來。
        # 給了 onerror 才收得到 —— 否則整個子樹會無聲無息地從清單裡消失,
        # 而畫面上算出來的雜湊看起來完全正常。
        bad.append(getattr(err, 'filename', None) or str(err))

    for d, dirs, fs in os.walk(root, onerror=note):
        # 就地改寫 dirs 才會讓 os.walk 不要走進去,指派給別的名字沒有用。
        dirs[:] = [x for x in dirs if not x.startswith('.')]
        for f in fs:
            if f in SKIP_NAMES or f.startswith('.'):
                continue
            p = os.path.join(d, f)
            # 符號連結跳過:它指到的東西可能在這個資料夾外面,
            # 而它自己的大小是連結的大小,拿來當內容的指紋沒有意義。
            if os.path.islink(p):
                continue
            try:
                # 把路徑分隔符統一成斜線。Windows 用反斜線,Mac 與 Linux 用斜線,
                # 不統一的話同一份資料夾在兩台機器上會算出兩個不同的雜湊。
                # 這一行是這支腳本能跨平台比對的關鍵。
                out.append((os.path.relpath(p, root).replace(os.sep, '/'),
                            os.path.getsize(p)))
            except OSError:
                # 讀不到大小(權限不足,或是掃描途中被刪掉、被搬走)就記下來,
                # 最後一起講。斷掉的符號連結不會走到這裡,上面 islink 就擋掉了。
                # 不可以靜靜跳過:那會算出一個看起來正常、其實少了東西的雜湊。
                bad.append(p)
    # 一定要排序:os.walk 走檔案的順序跟檔案系統有關,
    # 不排序的話同一份資料夾在兩台機器上一樣會算出不同的雜湊。
    out.sort()
    bad.sort()
    return out, bad


def sha256_file(p, chunk=1 << 20):
    """逐位元組算一個檔的 SHA-256。1 << 20 = 1048576,也就是一次讀 1 MB。"""
    h = hashlib.sha256()
    # 'rb' 是二進位唯讀模式。不能用文字模式:那會在 Windows 上
    # 把 0x0D 0x0A 併成 0x0A,算出來的就不是檔案真正的內容了。
    with open(p, 'rb') as f:
        # 分塊讀是為了 models.big 這種上百 MB 的檔:
        # 一次讀完要吃掉跟檔案一樣多的記憶體,分塊讀只佔 1 MB。
        while True:
            b = f.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def show(p, root, full):
    """把一個路徑變成「可以貼出來」的樣子:預設只留相對於 root 的那一段。

    這支腳本的輸出本來就是要貼給別人比對的,而完整路徑常常含
    Windows 使用者名稱、Mac 帳號名稱、外接碟的名字。那些跟指紋無關。

    full=True(--show-full-paths)才原樣印出。
    算不出相對路徑,或算出來會跑到 root 外面(以 .. 開頭、或 Windows 上
    根本是另一顆磁碟機所以 relpath 直接丟 ValueError),就整個遮掉 ——
    寧可少講,也不要在自己也不確定的情況下把一段路徑印出去。
    os.walk 的 onerror 偶爾會給一段錯誤訊息而不是路徑,那種也走這一條。
    """
    if full:
        return p
    try:
        rel = os.path.relpath(p, root)
    except (ValueError, TypeError):
        rel = None
    if rel and not os.path.isabs(rel) and \
            rel != os.pardir and not rel.startswith(os.pardir + os.sep):
        return rel.replace(os.sep, '/')
    return '(不在這個資料夾底下,已遮蔽;加 --show-full-paths 才會印出來)'


def selftest():
    """--selftest:自己造一份假的遊戲資料夾來測,完全不碰你的遊戲。

    這支腳本唯讀,所以測的是另外兩件事:
      · 遮蔽真的有遮到 —— 預設輸出裡不可以出現完整路徑
      · 唯讀真的是唯讀 —— 跑完之後那份資料夾要一個位元組都沒變

    三十道檢查,其中二十四道是餌(故意做一件「防線壞掉就會被印出來」的事):
      餌 1(1 道)把資料夾放在一層叫 ZZ_pretend_username 的路徑底下,
            預設輸出裡出現那個字就是漏了。
      餌 2(2 道)反向:加了 --show-full-paths 就**必須**印得出完整路徑,
            資料夾那一行與讀不到的清單兩邊都要。少了這一組,
            「整行根本沒印」或「遮蔽永遠生效」也會讓餌 1 通過。
      餌 3(3 道)種一個讀不到的子資料夾,它的路徑同樣要被遮成相對路徑,
            而且結束碼要是 1(不完整的指紋不可以看起來像正常的)。
      餌 4(2 道)把錨點 mvp2005.exe 做成指到資料夾外面的符號連結,
            外面那個檔的雜湊不可以出現在輸出裡。
      餌 5(2 道)直接餵一個資料夾外面的路徑給 show(),它要整段遮掉;
            加了旗標則要原樣印出來。這一條在正常的資料夾上碰不到,
            所以只能這樣驗。
      餌 6(2 道)在 python3 -O 底下跑一次 --selftest,它必須拒跑(結束碼 2)
            而且說清楚為什麼。守門被拆掉的話,-O 那一次會一路綠燈跑完,
            這兩道就會紅。(這一次本身就是上一層開的那個子程序時,
            這一組會照實說是略過 —— 不然會一層開一層停不下來。)
      餌 7(3 道)給三種不存在的路徑:Mac 的 /Users/…、Windows 的 C 槽 Users 底下、
            中間有空白的。結束碼要是 2、要說「找不到」,
            而且錯誤訊息裡不可以出現路徑裡那段假名字。
      餌 8(2 道)路徑指到一個檔案(不是資料夾);以及含空白的路徑沒加引號、
            被拆成兩段。兩種都要結束碼 2、要說清楚是哪一種錯,
            而且路徑裡的假名字一個都不可以印出來。
      餌 9(2 道)反向:加了 --show-full-paths,找不到的那條路徑、
            被拆開的那一段都**必須**原樣印出來。少了這一組,
            「錯誤訊息整行沒印」也會讓餌 7、餌 8 通過。
      餌 10(1 道)同一道 -O 守門,改在這個程序裡驗:把 _optimize_level
            暫時換成「回傳 1」再叫一次自我測試,它必須拒跑(結束碼 2)。
            餌 6 在「這一次是上一層開的」時會略過,這一道不會。
            (2026-09-24 加。這一道不是另開程序,是這個程序自己再叫一次。)
      餌 11(2 道)argparse 自己先擋下來的參數錯誤:把假路徑接在 --all= 後面、
            選項只打一半(--s=,同時對得上兩個選項)。結束碼要是 2、
            要說「參數有錯」,而且假名字一個都不可以印出來。(2026-09-24 加)
      餌 12(1 道)反向:同一個錯誤加了 --show-full-paths,就**必須**照原樣印出來。
            少了這一道,「錯誤訊息整段沒印」也會讓餌 11 通過。(2026-09-24 加)
      餌 13(1 道)子程序改用 cp1252 輸出(連中文都存不下的編碼)量同一份資料夾,
            必須跑完:結束碼跟正常那一次一樣、清單雜湊印得出來、沒有 Traceback。
            這是「輸出導到檔案、編碼存不下某些字」那條路。(2026-09-24 加)
    另外六道是一般斷言:資料夾名稱有印出來(擋住餌 1 假通過)、
    加旗標不會改到結束碼、遮蔽沒有動到清單雜湊本身、
    跑完之後那份資料夾一個位元組都沒變、
    餌 10 換回原本那一支之後守門照樣放行(餌 10 的陰性對照)、
    沒給路徑時自己寫的那句提醒照樣印得出來(餌 11 的陰性對照:攔截不可以連它一起吞掉)。
    做不出「讀不到的資料夾」的機器(以系統管理員身分跑、或 Windows)
    會少掉餌 3 那一組 4 道,畫面上會照實說是略過,不會假裝測過。
    餌 7 那三條假路徑萬一在這台機器上真的存在,那一道也照實說是略過。

    測試自己是另開一個 Python 程序跑真的命令列,不是呼叫內部函式 ——
    要驗的就是「讀者打那一行下去看到什麼」。餌 5 與餌 10 那四道是例外(見上面)。
    另開的程序一律明寫用 UTF-8 輸出(餌 13 除外):不寫的話,Windows 繁體中文版上
    子程序會用 cp950 輸出,而這裡用 UTF-8 解,中文比對全部對不上 ——
    那是測試自己的問題,不是腳本壞了(2026-09-24 在 Mac 上用 PYTHONIOENCODING=cp950
    模擬過,Windows 上還沒實測)。
    """
    # -O 會把 assert 整段拿掉。這一支的判斷句不是用 assert 寫的(是下面那個
    # need()),但守門照樣要有:-O 不會傳給自我測試另開的那幾個程序
    # (這台機器上量過:父程序 sys.flags.optimize 是 1,子程序是 0),
    # 所以 -O 底下跑出來的綠燈,量的不是讀者這一次跑的條件。
    if _optimize_level():
        print('  --selftest 不能在 python3 -O 底下跑:-O 會把 assert 整段拿掉,'
              '而且它不會傳給自我測試另開的那幾個程序 —— '
              '量到的不是你這一次跑的條件,綠燈不算數。請拿掉 -O 再跑一次。')
        return 2
    # 這一行要緊接在守門後面:_optimize_bait() 的陰性對照靠它收工(見那個函式)。
    _opt = _optimize_bait(selftest)

    import shutil
    import subprocess
    import tempfile

    script = os.path.abspath(__file__)
    if not os.path.isfile(script):
        # 只印檔名:完整路徑裡常常有帳號名稱,跟主程式那條錯誤訊息同一個理由。
        print('  自我測試要用到腳本檔本身,但找不到:%s' % os.path.basename(script))
        return 1

    def child_env(enc='utf-8'):
        """子程序的環境:明寫輸出編碼。

        不寫的話,子程序接管線時用的是系統語系的編碼(Windows 繁體中文是 cp950),
        而這裡是用 UTF-8 解它的輸出 —— 兩邊對不上,中文比對全部落空。
        2026-09-24 在 Mac 上模擬過(只讓子程序用 PYTHONIOENCODING=cp950,這裡照樣用 UTF-8 解):
        這一版 30 道裡 12 道因此變紅,全是這裡解碼對不上 —— 腳本本身沒壞,
        子程序那邊有 main() 開頭那段處理,不會印到一半中斷。
        餌 13 會另外傳別的編碼進來,驗的是另一件事。
        """
        env = dict(os.environ)
        env['PYTHONIOENCODING'] = enc
        return env

    def cli(*extra, **kw):
        """跑一次真的命令列,回傳 (結束碼, 畫面上的字)。

        enc= 是子程序輸出用的編碼,只有餌 13 會改它。"""
        enc = kw.get('enc', 'utf-8')
        pr = subprocess.Popen([sys.executable, script] + list(extra),
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                              env=child_env(enc))
        raw = pr.communicate()[0]
        return pr.returncode, raw.decode(enc, 'replace')

    def cli_opt(*extra):
        """同上,但加 -O 跑。專門用來驗「-O 底下要拒跑」那一道守門。

        順手放一個環境變數告訴子程序「你是我開的,不要再往下開一層」。
        守門正常的時候子程序第一行就停住了,根本用不到這個煞車;
        它是給「哪天有人把守門拿掉」那種情況用的 —— 沒有它,
        那一次會一層開一層停不下來。
        """
        env = child_env()
        env[NESTED_ENV] = '1'
        pr = subprocess.Popen([sys.executable, '-O', script] + list(extra),
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                              env=env)
        raw = pr.communicate()[0]
        return pr.returncode, raw.decode('utf-8', 'replace')

    def snapshot(d):
        """(相對路徑, 大小, 內容雜湊) 的清單,用來證明跑完什麼都沒變。"""
        got, _bad = walk(d)
        return [(rel, sz, sha256_file(os.path.join(d, rel)))
                for rel, sz in got]

    base = tempfile.mkdtemp(prefix='mvp_fingerprint_selftest_')
    canary = 'ZZ_pretend_username'          # 餌 1:假裝這是使用者名稱那一層
    locked = None
    try:
        root = os.path.join(base, canary, 'MVP Baseball 2005')
        os.makedirs(os.path.join(root, 'data', 'database'))
        with open(os.path.join(root, 'data', 'database', 'attrib.dat'), 'wb') as f:
            f.write(b'attrib' * 8)

        # 餌 4:資料夾外面的一個檔,拿錨點的檔名做成符號連結指過去。
        outside = os.path.join(base, 'outside_not_the_game.bin')
        with open(outside, 'wb') as f:
            f.write(b'this file is outside the game folder' * 4)
        secret = sha256_file(outside)[:32]
        os.symlink(outside, os.path.join(root, 'mvp2005.exe'))

        # 餌 3:一個進不去的子資料夾。有些系統(以系統管理員身分跑、
        # 或是 Windows)做不出這種東西,那一道就照實說「這台機器上做不出來」,
        # 不要假裝測過。
        locked = os.path.join(root, 'data', 'locked')
        os.makedirs(locked)
        with open(os.path.join(locked, 'inside.bin'), 'wb') as f:
            f.write(b'x' * 4)
        os.chmod(locked, 0)
        try:
            os.listdir(locked)
            blocked = False
        except OSError:
            blocked = True

        before = snapshot(root)

        rc, out = cli(root)
        rc_full, out_full = cli(root, '--show-full-paths')

        fails = []
        skips = []
        done = [0, 0]        # [總道數, 其中是餌的道數]

        def need(ok, why, bait=True):
            """記一道檢查。ok 是假的就把理由收起來,最後一起印。

            bait=True 代表這一道是「防線壞掉就會亮」的餌;
            bait=False 是一般斷言(用來擋住餌自己失效而沒人發現)。
            """
            done[0] += 1
            if bait:
                done[1] += 1
            if not ok:
                fails.append(why)

        # 餌 1:完整路徑不可以出現在預設輸出裡
        need(canary not in out and base not in out,
             '餌 1:預設輸出裡出現了完整路徑')
        # 資料夾名稱要印得出來 —— 不然餌 1 會因為「整行根本沒印」而假通過
        need('MVP Baseball 2005' in out,
             '預設輸出裡連資料夾名稱都沒有', bait=False)
        # 餌 2(反向):加了旗標就**必須**印得出完整路徑,兩個地方都要。
        # 只看「資料夾」那一行,不要拿整段輸出去比對(理由見 _line)。
        need((_line(out_full, '資料夾') or '').find(os.path.abspath(root)) >= 0,
             '餌 2:加了 --show-full-paths 還是印不出資料夾的完整路徑')
        # 餌 3:讀不到的項目也要遮蔽,而且結束碼要是 1
        if blocked:
            need('data/locked' in out, '餌 3:讀不到的項目沒有印出相對路徑')
            need(canary not in out, '餌 3:讀不到的項目把完整路徑漏出去了')
            need(rc == 1, '餌 3:有東西讀不到,結束碼卻是 %s(應該是 1)' % rc)
            need((_line(out_full, 'locked') or '')
                 .find(os.path.abspath(locked)) >= 0,
                 '餌 2:加了 --show-full-paths,讀不到的項目還是被遮著')
        else:
            skips.append('餌 3 那一組 4 道(這台機器做不出「讀不到的資料夾」)')
        # 餌 4:符號連結錨點要跳過,外面那個檔的雜湊不可以出現
        need('是符號連結' in out, '餌 4:符號連結錨點沒有被標成跳過')
        need(secret not in out, '餌 4:把資料夾外面那個檔的雜湊印出來了')
        # 餌 5:資料夾外面的路徑要整段遮掉,不是印出來。
        # 這一條在正常的資料夾上碰不到(所以上面那幾道測不到它),
        # 直接餵一個外面的路徑給 show() 才驗得到。
        outsider = os.path.abspath(os.path.join(base, 'not_under_root'))
        need(os.path.abspath(root) not in show(outsider, root, False)
             and outsider not in show(outsider, root, False),
             '餌 5:資料夾外面的路徑沒有被遮掉')
        need(show(outsider, root, True) == outsider,
             '餌 5 反向:加了 --show-full-paths,外面的路徑也該原樣印出來')
        # 餌 6:在 python3 -O 底下跑 --selftest 要拒跑。守門拆掉的話
        # 那一次會一路綠燈跑完(結束碼 0),這兩道就會紅。
        if os.environ.get(NESTED_ENV):
            skips.append('餌 6 那一組 2 道(這一次是上一層開的,不再往下開)')
        else:
            rc_opt, out_opt = cli_opt('--selftest')
            need(rc_opt == 2,
                 '餌 6:python3 -O 底下跑 --selftest,結束碼是 %s'
                 '(應該是 2,要拒跑)' % rc_opt)
            need('-O' in out_opt,
                 '餌 6:python3 -O 底下拒跑了,卻沒有說清楚為什麼')
        # 餌 7:給錯路徑的錯誤訊息也不可以把路徑印回來。
        # 讀者最常把錯誤訊息整段複製去問人,而那正是路徑給錯的時候。
        # 三條都是不存在的路徑;路徑裡那段假名字就是「帳號名稱」的替身。
        # Windows 那條用 join 組出來,不直接寫成一整串:原始碼裡不要出現
        # 一條看起來像真實使用者路徑的字串(這支的原始碼整份貼在頁面上)。
        surname = 'ZZ_pretend_surname'
        pretend = [
            ('Mac 路徑', '/Users/%s/Games/MVP Baseball 2005' % canary, (canary,)),
            ('Windows 路徑',
             '\\'.join(('C:', 'Users', canary, 'Games', 'MVP Baseball 2005')),
             (canary,)),
            ('含空白的路徑',
             '/Users/%s %s/Games/MVP Baseball 2005' % (canary, surname),
             (canary, surname)),
        ]
        first_missing = None
        for label, bad_path, secret_names in pretend:
            if os.path.exists(bad_path):
                skips.append('餌 7 的「%s」那一道(這條假路徑在這台機器上真的存在)'
                             % label)
                continue
            if first_missing is None:
                first_missing = bad_path
            rc7, out7 = cli(bad_path)
            if rc7 != 2:
                why7 = '結束碼是 %s(應該是 2)' % rc7
            elif '找不到' not in out7:
                why7 = '沒有說「找不到」'
            elif any(s in out7 for s in secret_names):
                why7 = '錯誤訊息把你給的路徑印出來了'
            else:
                why7 = None
            need(why7 is None, '餌 7(%s):%s' % (label, why7))
        # 餌 8:路徑指到一個檔案,不是資料夾。用上面已經造好的 attrib.dat,
        # 不另外造檔 —— 自我測試寫的東西越少越好。
        a_file = os.path.join(root, 'data', 'database', 'attrib.dat')
        rc8, out8 = cli(a_file)
        if rc8 != 2:
            why8 = '結束碼是 %s(應該是 2)' % rc8
        elif '檔案' not in out8:
            why8 = '沒有說那是一個檔案'
        elif canary in out8 or base in out8:
            why8 = '錯誤訊息把你給的路徑印出來了'
        else:
            why8 = None
        need(why8 is None, '餌 8(路徑指到檔案):%s' % why8)
        # 餌 8 之二:含空白的路徑沒加引號,被拆成兩段。多出來的那一段也不可以印。
        split_a = '/Users/%s' % canary
        split_b = '%s/Games/MVP Baseball 2005' % surname
        rc8b, out8b = cli(split_a, split_b)
        if rc8b != 2:
            why8b = '結束碼是 %s(應該是 2)' % rc8b
        elif '引號' not in out8b:
            why8b = '沒有提醒要用引號把路徑包起來'
        elif canary in out8b or surname in out8b:
            why8b = '把拆開的那幾段印出來了'
        else:
            why8b = None
        need(why8b is None, '餌 8(路徑被空白拆成兩段):%s' % why8b)
        # 餌 9(反向):加了旗標就**必須**原樣印出來。
        # 不然「錯誤訊息整行沒印」也會讓餌 7、餌 8 通過。
        if first_missing is None:
            skips.append('餌 9 的第一道(餌 7 那三條假路徑在這台機器上都存在)')
        else:
            _rc9, out9 = cli(first_missing, '--show-full-paths')
            need(first_missing in out9,
                 '餌 9:加了 --show-full-paths,找不到的那條路徑還是沒印出來')
        _rc9b, out9b = cli(split_a, split_b, '--show-full-paths')
        need(split_b in out9b,
             '餌 9:加了 --show-full-paths,被拆開的那一段還是沒印出來')
        # 遮蔽只動顯示,不可以動到結束碼,也不可以動到算出來的值
        need(rc == rc_full,
             '加了 --show-full-paths 之後結束碼變了', bait=False)
        need(_line(out, '清單雜湊') is not None
             and _line(out, '清單雜湊') == _line(out_full, '清單雜湊'),
             '遮蔽改到了清單雜湊本身', bait=False)
        # 唯讀:跑完之後那份資料夾一個位元組都沒變
        need(snapshot(root) == before,
             '跑完之後資料夾的內容變了 —— 它應該只讀不寫', bait=False)
        # 餌 10:同一道 -O 守門,改在這個程序裡驗(結果是開頭 _optimize_bait() 量的)。
        # 餌 6 在子程序才有,這一次若是上一層開的就略過;這一組每一次都跑得到。
        need(_opt[0], '餌 10:假裝開了 -O,--selftest 竟然沒有拒跑')
        need(_opt[1], '餌 10 陰性對照:沒開 -O 的時候守門也擋了下來,'
             '或是換回原本那一支沒換成功', bait=False)
        # 餌 11:argparse 自己先擋下來的參數錯誤,也不可以把讀者打的字印回來(2026-09-24 加)。
        # 兩種寫法各一道:路徑接在 --all= 後面、選項只打一半(--s= 同時對得上兩個選項)。
        # 這兩種在 main() 的遮蔽之前就結束了,餌 7、餌 8 都碰不到。
        arg_baits = [
            ('--all=', '--all=/Users/%s %s/Games' % (canary, surname)),
            ('--s=', '--s=/Users/%s %s/Games' % (canary, surname)),
        ]
        for label, bad_arg in arg_baits:
            rc11, out11 = cli(bad_arg)
            if rc11 != 2:
                why11 = '結束碼是 %s(應該是 2)' % rc11
            elif '參數有錯' not in out11:
                why11 = '沒有說是參數有錯'
            elif canary in out11 or surname in out11:
                why11 = '把你打的那一串印出來了'
            else:
                why11 = None
            need(why11 is None, '餌 11(%s):%s' % (label, why11))
        # 餌 12(反向):加了 --show-full-paths 就**必須**照原樣印出來。
        # 不然「錯誤訊息整段沒印」也會讓餌 11 通過。
        _rc12, out12 = cli(arg_baits[0][1], '--show-full-paths')
        need(canary in out12 and surname in out12,
             '餌 12:加了 --show-full-paths,參數錯誤還是沒把收到的內容印出來')
        # 陰性對照:我們自己寫的那一句(沒給路徑)照樣要印得出來,
        # 不可以被上面那道攔截一起吞掉。
        rc_np, out_np = cli()
        need(rc_np == 2 and '請給一個資料夾路徑' in out_np,
             '沒給路徑時,自己寫的那句提醒不見了(結束碼 %s)' % rc_np, bait=False)
        # 餌 13:輸出的編碼存不下某些字時,不可以印到一半就中斷(2026-09-24 加)。
        # 子程序改用 cp1252 輸出(西歐語系 Windows 用的編碼,連中文都存不下),
        # 量同一份資料夾。main() 開頭那道處理拿掉的話,第二行就會丟 UnicodeEncodeError、
        # 結束碼變 1、清單雜湊那一行印不出來。
        rc13, out13 = cli(root, enc='cp1252')
        hash_line = _line(out, '清單雜湊') or ''
        manifest13 = hash_line.split()[-1] if hash_line.split() else ''
        if 'Traceback' in out13:
            why13 = '丟出了一整段 Python 錯誤訊息'
        elif len(manifest13) != 64 or manifest13 not in out13:
            why13 = '清單雜湊那一行沒印出來'
        elif rc13 != rc:
            why13 = '結束碼是 %s(正常那一次是 %s)' % (rc13, rc)
        else:
            why13 = None
        need(why13 is None, '餌 13:輸出編碼存不下某些字時印到一半就停了 —— %s' % why13)

        for line in fails:
            print('  ❌ %s' % line)
        for line in skips:
            print('  ⚠️ 略過 %s' % line)
        if fails:
            print('自我測試:%d 道沒過(共 %d 道)' % (len(fails), done[0]))
            return 1
        print('自我測試:全部通過(%d 道檢查,其中 %d 道是餌%s)'
              % (done[0], done[1],
                 '' if not skips else ';另有 %d 組在這台機器上做不出來,'
                 '上面標了' % len(skips)))
        return 0
    finally:
        # 收尾:先把權限改回來,不然自己造的那個資料夾刪不掉。
        if locked and os.path.isdir(locked):
            try:
                os.chmod(locked, 0o700)
            except OSError:
                pass
        shutil.rmtree(base, ignore_errors=True)


def _line(out, key):
    """從輸出裡撈含某個字的第一行。自我測試專用。

    要一整行、不能用整段輸出去搜:2026-09-05 這一支就被這件事騙過 ——
    「資料夾那一行印了完整路徑嗎」拿整段輸出去比對,
    結果比中的是下面「讀不到的清單」裡那個更長的路徑,
    防線已經被拆掉了,測試還是綠的。
    """
    for line in out.splitlines():
        if key in line:
            return line.strip()
    return None


class _QuietParser(argparse.ArgumentParser):
    """argparse 自己擋下來的參數錯誤,預設也不把讀者打的那一串印回來。

    argparse 在把參數交給 main() 之前,會先自己擋掉幾種錯,而它的錯誤訊息
    會把讀者打的字原樣印出來。例如把路徑接在 --all= 後面,它印
    「argument --all: ignored explicit argument '/Users/〔名〕 〔姓〕/…'」;
    選項只打了一半又接了東西(--s=…),它印「ambiguous option: --s=… could match …」。
    這些都發生在 parse_known_args() 回傳之前,main() 裡的遮蔽接不到,所以在這裡攔。
    (2026-09-24 補:在這之前,這類寫法會把讀者打的那一串整段印出來。)

    做法是 argparse 那一句整句不印,只印用法與一段中文。不去猜它哪一段是讀者打的 ——
    argparse 換一版,訊息的樣子就可能不一樣,猜錯就漏。
    加了 --show-full-paths(一字不差)才照 argparse 原本的樣子印,跟其他錯誤訊息同一個規則。
    """

    def error(self, message):
        if '--show-full-paths' in sys.argv[1:]:
            argparse.ArgumentParser.error(self, message)
        self.print_usage(sys.stderr)
        self.exit(2, '\n'.join((
            '',
            '  參數有錯,這支看不懂你打的那一串。',
            '  最常見的原因:選項後面多接了東西(例如 --all=…),或選項名稱只打了一半。',
            '  這支只認得 --all、--show-full-paths、--selftest,三個後面都不接任何東西;',
            '  路徑請整條用雙引號包起來。',
            '  (為了不把帳號名稱印出來,這裡不重複你打的內容;'
            '要看它收到的是什麼,加 --show-full-paths。)',
            '', '')))

    def error_own(self, message):
        """我們自己寫好的錯誤訊息(裡面沒有讀者打的字),照 argparse 原本的樣子印。"""
        argparse.ArgumentParser.error(self, message)


def main():
    """算完指紋印出來:資料夾摘要、清單雜湊、錨點雜湊,以及選配的逐檔清單。"""
    # 輸出導到檔案或接管線時,Windows 上的 Python 用系統語系的編碼寫(繁體中文是 cp950),
    # 而 ⚠️ ❌ ✅ 這幾個 cp950 沒有 —— 不處理的話,印到那一行就丟 UnicodeEncodeError
    # 並以 1 結束,只留下半截輸出(2026-09-24 在 Mac 上用 PYTHONIOENCODING=cp950 重現過,
    # Windows 上還沒實測)。
    # 這裡不換編碼,只把「編不出來的那個字」換成問號,中文照舊。
    # 直接看主控台的人不受影響(Python 3.6 起,Windows 主控台走 UTF-16 的寫法)。
    try:
        sys.stdout.reconfigure(errors='replace')
    except (AttributeError, ValueError):
        pass
    ap = _QuietParser(
        description='幫一份遊戲資料夾算指紋,用來確認大家量的是同一份',
        epilog='量指紋時只讀不寫;--selftest 只在系統暫存資料夾造自己的假資料。')
    ap.add_argument('path', nargs='?', help='要量的資料夾')
    ap.add_argument('--all', action='store_true',
                    help='每個檔都算 SHA-256（很慢,通常不需要）')
    ap.add_argument('--show-full-paths', action='store_true',
                    help='連完整路徑一起印（預設只印資料夾名稱與相對路徑）')
    ap.add_argument('--selftest', action='store_true',
                    help='自我測試（不需要遊戲資料夾,不會碰到你的檔案）')
    # 用 parse_known_args 而不是 parse_args:多出來的參數要自己接。
    # 最常見的來源是路徑裡有空白卻沒加引號,一條路徑被拆成好幾段 ——
    # 交給 argparse 的話,它會用英文把多出來的那幾段原樣印出來,
    # 而那幾段通常就是帳號名稱的後半截(例如 /Users/〔名〕 〔姓〕/… 被拆開之後的「〔姓〕/…」)。
    # argparse 自己先擋下來的那幾種錯,不會走到這裡,是 _QuietParser 在攔。
    args, extra = ap.parse_known_args()

    if extra:
        # 回 2:跟 argparse 自己遇到多餘參數時用的結束碼一樣。
        print()
        print('  參數多了 %d 個。最常見的原因是路徑裡有空白卻沒用雙引號包起來,'
              % len(extra))
        print('  一條路徑被拆成了好幾段。請把整條路徑用雙引號包起來再跑一次。')
        if any(x.startswith('-') for x in extra):
            print('  也可能是選項打錯了:這支只認得 --all、--show-full-paths、--selftest。')
        if args.show_full_paths:
            for x in extra:
                print('     多出來的:%s' % x)
        else:
            # 預設不印那幾段:它們是路徑的一部分,常常就是帳號名稱。
            print('  (為了不把帳號名稱印出來,這裡不重複那幾段;'
                  '要看它們是什麼,加 --show-full-paths。)')
        print()
        return 2

    if args.selftest:
        return selftest()

    root = args.path
    if root is None:
        # 少給路徑跟給錯路徑一樣算「參數有錯」,argparse 自己也是用 2。
        # 這一句是我們自己寫的,裡面沒有讀者打的字,所以走 error_own 照原樣印。
        ap.error_own('請給一個資料夾路徑（或用 --selftest 自我測試）')
    if not os.path.isdir(root):
        # 這裡回 2 不是 1:argparse 自己在參數有錯時用的也是 2,
        # 這樣「參數給錯了」跟「跑完但結果不如預期」在批次檔裡分得開。
        # 預設不把路徑印回來:路徑給錯正是讀者最會把錯誤訊息整段貼出去問人的時候,
        # 而完整路徑裡常常有帳號名稱 —— 檔頭說明裡「預設不印完整路徑」那句話
        # 也要涵蓋這一條。讀者知道自己打了什麼,不需要我們複誦。
        # 存在卻不是資料夾,幾乎都是指到了檔案(例如直接把 mvp2005.exe 拖進來)。
        not_a_dir = os.path.exists(root)
        print()
        if args.show_full_paths:
            if not_a_dir:
                print('  這是一個檔案,不是資料夾:%s' % root)
            else:
                print('  找不到資料夾:%s' % root)
        else:
            if not_a_dir:
                print('  你給的路徑是一個檔案,不是資料夾。')
            else:
                print('  找不到你給的那個資料夾。')
            print('  (為了不把帳號名稱印出來,這裡不重複你給的路徑;'
                  '要看它收到的是什麼,加 --show-full-paths。)')
        print('  要指到「裡面有 data 資料夾」的那一層。')
        print()
        return 2

    files, unreadable = walk(root)
    total = sum(sz for _, sz in files)

    # 清單雜湊:每個檔一行「相對路徑 空格 大小」,用換行接成一整串,再算一次 SHA-256。
    # 只看結構與大小,完全不讀內容,所以幾 GB 的資料夾也只要幾秒。
    # 多一個檔、少一個檔、任何一個檔的大小變了,這個值就整個不一樣;
    # 但「內容改了而大小剛好沒變」它看不出來,那要靠底下的錨點雜湊。
    # 編碼明寫 UTF-8:中文檔名要先轉成位元組才算得了雜湊,
    # 寫出來是為了讓讀的人不必去查預設值是什麼。
    lines = ('%s %d' % (rel, sz) for rel, sz in files)
    manifest = hashlib.sha256('\n'.join(lines).encode('utf-8')).hexdigest()

    print()
    if args.show_full_paths:
        print('  資料夾   %s' % os.path.abspath(root))
    else:
        # 完整路徑裡常常有帳號名稱,而這份輸出的用途正是貼給別人看。
        # 只印最後一層:比對指紋用不到上面那幾層。
        full_root = os.path.abspath(root)
        print('  資料夾   %s' % (os.path.basename(full_root) or full_root))
        print('           ↑ 只印名稱。完整路徑可能含你的帳號名稱,'
              '要的話加 --show-full-paths。')
    print('  檔數     %s' % '{:,}'.format(len(files)))
    # 1073741824 = 1024 的三次方。這裡的 GB 是 2 的次方那一種,
    # 不是 10 的九次方那一種,兩種算出來的數字不一樣。
    print('  總大小   %s bytes（%.2f GB）' % ('{:,}'.format(total), total / 1073741824.0))
    print('  清單雜湊 %s' % manifest)
    print('           ↑ 路徑與大小排序後的 SHA-256。一樣 = 結構與大小完全相同。')
    if unreadable:
        # 這一段是整支腳本最重要的安全網。讀不到的東西沒有進上面那個雜湊,
        # 所以算出來的值跟「全部都讀得到」時不會一樣 —— 而它看起來完全正常。
        # 不印出來的話,讀者會把權限問題誤判成「我裝了模組」。
        print()
        print('  ⚠️ 有 %s 個檔案或資料夾讀不到(多半是權限不足):'
              % '{:,}'.format(len(unreadable)))
        for p in unreadable[:10]:
            print('       %s' % show(p, root, args.show_full_paths))
        if len(unreadable) > 10:
            print('       ...(還有 %s 個沒列出來)'
                  % '{:,}'.format(len(unreadable) - 10))
        print('     它們沒有算進上面的清單雜湊。這份指紋是不完整的,不要拿去比對。')
    print()
    print('  錨點檔的 SHA-256:')
    found = 0
    for rel in ANCHORS:
        # ANCHORS 裡一律寫斜線。這裡拆開再用本機的分隔符接回去,
        # 同一份清單在 Windows 上才找得到檔。
        p = os.path.join(root, *rel.split('/'))
        # 符號連結直接跳過,理由跟 walk() 裡那一段一樣:它可能指到這個
        # 資料夾外面,把外面那個檔的雜湊印出來既不是這份安裝的指紋,
        # 也等於把不相干的東西寫進一份要貼出來的輸出裡。
        # 要用 islink 不能用 exists:斷掉的符號連結 exists 是 False。
        if os.path.islink(p):
            print('    %-30s（是符號連結,跳過）' % rel)
            continue
        if not os.path.isfile(p):
            # 少一個錨點不算錯,照樣往下跑:有人只裝了部分內容,那也是一種指紋。
            print('    %-30s（沒有這個檔）' % rel)
            continue
        try:
            # 只印前 32 個十六進位字元(等於前 16 個位元組)。
            # 拿來比對兩份安裝夠用,而且一行放得下。
            digest = sha256_file(p)[:32]
            size = os.path.getsize(p)
        except OSError:
            # 檔在,但打不開(權限不足、外接碟中途拔掉)。沒攔的話這裡會丟出
            # 一整段 Python 錯誤訊息就結束 —— 對這一站的讀者來說那太嚇人了。
            print('    %-30s（讀不到,跳過）' % rel)
            unreadable.append(p)
            continue
        print('    %-30s %s  %s bytes' % (rel, digest, '{:,}'.format(size)))
        found += 1
    # 六個全都沒找到,幾乎一定是路徑指錯層(最常見的是已經指進 data 裡面了)。
    # 這種時候上面那個清單雜湊算出來仍然是有效的,但它量的不是一份遊戲安裝。
    if not found:
        print('    一個錨點都沒找到 —— 路徑是不是指錯了?'
              '要指到「裡面有 data 資料夾」的那一層。')
    print()

    # --all 會把每個檔都完整讀過一遍,幾 GB 的資料夾要跑很久,所以預設不做。
    # 它的用途是:兩台機器各存一份輸出,自己拿去逐行比對,找出差在哪一個檔。
    if args.all:
        print('  逐檔 SHA-256（%s 個）:' % '{:,}'.format(len(files)))
        for rel, sz in files:
            # rel 已經是斜線形式,而 Windows 的 os.path.join 也吃斜線,直接接得起來。
            p = os.path.join(root, rel)
            try:
                # 前 16 碼夠用來逐行掃過去,找出不一樣的那一列。
                digest = sha256_file(p)[:16]
            except OSError:
                # 走到這裡代表「大小讀得到、內容讀不到」。原本沒攔,整支腳本
                # 會在半截的清單上中斷,而前面已經印出來的部分看起來是好的。
                print('    %-16s  %-11s %s  （讀不到,跳過）' % ('-' * 16, sz, rel))
                unreadable.append(p)
                continue
            print('    %s  %-11s %s' % (digest, sz, rel))
        print()

    if unreadable:
        # 有東西讀不到 = 這份指紋不完整。結束碼跟「順利跑完」分開,
        # 批次檔跟後面的步驟才有辦法發現這件事,而不是拿一個錯的雜湊去比對。
        return 1
    return 0


# ─────────────────────────────────────────────────────────
#  「-O 拒跑」那道守門的餌(2026-09-24 加)
#
#  自我測試一開頭有一道守門:在 python -O 底下拒跑(-O 會把 assert 整段拿掉,
#  測試會變成一片假的綠燈)。這支的守門原本就有餌:自我測試的餌 6 另外開一個
#  python3 -O 的程序跑 --selftest,它必須拒跑。但餌 6 在「這一次本身就是上一層
#  開的子程序」時會略過,而守門原本直接問 sys.flags.optimize —— 那是唯讀的,
#  同一個程序裡沒辦法把 -O 打開又關掉。現在守門改問 _optimize_level(),
#  自我測試就能在同一個程序裡暫時把它換掉,再驗一次(餌 10,附陰性對照)。
# ─────────────────────────────────────────────────────────
def _optimize_level():
    """python 的 -O 等級:沒加 -O 是 0,加 -O 是 1,加 -OO 是 2。"""
    return sys.flags.optimize


class _OptGuardPassed(Exception):
    """_optimize_bait() 用的記號:再叫一次自我測試時,守門放行、走到了下一行。"""


def _optimize_bait(selftest_fn):
    """-O 守門的餌與陰性對照。回傳 (餌被擋下來了, 陰性對照被放行了)。

    自我測試在守門的下一行就叫這一支,這一支再叫兩次 selftest_fn(輸出收起來不印):
      · 餌:先把 _optimize_level 換成「回傳 1」(假裝開了 -O)。那一次必須在守門
        那裡就停下來 —— 結束碼 2,而且印出來的那句話提到 -O。
      · 陰性對照:換回原本那一支之後再叫一次,守門必須放行。放行之後的下一行
        就是這裡,所以那一次會丟出 _OptGuardPassed 立刻收工 ——
        不會把整套自我測試再跑一遍,也不會在磁碟上留下任何東西。
    守門被拆掉的話,餌那一次也會一路走到這裡、丟出 _OptGuardPassed,就算沒擋下來。
    """
    if getattr(_optimize_bait, 'busy', False):
        raise _OptGuardPassed()
    import contextlib
    import io
    global _optimize_level
    real = _optimize_level

    def once():
        buf = io.StringIO()
        try:
            with contextlib.redirect_stdout(buf):
                rc = selftest_fn()
        except SystemExit as e:
            rc = e.code
        except _OptGuardPassed:
            rc = '放行'
        except Exception as e:
            rc = '例外 %r' % (e,)
        return rc, buf.getvalue()

    _optimize_bait.busy = True
    try:
        _optimize_level = lambda: 1
        try:
            rc, said = once()
        finally:
            _optimize_level = real
        rc2, _said2 = once()
    finally:
        _optimize_bait.busy = False
    bait = rc == 2 and '-O' in said
    neg = rc2 == '放行' and _optimize_level is real and _optimize_level() == 0
    return bait, neg


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        # 中途按 Ctrl-C。這支從頭到尾只開檔案來讀,所以這句話是說得死的:
        # 什麼都沒有動到。但還是要印出來 —— 不然畫面上只會留下一整段
        # Python 的錯誤訊息,對這一站的讀者來說那看起來像「我把東西弄壞了」。
        # 結束碼 130 是慣例(128 加上 SIGINT 的 2),跟「順利跑完」分得開。
        print('\n  中斷了。這支只讀不寫,你的檔案一個位元組都沒有動到。')
        sys.exit(130)


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
