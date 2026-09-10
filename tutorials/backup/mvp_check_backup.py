#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
mvp_check_backup.py
檢查 EA MVP Baseball 2005 的備份狀況。

    python3 mvp_check_backup.py "遊戲安裝資料夾"
    python3 mvp_check_backup.py "遊戲安裝資料夾" "你的外部備份資料夾"
    python3 mvp_check_backup.py --selftest

例如:
    python3 mvp_check_backup.py "C:\\Program Files (x86)\\EA SPORTS\\MVP Baseball 2005"

這支腳本**全程唯讀**,不會建立、修改或刪除任何檔案。它只回答四個問題:

  1. 本站教學會動到的檔案,在不在?多大?什麼時候改的?
  2. 這些檔案旁邊有沒有工具自動建立的備份?
  3. 那些備份跟現在的檔案一不一樣(還原後應該一樣)?
  4. 給了外部備份資料夾的話,那份備份跟現在的檔案差在哪?

吃什麼(輸入)
  · 第一個參數:遊戲安裝資料夾,也就是同時看得到 data 這個子資料夾和 .exe 的那一層。
    拖一個檔進來(mvp2005.exe 或 controller.cfg)也可以,腳本會自己往上一層走。
  · 第二個參數(可以不給):你自己放備份的那個資料夾。
    保留原本的資料夾結構、或把檔案全部平放在同一層,兩種擺法都認得。

吐什麼(輸出)
  · 只有畫面上那四段報告。你的遊戲資料夾與備份資料夾裡沒有任何檔案被建立、
    修改或刪除,對它們唯一的開檔動作是比對用的兩個唯讀 'rb'。
  · 唯一的例外是 --selftest:它在系統暫存資料夾裡建自己的測試檔來驗證下面
    那幾道檢查真的會亮,跑完自己刪掉,全程不碰你的遊戲資料夾。
  · 回傳值:0 = 檢查完了(或自我測試全綠);
    1 = 參數不對、那個資料夾裡一個目標檔都找不到,或自我測試沒過;
    2 = 掃描途中讀取出錯(外接碟斷線、檔案被別的程式鎖住),
        或是在 python3 -O 底下跑 --selftest —— 它會拒跑。
        「測試沒跑」跟「測試沒過」是兩回事,所以不跟 1 混在一起;
        「碟不見了」跟「路徑打錯了」也是兩回事,所以也不跟 1 混在一起;
    130 = 你按了 Ctrl-C。

安全網
  · 唯讀是唯一的模式:沒有 --apply,也沒有還原功能。要還原請照
    「備份與還原 SOP」自己把檔案複製回去,這支只負責告訴你複製對了沒有。
  · 「一不一樣」是**逐位元組**比出來的,不是比大小、也不是比時間。
    大小不同才提早結束,大小一樣就整個讀完才敢說一樣。
  · 一份「備份」如果其實就是正本本身(符號連結、硬連結,或把遊戲資料夾
    自己當成第二個參數),逐位元組比對必然說「一樣」。這種情形會被指名
    講出來,不會給你一個綠勾 —— 那個綠勾會害人放心去改檔。
  · 讀不出來的檔(權限不足、壞掉的連結)會照實說「讀不出來」,
    不會混進「不一樣」裡,也不會讓整份報告中途斷掉。
  · 中途按 Ctrl-C 就只是少印幾行:這支從頭到尾沒有開任何檔案來寫,
    也沒有搬移或刪除,所以停在哪裡都不會留下半截的東西。它會講一句話
    告訴你這件事,而不是丟一串 Python 的錯誤訊息給你自己猜。
  · 同一個檔有好幾份內容不同的備份時,會指出**最舊的那一份才是原廠檔**,
    因為每支工具只在第一次寫入前備份,晚一點的那幾份裡已經含著前一次的修改。

做不到的事
  · 只看本站教學會動到的那幾個檔,不是整包遊戲的完整清單。
    別的課動的檔(models.big / mvp2005.exe / 語音檔 …)不在表上,
    完整的做法還是整包備份。
  · 只認得「原檔名 + 備份副檔名」而且放在原檔旁邊的備份。
    你自己改過名字、或搬去別的資料夾的那些,它看不到(那不代表你沒備份)。
  · 不會判斷備份內容合不合理(例如中途斷掉的半截檔),
    它只回答「跟現在的檔一不一樣」。
  · controller.cfg 沒有任何本站工具會替它備份(暖身課是請你自己用記事本改),
    所以它旁邊永遠不會出現備份檔。畫面上會直接請你自己複製一份,
    不會把它寫成「哪一支工具漏了」。

無外部相依,Python 3.7 以上即可。
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

import io
import os
import sys
import time
from pathlib import Path

# Windows 主控台預設編碼存不下 ✓ ✗ 這類符號,先把輸出轉成 UTF-8。
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except (AttributeError, ValueError):
    pass

# ── 本站教學實際會寫入的檔案 ────────────────────────
# 逐篇讀教學內文與腳本的寫入點整理出來的。唯讀的那幾課(例如五秒看穿一個檔案、
# 遊戲當掉了怎麼辦)不寫任何檔案,所以不在這張表上。
# ⚠️ 這裡不寫「幾篇教學」的數字:本站每加一課它就過期,而且沒有人會回頭改它。
# 一筆 = (相對於遊戲資料夾的路徑, 這個檔是什麼, 會動到它的課)。
# 第三欄目前沒有印在畫面上,留著是為了改這張表的時候,看得出動它的是哪幾課。
# ⚠️ 第三欄只列「指名改這個檔」的課。「一整包模組自動歸位」與「把你改好的
#    東西打包成一包」是通用安裝器,它們可能寫進下面任何一個檔,不逐列重複寫。
TARGETS = [
    ('data/database/attrib.dat',   '球員資料',
     ['修改球員跑壘速度', '幫球員換一張臉', '換打擊姿勢與投球姿勢',
      '把一位球員改成你想要的球員', '把真實成績換算成遊戲裡的能力值']),
    ('data/database/pitcher.dat',  '投手資料',
     ['換打擊姿勢與投球姿勢', '把真實成績換算成遊戲裡的能力值']),
    ('data/database/schedule.big', '賽程表',
     ['把賽程換到任何年份']),
    ('data/frontend/ingame.big',   '比賽中的介面',
     ['關掉跑壘者速度數值', '介面實例集', '介面萬用工具', '改記分板的顏色']),
    ('controller.cfg',             '手把與鍵盤設定',
     ['暖身課:打開一個遊戲的檔案']),
]

# 玩過一次遊戲才會被建立的檔。沒有它不代表有問題。
# ⚠️ 這裡比對的是 TARGETS 第一欄那個字串本身,不是檔名。
#    哪天把上面那筆改成帶資料夾的寫法,這裡就對不上了,而且不會報錯,
#    只會讓一台剛裝好的機器被說「找不到 controller.cfg」。
BORN_ON_FIRST_RUN = {'controller.cfg'}

# 本站沒有任何腳本會自動備份它的檔。暖身課是請你用記事本手動改 controller.cfg,
# 沒有工具在旁邊留備份,所以【2】那一段對它**永遠**是「沒有備份」。
# ⚠️ 不要因為「消不掉」就把這一項藏起來 —— 沒備份就是沒備份,藏起來是幫倒忙。
#    要改的是措辭:講清楚該自己複製一份,而不是讓人以為哪一支工具漏了。
NO_TOOL_BACKUP = {'controller.cfg'}

# ⚠️ 這份清單漏一個,那一支工具留的備份就完全看不見,而且不會有任何提示。
#    守門的是 .tools/site-check/selftest_backup_suffixes.py,不是 verify_site.py
#    (那一支沒有這項檢查)。它把教學腳本字面寫出的備份副檔名跟這份清單對一次,
#    但配不到通用的 .bak,也跳過 pack-a-mod 與 backup 兩課,那幾種少了不會紅。
# ⚠️ 這份清單的長度會一直變(多一課會寫檔的教學通常就多一種),所以這裡
#    **不寫死「幾支、幾種」** —— 那種數字放兩天就過期,而且沒有人會回頭改。
#    要知道現在缺不缺,跑上面那支檢查器,它會把兩邊對一次。
#    歷史上補過兩次:2026-09-03 補 .exepebak(執行檔那一課),
#    2026-09-05 補 .introbak(關掉開場動畫那一課,2026-09-04 才進站)。
# ⚠️ 補進清單不等於畫面上看得到:.exepebak 留在 mvp2005.exe 旁邊、
#    .modernizebak 同理、.introbak 留在 movies 資料夾的 .vp6 影片旁邊,
#    那三個檔都不在上面的 TARGETS 裡,所以【2】那一段仍然不會列它們。
#    TARGETS 只認核心五個檔,這是刻意的。
#    清單的順序只決定畫面上列出來的先後,不影響任何判斷。
BAK_SUFFIXES = [
    '.bak', '.audiobak', '.autobak', '.chantbak', '.datafilebak',
    '.exepebak', '.facebak',
    '.facetexbak', '.feltoolbak', '.fontbak', '.hudcolorbak', '.introbak',
    '.locbak', '.modernizebak',
    '.logobak', '.menutextbak', '.packbak', '.playerbak', '.portraitbak', '.ratingsbak',
    '.screenbak',
    '.shrinkbak', '.speedbak', '.unibak', '.unpackbak',
]

# 哪一支工具會留下哪一個備份檔。同一個 .bak 副檔名在不同檔案上是
# 不同工具留的,所以要連檔名一起看,不能只看副檔名。
# 鍵是 (原檔名, 備份副檔名) 的組合。查得到就能在畫面上寫出「這份是哪一課建立的」,
# 查不到就誠實說不知道,不要冒認成本站的工具。
BAK_OWNER = {
    ('attrib.dat',   '.bak'):        '換打擊姿勢與投球姿勢',
    ('attrib.dat',   '.speedbak'):   '修改球員跑壘速度',
    ('attrib.dat',   '.facebak'):    '幫球員換一張臉',
    ('pitcher.dat',  '.bak'):        '換打擊姿勢與投球姿勢',
    ('schedule.big', '.bak'):        '把賽程換到任何年份',
    ('ingame.big',   '.bak'):        '關掉跑壘者速度數值',
    ('ingame.big',   '.feltoolbak'): '介面萬用工具 fel_toolkit',
}

# 上面那張表處理的是「同一個副檔名出現在不同檔案上」的情形（只有 .bak 這樣）。
# 其餘每一個副檔名都只屬於一支工具，看副檔名就知道是誰留的。
BAK_OWNER_BY_SUFFIX = {
    '.audiobak':     '換掉遊戲的聲音',
    '.autobak':      '一整包模組自動歸位',
    '.chantbak':     '把應援曲指給別的球員',
    '.datafilebak':  '介面萬用工具 fel_toolkit',
    '.exepebak':     '執行檔上的六個旋鈕',
    '.facebak':      '幫球員換一張臉',
    '.facetexbak':   '做一張新的球員臉皮',
    '.feltoolbak':   '介面萬用工具 fel_toolkit',
    '.fontbak':      '中文版配大球場就跳出',
    '.locbak':       '中文版配大球場就跳出',
    '.modernizebak': '2026 年的電腦怎麼跑得起 2005 年的遊戲',
    '.hudcolorbak':  '改記分板的顏色',
    '.introbak':     '關掉開場動畫',
    '.logobak':      '換球隊隊徽',
    '.menutextbak':  '改主選單的文字',
    '.packbak':      '把你改好的東西打包成一包（安裝前留的）',
    '.playerbak':    '把一位球員改成你想要的球員',
    '.portraitbak':  '換球員大頭照',
    '.ratingsbak':   '把真實成績換算成遊戲裡的能力值',
    '.screenbak':    '換掉開機畫面',
    '.shrinkbak':    '球場超過 10MB 就當機',
    '.speedbak':     '修改球員跑壘速度',
    '.unibak':       '把一套球衣裝進遊戲',
    '.unpackbak':    '封裝檔可以拆成散裝嗎',
}


def human(n):
    """把位元組數寫成人看得懂的樣子。

    1024 以下直接講 bytes:對「這個檔多大」這種問題,342 bytes 比 0.3 KB 好懂。
    到 GB 就停住不再往上換,遊戲檔不會大到需要更上面的單位。
    None 是「大小讀不出來」,不是 0 —— 印成 0 bytes 會讓人以為那個檔是空的。
    """
    if n is None:
        return '(讀不到)'
    if n < 1024:
        return '%d bytes' % n
    for unit in ('KB', 'MB', 'GB'):
        n /= 1024.0
        if n < 1024 or unit == 'GB':
            return '%.1f %s' % (n, unit)
    return '%.1f GB' % n


def size_of(path):
    """檔案大小;讀不到就回 None(權限不足、剛好被刪掉、壞掉的連結)。

    這支是在別人的機器上跑的,拿不到大小是常態不是例外。原本直接 .stat()
    會讓整份報告在中途噴 traceback,後面幾段就都看不到了。
    """
    try:
        return path.stat().st_size
    except OSError:
        return None


def when(path):
    """這個檔上次被改的時間,只到分鐘;讀不到就照實說。"""
    # 只顯示到分鐘。秒數對判斷「哪一份比較舊」沒有幫助,
    # 卻會把這台機器的活動時間精確地印出來。
    try:
        return time.strftime('%Y-%m-%d %H:%M',
                             time.localtime(path.stat().st_mtime))
    except OSError:
        return '(讀不到)'


def mtime_of(path):
    """排序用的修改時間;讀不到就當成無限新。

    「最舊的那一份才是原廠檔」是要印給人看的結論,挑錯了會害人還原到
    已經改過的版本。讀不到時間的那一份寧可排到最後,也不要被誤選成最舊。
    """
    try:
        return path.stat().st_mtime
    except OSError:
        return float('inf')


def same_file(a, b):
    """兩個路徑是不是「同一個檔」(符號連結、硬連結,或根本同一條路徑)。

    ⚠️ 這是這支腳本能犯的最嚴重的錯:一份「備份」如果其實就是正本本身,
       逐位元組比對必然回 True,畫面上就出現一個綠勾,讀者於是放心去改檔 ——
       而那一刻備份跟著一起被改掉,等到要還原才發現什麼都沒有。
       實測兩種踩法,加這道檢查之前兩種都印綠勾:
         (1) 把遊戲資料夾自己當成第二個參數(外部備份 = 遊戲本身);
         (2) ln -s attrib.dat attrib.dat.speedbak(備份指回正本)。
    """
    try:
        return os.path.samefile(str(a), str(b))
    except OSError:
        return False


def same_bytes(a, b, chunk=1 << 20):
    """兩個檔案內容是否完全相同。大小不同就直接回 False,不必整個讀。

    一次讀 1 MB(1 << 20)兩邊對一段,不把整個檔吃進記憶體:
    這張表上的 ingame.big 在本站的測試機上是 2.5 MB,沒有必要整個吃進來。
    兩邊同時讀到空字串,代表一起走到檔尾,那才回 True。

    回三種值不是兩種:True 一樣 / False 不一樣 / None 讀不出來。
    ⚠️ None 不可以當成 False —— 「讀不到」跟「不一樣」是兩件事,混為一談
       會讓人去追一個根本不存在的差異;而原本沒有 None 這一種的時候,
       一個 chmod 000 的備份檔會讓整份報告當場 traceback 斷在半路。
    """
    try:
        # 先比大小是為了快,不是為了省事:大小不同就一定不一樣,連開檔都不必。
        if a.stat().st_size != b.stat().st_size:
            return False
        # 全程 'rb'。這是檢查你的檔案時唯一的開檔動作,而且兩個都是唯讀。
        with open(a, 'rb') as fa, open(b, 'rb') as fb:
            while True:
                x = fa.read(chunk)
                y = fb.read(chunk)
                if x != y:
                    return False
                if not x:
                    return True
    except OSError:
        return None


def _run_capture(argv):
    """跑一次 main(),把畫面上的字接起來回傳。只有自我測試用得到。"""
    import contextlib
    import traceback
    buf = io.StringIO()
    saved = sys.argv
    sys.argv = argv
    try:
        with contextlib.redirect_stdout(buf):
            code = main()
    except Exception:
        # 噴例外本身就是一種失敗,但不可以連帶把後面幾個餌一起帶走 ——
        # 那會讓人以為只壞了一件事。回一個不可能的代碼,讓 check 去報。
        return 99, buf.getvalue() + '\n' + traceback.format_exc()
    finally:
        sys.argv = saved
    return code, buf.getvalue()


def _run_cli(argv):
    """跑一次 cli()(不是 main()),把畫面上的字接起來回傳。只有自我測試用得到。

    ⚠️ 為什麼不共用上面那支:那支叫的是 main(),而 Ctrl-C 與「掃描途中讀取
       出錯」這兩條路是外面的 cli() 接的。用 _run_capture 去測,cli() 的兩個
       except 一次都不會執行 —— 餌會綠,而綠的理由是它根本沒測到那道守門。
    ⚠️ 這裡接的是 BaseException 不是 Exception:Ctrl-C 丟的 KeyboardInterrupt
       不是 Exception 的子類。cli() 的守門哪天被拿掉,例外會從這裡浮上來;
       接住它,那個餌才會紅掉,而不是把整份自我測試一起帶走。
    """
    import contextlib
    import traceback
    buf = io.StringIO()
    saved = sys.argv
    sys.argv = argv
    try:
        with contextlib.redirect_stdout(buf):
            code = cli()
    except BaseException:
        return 99, buf.getvalue() + '\n' + traceback.format_exc()
    finally:
        sys.argv = saved
    return code, buf.getvalue()


def self_test():
    """種餌自我測試:每一道守門各放一個餌,抓不到就紅。

    為什麼要有:下面這幾道檢查(備份其實是正本本身 / 指不到東西的連結 /
    讀不出來 / 備份放在遊戲資料夾裡面)都是「沒事的時候完全不出聲」的那種。
    沒有餌的話,它們壞掉跟正常運作在畫面上長得一模一樣 —— 本站踩過這個坑。
    每一個餌都先確認「不下餌時不會亮」,再確認「下了餌一定亮」。

    ⚠️ 全程在系統暫存資料夾裡建自己的測試檔,跑完自己刪掉,
       不碰你的遊戲資料夾。這是整支腳本唯一會寫檔的地方。

    ⚠️ 在 python3 -O 底下不跑,直接以結束碼 2 收工(不回傳 True/False)。
    """
    # ⚠️ python3 -O 會把整份程式裡的 assert 整段拿掉。本站別支工具的自我測試是
    #    用 assert 判斷的,在 -O 底下那些餌一條都不會執行,螢幕上卻照樣一路 ✅ ——
    #    那是一片假的綠燈,比沒有測試更危險。
    #    這一支目前用的是下面那個 check() 不是 assert,所以 -O 還不會讓它假綠;
    #    擋掉是為了跟全站的自我測試一致,而且哪天這裡改寫成 assert,守門已經在了,
    #    不必指望那時候有人記得補。
    #    這裡直接結束整支程式,不回傳 True/False ——「測試沒跑」跟「測試沒過」
    #    是兩回事,用 1(有一項紅了)會把它們混在一起。
    if sys.flags.optimize:
        print('--selftest 不能在 python3 -O 底下跑:-O 會把 assert 整段拿掉,'
              '哪天這裡改用 assert 判斷就會變成一片假的綠燈。請拿掉 -O 再跑一次。')
        sys.exit(2)
    import shutil
    import tempfile

    print('自我測試(在系統暫存資料夾裡跑,不碰你的遊戲資料夾)')
    ok = [True]

    def check(label, cond, out=''):
        print('   %s %s' % ('✅' if cond else '❌', label))
        if not cond:
            ok[0] = False
            print('      實際印出來的是:')
            for line in out.strip().splitlines()[-12:]:
                print('      | %s' % line)

    def link(target, path):
        """做一個符號連結;這台機器不給做就回 False(Windows 常見)。"""
        try:
            os.symlink(target, path)
            return True
        except (OSError, NotImplementedError, AttributeError):
            return False

    td = tempfile.mkdtemp(prefix='mvp_check_backup_selftest_')
    try:
        root = os.path.join(td, 'game')
        vault = os.path.join(td, 'vault')
        rels = ['data/database/attrib.dat', 'data/database/pitcher.dat',
                'data/database/schedule.big', 'data/frontend/ingame.big']
        for d in ('data/database', 'data/frontend'):
            os.makedirs(os.path.join(root, *d.split('/')))
        os.makedirs(vault)
        for i, rel in enumerate(rels):
            with open(os.path.join(root, *rel.split('/')), 'wb') as f:
                f.write(bytes(bytearray([65 + i])) * (4096 + i))
            shutil.copy2(os.path.join(root, *rel.split('/')),
                         os.path.join(vault, os.path.basename(rel)))

        # 陰性對照:乾淨的一份必須全綠。它紅了,後面的餌抓到也不算數。
        code, out = _run_capture(['mvp_check_backup.py', root, vault])
        check('陰性對照:乾淨的資料夾 + 真的另一份備份 = 沒有紅字',
              code == 0 and '涵蓋全部' in out and '值得注意' not in out, out)

        db = os.path.join(root, 'data', 'database')
        att = os.path.join(db, 'attrib.dat')

        # 餌一:一份是真的複本、一份是指回正本的連結。兩者必須被分開講。
        shutil.copy2(att, att + '.facebak')
        if link('attrib.dat', att + '.speedbak'):
            code, out = _run_capture(['mvp_check_backup.py', root])
            check('餌一:指回正本的「備份」被指名,真的複本仍然說一樣',
                  '就是正本本身' in out and '跟現在的檔案一樣' in out, out)
            os.remove(att + '.speedbak')
        else:
            print('   ⏭ 餌一:這台機器不給做符號連結,略過')
        os.remove(att + '.facebak')

        # 餌二:名字在、卻指不到東西的備份,不可以在畫面上消失成「沒有備份」。
        pit = os.path.join(db, 'pitcher.dat')
        if link(os.path.join(td, 'nowhere.dat'), pit + '.bak'):
            code, out = _run_capture(['mvp_check_backup.py', root])
            check('餌二:指不到東西的備份會被指名,不會被當成沒有備份',
                  '指不到東西的連結' in out, out)
            os.remove(pit + '.bak')
        else:
            print('   ⏭ 餌二:這台機器不給做符號連結,略過')

        # 餌三:讀不出來的備份要照實說,而且整份報告不可以斷在半路。
        sch = os.path.join(db, 'schedule.big')
        shutil.copy2(sch, sch + '.bak')
        os.chmod(sch + '.bak', 0)
        readable = True
        try:
            with open(sch + '.bak', 'rb') as f:
                f.read(1)
        except OSError:
            readable = False
        # readable=True 代表「chmod 0 之後還是讀得到」(root、或不吃權限的
        # 檔案系統)。那種機器上餌三、餌七都測不到東西,誠實略過,不要假綠。
        if readable:
            print('   ⏭ 餌三:這裡的權限擋不住讀取(root 或該檔案系統),略過')
        else:
            code, out = _run_capture(['mvp_check_backup.py', root])
            # ⚠️ 餌要下在正確的地方:只驗「有沒有出現『讀不出來』」是抓不到
            #    「把 None 當成不一樣」這個寫法的 —— 那時候備註欄照樣會寫
            #    讀不出來。所以連「不可以說成內容不同」一起驗。
            check('餌三:讀不出來的備份照實說,沒被講成內容不同,報告也沒斷',
                  code == 0
                  and '讀不出來(權限不足或檔案有問題)' in out
                  and '跟現在的檔案不同' not in out
                  and '=' * 52 in out, out)
        os.chmod(sch + '.bak', 0o600)
        os.remove(sch + '.bak')

        # 餌四:備份資料夾放在遊戲資料夾裡面 —— 會跟遊戲一起消失。
        inner = os.path.join(root, 'backup')
        os.makedirs(inner)
        for rel in rels:
            shutil.copy2(os.path.join(root, *rel.split('/')),
                         os.path.join(inner, os.path.basename(rel)))
        code, out = _run_capture(['mvp_check_backup.py', root, inner])
        check('餌四:備份資料夾在遊戲資料夾裡面會被提醒',
              '在遊戲資料夾裡面' in out, out)
        shutil.rmtree(inner)

        # 餌五:把遊戲資料夾自己當成備份資料夾 —— 加這道檢查之前這裡全是綠勾。
        code, out = _run_capture(['mvp_check_backup.py', root, root])
        check('餌五:遊戲資料夾自己當備份時不會出現「涵蓋全部」',
              '就是遊戲裡的那個檔本身' in out and '涵蓋全部' not in out, out)

        # 餌六:【1】那一段的目標檔本身是壞掉的連結。
        cfg = os.path.join(root, 'controller.cfg')
        if link(os.path.join(td, 'nowhere.cfg'), cfg):
            code, out = _run_capture(['mvp_check_backup.py', root])
            check('餌六:目標檔是壞掉的連結時不會說成「還沒玩過遊戲」',
                  '這個名字在' in out and '玩過一次遊戲才會出現' not in out, out)
            os.remove(cfg)
        else:
            print('   ⏭ 餌六:這台機器不給做符號連結,略過')

        # 餌七:外部備份那一段也有同一組三態,要各自下餌 —— 【2】綠不代表【3】綠。
        if readable:
            print('   ⏭ 餌七:同上,權限擋不住讀取,略過')
        else:
            os.chmod(os.path.join(vault, 'attrib.dat'), 0)
            try:
                code, out = _run_capture(['mvp_check_backup.py', root, vault])
                check('餌七:外部備份讀不出來時不說成內容不同,也不說涵蓋全部',
                      code == 0
                      and '讀不出來(權限不足或檔案有問題)' in out
                      and '內容不同' not in out and '涵蓋全部' not in out, out)
            finally:
                os.chmod(os.path.join(vault, 'attrib.dat'), 0o600)

        # 餌八:同一個檔有兩份以上備份時,「讀不出來」不可以被算成「內容不同」。
        #       算錯的後果不是少講一句,是憑空多一句「最舊的那一份才是原廠檔」,
        #       把人指去還原一份它根本沒讀到的檔。先驗它該講的時候有講。
        shutil.copy2(att, att + '.bak')
        with open(att + '.speedbak', 'wb') as f:
            f.write(b'X' * 512)
        code, out = _run_capture(['mvp_check_backup.py', root])
        check('餌八(陽性對照):真的有兩份內容不同的備份時要講出來',
              '份內容不同的備份' in out, out)
        shutil.copy2(att, att + '.speedbak')      # 改成兩份一模一樣
        code, out = _run_capture(['mvp_check_backup.py', root])
        check('餌八(陰性對照):兩份一模一樣就不可以說成不同',
              '份內容不同的備份' not in out, out)
        os.chmod(att + '.speedbak', 0)
        if readable:
            print('   ⏭ 餌八:同上,權限擋不住讀取,略過最後一段')
        else:
            code, out = _run_capture(['mvp_check_backup.py', root])
            check('餌八:讀不出來的那一份不會被算成「內容不同的備份」',
                  '份內容不同的備份' not in out, out)
        os.chmod(att + '.speedbak', 0o600)
        os.remove(att + '.speedbak')
        os.remove(att + '.bak')

        # 餌九:報告跑到一半,某個檔剛好被別的程式刪掉/搬走(這是真的會發生的:
        #       雲端同步、防毒、另一支工具都可能在同一秒動它)。要製造這個時機
        #       需要兩個行程搶時間,所以這裡讓那個名字的 stat 在「問過一次之後」
        #       開始丟例外 —— 測的是「後面幾段還印不印得完」,不是 stat 本身。
        shutil.copy2(att, att + '.bak')
        with open(att + '.facebak', 'wb') as f:
            f.write(b'Y' * 512)
        shutil.copy2(att, att + '.playerbak')
        real_stat = Path.stat
        seen = [0]

        def flaky_stat(self, *a, **k):
            if self.name.endswith('.playerbak'):
                seen[0] += 1
                if seen[0] > 1:                 # 第一次還在,之後就不見了
                    raise OSError(2, 'no such file')
            return real_stat(self, *a, **k)

        Path.stat = flaky_stat
        try:
            code, out = _run_capture(['mvp_check_backup.py', root])
        finally:
            Path.stat = real_stat
        check('餌九:檔案在報告中途消失時,四段報告照樣印得完',
              code == 0 and '(讀不到)' in out and '=' * 52 in out, out)
        for s in ('.bak', '.facebak', '.playerbak'):
            os.remove(att + s)

        # 餌十:外部備份是完整的時候,結論不可以說「你也還沒有任何備份」——
        #       那句話跟【3】剛印的「涵蓋全部」在同一個畫面上互相打臉。
        code, out = _run_capture(['mvp_check_backup.py', root, vault])
        check('餌十:外部備份完整時,結論不會說「你也還沒有任何備份」',
              '涵蓋全部' in out and '你也還沒有任何備份' not in out, out)

        # ── 下面三道測的是 cli() 那兩道網,不是 main() 裡面的判斷 ──
        # 陰性對照要先跑:一道接得太寬的網,會把一次好好的檢查講成「讀取出錯」,
        # 而那種壞法在只有陽性餌的時候是全綠的。
        code, out = _run_cli(['mvp_check_backup.py', root, vault])
        check('餌十一(陰性對照):沒有中斷也沒有出錯時,cli() 照樣回 0',
              code == 0 and '涵蓋全部' in out
              and '已中止' not in out and '讀取途中出錯' not in out, out)

        # 餌十一:掃描途中按 Ctrl-C。這支全程唯讀,停在哪裡都不會留下半截的
        #        東西 —— 但它得把這句話講出來。加這道網之前,Ctrl-C 換來的是
        #        一整串 Python traceback(本站實測,結束碼一樣是 130),
        #        而讀者看到 traceback 的第一個念頭是「我把它弄壞了」。
        #        順便驗它不可以印出跑完才有的那句結論 —— 沒跑完就說跑完了,
        #        那是這道網最容易犯的錯。
        # ⚠️ 這裡用 raise 不用真的送 SIGINT:訊號由直譯器挑時機送達,寫成餌會
        #    偶爾落在別的地方,而偶爾紅一次的自我測試比沒有測試更難處理。
        #    真的送一次 SIGINT 的那一版另外測過,走的是同一條路,結果一樣。
        stat_before_ctrl_c = Path.stat

        def stat_ctrl_c(self, *a, **k):
            if self.name == 'ingame.big':       # 掃到第四個檔才中斷
                raise KeyboardInterrupt
            return stat_before_ctrl_c(self, *a, **k)

        Path.stat = stat_ctrl_c
        try:
            code, out = _run_cli(['mvp_check_backup.py', root])
        finally:
            Path.stat = stat_before_ctrl_c
        check('餌十一:掃描途中按 Ctrl-C 會講一句中文並以 130 收工,不噴 traceback',
              code == 130 and '已中止' in out and 'Traceback' not in out
              and '沒有建立、修改或刪除任何檔案' not in out, out)

        # 餌十二:掃描途中讀取出錯 —— 外接碟被拔掉、防毒把檔案鎖住、雲端同步
        #        把資料夾抽走,在這支唯讀的腳本上長成同一個樣子:某個呼叫丟
        #        OSError。size_of / when / mtime_of / same_bytes 這幾支自己
        #        接得住,但不是每一個呼叫都包得完,所以外面要有一道網。
        #        結束碼要跟「路徑打錯了」的 1 分開,不然批次檔判斷不出差別
        #        (本站實測:加這道網之前,兩種情形都是 1,而且都噴 traceback)。
        is_file_before_io_error = Path.is_file

        def is_file_io_error(self, *a, **k):
            if self.name == 'ingame.big':
                raise OSError(5, 'input/output error')
            return is_file_before_io_error(self, *a, **k)

        Path.is_file = is_file_io_error
        try:
            code, out = _run_cli(['mvp_check_backup.py', root])
        finally:
            Path.is_file = is_file_before_io_error
        check('餌十二:掃描途中讀取出錯會講一句中文並以 2 收工,不噴 traceback',
              code == 2 and '讀取途中出錯' in out and 'Traceback' not in out, out)

    finally:
        shutil.rmtree(td, ignore_errors=True)

    print('   %s 自我測試%s' % ('✅' if ok[0] else '❌',
                                '全部通過' if ok[0] else '沒過'))
    return ok[0]


def main():
    """照【1】到【4】的順序把四個問題各回答一次,全程唯讀,最後給一段結論。"""
    # --selftest 是這支唯一認得的旗標,而且它只在系統暫存資料夾裡跑,
    # 不碰你的遊戲資料夾。要放在濾掉旗標之前判斷,否則會被下一行吃掉。
    if '--selftest' in sys.argv[1:]:
        return 0 if self_test() else 1
    # 其餘 -- 開頭的東西濾掉:這支沒有 --apply 之類會動到檔案的旗標,
    # 但從別課複製指令過來的人很容易把字尾帶著。濾掉它,才不會被當成路徑。
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    # 沒給路徑就把檔頭那段說明當使用說明印出來。
    # 回傳 1 而不是 0:它沒有真的檢查過任何東西,不要讓外面誤判成「一切正常」。
    if not args:
        print(__doc__)
        return 1

    # 路徑常常是「把檔案拖進終端機」得到的,拖到的可能是 exe 或 .cfg,
    # 所以下面接受檔案,取它的上一層當遊戲資料夾。
    root = Path(args[0]).expanduser()
    if root.is_file():                       # 拖到 exe 或 .cfg 也接受
        root = root.parent
    if not root.is_dir():
        print('✗ 找不到這個資料夾:%s' % root)
        return 1

    vault = Path(args[1]).expanduser() if len(args) > 1 else None
    if vault is not None and not vault.is_dir():
        print('✗ 找不到你給的備份資料夾:%s' % vault)
        return 1

    print('遊戲資料夾  %s' % root)
    if vault:
        print('外部備份    %s' % vault)
    print('')

    # 一路收集「值得注意」的事,最後在【4】一次講完。
    # 邊走邊喊會讓畫面上的重點被四段報告沖散。
    notes = []

    # ── 1. 該備份哪些檔 ────────────────────────────────
    # 大小與修改時間都印出來,是為了讓你自己認得出「這個檔我上次動是什麼時候」。
    # 一份備份對不對得上某個時間點,只有你知道,腳本判斷不了。
    print('【1】本站教學會動到的檔案')
    total = 0
    present = []
    for rel, desc, lessons in TARGETS:
        p = root / rel
        if p.is_file():
            size = size_of(p)
            total += size or 0
            present.append((rel, p))
            print('  ✅ %-28s %12s  %s  %s'
                  % (rel, human(size), when(p), desc))
        else:
            print('  ✗  %-28s %12s  %-19s  %s'
                  % (rel, '(不存在)', '', desc))
            # is_file() 對「指向不存在的目標」的符號連結回 False,畫面上跟
            # 「真的沒有這個檔」長得一模一樣。用 lexists 把兩者分開:
            # 那個名字確實在,只是指向空的地方 —— 那是壞掉,不是沒有。
            if os.path.lexists(p):
                print('     ⚠ 這個名字在,但它是一個指不到東西的連結。')
                notes.append('%s 是一個指不到東西的連結' % rel)
            # ⚠️ controller.cfg 是玩過一次遊戲之後才會被建立的。
            #    一台剛安裝好、還沒玩過的機器沒有它是正常的,
            #    把它列成「值得注意」會讓第一次接觸的人以為自己裝壞了。
            elif rel in BORN_ON_FIRST_RUN:
                print('     (這個檔要玩過一次遊戲才會出現,現在沒有是正常的)')
            else:
                notes.append('找不到 %s' % rel)
    print('')
    print('  這 %d 個檔合計 %s(%s bytes)。'
          % (len(present), human(total), format(total, ',')))
    # ⚠️ 這裡不要寫「涵蓋 N 課裡的 M 課」。程式印出來的字最像事實,讀者不會
    #    去懷疑,而那兩個數字每加一課就過期。更不可以寫成「涵蓋所有會改檔的
    #    教學」——那是反方向的謊,照著做的人會以為備份好了,接著去跑換臉皮 /
    #    換球衣 / 改執行檔那幾課,而那些檔一份備份都沒有。
    print('  把它們複製到別的地方,只涵蓋上面列出的那幾課動的檔。')
    print('  ⚠️ 本站還有別的課動的是別的檔(models.big / datafile.big / mvp2005.exe /')
    print('     portrait.big / uniforms.big / fonts.big / .LOC / 語音檔 …),')
    print('     那些不在上面的清單裡。整包備份才是完整的做法,見「備份與還原 SOP」。')
    if not present:
        print('  一個都找不到 —— 你選的可能不是遊戲安裝資料夾。')
        print('  正確的資料夾裡面應該同時看得到 data 這個子資料夾和 .exe。')
        return 1

    # ── 2. 旁邊有沒有工具自動留的備份 ──────────────────
    # 本站的工具都把備份留在原檔旁邊、用「原檔名 + 備份副檔名」命名,
    # 所以只在同一個資料夾裡找,而且連原檔名一起比對:
    # 同一個 .bak 出現在不同檔案上,是不同的工具留的。
    print('\n【2】遊戲資料夾裡的備份檔')
    any_bak = False
    missing_bak = []
    for rel, p in present:
        cand = [p.parent / (p.name + s) for s in BAK_SUFFIXES]
        baks = [b for b in cand if b.is_file()]
        # 名字在、卻指不到東西的備份:is_file() 說 False,於是它在畫面上整個
        # 消失,讀者看到的是「沒有備份」。一個救不了你的名字擺在那裡,
        # 比沒有更危險 —— 所以要指名講出來。
        for b in [c for c in cand if not c.is_file() and os.path.lexists(c)]:
            print('  ⚠  %-28s 是一個指不到東西的連結,救不了你' % b.name)
            notes.append('%s 是一個指不到東西的連結,不是有效的備份' % b.name)
        if not baks:
            print('  ·  %-28s 沒有備份' % rel)
            if rel in NO_TOOL_BACKUP:
                print('     (本站沒有腳本會自動備份它 —— 請自己複製一份到別的地方)')
            # 先記著,最後再決定要不要算成「值得注意」——
            # 一台什麼都沒改過的機器本來就不該有備份,
            # 那不是問題,是還沒開始。
            missing_bak.append(rel)
            continue
        # 同一個檔可能被好幾支工具動過,每支各留自己那一份。全部列出來,
        # 因為「哪一份才是原廠檔」要靠時間先後判斷,少列一份就會挑錯。
        any_bak = True
        for b in baks:
            suffix = b.name[len(p.name):]
            if same_file(b, p):
                # 同一個檔:改正本的那一刻它跟著被改。這不是備份。
                mark, state = '⚠ ', '它就是正本本身,不是另一份'
                notes.append('%s 其實就是 %s 本身(同一個檔),不是備份'
                             % (b.name, p.name))
            else:
                eq = same_bytes(b, p)
                mark = '✅' if eq is not None else '⚠ '
                state = ('跟現在的檔案一樣' if eq is True else
                         '跟現在的檔案不同' if eq is False else
                         '讀不出來(權限不足或檔案有問題)')
                if eq is None:
                    notes.append('%s 讀不出來,無法確認它是不是有效的備份'
                                 % b.name)
            print('  %s %-28s %12s  %s  %s'
                  % (mark, b.name, human(size_of(b)), when(b), state))
            # 先查 (檔名, 副檔名) 這個組合,查不到再退回只看副檔名。
            # 順序不能反:.bak 這個副檔名同時屬於好幾課,只看副檔名會認錯人。
            owner = (BAK_OWNER.get((p.name, suffix))
                     or BAK_OWNER_BY_SUFFIX.get(suffix))
            print('     ↑ %s' % ('「%s」這一課建立的' % owner if owner
                                 else '不是本站工具建立的,可能是你自己複製的'))
        # 同一個檔有兩份以上備份時,它們是不同時間點的快照,不是同一份東西。
        # 每支工具只在第一次 --apply 時建立備份,所以最舊的那一份才是原廠檔。
        # 兩兩比對,而不是只比最舊跟最新:內容相同的多份備份(例如同一支工具
        # 重跑過)不算異常,只有真的存在內容不同的兩份時才值得把人叫住。
        if len(baks) > 1:
            pairs = [(baks[i], baks[j])
                     for i in range(len(baks)) for j in range(i + 1, len(baks))]
            # 用 is False,不用 not:same_bytes 讀不出來時回 None,
            # 而 not None 是 True —— 那會把「讀不到」講成「內容不同」。
            if any(same_bytes(x, y) is False for x, y in pairs):
                oldest = min(baks, key=mtime_of)
                print('     ⚠ %s 有 %d 份內容不同的備份 —— 它們是不同時間點的快照。'
                      % (p.name, len(baks)))
                print('       最舊的是 %s,它才是原廠檔;' % oldest.name)
                print('       其他幾份裡面已經含著前一次的修改。')
                notes.append('%s 有 %d 份內容不同的備份,原廠檔是 %s'
                             % (p.name, len(baks), oldest.name))
    if not any_bak:
        print('  一個備份都沒有。如果你還沒改過任何東西,這是正常的。')
        # 全部都沒備份 = 還沒開始動手,不是「值得注意」。
        # 這一段本來就已經印了「這是正常的」,再把每個檔各記一條
        # 進結論,等於自己打自己(實測:剛安裝好的原版會被說「有 5 項值得注意」)。
    else:
        # 有些檔備份了、有些沒有 —— 那才值得提醒。
        for rel in missing_bak:
            if rel in NO_TOOL_BACKUP:
                # 寫「沒有任何備份」會讓人去找是哪一支工具漏了,而答案是「沒有
                # 那一支」。講清楚要自己複製,這一項才是做得完的,不是永遠的紅字。
                notes.append('%s 沒有備份 —— 本站沒有腳本會自動備份它,'
                             '請自己複製一份到別的地方' % rel)
            else:
                notes.append('%s 沒有任何備份' % rel)

    # ── 3. 外部備份資料夾 ──────────────────────────────
    print('\n【3】外部備份資料夾')
    # 「外部備份是完整的」要留到結論那一段用:沒有這個變數的時候,一個檔案
    # 都不缺的人會在最後一行被告知「你也還沒有任何備份」,而【3】就在上面
    # 三行寫著涵蓋全部 —— 同一個畫面自己打自己。
    vault_ok = False
    if vault is None:
        print('  沒有給。要一起檢查的話,把備份資料夾當第二個參數:')
        print('    python3 %s "遊戲資料夾" "備份資料夾"'
              % os.path.basename(sys.argv[0]))
    else:
        # 備份放在遊戲資料夾裡面等於沒有備份:重灌、把整包刪掉、還原到某個
        # 時間點,兩份會一起消失。這一段只提醒,不改任何判斷。
        try:
            r = os.path.realpath(str(root))
            inside = os.path.commonpath([r, os.path.realpath(str(vault))]) == r
        except (OSError, ValueError):
            inside = False          # 不同磁碟機(Windows)會丟 ValueError
        if inside:
            print('  ⚠ 這個備份資料夾在遊戲資料夾裡面 —— 遊戲整包被刪掉或重灌時,')
            print('    它會跟著一起消失。請複製一份到別的地方,別顆硬碟更好。')
            notes.append('外部備份資料夾在遊戲資料夾裡面,會跟遊戲一起消失')
        # 少一個檔在還原那天才會發現,而那天通常來不及了,所以現在就記一條。
        miss = 0
        bad = 0
        for rel, p in present:
            # 兩種擺法都接受:保留原資料夾結構,或全部平放在同一層
            cand = [vault / rel, vault / p.name]
            b = next((c for c in cand if c.is_file()), None)
            if b is None:
                print('  ✗  %-28s 備份資料夾裡沒有' % rel)
                miss += 1
                notes.append('外部備份缺少 %s' % rel)
                continue
            if same_file(b, p):
                # 最兇的假安全:把遊戲資料夾自己當成備份資料夾,每一列都是綠勾。
                print('  ⚠  %-28s %12s  %s  這就是遊戲裡的那個檔本身,不是備份'
                      % (rel, human(size_of(b)), when(b)))
                notes.append('外部備份裡的 %s 就是遊戲裡的那個檔本身,'
                             '等於沒有備份' % rel)
                bad += 1
                continue
            eq = same_bytes(b, p)
            if eq is None:
                notes.append('外部備份裡的 %s 讀不出來,無法確認' % rel)
                bad += 1
            print('  %s %-28s %12s  %s  %s'
                  % ('✅' if eq is True else '⚠ ', rel, human(size_of(b)),
                     when(b),
                     '內容一致' if eq is True else
                     '內容不同(你改過了)' if eq is False else
                     '讀不出來(權限不足或檔案有問題)'))
        # ⚠️ 只有「一個都不缺、而且每一份都真的是另一份檔」才敢說涵蓋全部。
        #    少了 bad 這個條件,一個指回正本的連結會讓這行印出來。
        if miss == 0 and bad == 0:
            vault_ok = True
            print('\n  備份資料夾涵蓋全部 %d 個檔案。' % len(present))

    # ── 4. 結論 ────────────────────────────────────────
    # 結論只有三種狀態,不可以互相混:有事情要注意 / 什麼都還沒備份 / 都備份好了。
    # 混在一起講,等於把「你還沒開始」講成「你已經安全了」。
    print('\n' + '=' * 52)
    if notes:
        print('有 %d 項值得注意:' % len(notes))
        for i, n in enumerate(notes, 1):
            print('  %d. %s' % (i, n))
    elif not any_bak and vault_ok:
        # 遊戲資料夾裡沒有工具留的備份,但外部那份是完整的 —— 這種人是備份
        # 做得最好的那一種,不可以對他說「你還沒有任何備份」。
        print('遊戲資料夾裡沒有工具留的備份 —— 你還沒動手改,那是正常的。')
        print('你給的那個外部備份資料夾涵蓋了上面【1】列的每一個檔。')
    elif not any_bak:
        # ⚠️ 不要在這裡說「每一個都有備份」—— 一個都沒有的時候
        #    那句話是反方向的謊。沒有問題不等於已經備份好了。
        print('目前沒有需要處理的事 —— 但你也還沒有任何備份。')
        print('動手改之前,先把上面【1】列的那幾個檔複製到別的地方。')
    else:
        print('該備份的檔案都在,而且每一個都有備份。')
    print('\n本次檢查全程唯讀,沒有建立、修改或刪除任何檔案。')
    return 0


def cli():
    """main() 外面的最後一道網:接住 Ctrl-C 與掃描途中的讀取錯誤,回傳結束碼。

    為什麼不直接寫 sys.exit(main()):那樣的話,中途按 Ctrl-C 換來的是一整串
    Python traceback(本站實測),而讀者看到 traceback 的第一個念頭是
    「我把它弄壞了」。這支全程唯讀,停在哪裡都沒有東西會壞 —— 要講的就是這句。

    抽成一支函式、而不是寫在下面 `if __name__` 底下,是為了讓自我測試叫得到:
    掛在 `if __name__` 裡面的那幾行,除非另外開一個行程,否則沒有辦法下餌,
    而本站的腳本一律不開子行程。餌十一與餌十二測的就是這裡的兩個 except。
    """
    try:
        return main()
    except KeyboardInterrupt:
        # 這支從頭到尾沒有開任何檔案來寫,也沒有搬移或刪除,所以中途停掉
        # 就只是少印幾行。措辭限定在「你的遊戲資料夾與備份資料夾」:
        # --selftest 確實會在系統暫存資料夾裡建自己的測試檔,講成
        # 「沒有動到任何檔案」在那條路上就不精確了。
        # 結束碼 130 = 128 + SIGINT,跟其他幾種結束方式分得開。
        print('\n\n已中止。你的遊戲資料夾與備份資料夾全程唯讀,沒有動到任何檔案。')
        return 130
    except OSError as e:
        # 掃描途中檔案被移走、被鎖住,或整顆碟不見了會走到這裡:雲端同步、
        # 防毒隔離、外接碟斷線都算。裡面幾支(size_of / when / mtime_of /
        # same_bytes)自己接得住,這一道是接剩下的,讓報告不要以 traceback 收場。
        # 結束碼 2,跟「路徑打錯了」的 1 分開,批次檔才判斷得出差別。
        print('\n✗ 讀取途中出錯:%s' % e)
        print('  可能的原因:遊戲資料夾或備份資料夾正在被別的程式動')
        print('  (雲端同步、防毒掃描),或是外接碟中途斷線。')
        print('  關掉那些程式、確認碟還在,再跑一次。')
        print('  本次檢查全程唯讀,沒有建立、修改或刪除任何檔案。')
        return 2


if __name__ == '__main__':
    sys.exit(cli())

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
