#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
mvp_shift_schedule_year.py
把 EA MVP Baseball 2005 的賽程整體平移到別的年份。

    預覽(不會改檔)  python3 mvp_shift_schedule_year.py "路徑/schedule.big" 2027
    實際套用        python3 mvp_shift_schedule_year.py "路徑/schedule.big" 2027 --apply
    還原            python3 mvp_shift_schedule_year.py "路徑/schedule.big" --restore
    自我測試        python3 mvp_shift_schedule_year.py --selftest
                    (不要加 -O。-O 會把 assert 整句拿掉,靠 assert 的測試會變成假綠;
                     這一支的檢查不靠 assert,守門照樣在 —— 加了會直接回 2。)

原理:schedule.big 是 EA 的 BIGF 封裝檔,裡面 9 個 .dat 其實全是 CSV 文字。
每一項外面可能包一層 QFS/RefPack 壓縮,也可能就是純文字,本工具兩種都自動處理,
而且原本是哪一種,寫回去就還是哪一種。

⚠️ 2026-08-28 訂正:這一段原本寫「MLB 主賽程(mlb162_*.dat)直接以純文字存放;
小聯盟與春訓外面多包一層壓縮」。那是拿一台裝過賽程模組的機器量的。
改用剛安裝好的原版重量,九個表全部都是 QFS 壓縮(mlb162_1 是 14.5 KB 解成 79.5 KB,另外兩個各是 17.6→78.8、14.0→64.1)。
「MLB 沒壓縮」是模組留下的狀態,不是遊戲原本的樣子。功能不受影響,
本工具本來就兩種都吃,但你螢幕上看到的「狀態」那一欄會因機器而異。

日期欄有兩種寫法:補零(03/26/2026)與不補零(3/6/2005),兩種都吃。

⚠️ 2026-09-03 再訂正:上面那句原本寫成「MLB 主賽程補零,春訓不補零」,那也是拿裝過
賽程模組那台量的,跟上一段是同一種病。把兩份 schedule.big 各自解開、逐個日期數過:
剛安裝好的原版九個表**全部不補零**(mlb162_1.dat 第一場就是 4/3/2005,19:05,NYY,Bos,0,
2,431 個日期裡補零 0 個);本站測試機那台反過來,八個表都補零,連 a140_1、aa140_1~2、
aaa144_1~2 這五個小聯盟表也補,只有 mlbspr_1.dat 不補,而那個檔正好是兩台上位元組
完全相同、九個表裡唯一沒被賽程模組換過的一個。所以補零與否是「這一表有沒有被
賽程模組換過」,不是「MLB 還是春訓」。
表頭同理:原版只有 mlb162_1.dat 是 DATE,Time,Home,Road,Half,mlb162_2/_3 跟小聯盟一樣
是 DATE,GAMETIME,HOME,AWAY,HALF(mlb162_2 的表頭末尾還多一個逗號,每一列也多一個
時間欄);測試機那台才是三個 MLB 檔統一成 Time、Home、Road。
功能都不受影響,本工具兩種寫法都吃。

每個賽程表**各自**位移到目標年(以該表自己最多的年份為基準)。用位移而不是硬改成
目標年,是因為表內若橫跨兩個年度,彼此的前後關係才不會被打亂;而各表獨立計算,
則是因為實際檔案裡各表原本年份常常不一致(遊戲原版春訓是 2005、主賽程被模組換過)。

寫回時採 append 模式:新資料接在檔尾,只改目錄 8 bytes + 檔頭 4 bytes,
原始資料區一個 byte 都不動。切勿用「全部讀出再重新打包」的方式存檔。

輸入
    · 一個 data/database/schedule.big(開頭四個位元組必須是 BIGF)
    · 一個目標年份(1900-2999);或者只給 --restore
輸出
    · 預設只往螢幕印表格與統計,一個位元組都不寫
    · 加了 --apply 才動檔:就地換掉 schedule.big,並在它旁邊留一份 schedule.big.bak

安全網(四道)
    1. 預設是預覽。沒打 --apply 就不可能改到檔。
    2. 第一次 --apply 之前先備份,而且是原子的:先寫一個**隨機命名**的暫存檔
       (tempfile.mkstemp,開檔用 O_CREAT|O_EXCL,就開在同一個資料夾),
       fsync 之後比對 SHA-256,再 os.replace 換上 .bak。
       所以 .bak 要嘛完整、要嘛不存在,不會留下半截的假備份。
       備份這一步自己失敗(磁碟滿、外接碟被拔掉)的時候,螢幕會明講
       「.bak 沒有建起來」,不會說成「沿用你原本就有的那一份」——
       那個時候旁邊根本沒有備份,說成那樣等於騙你手上有一份可以回頭的東西。
       .bak 已經存在就保留最早那一份,不覆蓋。
       名字隨機而且不接受既有檔案,所以事先在那個位置放一個符號連結也劫持不了。
    3. 寫檔本身也是原子的:一樣先寫同資料夾的隨機暫存檔、fsync、再 os.replace。
       中途被中斷時,原檔仍然是完整的舊內容。
       正本與 .bak 只要有一個是符號連結,本工具直接拒絕動手(不跟著連結寫到資料夾外)。
       你在指令列上給的那個路徑自己是符號連結的時候也一樣:預覽只是讀,照樣讓你看;
       要動手(--apply 或 --restore)就停下來,請你把真正那個檔的路徑直接給它 ——
       跟著連結走等於替你決定去改資料夾外面的東西。
       另外「os.replace 換過去」跟「登記已經換過了」被綁成不可中斷的一段:
       Ctrl-C 插不進這兩件事中間,所以被中斷時螢幕上那句話一定跟磁碟上的狀態一致。
       真的卡在那一步(極少數環境裝不上訊號處理器)會說「中斷時正在替換」,不會說死。
    4. 複驗做兩次,兩次看同樣三項:項目數要跟改之前一樣、「未對齊日期」要是 0、
       解不開的表要跟動手之前是同一批(沒有新的表被寫壞)。
       第一次在**換名之前**,用本工具自己的解析器把暫存檔重讀一遍;沒過就不換名,
       暫存檔刪掉,遊戲檔一個位元組都沒有動。
       第二次在換名之後,從磁碟把正本讀回來再驗一遍;沒過會明講,並要你 --restore。
    另外 --restore 之前還會再擋一次:備份必須是 BIGF、備份的目錄要解得開、
    裡面要真的有 mlb162_1.dat,而且檔頭宣告的長度要等於實際長度;正本如果還在,
    它也必須是 BIGF(正本已經被刪掉的話照樣可以還原 —— 那正是備份的用途)。
    還原本身也是原子的:先寫同資料夾的隨機暫存檔、fsync、SHA-256 跟備份對上了
    才 os.replace 換上去 —— 中途任何一步失敗,正本一個位元組都不會被動到。
    換完還會把備份與正本整份讀回來比一次,對不上就不會印「已還原」。
    剛好在換名那一瞬間按 Ctrl-C 的話,螢幕說的是「還原已經做完了」,
    不會反過來叫你「回到動手之前」—— 你跑的就是還原,再跑幾次結果都一樣。

做不到的事(先講,免得白做)
    · 改不了已經開始的王朝。賽程是開新 Dynasty 的那一刻抄進存檔的,
      改 schedule.big 只對之後新開的王朝有效。
    · 只換年份數字,不重算星期幾,也不管那一年真實世界的賽制。
    · 明星賽那一列(HALF 欄寫 -)照樣跟著平移,平移後不會等於該年真正的明星賽日期。
      要對到真實日期,那一列得自己手動改。
    · 不新增、不刪除任何一場比賽;時間、主客隊、上下半季那幾欄一律不碰。
    · 只認得 m/d/yyyy 這種寫法的日期。賽程模組若換成別的日期格式,
      這支會把那一表判成「無日期」而跳過,不會亂猜。
    · --restore 只還原 schedule.big 這一個檔,而且只認得本工具留下的 .bak。
      整包遊戲的備份請自己另外做。

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

import hashlib
import re
import os
import shutil
import signal
import struct
import sys
import tempfile
from pathlib import Path

# 這一輪(--apply 或 --restore)有沒有真的把某個檔案換掉,以及換的是哪一種。
# Ctrl-C 的時候要靠它決定該說「什麼都沒有動到」還是「檔案已改,請 --restore」。
# 每一筆是 (種類, 路徑);種類有三種:
#   'live'    換上去的是這一輪算出來的新賽程(--apply 那條路)
#   'restore' 換上去的是 .bak 裡那一份(--restore 那條路,或複驗沒過的自動還原)
#   'backup'  換的是 .bak 自己
# 分開記是因為三者要對使用者講的話完全不同:多出一個 .bak 不痛不癢;
# 遊戲檔被換成新的那一份才需要叫他去 --restore;
# 而「已經還原完了」反過來不可以叫他再去撤銷 —— 他跑的就是還原。
_REPLACED = []

# ── Ctrl-C 不可以說謊(2026-09-06 第三輪稽核加)──────────────────────
# 上面那份清單原本有一個兩行寬的破口:os.replace() 已經把新檔扶正了,
# append 到 _REPLACED 還沒跑完,Ctrl-C 剛好落在這兩行中間 ——
# 檔案是新的,清單卻是舊的,收尾就會照舊的清單講話。
# 上一輪的補法是「先登記再換名」,方向反過來:寧可多講一句「已經換掉了」,
# 也不要少講。誠實是誠實了,可是他會被叫去跑一次其實不需要的 --restore。
#
# 這一輪兩道一起補:
#   (a) 把「換名 + 登記」用 _NoInterrupt 包成不可中斷的一段。這段期間收到的
#       SIGINT 先記著,離開之後才照常丟出來 —— 所以收尾看到的登記一定跟磁碟一致,
#       而且不必再靠「寧可多記一筆」那種近似解。
#   (b) 保險:進去之前先把「正在換 X」登記在 _INFLIGHT。(a) 幾乎不會讓 (b)
#       被用到 —— 唯一漏得掉的是 signal.signal() 自己裝不上去的環境
#       (不是主執行緒會丟 ValueError),那時 (a) 退回原本的行為,
#       而 (b) 讓收尾至少講得出「中斷時正在替換 X」,不會講成「沒動到」。
#
# 三態因此是:_REPLACED 有 → 已換;_INFLIGHT 有 → 正在換(不確定);
# 兩個都空 → 真的一個位元組都沒動。
_INFLIGHT = []


class _NoInterrupt(object):
    """把「os.replace + 登記」包起來,這段期間不讓 Ctrl-C 插隊。

    收到 SIGINT 先記著,離開這一段之後再照常丟出 KeyboardInterrupt。

    ⚠️ 這不是「吃掉 Ctrl-C」。使用者按下去的那一次一定會生效,只是延到
       這兩行跑完 —— 而這兩行加起來是一次改名加一次 append,不會讓人等。
       換來的是「程式講的話跟硬碟上的狀態一致」。

    ⚠️ signal.signal 只有主執行緒裝得上,裝不上就退回原本的行為(不會更糟),
       這正是外面那個 _INFLIGHT 存在的理由。
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


def _replace_and_record(tmp, dst, kind):
    """把暫存檔扶正,並且在同一個不可中斷的區段裡登記「已經換過了」。

    三個寫入點(建備份 / 寫賽程檔 / 還原)全部走這一個函式,沒有第二條路 ——
    要稽核「這支程式什麼時候會說自己動過檔案」,看這裡就夠了。
    """
    dst = os.fspath(dst)

    def _leave_middle():
        """把「正在換」那一筆收掉。只有在**知道結果**的時候才可以呼叫。"""
        try:
            _INFLIGHT.remove((kind, dst))
        except ValueError:
            pass

    _INFLIGHT.append((kind, dst))
    try:
        with _NoInterrupt():
            os.replace(tmp, dst)           # os.replace 是原子的
            _REPLACED.append((kind, dst))
            _leave_middle()                # 三件事在同一段裡做完,中間插不進 Ctrl-C
    except OSError:
        # 只有 OSError 才證明得了「換名這件事沒有發生」——
        # os.replace 換名失敗會丟 OSError,而它一旦成功就不會再丟 OSError 了。
        _leave_middle()
        raise
    # ⚠️ 這裡**故意不寫 finally**。OSError 以外的例外(訊號處理器裝不上去的環境
    #    真的被 Ctrl-C 插在中間、MemoryError…)代表「換成功了沒有,不知道」——
    #    那一筆「正在換」就要留著,收尾才講得出「中斷時正在替換 X」。
    #    寫成 finally 的話它會被清掉,收尾就會退回去說「沒動到」,而那可能是假的。
    #    2026-09-06 實測:第一版寫 finally,餌九(c) 當場印出「遊戲檔沒有被動到」,
    #    而那個檔已經換掉了。


def _interrupt_report():
    """Ctrl-C(或任何中斷)的收尾要講的話,照當下的進度各講各的。回傳一串要印的行。

    抽成函式是為了讓 --selftest 驗得到這幾句話本身 —— 講錯話是這一支最嚴重的
    失誤形態(檔案已經換掉了卻說「沒動到」),而它只有在中斷的時候才看得見。

    ⚠️ 2026-09-11 補第五種話:原本 --restore 被中斷時沿用「已經換過了 /
       要回到動手之前,請跑 --restore」那一句。話沒說錯,方向錯了 ——
       他跑的就是 --restore,而那個檔已經是 .bak 那一份了;
       叫他「回到動手之前」等於暗示要撤銷掉他剛剛做完的還原。
       現在照「最後一次換名換上去的是哪一份」分開講。
    """
    # 只看玩家那個遊戲檔的**最後一次**換名 —— 那才是磁碟現在的樣子。
    # 為什麼是最後一次:--apply 複驗沒過會在同一輪裡自動還原,
    # 同一個檔會先被換成新的(live)、再被換回備份那一份(restore)。
    last_live = None
    for _k, _p in _REPLACED:
        if _k in ('live', 'restore'):
            last_live = (_k, _p)
    backups = [p for k, p in _REPLACED if k == 'backup']
    mid = list(_INFLIGHT)
    out = []

    def _cmd(path):
        # .bak 換到一半的話,要還原的是它旁邊那個正本,不是 .bak 自己。
        target = path[:-4] if path.endswith('.bak') else path
        return '    python3 %s "%s" --restore' % (Path(sys.argv[0]).name, target)
    if last_live and last_live[0] == 'live':
        out.append('')
        out.append('⚠️ 你按了 Ctrl-C,但這個檔已經換過了:')
        out.append('    %s' % last_live[1])
        out.append('  要回到動手之前,請跑:')
        out.append(_cmd(last_live[1]))
    elif last_live and last_live[0] == 'restore':
        # 還原已經換名成功了,只是「✓ 已從備份還原」那一行來不及印。
        # 這時候要講的是「做完了」,不是「去撤銷」。
        out.append('')
        out.append('· 你按了 Ctrl-C,不過還原已經做完了:')
        out.append('    %s' % last_live[1])
        out.append('  這個檔現在就是 .bak 裡那一份。螢幕上那句確認來不及印而已,')
        out.append('  想再確認一次就再跑一遍(跑幾次結果都一樣):')
        out.append(_cmd(last_live[1]))
    elif mid:
        # 只有「換名 + 登記」那道保險裝不上的環境才會走到這裡。
        # 不確定就要說不確定,不可以猜一個好聽的。
        out.append('')
        out.append('⚠️ 你按了 Ctrl-C,而中斷時正在替換這個檔:')
        for _k, p in mid:
            out.append('    %s' % p)
        out.append('  換過去了沒有,這裡不敢說死。請用 --restore 還原,'
                   '或自己拿 .bak 跟它比對一次:')
        out.append(_cmd(mid[0][1]))
    elif backups:
        # ⚠️ 這一格原本寫的是 elif _REPLACED —— 只要清單裡有東西就講「遊戲檔沒有被動到」。
        #    哪天多一種登記(這一輪就多了 'restore'),它會靜靜地掉進這一句裡變成假話。
        #    改成只認 'backup',認不得的種類會落到最後那一句,而那一句不保證任何事。
        out.append('')
        out.append('· 你按了 Ctrl-C。遊戲檔沒有被動到,只是旁邊多了一份備份:')
        for p in backups:
            out.append('    %s' % p)
        out.append('  那份備份是完整的,留著或刪掉都可以。')
    elif _REPLACED:
        # 認不得的種類:寧可承認自己講不清楚,也不要替它挑一句好聽的。
        # (現在不會走到這裡 —— 留著是為了「以後有人加第四種」的那一天。)
        out.append('')
        out.append('⚠️ 你按了 Ctrl-C。這一輪換過下面這些檔,請自己看一下:')
        for k, p in _REPLACED:
            out.append('    %s(%s)' % (p, k))
        out.append('  不確定的話請拿 .bak 跟它比對一次。')
    else:
        out.append('')
        out.append('· 你按了 Ctrl-C。還沒有換掉任何檔案,你的遊戲檔沒有被動到。')
    return out


def _print_interrupt_report():
    """把上面那幾句真的印出來。單獨一個函式,--selftest 才收得到同一份輸出。"""
    print('')
    for line in _interrupt_report():
        print(line)


# ── 備份的原子性(2026-08-29 上線前稽核加)────────────────────────────
# 原本是直接 shutil.copy2(遊戲檔, .bak)。複製途中被中斷(磁碟滿、外接碟拔掉、
# Windows 上按 Ctrl-C)會留下一個**半截的 .bak**;下一次執行看到它「存在」
# 就印「備份已存在,保留最早那一份」繼續改遊戲檔,之後 --restore
# 會拿那個半截檔覆蓋掉正本。
#
# 實測(2026-08-29):把 2,665,562 bytes 的備份截成 300,000 bytes,
# 本站防護最嚴的那支還原指令三道把關全過、印「✓ 已從備份還原」、exit code 0,
# 2.66 MB 的遊戲檔當場被 300 KB 蓋掉。magic 只看開頭,看不出後面少了多少。

def _refuse_if_symlink(path, what):
    """目的地是符號連結就當場停手。

    ⚠️ 一定要用 os.path.islink(它走 lstat),不可以用 Path.exists() ——
       連結存在、但它指到的東西不存在時,exists() 回的是 False,
       等於整個檢查形同虛設。

    為什麼要擋:本站所有寫檔都是「寫暫存檔 → os.replace」。os.replace 換掉的是
    連結本身,不會傷到連結指到的檔;但如果**正本或 .bak 自己**就是連結,
    使用者以為改到的那一份跟實際被換掉的那一份就不是同一個東西了。
    這種情況寧可停下來讓他自己看清楚,也不要安靜地做一件他沒要求的事。
    """
    if os.path.islink(os.fspath(path)):
        raise SystemExit(
            '%s 是一個符號連結:%s\n'
            '  本工具不跟著符號連結寫檔(那會改到資料夾外面的檔案)。\n'
            '  請先把它刪掉或改名,或直接指向真正的那個檔案。' % (what, os.fspath(path)))


def _unique_temp(target, tag):
    """在 target 所在的資料夾裡開一個誰都搶不走的暫存檔,回傳 (fd, 路徑)。

    ⚠️ 2026-09-05 資安稽核:原本寫的是 open(dst + '.part', 'wb')。名字是**猜得到的**,
       只要事先在那個位置放一個指向資料夾外面的符號連結,open(..., 'wb')
       就會跟著連結過去,把外面那個檔案截成 0 —— 而且是在 os.replace 之前,
       所以「os.replace 只換連結本身」救不了它。

    tempfile.mkstemp 用 O_CREAT|O_EXCL 開檔:名字是隨機的,而且如果那個名字
    已經被別人先建起來(即使只是一個符號連結),開檔會直接失敗,不會跟過去。
    暫存檔就開在目的地同一個資料夾,os.replace 才會是同一個檔案系統上的原子換名。

    ⚠️ 誠實說一件事:被 SIGKILL(kill -9、系統直接斷電)殺掉的話,
       這個暫存檔會留在資料夾裡 —— 那種訊號攔不到,沒有任何程式收得了尾。
       它是隱藏檔(檔名以「.」開頭),名字長這樣:.schedule.big.part-xxxxxxxx,
       遊戲不會讀它,看到了直接刪掉就好。正本本身仍然是完整的。
    """
    target = os.fspath(target)
    folder = os.path.dirname(os.path.abspath(target)) or '.'
    return tempfile.mkstemp(dir=folder,
                            prefix='.' + os.path.basename(target) + '.' + tag + '-')


def _sha256(path):
    """整份讀完算一次 SHA-256。賽程檔只有幾百 KB,不值得為了省時間少驗一道。"""
    h = hashlib.sha256()
    with open(os.fspath(path), 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def _write_verified(src, dst, tag, mode_from=None, kind='live'):
    """把 src 的內容原子地換到 dst 上:寫隨機暫存檔 → fsync → 對 SHA-256 → os.replace。

    任何一步失敗都把暫存檔刪掉,dst 一個位元組都不會被動到。
    mode_from 是「權限要跟誰一樣」的那個檔(通常是 dst 自己);
    給 None 就跟 src 一樣。
    kind 是給 Ctrl-C 訊息用的:'live' 是把玩家的遊戲檔換成這一輪算出來的新賽程,
    'restore' 是把它換回 .bak 那一份,'backup' 換的是 .bak 自己。
    """
    src, dst = os.fspath(src), os.fspath(dst)
    _refuse_if_symlink(dst, tag)
    want = _sha256(src)
    fd, tmp = _unique_temp(dst, 'part')
    try:
        with os.fdopen(fd, 'wb') as fo:
            with open(src, 'rb') as fi:
                shutil.copyfileobj(fi, fo)
            fo.flush()
            os.fsync(fo.fileno())      # 先落地,再改名 —— 順序反了就白做
        # 時間戳跟著內容走(原本用的 shutil.copy2 就是這個語意,不要改掉),
        # 權限則跟著 mode_from —— 還原時那是「要被換掉的那個檔」,
        # 備份時是原檔。新開的暫存檔權限來自 mkstemp,只有 0600,
        # 不帶過去的話原本 644 的檔會變成只有自己讀得到。
        try:
            shutil.copystat(src, tmp)
            if mode_from:
                shutil.copymode(mode_from, tmp)
        except OSError:
            pass                       # 權限或時間戳沒帶到不算致命,內容是對的
        # 讀回來對雜湊。「寫出去」跟「磁碟上真的有這些位元組」是兩件事。
        if _sha256(tmp) != want:
            raise OSError('寫出來的內容跟來源對不上(%s)' % dst)
        # ⚠️ 換名與登記中間不可以有縫。2026-09-05 實測抓到:Ctrl-C 剛好落在
        #    os.replace 回來、下一行還沒跑到的那個瞬間,檔案其實已經換掉了,
        #    而紀錄還是空的 —— 螢幕上就會印「還沒有換掉任何檔案」。
        #    那一版的補法是「先記錄再換名」(寧可多記一筆),2026-09-06 改成
        #    _replace_and_record:兩件事包在不可中斷的一段裡做,不必再近似。
        _replace_and_record(tmp, dst, kind)
    except BaseException:
        # 連 KeyboardInterrupt 都要接:按 Ctrl-C 一樣會留下半截的暫存檔。
        # 清乾淨之後再把原本的例外丟回去,不吞掉任何錯誤。
        try:
            if os.path.lexists(tmp):   # lexists:暫存檔如果是連結也要刪得掉
                os.remove(tmp)
        except OSError:
            pass
        raise


def _atomic_copy(src, dst):
    """備份要嘛完整、要嘛不存在 —— 中間狀態不會留在 dst 這個名字上。

    ⚠️ 本站有些腳本用 pathlib.Path 存路徑,有些用字串。
       2026-08-29 第一版寫成 dst + '.part',在 Path 上直接 TypeError,
       等於所有備份都失敗 —— 而且「半截備份被擋下來」那個測試照樣是綠的。
       是陰性對照(先證明正常流程真的會產生備份)抓到的。
    """
    # 備份的權限跟著原檔走,所以 mode_from 不用給。
    _write_verified(src, dst, '備份檔', kind='backup')


def _restore_from_backup(bak, dst):
    """還原之前先擋掉明顯壞掉的備份。

    ⚠️ 這裡**不能**比對「備份與目標大小相同」—— 本站多數腳本是把資料接到
    檔尾來改檔(專案鐵律:封裝檔不可重新打包),改完之後正本本來就比備份大,
    那樣比會擋掉每一次合法的還原。

    ── 2026-08-30 補上三道(上線前資安稽核抓到的真漏洞)────────────────
    原本只有「不是 0 bytes」+「BIGF 檔頭宣告長度」兩道。**BIGF 以外全破。**
    實測拿「前 1/8 的半截備份」去還原,六支腳本把正本吃掉而且都印成功:
        mvp_fix_loc / mvp_menu_text   .LOC        416,753 →  52,094
        mvp_edit_speed / mvp_ratings
        / mvp_player                  attrib.dat  840,643 → 105,080
        mvp_modernize                 mvp2005.exe 5,443,584 → 680,448
                                      (它還印「複驗:內容與備份相同 ✅」)
    最後那個會讓遊戲**完全開不起來**,而站上每一課都寫著「隨時可以 --restore」。

    現在檢查五件事:
      1. 備份不是 0 bytes
      2. BIGF:檔頭第 4-8 個位元組宣告的總長度要等於實際長度
         (兩種位元組序都接受;哪些檔是大端、各有幾個,以 reference/bigf.html 量到的為準,這裡不寫會過期的數字)
      3. LOCH(語系檔):檔頭指到的 LOCL 要在檔內,而且最後一條字串的位移
         也要在檔內 —— 截斷之後那個位移一定會超出去
      4. MZ(執行檔):PE 節區表裡 raw offset + raw size 的最大值不得超過檔案長度
      5. **通用地板**:非 BIGF 的備份不得小於「要被蓋掉的那個檔」的一半。
         非 BIGF 的工具都是原地改(大小幾乎不變),所以這條很安全;
         BIGF 走 append 會越改越大,所以刻意**不套**這條,由第 2 道負責。
    """
    import struct
    bak, dst = os.fspath(bak), os.fspath(dst)
    if not os.path.exists(bak):
        raise SystemExit('找不到備份:%s' % bak)
    # 下面每一種格式的把關都是同一個思路:檔案裡本來就有「我應該多大」的欄位,
    # 拿它跟實際長度對一次,截斷過的備份就藏不住了。
    n = os.path.getsize(bak)
    if n == 0:
        raise SystemExit(
            '備份是 0 bytes(多半是上次備份到一半被中斷),不敢拿它覆蓋 %s。' % dst)
    with open(bak, 'rb') as _f:
        head = _f.read(8)

    def _stop(why):
        raise SystemExit(
            '這份備份是壞的,不敢拿它覆蓋 %s。\n'
            '  %s\n'
            '  多半是備份途中被中斷(磁碟滿、外接碟拔掉、按了 Ctrl-C)。\n'
            '  請改用你自己另外留的那一份備份。' % (dst, why))

    # 【BIGF】封裝檔:檔頭第 4 到 8 個位元組寫著整個檔案應該有多長。
    # 大小端兩種都收,因為本專案實測本機 295 個 BIGF 檔,288 個小端、7 個大端。
    if len(head) == 8 and head[:4] == b'BIGF':
        le = struct.unpack('<I', head[4:8])[0]
        be = struct.unpack('>I', head[4:8])[0]
        if le != n and be != n:
            _stop('檔頭說它應該是 %d bytes(或 %d),實際只有 %d bytes。' % (le, be, n))
        return _do_copy(bak, dst)

    # 【LOCH】語系檔:檔頭位移 16 起算的 4 個位元組(小端)指向字串區 LOCL。
    # 字串靠一張位移表去找,截斷之後「最後一條字串的位移」一定會指到檔案外面,
    # 所以把最後一條算出來看它落在哪裡,就知道這份備份完不完整。
    if len(head) >= 4 and head[:4] == b'LOCH':
        try:
            d = open(bak, 'rb').read()
            L = struct.unpack('<I', d[16:20])[0]
            if L + 16 > n or d[L:L + 4] != b'LOCL':
                _stop('語系檔的字串區(LOCL)應該在位移 %d,那裡不是 LOCL。' % L)
            lcnt = struct.unpack('<I', d[L + 12:L + 16])[0]
            if lcnt <= 0 or L + 16 + lcnt * 4 > n:
                _stop('語系檔的位移表被截斷了(宣告 %d 條)。' % lcnt)
            last = struct.unpack('<I', d[L + 16 + (lcnt - 1) * 4:L + 20 + (lcnt - 1) * 4])[0]
            if L + last >= n:
                _stop('語系檔最後一條字串在位移 %d,超出檔案結尾(%d bytes)。'
                      % (L + last, n))
        except SystemExit:
            raise
        except (struct.error, IndexError):
            _stop('讀不出語系檔的結構,它壞了。')

    # 【MZ】Windows 執行檔:位移 0x3C 起算的 4 個位元組(小端)指向 PE 檔頭,
    # PE 檔頭後面接著節區表,每個節區各佔 40 個位元組,其中位移 16 起算的
    # 兩個 4 位元組數字是「這一段在檔案裡有多長、從哪裡開始」。
    # 把每一段的結尾算出來取最大值,超過檔案長度就是被截斷過。
    if len(head) >= 2 and head[:2] == b'MZ':
        try:
            d = open(bak, 'rb').read()
            pe = struct.unpack('<I', d[0x3C:0x40])[0]
            if pe + 24 > n or d[pe:pe + 4] != b'PE\x00\x00':
                _stop('執行檔的 PE 檔頭不在它該在的地方,檔案不完整。')
            nsec = struct.unpack('<H', d[pe + 6:pe + 8])[0]
            optsz = struct.unpack('<H', d[pe + 20:pe + 22])[0]
            sec = pe + 24 + optsz
            end = 0
            for i in range(nsec):
                o = sec + i * 40
                if o + 40 > n:
                    _stop('執行檔的節區表被截斷了(宣告 %d 個節區)。' % nsec)
                raw_sz, raw_off = struct.unpack('<II', d[o + 16:o + 24])
                end = max(end, raw_off + raw_sz)
            if end > n:
                _stop('執行檔的節區指到 %d bytes,實際只有 %d bytes。' % (end, n))
        except SystemExit:
            raise
        except (struct.error, IndexError):
            _stop('讀不出執行檔的結構,它壞了。')

    # 通用地板 —— 非 BIGF 走到這裡
    if os.path.exists(dst):
        live = os.path.getsize(dst)
        if live > 0 and n * 2 < live:
            _stop('備份只有 %d bytes,而要被蓋掉的那個檔有 %d bytes ——'
                  '差太多了(不到一半)。' % (n, live))
    return _do_copy(bak, dst)


def _do_copy(bak, dst):
    """真正動手的只有這一個函式,而且是所有把關都過了才會走到。

    獨立成一個函式是為了讓「還原」只有一個出口:
    以後要再加驗證,只要確認每條路都經過 _restore_from_backup 就好。

    ⚠️ 2026-09-05 資安稽核:原本這裡是 shutil.copy2(bak, dst) 一行。
       copy2 會**先把 dst 截成 0 bytes**,再一段一段寫回去。備份本身再怎麼驗,
       只要複製途中磁碟滿、外接碟被拔掉、程序被殺、按了 Ctrl-C,
       玩家的正本就停在 0 bytes 或半截 —— 而他跑的明明是「還原」。
       改成寫同資料夾的隨機暫存檔、對完 SHA-256 才 os.replace 換上去:
       失敗的話正本原封不動,還是還原之前那一份。
    """
    bak, dst = os.fspath(bak), os.fspath(dst)
    _refuse_if_symlink(bak, '備份檔')
    # 權限跟著「要被換掉的那個檔」走;正本已經被刪掉的話就跟著備份走。
    keep = dst if os.path.isfile(dst) and not os.path.islink(dst) else None
    # kind='restore':換上去的是備份那一份。被 Ctrl-C 打斷時要說「還原做完了」,
    # 不可以沿用 --apply 那句「要回到動手之前,請跑 --restore」—— 他跑的就是還原。
    _write_verified(bak, dst, '要還原的目標', mode_from=keep, kind='restore')




MAX_UNCOMPRESSED = 256 * 1024 * 1024
# 日期欄有兩種寫法:補零(03/26/2026)與不補零(3/6/2005),兩種都要吃。
# 哪一種跟「是不是 MLB」無關,是「這一表有沒有被賽程模組換過」:
# 剛安裝好的原版九個表全部不補零,本站測試機那台八個表補零、只有 mlbspr_1.dat 不補。
DATE_RE = re.compile(rb'(\b\d{1,2}/\d{1,2}/)(\d{4})\b')

# Windows 主控台預設編碼(繁中是 cp950)存不下 ✓ ✗ 這類符號,
# 輸出被重導向到檔案時會直接 UnicodeEncodeError 中斷。先把輸出轉成 UTF-8。
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except (AttributeError, ValueError):
    pass


# ─────────────────────────────────────────────────────────
#  QFS / RefPack 解壓
# ─────────────────────────────────────────────────────────
def qfs_decompress(data: bytes) -> bytes:
    """QFS / RefPack 解壓。不是壓縮資料就原樣還你,所以可以無腦套在每一項上。

    怎麼認出它是壓縮資料:第 2 個位元組(位移 1)是 0xFB。
    第 1 個位元組(位移 0)的最低位元決定尺寸欄擺在哪裡:
      · bit0 = 1:解壓後長度是位移 6 起算的 4 個位元組,壓縮資料從位移 10 開始
      · bit0 = 0:解壓後長度是位移 2 起算的 3 個位元組,壓縮資料從位移 5 開始
    兩種尺寸欄都是**大端**。本站在 schedule.big 上看到的都是 0x10 0xFB(bit0 = 0),
    下面 main() 判斷「這一項原本有沒有壓縮」認的就是這兩個位元組。

    ⚠️ 檔頭宣稱的長度是「檔案自己說的」,不能當成可信的上限,
       所以每次往結果裡加東西之後,都還要再過 guard() 那一關。
    """
    if len(data) < 2 or data[1] != 0xFB:
        return data                                    # 未壓縮,原樣返回

    # 兩種檔頭長度不一樣,所以要先確認位元組數夠再讀;
    # 不然 int.from_bytes 會安靜地把一段太短的資料解讀成一個很小的數字。
    if data[0] & 0x01:
        if len(data) < 10:
            raise ValueError('QFS 檔頭不完整')
        size = int.from_bytes(data[6:10], 'big')
        pos = 10
    else:
        if len(data) < 5:
            raise ValueError('QFS 檔頭不完整')
        size = int.from_bytes(data[2:5], 'big')
        pos = 5

    # 第一道:檔頭宣稱的大小本身要合理(上限 256 MB),先擋掉一眼就荒謬的值。
    if not 0 <= size <= MAX_UNCOMPRESSED:
        raise ValueError(f'QFS 宣稱解壓尺寸異常:{size}')

    out = bytearray()
    end = len(data)

    def guard():
        # ⚠️ 只檢查檔頭宣稱的大小是不夠的 —— 那是「檔案自己說的」。
        #    惡意檔可以宣稱很小(通過上面那道),再用反向參照無限吐資料,
        #    把記憶體吃光。實際輸出也要有上限,而上限就是它自己宣稱的大小。
        if len(out) > size:
            raise ValueError(f'QFS 解出來的資料超過檔頭宣稱的 {size} 位元組 —— '
                     f'這個檔可能已損毀或被動過手腳')

    def copy_back(offset, length):
        """從已經解出來的結果往回 offset 個位元組,複製 length 個過來。

        ⚠️ 這裡**必須**一個位元組一個位元組抄,不可以先切片再一次接上去。
           length 允許大於 offset(例如往回 1 個、複製 40 個),
           那是這個格式用來表達「同一小段一直重複」的手法:
           抄的過程中剛寫進去的位元組,馬上就會被後面幾輪讀到。
           先切片的話,抄到的是「複製開始之前」的舊內容,結果就錯了。
        """
        if not 0 < offset <= len(out):
            raise ValueError(f'QFS 反向參照越界 offset={offset}')
        src = len(out) - offset
        for _ in range(length):
            out.append(out[src])
            src += 1
        guard()

    # 指令流的規則:每個指令自己說「先照抄幾個位元組(0 到 3 個)」,
    # 再說「往回多遠、複製多長」。用第一個位元組的大小分成五類:
    #   0xFC 以上     結束,後面最多再照抄 3 個位元組
    #   0xE0 到 0xFB  純照抄一段(最多 112 個位元組),沒有往回複製
    #   0xC0 到 0xDF  4 個位元組的指令,能表達最遠、最長的往回複製
    #   0x80 到 0xBF  3 個位元組的指令
    #   0x00 到 0x7F  2 個位元組的指令,最短也最常見
    # 後三類拆法不同,但拆出來都是同一組 (n, length, offset),所以共用同一段收尾。
    while pos < end:
        b0 = data[pos]
        if b0 >= 0xFC:                                 # 結束標記 + 0~3 個 literal
            n = b0 & 0x03
            pos += 1
            out += data[pos:pos + n]
            guard()
            break
        if b0 >= 0xE0:                                 # 純 literal
            n = ((b0 & 0x1F) << 2) + 4
            pos += 1
            out += data[pos:pos + n]
            guard()
            pos += n
            continue
        if b0 >= 0xC0:                                 # 4-byte 指令
            b1, b2, b3 = data[pos + 1], data[pos + 2], data[pos + 3]
            pos += 4
            n = b0 & 0x03
            length = ((b0 & 0x0C) << 6) + b3 + 5
            offset = ((b0 & 0x10) << 12) + (b1 << 8) + b2 + 1
        elif b0 >= 0x80:                               # 3-byte 指令
            b1, b2 = data[pos + 1], data[pos + 2]
            pos += 3
            n = (b1 >> 6) & 0x03
            length = (b0 & 0x3F) + 4
            offset = ((b1 & 0x3F) << 8) + b2 + 1
        else:                                          # 2-byte 指令
            b1 = data[pos + 1]
            pos += 2
            n = b0 & 0x03
            length = ((b0 & 0x1C) >> 2) + 3
            offset = ((b0 & 0x60) << 3) + b1 + 1
        # 三種指令的共同結尾:先照抄那 n 個位元組,再做那一次往回複製。
        out += data[pos:pos + n]
        guard()
        pos += n
        copy_back(offset, length)

    # 這一行看起來是「截到檔頭宣稱的長度」,實際上它永遠切不到東西:
    # 上面每一次往 out 加料之後都會叫一次 guard(),一超過 size 就當成壞檔擋下來,
    # 連結束指令那 0 到 3 個位元組也是先 guard() 再 break,
    # 所以能走到這一行的時候,len(out) 一定小於或等於 size。
    # 2026-09-03 實測:餵一份宣稱 6 個位元組、實際會吐出 7 個的資料流進來,
    # 拿到的是「QFS 解出來的資料超過檔頭宣稱的 6 位元組」這個錯誤,
    # 不是一份被切短的結果;再拿本站測試機 MVP2026/data/frontend/ 底下
    # 98 個封裝檔裡的 9,643 個 QFS 項目各解一次,沒有一項解出來的長度
    # 超過檔頭宣稱的大小,也就是 [:size] 一次都沒有真的切到東西。
    # 所以它是最後一道保險,不是這支程式的正常路徑。
    return bytes(out[:size])


# ─────────────────────────────────────────────────────────
#  QFS / RefPack 壓縮(純 literal 編碼)
#
#  RefPack 允許整份資料都用 literal 指令表達。不做字串匹配搜尋,
#  所以瞬間完成,格式一樣合法,也不必依賴壓縮器實作正確。
# ─────────────────────────────────────────────────────────
def qfs_compress_literal(data: bytes) -> bytes:
    """包回 QFS / RefPack,但只用「照抄」指令,完全不做字串比對搜尋。

    產出的資料會比原始資料大一點(每 112 個位元組多一個指令位元組,再加檔頭 5 個),
    但格式完全合法,而且瞬間完成。
    這是刻意的取捨:壓縮率對這個用途沒有意義,而「壓縮器實作有沒有寫錯」
    會直接害玩家的賽程檔壞掉。只用照抄就沒有這個風險。
    """
    n = len(data)
    # 檔頭 5 個位元組:0x10 0xFB 之後接解壓後長度,3 個位元組、大端。
    # 3 個位元組表示得下 16,777,215;本站量到最大的賽程表是 79.5 KB,差很遠。
    out = bytearray([0x10, 0xFB, (n >> 16) & 0xFF, (n >> 8) & 0xFF, n & 0xFF])
    # 照抄指令一次只能抄 4 的倍數,除不盡的尾巴(0 到 3 個)交給結束指令帶走。
    tail = n % 4
    body = n - tail
    pos = 0
    # 上限 112 不是隨便挑的:指令位元組是 0xE0 | ((chunk - 4) // 4),
    # chunk = 112 時剛好算出 0xFB;再往上一格就變成 0xFC,
    # 那是「結束」的意思,解壓端會當場停在那裡。
    while pos < body:
        chunk = min(112, body - pos)                   # 必為 4 的倍數,上限 112
        out.append(0xE0 | ((chunk - 4) // 4))          # 0xE0~0xFB,不會撞到 0xFC
        out += data[pos:pos + chunk]
        pos += chunk
    # 結束指令的低 2 個位元順便帶走最後那 0 到 3 個位元組。
    out.append(0xFC | tail)
    out += data[pos:]
    return bytes(out)


# ─────────────────────────────────────────────────────────
#  BIG 檔目錄
# ─────────────────────────────────────────────────────────
class BigFormatError(Exception):
    """.big 檔頭或目錄不合格式。"""


def list_entries(data: bytes):
    """回傳 [(名稱, TOC 欄位位置, 資料 offset, 資料長度), ...]。

    BIGF 的檔頭固定 16 個位元組:
        位移 0 到 4    b'BIGF'
        位移 4 到 8    整個檔案的總長度(本工具寫回時用**小端**寫這一格)
        位移 8 到 12   目錄有幾項(**大端**)
        位移 12 到 16  檔頭長度,本工具用不到
    接著從位移 16 開始,一項一項排下去:
        4 個位元組 資料在檔案裡的位移(大端)
        4 個位元組 資料長度(大端)
        名稱,以一個 0x00 收尾,長度不固定

    ⚠️ 同一個檔頭裡混用大小端不是筆誤:項目數與每一項的位移、長度都是大端,
       只有總長度那一格是小端。本專案量過本機 295 個 BIGF 檔,
       288 個的總長度欄是小端、7 個是大端,所以還原時兩種都接受。

    回傳的第 2 欄(field)是「那 8 個位元組本身在檔案裡的位置」,不是資料的位置。
    有了它,之後要把某一項搬到檔尾,只要覆寫那 8 個位元組,不必重排整個目錄。
    """
    if len(data) < 16 or data[:4] != b'BIGF':
        raise BigFormatError('檔頭前四碼不是 BIGF,這不是 EA BIG 封裝檔')
    count = int.from_bytes(data[8:12], 'big')
    # 項目數先做健全性檢查:壞掉的檔常常在這一格冒出天文數字,
    # 沒擋的話下面那個迴圈會空轉幾十億次。
    if not 0 < count < 100000:
        raise BigFormatError(f'目錄項目數異常({count}),檔案可能已損毀')

    items = []
    pos = 16
    for i in range(count):
        # 名稱是不定長度的,所以每一項的起點只能邊走邊算,不能用乘法直接跳。
        field = pos
        if pos + 8 > len(data):
            raise BigFormatError(f'目錄在第 {i + 1} 項處被截斷,檔案不完整')
        offset, size = struct.unpack('>II', data[pos:pos + 8])
        pos += 8
        end = data.find(b'\x00', pos)
        if end < 0:
            raise BigFormatError(f'第 {i + 1} 項的名稱沒有結束符,檔案已損毀')
        # 目錄指到檔案外面 = 這個檔被截斷過或改壞過,不要再往下走。
        if offset + size > len(data):
            raise BigFormatError(f'第 {i + 1} 項的資料範圍超出檔案結尾')
        items.append((data[pos:end].decode('latin-1', 'replace'), field, offset, size))
        pos = end + 1
    return items


# ─────────────────────────────────────────────────────────
#  賽程平移
# ─────────────────────────────────────────────────────────
def scan_years(text: bytes):
    """回傳 {年份: 出現次數}。

    為什麼要數次數,而不是看到第一個日期就算了:一份賽程表可能橫跨兩個年度
    (春訓 3 月到季後 10 月),還可能夾雜少數幾筆雜訊。
    取「出現最多次的那個年份」當基準,比取第一個穩。
    """
    years = {}
    for m in DATE_RE.finditer(text):
        y = int(m.group(2))
        years[y] = years.get(y, 0) + 1
    return years


def shift_years(text: bytes, delta: int):
    """該表所有日期一起位移 delta 年,回傳 (新內容, 改動筆數)。

    位移而非硬改成目標年:表內若橫跨兩個年度(春訓 3 月到季後 10 月、
    或跨年的冬季賽程),彼此的前後關係才不會被打亂。
    每個賽程表各自計算自己的 delta,所以不同表原本年份不同也能一起對齊到目標年。
    """
    # 用長度 1 的 list 當計數器:巢狀函式要改外層的數字,這是最省事的寫法。
    count = [0]

    def rep(m):
        count[0] += 1
        # group(1) 是「月/日/」那一段,原樣留著,所以補零與不補零兩種寫法都不會被動到。
        # :04d 保證年份永遠是 4 位數,長度不變,整份 CSV 的位元組數才不會亂跑。
        return m.group(1) + f'{int(m.group(2)) + delta:04d}'.encode()

    return DATE_RE.sub(rep, text), count[0]


# ─────────────────────────────────────────────────────────
#  自我測試(--selftest)
#
#  不碰任何遊戲檔:自己在系統暫存資料夾造一個最小但合法的 schedule.big,
#  跑完預覽 / --apply / --restore 全程,再逐一「下餌」——
#  先做出每一道守門要擋的那個情況,確認它真的擋得下來,
#  而且旁邊、外面的檔案一個位元組都沒被動到。
#
#  ⚠️ 只有正向測試會騙人。本站踩過:「半截備份被擋下來」那條測試一直是綠的,
#     實際上是備份根本沒產生過(TypeError),所以永遠沒有東西可以擋。
#     所以每一條餌都配一個陰性對照:先證明正常流程真的會走到那一步。
# ─────────────────────────────────────────────────────────
def _build_big(entries):
    """造一個最小但合法的 BIGF。entries 是 [(名稱, 內容 bytes), ...]。"""
    dirlen = 16 + sum(8 + len(n.encode()) + 1 for n, _ in entries)
    toc, body, off = b'', b'', dirlen
    for n, p in entries:
        toc += struct.pack('>II', off, len(p)) + n.encode() + b'\x00'
        body += p
        off += len(p)
    total = dirlen + len(body)
    return (b'BIGF' + struct.pack('<I', total) +
            struct.pack('>I', len(entries)) + struct.pack('>I', dirlen) + toc + body)


def _selftest():
    # ── 不准在 python -O 底下假綠(2026-09-06,全站統一)────────────
    # -O 會把 assert 整句拿掉。這一支的檢查是自己寫的 check(),-O 拿不掉它 ——
    # 但這道守門照樣要有:哪天有人在這裡補一句普通的 assert,
    # 沒有它就會靜靜地變成假綠,而且沒有任何人會發現。
    if sys.flags.optimize:
        print('--selftest 不能在 python -O 下跑:-O 會把 assert 全部拿掉,測試會假綠')
        return 2

    import contextlib
    import io as _io
    import random

    fails = []
    n_ok = [0]

    def check(name, cond, detail=''):
        if cond:
            n_ok[0] += 1
            print('  ✓ %s' % name)
        else:
            fails.append(name)
            print('  ✗ %s  %s' % (name, detail))

    def send_sigint():
        """真的送一次 SIGINT 給自己 —— 不是自己 raise KeyboardInterrupt。

        差別很重要:只有真的訊號才驗得到 _NoInterrupt 有沒有把它擋在區段外面。
        自己 raise 的那一種繞過訊號處理器,測到的是另一件事(見九(c))。
        """
        if hasattr(signal, 'raise_signal'):
            signal.raise_signal(signal.SIGINT)      # 3.8 以上
        else:
            os.kill(os.getpid(), signal.SIGINT)     # 3.7 的退路

    # 3.7 的退路在 Windows 上送不出 SIGINT(還沒實測),那裡就跳過那一條餌。
    can_signal = hasattr(signal, 'raise_signal') or os.name == 'posix'

    def run(*argv):
        """跑一次 main(),把螢幕輸出收起來。回傳 (結束碼, 輸出, 這輪換過哪些檔)。"""
        old_argv = sys.argv
        sys.argv = ['mvp_shift_schedule_year.py'] + list(argv)
        del _REPLACED[:]
        del _INFLIGHT[:]
        buf = _io.StringIO()
        try:
            with contextlib.redirect_stdout(buf):
                try:
                    code = main()
                except SystemExit as e:
                    code = e.code if isinstance(e.code, int) else 1
                    if not isinstance(e.code, int):
                        print(e.code)
                except KeyboardInterrupt:
                    # __main__ 那邊收到 Ctrl-C 就是印這幾句話再回 130。
                    # 這裡走同一個函式,測的才是使用者真的會看到的那幾句。
                    _print_interrupt_report()
                    code = 130
        finally:
            sys.argv = old_argv
        return code, buf.getvalue(), list(_REPLACED)

    # 一張最小的賽程表:表頭 + 幾場比賽,日期兩種寫法都放進去。
    csv = (b'DATE,Time,Home,Road,Half\r\n'
           b'4/3/2005,19:05,NYY,Bos,0\r\n'
           b'04/12/2005,13:05,Bos,NYY,0\r\n'
           b'10/2/2005,19:05,NYY,Bos,1\r\n')
    other = b'DATE,Time,Home,Road,Half\r\n3/6/2005,13:05,Min,Cle,0\r\n'

    print('mvp_shift_schedule_year.py 自我測試')
    print('(不需要遊戲檔,全程只動系統暫存資料夾)\n')

    # ── 1. QFS 壓縮 / 解壓來回 ────────────────────────────
    print('一、QFS / RefPack')
    random.seed(20260905)
    ok = True
    for n in (0, 1, 3, 4, 5, 112, 113, 1000, 4096):
        blob = bytes(random.randrange(256) for _ in range(n))
        if qfs_decompress(qfs_compress_literal(blob)) != blob:
            ok = False
    check('壓回去再解開,拿到的是同一份資料(9 種長度)', ok)
    check('不是壓縮資料的話原樣返回', qfs_decompress(csv) == csv)

    # ── 2. 日期位移 ──────────────────────────────────────
    print('\n二、日期位移')
    got, cnt = shift_years(b'4/3/2005,x\r\n04/12/2005,y\r\n', 22)
    check('補零與不補零兩種寫法都吃,而且原樣保留',
          got == b'4/3/2027,x\r\n04/12/2027,y\r\n' and cnt == 2, repr(got))
    check('年份永遠補成 4 位數(位元組數不會亂跑)',
          shift_years(b'1/1/0999,x', 1)[0] == b'1/1/1000,x')
    check('數年份取最多的那個', max(scan_years(csv), key=scan_years(csv).get) == 2005)

    tmpdir = tempfile.mkdtemp(prefix='mvp_shift_selftest-')
    big_path = os.path.join(tmpdir, 'schedule.big')
    bak_path = big_path + '.bak'
    origin = _build_big([('mlb162_1.dat', qfs_compress_literal(csv)),
                         ('mlbspr_1.dat', other)])

    def reset():
        """回到「剛拿到的遊戲檔」那個狀態,順便把上一條餌留下的東西清乾淨。"""
        for f in os.listdir(tmpdir):
            p = os.path.join(tmpdir, f)
            if os.path.lexists(p):
                os.remove(p)
        with open(big_path, 'wb') as f:
            f.write(origin)

    def leftovers():
        """有沒有留下暫存檔沒收。"""
        return sorted(f for f in os.listdir(tmpdir)
                      if f.startswith('.') and 'schedule.big' in f)

    try:
        # ── 3. 正常流程(先證明它真的會動,後面的餌才有意義)──
        print('\n三、正常流程(陰性對照:證明每一步真的會發生)')
        reset()
        code, out, replaced = run(big_path, '2027')
        check('預覽不寫檔', code == 0 and open(big_path, 'rb').read() == origin
              and not os.path.lexists(bak_path))
        check('預覽不會把任何檔案換掉(Ctrl-C 訊息靠這個判斷)', replaced == [],
              str(replaced))

        code, out, replaced = run(big_path, '2027', '--apply')
        after = open(big_path, 'rb').read()
        check('--apply 成功、複驗過關', code == 0 and '完成。' in out, out[-200:])
        check('備份留下來了,而且跟原始檔逐位元組相同',
              os.path.isfile(bak_path) and open(bak_path, 'rb').read() == origin)
        def read_table(blob, want):
            for nm, _f, off, sz in list_entries(blob):
                if nm == want:
                    return qfs_decompress(blob[off:off + sz])
            raise AssertionError(want)
        check('賽程真的變成 2027 年,而且補零寫法原樣保留',
              b'4/3/2027' in read_table(after, 'mlb162_1.dat')
              and b'04/12/2027' in read_table(after, 'mlb162_1.dat'))
        check('沒被列進 todo 的表一個位元組都沒動'
              '(mlbspr_1.dat 也是 2005,所以它也會被改 —— 這裡驗它確實改了)',
              b'3/6/2027' in read_table(after, 'mlbspr_1.dat'))
        check('--apply 記錄了「遊戲檔被換掉」跟「做了備份」兩件事,而且分得開',
              replaced == [('backup', bak_path), ('live', big_path)], str(replaced))
        check('沒有留下任何暫存檔', leftovers() == [], str(leftovers()))
        check('跑完了不會留著「正在換」的登記(留著的話 Ctrl-C 會多講一句不存在的事)',
              _INFLIGHT == [], str(_INFLIGHT))

        code, out, replaced = run(big_path, '--restore')
        check('--restore 把檔案還原成一模一樣',
              code == 0 and open(big_path, 'rb').read() == origin, out[-200:])
        check('還原之後也沒有留下暫存檔', leftovers() == [], str(leftovers()))

        # ── 4. 餌:可預測名稱的暫存檔被人先放成符號連結 ────
        print('\n四、餌:.tmp / .part 事先被做成指向資料夾外面的符號連結')
        reset()
        outside = os.path.join(tmpdir, 'outside_target.bin')   # 假裝它在別的資料夾
        outside_body = b'PLAYER SAVE DATA' * 64
        with open(outside, 'wb') as f:
            f.write(outside_body)
        decoys = [big_path + '.tmp', bak_path + '.part', big_path + '.part']
        for d in decoys:
            os.symlink(outside, d)
        code, out, _ = run(big_path, '2027', '--apply')
        check('--apply 照樣成功(不是靠中止來避開)', code == 0, out[-200:])
        check('外面那個檔案一個位元組都沒被動到',
              open(outside, 'rb').read() == outside_body)
        check('那三個誘餌連結原封不動(代表工具根本沒去碰那些名字)',
              all(os.path.islink(d) for d in decoys))

        # ── 5. 餌:.bak 自己就是符號連結 ──────────────────
        print('\n五、餌:.bak 自己是一個指向資料夾外面的符號連結')
        reset()
        with open(outside, 'wb') as f:
            f.write(outside_body)
        os.symlink(outside, bak_path)
        before = open(big_path, 'rb').read()
        code, out, _ = run(big_path, '2027', '--apply')
        check('--apply 拒絕動手,結束碼非 0', code != 0, 'code=%r' % code)
        check('拒絕的理由講清楚是符號連結', '符號連結' in out, out[-200:])
        check('正本沒被改', open(big_path, 'rb').read() == before)
        check('連結指到的外部檔案沒被改', open(outside, 'rb').read() == outside_body)
        code, out, _ = run(big_path, '--restore')
        check('--restore 也一樣拒絕', code != 0 and '符號連結' in out, out[-200:])
        check('外部檔案還是沒被改', open(outside, 'rb').read() == outside_body)

        # ── 6. 餌:還原做到一半失敗 ───────────────────────
        print('\n六、餌:還原到 os.replace 那一步失敗')
        reset()
        run(big_path, '2027', '--apply')
        changed = open(big_path, 'rb').read()
        real_replace = os.replace

        def boom(a, b):
            raise OSError('外接硬碟被拔掉了(這是自我測試故意製造的)')

        os.replace = boom
        try:
            code, out, _ = run(big_path, '--restore')
        finally:
            os.replace = real_replace
        check('還原失敗時結束碼非 0', code != 0, 'code=%r' % code)
        check('正本原封不動,還是還原之前那一份(沒有被截成 0 或半截)',
              open(big_path, 'rb').read() == changed)
        check('失敗之後沒有留下暫存檔', leftovers() == [], str(leftovers()))
        code, out, _ = run(big_path, '--restore')
        check('把 os.replace 放回去之後,還原照樣成功(陰性對照)',
              code == 0 and open(big_path, 'rb').read() == origin)

        # ── 7. 餌:備份被截成半截 ─────────────────────────
        print('\n七、餌:.bak 是半截的(備份途中被中斷)')
        reset()
        run(big_path, '2027', '--apply')
        changed = open(big_path, 'rb').read()
        whole = open(bak_path, 'rb').read()
        with open(bak_path, 'wb') as f:
            f.write(whole[:len(whole) // 3])
        code, out, _ = run(big_path, '--restore')
        check('半截的備份被擋下來,結束碼非 0', code != 0, 'code=%r' % code)
        check('正本沒有被那份半截備份蓋掉',
              open(big_path, 'rb').read() == changed)
        with open(bak_path, 'wb') as f:
            f.write(whole)
        code, out, _ = run(big_path, '--restore')
        check('備份補回來就還原得了(陰性對照)',
              code == 0 and open(big_path, 'rb').read() == origin)

        # ── 8. 餌:算出來的東西本身就不對 ─────────────────
        # 兩道複驗要各驗一次:8a 是換名之前那一道(它應該讓遊戲檔完全不被動到),
        # 8b 把那一道拆掉,證明換名之後那一道還在,而且會自動還原。
        print('\n八、餌:寫出去的內容不對(換名前那一道)')
        reset()
        real_shift = shift_years
        globals()['shift_years'] = lambda t, d: real_shift(t, d + 5)   # 故意移錯年
        try:
            code, out, replaced = run(big_path, '2027', '--apply')
        finally:
            globals()['shift_years'] = real_shift
        check('8a 驗不過就是結束碼非 0(不可以印個 ❌ 然後回 0)', code != 0,
              'code=%r' % code)
        check('8a 沒有換名 —— 遊戲檔一個位元組都沒有動',
              open(big_path, 'rb').read() == origin and replaced == [
                  ('backup', bak_path)], str(replaced))
        check('8a 螢幕上就是這樣講的', '一個位元組都沒有動' in out, out[-300:])
        check('8a 暫存檔收乾淨了', leftovers() == [], str(leftovers()))

        print('\n八之二、餌:把換名前那一道拆掉,換名後那一道要接得住')
        reset()
        real_pre = _preverify
        globals()['_preverify'] = lambda *a, **k: None      # 假裝換名前驗過了
        globals()['shift_years'] = lambda t, d: real_shift(t, d + 5)
        try:
            code, out, replaced = run(big_path, '2027', '--apply')
        finally:
            globals()['shift_years'] = real_shift
            globals()['_preverify'] = real_pre
        check('8b 複驗沒過就是結束碼非 0', code != 0, 'code=%r' % code)
        check('8b 螢幕上有講怎麼還原', '--restore' in out, out[-300:])
        check('8b 這一輪的備份是自己做的,所以直接自動還原了',
              '已自動還原' in out and open(big_path, 'rb').read() == origin,
              out[-300:])
        check('8b 陰性對照:把那一道放回去,同樣的內容會在換名之前就被擋下來',
              _preverify is real_pre)


        # ── 9. 餌:Ctrl-C 落在四個不同的時機 ─────────────
        # ⚠️ 這一條是 2026-09-05 真的抓到東西的餌:第一版把「記錄換過檔」
        #    寫在 os.replace **後面**一行,而 CPython 是在位元碼邊界丟
        #    KeyboardInterrupt 的 —— Ctrl-C 落在那個縫隙時,檔案已經換掉了,
        #    螢幕上卻印「你的遊戲檔沒有被動到」。
        print('\n九、餌:Ctrl-C 落在四個不同的時機')
        real_fsync, real_replace = os.fsync, os.replace

        def fsync_bomb(nth):
            hit = [0]

            def f(fd):
                real_fsync(fd)
                hit[0] += 1
                if hit[0] == nth:
                    raise KeyboardInterrupt
            return f

        # (a) 連備份都還沒寫完
        reset()
        os.fsync = fsync_bomb(1)
        try:
            code, out, replaced = run(big_path, '2027', '--apply')
        finally:
            os.fsync = real_fsync
        check('(a) 備份還沒寫完就 Ctrl-C:沒有任何檔案被換掉',
              code == 130 and replaced == []
              and open(big_path, 'rb').read() == origin
              and not os.path.lexists(bak_path), str(replaced))
        check('(a) 沒有留下暫存檔', leftovers() == [], str(leftovers()))

        # (b) 備份寫好了,遊戲檔還沒換
        reset()
        os.fsync = fsync_bomb(2)
        try:
            code, out, replaced = run(big_path, '2027', '--apply')
        finally:
            os.fsync = real_fsync
        check('(b) 備份剛做好就 Ctrl-C:記到的是備份、不是遊戲檔',
              code == 130 and replaced == [('backup', bak_path)]
              and open(big_path, 'rb').read() == origin, str(replaced))
        check('(b) 那份備份是完整的(不是半截)',
              open(bak_path, 'rb').read() == origin)

        # (c) 換名已經成功,但登記還沒跑到 —— 三態裡「正在換」的那一格。
        #     這裡是自己 raise KeyboardInterrupt,不是送訊號:它繞過訊號處理器,
        #     等於模擬「_NoInterrupt 裝不上去的環境」(不是主執行緒之類)。
        #     那時候程式不知道換成功了沒有,就要說不知道 ——
        #     不可以說「沒動到」(檔案其實已經換掉了),也不該打包票說「已經換掉」。
        reset()

        def replace_bomb(a, b):
            real_replace(a, b)
            if os.fspath(b) == big_path:
                raise KeyboardInterrupt      # 換完了才中斷 —— 最容易講錯話的那格
            return None

        os.replace = replace_bomb
        try:
            code, out, replaced = run(big_path, '2027', '--apply')
        finally:
            os.replace = real_replace
        check('(c) 卡在換名那一步:結束碼 130,而且檔案真的已經換掉了',
              code == 130 and open(big_path, 'rb').read() != origin,
              'code=%r' % code)
        check('(c) 這時候絕對不可以說「沒有動到」',
              '沒有被動到' not in out and '正在替換' in out, out[-300:])
        check('(c) 而且要把還原指令給他', '--restore' in out, out[-300:])
        check('(c) 這時候 .bak 還在,還原得回去',
              run(big_path, '--restore')[0] == 0
              and open(big_path, 'rb').read() == origin)

        # (d) 真的送一次 SIGINT,而且剛好落在「換名 + 登記」中間。
        #     這一格才是 _NoInterrupt 存在的理由:訊號會被先記著,
        #     等那兩行跑完才丟出來,所以收尾看到的登記跟磁碟一定一致。
        #     ⚠️ 這條餌會紅的話,長相是「說成正在替換」或更糟的「說沒動到」——
        #        本站拿「把 _NoInterrupt.__enter__ 改成什麼都不裝」的變體驗過,
        #        它確實會掉到 (c) 那一格去。
        if can_signal:
            reset()

            def replace_then_signal(a, b):
                real_replace(a, b)
                if os.fspath(b) == big_path:
                    send_sigint()
                return None

            os.replace = replace_then_signal
            try:
                code, out, replaced = run(big_path, '2027', '--apply')
            finally:
                os.replace = real_replace
            check('(d) 真訊號落在不可中斷段裡:結束碼 130、檔案真的換了',
                  code == 130 and open(big_path, 'rb').read() != origin,
                  'code=%r' % code)
            check('(d) 登記跟磁碟一致 —— 講的是「已經換過了」,不是「正在替換」',
                  ('live', big_path) in replaced and '已經換過了' in out
                  and '正在替換' not in out, str(replaced) + out[-300:])
            check('(d) 還原指令有印出來', '--restore' in out, out[-300:])
            check('(d) 跑完不會留著「正在換」的登記', _INFLIGHT == [], str(_INFLIGHT))
            check('(d) 還原得回去',
                  run(big_path, '--restore')[0] == 0
                  and open(big_path, 'rb').read() == origin)
        else:
            print('  · (d) 這台送不出 SIGINT,跳過(還沒實測的環境)')


        # ── 10. 目錄與格式把關 ───────────────────────────
        print('\n十、格式把關')
        reset()
        os.remove(bak_path) if os.path.lexists(bak_path) else None
        with open(bak_path, 'wb') as f:
            f.write(b'NOTBIGF' + b'\x00' * 500)
        code, out, _ = run(big_path, '--restore')
        check('不是 BIGF 的備份會被擋', code != 0 and 'BIGF' in out, out[-200:])
        reset()
        code, out, _ = run(big_path, '2027')
        check('年份超出 1900-2999 會被擋', run(big_path, '20270')[0] != 0)
        check('沒有 .bak 就 --restore 會講清楚找不到備份',
              run(big_path, '--restore')[0] != 0)

        # ── 11. 餌:你在指令列上給的那個路徑自己是符號連結 ────
        # ⚠️ 這一條是 2026-09-06 補的:上一版讀到連結會 realpath 之後**照樣寫**。
        #    寫到的檔案跟他打的那個路徑不是同一個名字,而螢幕上一個字都不提 ——
        #    等於替他決定去改資料夾外面的東西。現在要動手的兩條路一律停手,
        #    唯讀那條路照舊(只是讀,跟著連結走沒有風險)。
        print('\n十一、餌:你給的路徑自己是一個指向別處的符號連結')
        reset()
        outside_big = os.path.join(tmpdir, 'somewhere_else.big')
        with open(outside_big, 'wb') as f:
            f.write(origin)
        outside_sha = _sha256(outside_big)
        link = os.path.join(tmpdir, 'link.big')
        os.symlink(outside_big, link)
        code, out, replaced = run(link, '2027')
        check('(陰性對照)預覽照樣看得到,而且有講它跟到哪裡去',
              code == 0 and '符號連結' in out, out[-200:])
        check('(陰性對照)預覽一個檔都沒動', replaced == []
              and _sha256(outside_big) == outside_sha)
        code, out, replaced = run(link, '2027', '--apply')
        check('--apply 拒絕跟著連結寫,結束碼非 0', code != 0, 'code=%r' % code)
        check('拒絕的時候有講清楚是符號連結', '符號連結' in out, out[-200:])
        check('連結指到的那個檔一個位元組都沒被動到',
              _sha256(outside_big) == outside_sha)
        check('連結本身還是連結(沒有被換成實體檔)', os.path.islink(link))
        check('也沒有在旁邊生出 .bak', not os.path.lexists(link + '.bak')
              and not os.path.lexists(outside_big + '.bak'))
        code, out, replaced = run(link, '--restore')
        check('--restore 也一樣拒絕', code != 0 and '符號連結' in out, out[-200:])
        check('拒絕之後那個檔還是原樣', _sha256(outside_big) == outside_sha)

        # ── 12. 餌:失敗就發生在「做備份」那一步 ──────────
        # ⚠️ 2026-09-11 補的餌,補之前它是紅的:.bak 的狀態其實有三種,
        #    舊版只講兩種。備份自己失敗的時候 backup_made 是 False,
        #    於是印出「沿用你原本就有的那一份,沒有被動到」——
        #    可是旁邊根本沒有 .bak。讀者照這句話以為自己有備份,
        #    那是本站最不能犯的錯,所以它要有一條自己的餌守著。
        print('\n十二、餌:做備份那一步就失敗(磁碟滿 / 外接碟被拔掉)')

        def fsync_oserror(nth):
            hit = [0]

            def f(fd):
                hit[0] += 1
                if hit[0] == nth:
                    raise OSError('外接硬碟被拔掉了(這是自我測試故意製造的)')
                return real_fsync(fd)
            return f

        reset()
        os.fsync = fsync_oserror(1)          # 第一次 fsync 就是在寫 .bak
        try:
            code, out, replaced = run(big_path, '2027', '--apply')
        finally:
            os.fsync = real_fsync
        check('(12) 備份做不出來就結束碼非 0', code != 0, 'code=%r' % code)
        check('(12) 而且真的沒有 .bak 留下來', not os.path.lexists(bak_path))
        check('(12) 絕對不可以說「沿用你原本就有的那一份」(那是假的)',
              '沿用你原本就有的那一份' not in out and '沒有建起來' in out, out[-300:])
        check('(12) 遊戲檔一個位元組都沒有動',
              replaced == [] and open(big_path, 'rb').read() == origin, str(replaced))
        check('(12) 沒有留下暫存檔', leftovers() == [], str(leftovers()))

        # 陰性對照:.bak 本來就在、失敗發生在寫遊戲檔那一步 ——
        # 這時候「沿用你原本就有的那一份」才是真話,那一句要照樣印得出來。
        reset()
        shutil.copyfile(big_path, bak_path)
        bak_before = open(bak_path, 'rb').read()
        os.fsync = fsync_oserror(1)          # .bak 已存在,所以第一次 fsync 是寫遊戲檔
        try:
            code, out, replaced = run(big_path, '2027', '--apply')
        finally:
            os.fsync = real_fsync
        check('(12 陰性對照) .bak 本來就在,「沿用你原本就有的那一份」才印得出來',
              code != 0 and '沿用你原本就有的那一份' in out, out[-300:])
        check('(12 陰性對照) 那份舊備份確實沒有被動到',
              open(bak_path, 'rb').read() == bak_before)
        check('(12 陰性對照) 遊戲檔也沒有被動到',
              open(big_path, 'rb').read() == origin)

        # 直接對 _interrupt_report() 下餌:塞一筆它認不得的種類進去。
        # 舊版那句 elif _REPLACED 會把它講成「遊戲檔沒有被動到」——
        # 種類是這一輪才多出第三個('restore'),第四個遲早也會有,
        # 所以「認不得就承認不確定」這件事要有自己的餌守著。
        del _REPLACED[:]
        del _INFLIGHT[:]
        _REPLACED.append(('未來才會有的種類', big_path))
        _rep = '\n'.join(_interrupt_report())
        del _REPLACED[:]
        check('(12b) 認不得的登記種類不會被講成「遊戲檔沒有被動到」',
              '沒有被動到' not in _rep and '請自己看一下' in _rep, _rep)

        # ── 13. 餌:--restore 剛換名成功就被 Ctrl-C 打斷 ──
        # ⚠️ 2026-09-11 補的餌,補之前它也是紅的:還原沿用 --apply 那一句
        #    「已經換過了 / 要回到動手之前,請跑 --restore」。方向剛好相反 ——
        #    他跑的就是 --restore,那個檔已經是 .bak 那一份了,
        #    叫他「回到動手之前」等於要他撤銷掉自己剛做完的還原。
        if can_signal:
            print('\n十三、餌:--restore 換名成功的那一瞬間收到真訊號')
            reset()
            run(big_path, '2027', '--apply')

            def replace_then_signal_any(a, b):
                real_replace(a, b)
                if os.fspath(b) == big_path:
                    send_sigint()
                return None

            os.replace = replace_then_signal_any
            try:
                code, out, replaced = run(big_path, '--restore')
            finally:
                os.replace = real_replace
            check('(13) 結束碼 130,而且檔案真的已經換回備份那一份',
                  code == 130 and open(big_path, 'rb').read() == origin,
                  'code=%r' % code)
            check('(13) 登記記成 restore,不是 live',
                  ('restore', big_path) in replaced
                  and ('live', big_path) not in replaced, str(replaced))
            check('(13) 講的是「還原已經做完了」,不是叫他回到動手之前',
                  '還原已經做完了' in out and '要回到動手之前' not in out, out[-300:])
            check('(13) 再跑一次還原照樣成功(跑幾次結果都一樣)',
                  run(big_path, '--restore')[0] == 0
                  and open(big_path, 'rb').read() == origin)
            check('(13) 跑完不會留著「正在換」的登記', _INFLIGHT == [], str(_INFLIGHT))
            check('(13) 沒有留下暫存檔', leftovers() == [], str(leftovers()))

            # 陰性對照:同一招打在 --apply 上,講的要是相反的那一句 ——
            # 證明這兩條路現在真的分開講話,不是我把訊息通通改掉了。
            reset()
            os.replace = replace_then_signal_any
            try:
                _c2, _apply_out, _r2 = run(big_path, '2027', '--apply')
            finally:
                os.replace = real_replace
            check('(13 陰性對照) 同一招打在 --apply 上,講的就是「要回到動手之前」',
                  _c2 == 130 and '要回到動手之前' in _apply_out
                  and '還原已經做完了' not in _apply_out, _apply_out[-200:])
            check('(13 陰性對照) --apply 那一輪登記的是 live',
                  ('live', big_path) in _r2, str(_r2))
        else:
            print('  · (13) 這台送不出 SIGINT,跳過(還沒實測的環境)')
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

    print('\n' + '-' * 46)
    if fails:
        print('✗ %d 項沒過:%s' % (len(fails), ', '.join(fails)))
        return 1
    print('✓ 全部 %d 項通過。' % n_ok[0])
    return 0


def _verify_blob(blob, target):
    """把一份寫好的 schedule.big 重新解析一次,回傳
    (項目清單, 未對齊日期數, 解不開的表, 出現過哪些年份)。

    換名之前驗暫存檔、換名之後驗正本,兩次都走這一個函式 ——
    兩邊用同一把尺,才不會出現「寫出去之前說好、讀回來說壞」這種沒人解釋得了的事。

    ⚠️ 這裡一定要接例外。掃描階段刻意放過「解不開的那一項」,複驗階段卻對同一項
       再解一次;不接的話,換名之後這裡一炸就是整支噴 traceback ——
       使用者看不到複驗結果、看不到還原指令,只會以為工具把他的賽程檔弄壞了。
       2026-09-05 實測過。但也不能無聲跳過:動手前解得開、寫完卻解不開,
       那才是真的寫壞了,所以記下來交給呼叫的人跟動手之前那一批比對。
    """
    entries = list_entries(blob)
    off_target = 0
    now, bad = set(), set()
    for name, field, offset, size in entries:
        try:
            text = qfs_decompress(blob[offset:offset + size])
        except (ValueError, IndexError):
            bad.add(name)
            continue
        ys = scan_years(text)
        now |= set(ys)
        # 允許跨年賽季落在目標年前後一年,其餘視為沒改到
        off_target += sum(v for y, v in ys.items() if not target - 1 <= y <= target + 1)
    return entries, off_target, bad, now


def _preverify(tmp_path, target, n_before, skipped):
    """換名**之前**先把暫存檔重讀一次。過關回傳 None,不然回傳一句人看得懂的原因。

    ⚠️ 為什麼要在換名之前多驗這一次(2026-09-06 加):原本只有換名之後那一次,
       而那時候玩家的賽程檔**已經被換掉了** —— 驗出問題只能靠自動還原補救。
       改成先驗暫存檔:沒過就不換名,把暫存檔刪掉就好,
       「遊戲檔一個位元組都沒有動」這句話才講得出口。
       換名之後那一次照樣留著:磁碟真的騙人的時候(寫進去跟讀回來不一樣),
       只有從正本讀回來才驗得到。兩次不是重複,是兩件不同的事。
    """
    try:
        with open(os.fspath(tmp_path), 'rb') as f:
            blob = f.read()
        entries, off_target, bad, _years = _verify_blob(blob, target)
    except (BigFormatError, ValueError, IndexError, struct.error, OSError) as e:
        return '重讀不回來(%s)' % (e or e.__class__.__name__)
    if len(entries) != n_before:
        return '項目數變成 %d 個,動手之前是 %d 個' % (len(entries), n_before)
    if off_target:
        return '有 %d 個日期沒有落在 %d 年前後' % (off_target, target)
    if bad != skipped:
        return ('解不開的表跟動手之前不是同一批(現在 %d 個,動手之前 %d 個)'
                % (len(bad), len(skipped)))
    return None



def main():
    """指令列入口。回傳值就是行程的結束碼:0 是成功或預覽完成,1 是有問題。

    三種模式(預覽 / --apply / --restore)共用同一段解析與掃描,
    所以你在預覽看到的那張表,就是加上 --apply 之後真的會做的事。
    """
    # 不用 argparse:位置參數只有兩個(檔案、年份),旗標只有兩個,自己切最短也最好讀。
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    flags = {a for a in sys.argv[1:] if a.startswith('--')}
    # --selftest 擺在最前面:它不需要遊戲檔,也不該被「沒給路徑」擋掉。
    if '--selftest' in flags:
        return _selftest()
    if not args:
        print(__doc__)
        return 1

    big = Path(args[0]).expanduser()
    # 你在指令列上給的那個路徑自己是符號連結的話:
    # 寫回是「寫暫存檔再 os.replace」,而 os.replace 換掉的是**連結本身**:
    # 連結會變成一個普通檔,真正那一份原封不動被孤立在原處,螢幕上照樣印「完成。」
    # 之後你對「真正那一份」做的修改就再也不會生效,而且完全看不出來。
    # 2026-09-05 實測過。Windows 讀者幾乎碰不到,Mac / Linux 才有。
    #
    # ⚠️ 2026-09-06 訂正:上一版的做法是「跟著連結走到它指向的那個檔,然後照樣寫」。
    #    那比「把連結本身換成實體檔」好(至少動到的是同一份資料),但仍然是
    #    替使用者決定去改資料夾外面的東西 —— 要改哪一個檔應該由他自己講明白。
    #    所以會動手的那兩條路一律停下來;唯讀那條路不受限:
    #    只是讀,跟著連結走沒有風險。
    if big.is_symlink():
        if '--apply' in flags or '--restore' in flags:
            print(f'✗ 你給的這個路徑是一個符號連結:{big}')
            print('  本工具不跟著符號連結寫檔 —— 它指到的那個檔可能根本不在這個資料夾裡。')
            print('  請把真正那個檔的路徑直接給它,或把它換成實體檔,再跑一次。')
            print('  (目前沒有動到任何檔案。)')
            return 1
        _real = Path(os.path.realpath(os.fspath(big)))
        print(f'· 這是符號連結,預覽跟著它走到:{_real}')
        print('  (真的要改請直接給上面那個路徑 —— 動手的時候本工具不跟著連結寫。)')
        big = _real
    # 備份固定叫「原檔名 + .bak」,就放在原檔旁邊:玩家看得到,也刪得掉。
    backup = big.with_suffix(big.suffix + '.bak')

    # ── 還原 ──────────────────────────────────────────
    # ⚠️ 還原這條路**故意不先檢查正本在不在**。原本是先擋掉「找不到檔案」才進來,
    #    結果「正本已經被刪掉、只剩 .bak」這個最需要還原的情況反而被自己擋住,
    #    印的是「✗ 找不到檔案」。2026-09-05 實測過。
    #    路徑打錯也不會因此亂寫檔:備份檔名是從你給的那個路徑推出來的,
    #    路徑錯 → .bak 也不存在 → 下面第一道就擋掉了。
    if '--restore' in flags:
        # 還原一共五道把關,由淺到深:備份在不在 → 備份是 BIGF 嗎 →
        # (正本若還在)它也是 BIGF 嗎 → 備份的目錄解不解得開 →
        # 目錄裡真的有賽程表嗎。全過了才交給 _restore_from_backup,
        # 它會再驗一次檔頭宣告的長度;複製完還會整份比對一次才敢說「已還原」。
        if os.path.islink(os.fspath(backup)):
            # ⚠️ 這裡不可以用 backup.is_file()/exists():它們會跟著連結走,
            #    連結指到的檔存在就一路通過。要用 os.path.islink(走 lstat)。
            print(f'✗ 備份檔是一個符號連結:{backup}')
            print('  本工具不跟著符號連結還原 —— 連結指到的那一份未必是這個遊戲的備份。')
            print('  請把它刪掉或改名,再把真正的備份放回來。')
            return 1
        if not backup.is_file():
            print(f'✗ 找不到備份:{backup}')
            return 1
        # ⚠️ 還原前一定要確認這兩個檔真的是封裝檔。
        #    本站好幾課都會留下 .bak,如果使用者拖錯檔案,
        #    這裡會拿別課的舊快照蓋掉現在這個檔,而且完全看不出來。
        #    2026-08-25 上線前稽核抓到的,補上這道把關。
        if backup.read_bytes()[:4] != b'BIGF':
            print(f'✗ 這個備份不是本工具建立的:{backup.name}')
            print('  它的開頭不是 BIGF,不敢拿它覆蓋任何東西。')
            return 1
        if not big.exists():
            # 正本不見了 —— 這正是備份存在的意義,照樣讓他還原回去。
            print(f'· {big.name} 已經不在了,將直接從備份重建。')
        elif not big.is_file():
            print(f'✗ 要還原的目標不是一個檔案:{big}')
            return 1
        elif big.read_bytes()[:4] != b'BIGF':
            print(f'✗ 要還原的目標不是封裝檔:{big.name}')
            print('  路徑可能指錯了。')
            return 1
        # ⚠️ 這裡原本查的是備份裡有沒有 b'schedule' 這個字。
        #    那是憑印象寫的 —— schedule.big 從頭到尾根本沒有這個字,
        #    它的項目叫 a140_1.dat / mlb162_1.dat 那些。結果是這道把關
        #    擋掉了「所有」合法還原:照教學改完、螢幕上印著還原指令,
        #    一跑就被自己的工具攔下來,還說「這可能是別的教學的備份」。
        #    改成查 TOC 裡真的存在的東西。
        try:
            bak_entries = {e[0] for e in list_entries(backup.read_bytes())}
        except Exception as e:
            print(f'✗ 這個備份解不開:{backup.name}({e})')
            print('  它的目錄結構壞了,不敢拿它覆蓋任何東西。')
            return 1
        if 'mlb162_1.dat' not in bak_entries:
            print(f'✗ 這個備份看起來不是賽程表:{backup.name}')
            print('  裡面找不到 mlb162_1.dat(大聯盟 162 場的賽程)。')
            print(f'  它裝的是:{", ".join(sorted(bak_entries)[:5])}')
            return 1
        # ⚠️ _restore_from_backup 會丟 OSError(磁碟滿、外接碟被拔掉、
        #    寫出來的內容跟備份對不上)。不接的話使用者看到的是一整片 traceback,
        #    而他當下最想知道的其實只有一句:「我的檔還在不在?」
        #    還原是原子的,失敗時正本原封不動 —— 那就把這句話直接講給他聽。
        try:
            _restore_from_backup(backup, big)
        except OSError as e:
            print(f'✗ 還原失敗:{e}')
            print(f'  {big.name} 沒有被動到,還是還原之前那一份。')
            print(f'  備份也還在:{backup.name}')
            return 1
        # 印「已還原」之前,先真的確認它還原成功了。
        # ⚠️ 比的是**整份內容**,不是大小、不是開頭那幾個位元組,
        #    也不可以用 zip() 逐段比 —— zip() 會在短的那一邊停下來,
        #    正本被截短反而會比出「完全相同」。賽程檔只有幾百 KB,整份讀回來比最實在。
        if backup.read_bytes() != big.read_bytes():
            print(f'✗ 還原後的內容跟備份對不上:{big.name}')
            print(f'  請直接把 {backup.name} 手動複製成 {big.name}。')
            return 1
        print(f'✓ 已從備份還原:{backup.name} → {big.name}')
        return 0

    # 還原以外的路都需要正本還在(要改的就是它)。
    if not big.is_file():
        print(f'✗ 找不到檔案:{big}')
        return 1

    if len(args) < 2:
        print('✗ 請指定目標年份,例如:')
        print(f'    python3 {Path(sys.argv[0]).name} "{big}" 2027')
        return 1
    try:
        target = int(args[1])
    except ValueError:
        print(f'✗ 目標年份必須是數字,收到「{args[1]}」')
        return 1
    # 年份限在 1900 到 2999:四位數是格式的硬性要求(寫回去要剛好 4 位),
    # 手滑打成 20030 這種值也會在這裡被擋下來,不會有機會寫進檔案。
    if not 1900 <= target <= 2999:
        print(f'✗ 目標年份 {target} 超出合理範圍(1900-2999)')
        return 1

    # 整個檔一次讀進記憶體再改。schedule.big 只有幾百 KB,不必做串流處理。
    # 用 bytearray 是因為等一下要就地覆寫目錄那 8 個位元組與檔頭那 4 個。
    data = bytearray(big.read_bytes())
    print(f'檔案    {big}')
    print(f'大小    {len(data):,} bytes')

    try:
        entries = list_entries(bytes(data))
    except BigFormatError as e:
        print(f'\n✗ {e}')
        print('  請確認選到的是遊戲 data/database 資料夾裡的 schedule.big')
        return 1
    print(f'內含    {len(entries)} 個賽程表\n')

    # ── 掃描各表年份 ──────────────────────────────────
    plans = []
    print(f"  {'賽程表':<16}{'狀態':<10}{'目前年份':<14}{'場次':>7}{'位移':>7}")
    print('  ' + '-' * 56)
    # 逐項解開來看:先試著解壓(不是壓縮資料會原樣回來),再數年份。
    # 解不開的那一項只印一行就跳過,不讓整支停下來,其他表照樣可以改。
    #
    # ⚠️ 這裡**不能只接 ValueError**。qfs_decompress 碰到「指令流被切掉一半」的
    #    壞檔時,是在 data[pos + 1] 那幾行直接 IndexError。2026-09-05 實測:
    #    把某一項 TOC 的長度欄砍成一半,舊版整支噴 traceback,九個表一個都印不出來,
    #    跟上面這行註解自己寫的「不讓整支停下來」剛好相反。
    #    只接這兩種,是因為 qfs_decompress 就只會丟這兩種 —— 多寫幾種等於騙人。
    skipped = set()          # 動手之前就解不開的表,等一下複驗要允許它同樣解不開
    for name, field, offset, size in entries:
        raw = bytes(data[offset:offset + size])
        try:
            text = qfs_decompress(raw)
        except (ValueError, IndexError) as e:
            # IndexError 的原文只有「index out of range」,對讀者沒有意義,
            # 換成講人話的那一句(它就只有「被截斷」這一種成因)。
            why = e if isinstance(e, ValueError) else '這一項的資料被截斷了(解壓指令讀到檔案結尾)'
            print(f'  {name:<16}解壓失敗:{why}')
            skipped.add(name)
            continue
        # 記住這一項原本有沒有壓縮,寫回去時照原樣處理:
        # 不把本來是純文字的表擅自壓起來,也不把壓縮的表攤成純文字。
        packed = raw[:2] == b'\x10\xFB'
        years = scan_years(text)
        if not years:
            print(f'  {name:<16}{"(無日期)":<12}')
            continue
        # 每一表自己算自己的位移。實際檔案裡各表原本的年份常常不一致
        # (原版春訓是 2005、主賽程可能被模組換過),各算各的才有辦法一起對齊到同一年。
        main_year = max(years, key=years.get)          # 以該表最多的年份為基準
        delta = target - main_year
        total = sum(years.values())
        ylabel = '/'.join(str(y) for y in sorted(years))
        print(f'  {name:<16}{"壓縮" if packed else "純文字":<10}{ylabel:<14}{total:>7,}{delta:>+7d}')
        plans.append((name, field, offset, size, text, packed, main_year, delta))

    if not plans:
        print('\n✗ 這個 .big 裡找不到任何含日期的賽程表')
        print('  請確認選到的是 data/database/schedule.big')
        return 1

    # 位移是 0 的表(已經是目標年)完全不碰:不重寫、不重壓、也不接到檔尾。
    todo = [p for p in plans if p[7] != 0]
    if not todo:
        print(f'\n全部賽程表已經是 {target} 年,沒有需要改的地方。')
        return 0

    total_dates = sum(sum(scan_years(p[4]).values()) for p in todo)
    print(f'\n目標 {target} 年 · 每個表各自位移到該年')
    print(f'將改寫 {len(todo)} 個賽程表、共 {total_dates:,} 個日期')
    if len(todo) < len(plans):
        print(f'({len(plans) - len(todo)} 個表已是 {target} 年,跳過)')

    # 沒有 --apply 就在這裡停。到目前為止每一行都只是讀檔與印字。
    if '--apply' not in flags:
        print('\n這是預覽,沒有改到任何檔案。')
        print('確定要套用請加上 --apply：')
        print(f'\n  python3 {Path(sys.argv[0]).name} "{big}" {target} --apply\n')
        return 0

    # ── 實際套用 ──────────────────────────────────────
    # 只在第一次備份。已經有 .bak 就保留最早那一份,那才是「原始的」;
    # 蓋掉的話,改了兩輪之後就再也回不到出廠狀態了。
    if os.path.islink(os.fspath(backup)):
        # ⚠️ 連結指到的地方通常在別的資料夾。真讓它過關的話,「備份已存在,保留不覆蓋」
        #    這句話會是假的 —— 玩家的原始檔其實從來沒被備份到。
        #    也不可以用 backup.exists() 判斷:連結指到的檔不存在時它回 False。
        print(f'✗ 備份檔是一個符號連結:{backup}')
        print('  本工具不跟著符號連結寫檔,也不把它當成有效的備份。')
        print('  請先把它刪掉或改名,再重跑一次。')
        return 1
    # ⚠️ 這一段會碰兩個檔:.bak 與正本。一支只改一個遊戲檔的工具談不上
    #    「要嘛全做要嘛全不做」,但「中途停下來的時候,哪一個檔現在是什麼狀態」
    #    一定要講得出來 —— 使用者當下最想知道的就只有這件事。
    #    所以下面整段包在一起,OSError(磁碟滿、外接碟被拔掉、權限不足)
    #    一律逐檔講清楚再回非 0,不要噴一整片 traceback 給讀者看。
    #    Ctrl-C 走的是同一條誠實路徑,只是收尾的話在 _interrupt_report() 裡。
    backup_made = False
    try:
        if not backup.exists():
            _atomic_copy(big, backup)
            backup_made = True
            print(f'\n✓ 已備份原始檔:{backup.name}')
        else:
            print(f'\n· 備份已存在,保留不覆蓋:{backup.name}')

        # ⚠️ 這裡是整支最要小心的地方,鐵律是「只接不改」。
        #    新資料接到檔尾,然後只覆寫兩個地方:那一項目錄的 8 個位元組
        #    (位移與長度,大端),加上檔頭第 4 到 8 個位元組的總長度(小端)。
        #    舊資料原封不動留在檔案中間,只是沒有人指向它了,檔案因此會變大。
        #    絕對不可以改成「全部讀出來再重新打包」:封裝檔裡常有目錄沒指到的
        #    孤兒資料,重新打包會把它們整包丟掉。詳見本站的 BIGF 格式頁。
        #
        #    改動全部做在記憶體裡那份 data 上,再整份寫到一個暫存檔 ——
        #    玩家那個檔在「最後換名」之前完全沒有被打開來寫過。
        changed = 0
        for name, field, offset, size, text, packed, _, delta in todo:
            new_text, n = shift_years(text, delta)
            changed += n
            payload = qfs_compress_literal(new_text) if packed else new_text
            new_offset = len(data)
            data += payload                                        # 接到檔尾
            data[field:field + 8] = struct.pack('>II', new_offset, len(payload))
            data[4:8] = struct.pack('<I', len(data))               # 更新檔頭總長

        # 先寫暫存檔再換掉,不要直接截斷原檔重寫。
        # 中途被中斷的話,原檔會停在半殘狀態;雖然 .bak 還在,
        # 但使用者不會知道發生了什麼。2026-08-25 上線前稽核統一。
        #
        # ⚠️ 2026-09-05 資安稽核:暫存檔原本固定叫「原檔名 + .tmp」。名字猜得到,
        #    事先在那裡放一個指向資料夾外面的符號連結,open(..., 'wb') 就會跟過去,
        #    把外面那個檔案截成 0 —— 而且是發生在 os.replace 之前,
        #    所以「os.replace 只換掉連結本身」救不了它。
        #    改用 tempfile.mkstemp(同一個資料夾、O_CREAT|O_EXCL、隨機名字):
        #    名字被佔用就直接開檔失敗,不會跟著連結走。
        # 原檔的權限位元要一起帶到新檔上。os.replace 換掉的是「整個檔」,
        # 新檔的權限來自 umask(mkstemp 更嚴,只給 0600);原檔若本來是 644,
        # 不帶過去的話改完就變成只有自己讀得到。反過來原檔是 600 的話,
        # 用 open() 產生的新檔會鬆成 644,同一台機器的其他使用者也讀得到。
        # 2026-09-05 實測:兩個方向都會發生。Windows 走資料夾 ACL 繼承,不受影響。
        try:
            _mode = os.stat(os.fspath(big)).st_mode & 0o7777
        except OSError:
            _mode = None
        # 開檔之前再看一次「正本是不是符號連結」。最前面那一道是在讀檔之前做的,
        # 這中間如果有人把它換掉,只有這一道攔得到。多驗一次不花錢。
        _refuse_if_symlink(big, '要寫入的遊戲檔')
        _fd, _tmp = _unique_temp(big, 'tmp')
        _pre_bad = None
        try:
            with os.fdopen(_fd, 'wb') as _f:
                _f.write(bytes(data))
                _f.flush()
                os.fsync(_f.fileno())
            if _mode is not None:
                try:
                    os.chmod(_tmp, _mode)
                except OSError:
                    # 權限沒帶過去不算致命(檔案內容是對的),不要因此中斷寫入。
                    pass
            # ── 換名之前先自驗一次 ──────────────────────────
            # 沒過就**不換名**:玩家的賽程檔到這一刻為止一個位元組都沒被動過,
            # 把暫存檔刪掉就乾淨了。理由見 _preverify() 的說明。
            _pre_bad = _preverify(_tmp, target, len(entries), skipped)
            if _pre_bad is None:
                # 換名與登記是同一步,中間插不進 Ctrl-C(見 _replace_and_record)。
                _replace_and_record(_tmp, big, 'live')
        except BaseException:
            # 中途爆掉(含 Ctrl-C)就把暫存檔收乾淨,正本維持它原本的樣子。
            try:
                if os.path.lexists(_tmp):
                    os.remove(_tmp)
            except OSError:
                pass
            raise
        if _pre_bad is not None:
            try:
                if os.path.lexists(_tmp):
                    os.remove(_tmp)
            except OSError:
                pass
            print('\n✗ 寫出來的那一份自己驗不過:%s' % _pre_bad)
            print(f'  所以沒有換名。{big.name} 一個位元組都沒有動,還是你原本那一份。')
            print('  那個暫存檔也刪掉了。')
            if backup_made:
                print(f'  剛才建的 {backup.name} 留著,它的內容就是你現在手上這一份。')
            print('  請把上面那一行連同你的 schedule.big 大小回報給本站。')
            return 1
    except OSError as _e:
        # 逐檔講清楚誰動了、誰沒動。「沒動到」這句話要有根據 ——
        # 根據就是 _REPLACED:換名成功才會有那一筆。
        _live_done = ('live', os.fspath(big)) in _REPLACED
        print(f'\n✗ 寫入過程失敗:{_e}')
        # ⚠️ 2026-09-11 修:.bak 的狀態有**三**種,原本只講兩種。
        #    失敗如果就發生在做備份那一步(磁碟滿、外接碟被拔掉),
        #    backup_made 是 False,而舊版這時會印「沿用你原本就有的那一份,沒有被動到」——
        #    可是那一份根本沒有建起來,旁邊一個 .bak 都沒有。
        #    讀者照著這句話以為自己有備份,那正是本站最不能犯的錯。
        #    2026-09-11 實測(餌 A):第一次 fsync 丟 OSError,舊版當場印出那句假話。
        if backup_made:
            print(f'  · {backup.name}:這一輪剛做好的,內容是動手之前的原檔。')
        elif os.path.lexists(os.fspath(backup)):
            print(f'  · {backup.name}:沿用你原本就有的那一份,沒有被動到。')
        else:
            print(f'  · {backup.name}:沒有建起來 —— 失敗就發生在做備份這一步,'
                  f'現在旁邊沒有備份。')
        if _live_done:
            print(f'  · {big.name}:已經換成新的那一份了。要回到動手之前:')
            print(f'    python3 {Path(sys.argv[0]).name} "{big}" --restore')
        else:
            print(f'  · {big.name}:一個位元組都沒有動,還是你原本那一份。')
        return 1

    # ── 寫入後複驗 ────────────────────────────────────
    # 複驗是「重新從磁碟讀回來」,不是拿記憶體裡那份 data 再算一次。
    # 拿記憶體那份驗等於自己驗自己,寫檔那一步出錯也照樣印全對。
    #
    # 跟換名之前那一次用的是同一個函式(_verify_blob),差別只在讀的是誰:
    # 那一次讀暫存檔,這一次讀已經扶正的正本。兩次都要,因為它們抓的不是同一種錯 ——
    # 前一次抓「我算出來的東西本身就不對」,這一次抓「寫出去跟讀回來不一樣」。
    check = big.read_bytes()
    ok_entries, off_target, bad, now = _verify_blob(check, target)

    print(f'\n✓ 已寫入 {big.name}')
    print(f'  項目數     {len(ok_entries)} 個(原本 {len(entries)} 個)')
    print(f'  檔案大小   {len(check):,} bytes')
    print(f'  改寫日期   {changed:,} 個')
    print(f'  現在年份   {"/".join(str(y) for y in sorted(now))}')
    print(f'  未對齊日期   {off_target} 個(應為 0)')
    print(f'  解不開的表   {len(bad)} 個(動手之前就解不開的有 {len(skipped)} 個)')
    # 三個條件都要成立才算過:項目數沒變(代表目錄沒被寫壞)、
    # 沒有任何一個日期落在目標年前後一年之外、
    # 而且「解不開的表」跟動手之前是同一批(沒有哪個表是被這支寫壞的)。
    if len(ok_entries) == len(entries) and off_target == 0 and bad == skipped:
        print(f'\n完成。開遊戲進入「新賽季」就會看到 {target} 年的賽程。')
        print(f'要還原:python3 {Path(sys.argv[0]).name} "{big}" --restore')
        return 0
    # ⚠️ 複驗沒過不能只印一個 ❌ 了事 —— 檔案**已經被換掉了**。
    #    這一輪如果是本工具自己剛做的備份,那份備份就等於「跑這支之前的樣子」,
    #    直接還原回去最安全,而且還原本身是原子的(對完 SHA-256 才 os.replace)。
    #    備份若是上一輪留下來的就不自動動手:那未必是他這次想回到的狀態,
    #    只把指令印出來讓他自己決定。兩條路都 return 1。
    print('\n✗ 複驗未通過。')
    _cmd = f'python3 {Path(sys.argv[0]).name} "{big}" --restore'
    if backup_made:
        try:
            _restore_from_backup(backup, big)
            print(f'  已自動還原成剛才那份備份:{backup.name} → {big.name}')
            # ⚠️ 就算自動還原成功了,這行指令還是要印出來。
            #    自動還原也可能有失手的一天,而使用者當下最需要的就是那一行;
            #    要他回頭去翻教學頁,等於這裡少講了一句話。
            print(f'  想再確認一次可以自己跑:{_cmd}')
        except (SystemExit, OSError) as e:
            print(f'  自動還原沒有成功:{e}')
            print(f'  請自己跑一次:{_cmd}')
    else:
        print('  這份 .bak 是上一輪留下的,沒有自動還原'
              '(它未必是你這次想回到的狀態)。')
        print(f'  要回到那份備份的狀態:{_cmd}')
    print('  然後請回報給本站。')
    return 1


if __name__ == '__main__':
    # ⚠️ Ctrl-C 不可以安靜地回 0 —— 那等於告訴玩家「沒事」。
    #    也不可以一律說「什麼都沒有動到」:如果 os.replace 已經跑過,
    #    檔案就真的換過了,他需要知道要 --restore。
    #    _REPLACED(已換)與 _INFLIGHT(正在換)記的就是這一輪的真實狀態,
    #    每一種各講各的話,那幾句在 _interrupt_report() 裡,--selftest 驗得到。
    #    130 是 shell 對 SIGINT 的慣例(128 + 2),不是 0 也不是 1。
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        # 每一種各講各的話,那幾句在 _interrupt_report() 裡(--selftest 驗得到它)。
        _print_interrupt_report()
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
