#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
mvp_install_uniform.py — 把一套球衣裝進 MVP Baseball 2005

社群做的球衣包解開之後是一堆 .fsh 檔。這支腳本會：
  · 看懂每個檔該進哪一個封裝檔(一套球衣要分裝到三個地方)
  · 先告訴你哪些裝得進去、哪些裝不進去,以及為什麼
  · 確認之後才寫入,而且一律「接到檔尾」,原本的資料一個位元組都不動

一套球衣分裝到三個封裝檔:
  u###?.fsh · f###?.fsh   →  data/models.big          球場上穿的
  ###.fsh · ###?.fsh      →  data/frontend/uniforms.big  選單裡看到的
  l###?.fsh               →  data/frontend/logos.big     隊徽

⚠️ **只能換掉封裝檔裡已經有的項目,不能新增。**
   目錄放在檔案最前面,資料緊接在後。多一個項目會讓目錄變長,
   後面所有資料都得往後挪 —— 那是「重新打包」,會弄丟目錄沒指到的資料
   (實測 uniforms.big 有 25.1%、logos.big 有 45.9% 的位元組不在目錄範圍內)。
   所以腳本遇到「封裝檔裡沒有同名項目」的檔案會**跳過並告訴你**,不會硬塞。

球衣檔本身已經是遊戲格式(QFS 壓縮過的 FSH),所以原封不動接進去就好,
不需要解壓也不需要重新編碼。

寫回封裝檔一律用「接到檔尾」的方式:新資料接在檔案最後面,
只改目錄裡那一項的 8 個位元組 + 檔頭的 4 個位元組。
原本的資料一個位元組都不動,所以出錯了也還原得回來。

而且這些改動**不是直接做在你的遊戲檔上**:腳本先把要動的封裝檔各複製一份
到它旁邊,整批球衣全部套到那一份複本上、驗過,最後才用作業系統的原子改名
一次換上去。所以遊戲檔只有兩種狀態 —— **全部裝好,或完全沒動**,
不會停在「裝了一半」或「目錄改了、檔頭還沒改」那種半殘的樣子。
代價是動手的時候要多一份跟封裝檔一樣大的暫存空間,而且比舊版慢
(備份複製一次、工作複本再複製一次);models.big 有五百多 MB,差別最明顯。

【三個指令,一路由鬆到緊】
    python3 mvp_install_uniform.py "<遊戲資料夾>" --scan    "<球衣包資料夾>"
    python3 mvp_install_uniform.py "<遊戲資料夾>" --install "<球衣包資料夾>"
    python3 mvp_install_uniform.py "<遊戲資料夾>" --install "<球衣包資料夾>" --apply
    python3 mvp_install_uniform.py "<遊戲資料夾>" --restore
前兩個完全不動檔案。**只有加了 --apply 才會寫入。**
另外還有一個 python3 mvp_install_uniform.py --selftest,它不需要遊戲資料夾,
也不碰任何遊戲檔:只在系統暫存區驗這支腳本自己的守門有沒有在工作。

【輸入是什麼、輸出是什麼】
  · 輸入一:遊戲資料夾。真正會被打開的只有三個封裝檔
    (data/models.big、data/frontend/uniforms.big、data/frontend/logos.big)。
  · 輸入二:已經解壓縮的球衣包資料夾。腳本會**遞迴**往下找所有 .fsh,
    包在再一層資料夾裡也沒關係。
  · 輸出:沒有新檔案。改的是封裝檔本身,而且**只改這一批球衣真的會動到的
    那幾個**,動到的才各留一份 .unibak 備份。球衣包裡沒有隊徽檔(l###)的話,
    logos.big 從頭到尾不會被碰,也不會有它的備份。
    畫面上會逐檔告訴你「幾個位元組、接在第幾個位元組」。

【安全網在哪】
  · 預設不寫:--scan 與不加 --apply 的 --install 都只是清點與預覽。
  · 先全部認過再動手:動任何檔案之前,球衣包裡每一個要裝的檔都先確認開頭
    是不是遊戲的圖檔。有一個不是就整批停下來,那時候一個位元組都還沒寫。
  · 只加不改:新資料一律接在檔尾,原本的位元組一個都不動。
    就算新資料是壞的,舊資料還完整躺在檔案裡。
  · 在複本上做,最後才換名:整批球衣先套到旁邊的工作複本上,驗完才一次換上去。
    中途失敗或按了 Ctrl-C,遊戲檔一個位元組都沒有被打開來寫過。
    要動好幾個封裝檔時也是一起換,其中一次換名失敗就把已經換上去的換回來
    (靠一個不佔空間的硬連結;exFAT 這種做不出硬連結的磁碟就退回逐檔誠實回報,
     不假裝退得回去)。
  · 自動備份:第一次動某個封裝檔之前先複製成 .unibak,而且是先寫進一個
    臨時取名的暫存檔、驗過內容才 os.replace,不會留下半截備份。
    已經有備份就保留最早那一份。
  · 不跟著符號連結走:要寫的封裝檔或備份檔如果是符號連結,直接停下來。
    暫存檔的名字也是每次臨時取的(不是固定的 .part),沒有人能先佔那個名字。
  · 逐位元組複驗**兩輪**:換名之前先驗工作複本(沒過就整批不換,遊戲檔沒動),
    換上去之後再讀你真正的遊戲檔驗一次。兩輪都是重新讀目錄、把寫進去的位元組
    讀回來跟來源比對,再檢查檔頭的大小欄位。第二輪有一項沒過就叫你 --restore。
  · --restore 也是全部驗完才開始蓋:先驗每一份備份完不完整(0 bytes、
    檔頭宣告的長度對不上、只有正本一半大…),有一份壞掉就整支停下,
    不會留下「一半還原、一半沒還原」的混合狀態。覆蓋本身也走
    暫存檔 + os.replace,而且**先跟備份逐位元組比對過才換上去** ——
    正本要嘛是原來那份、要嘛是還原好的,不會是半截。

【這支做不到的事】
  · **不能新增項目,只能換掉已經有的。** 遇到封裝檔裡沒有同名項目的檔會跳過。
    例如球衣包附了 122b,而原版那一隊本來就只有 122a,那個位置不存在。
  · 不改圖、不轉檔、不縮圖。給什麼位元組就裝什麼位元組。
  · 不認得球衣包裡的 .png / .bmp / 說明文字,只認 .fsh。
  · 不會幫你確認「進遊戲之後那支球隊真的變了」。那要你自己用眼睛看,
    本站的實測是在封裝檔的複本上做的,沒有實機驗過畫面。

自包含:整支腳本就是這一個檔,只用 Python 內建模組,不需要安裝任何套件。
⚠️ 2026-09-04 訂正:上面這句原本掛著「連讀寫 PNG 都是自己做的」,那在**這一支**上不成立,
   已經拿掉。這個檔從頭到尾沒有任何 PNG 的程式碼,它也不需要:球衣檔是原封不動接進去的。
   (2026-09-04 在 site/tutorials/ 底下的 29 支腳本上查:帶著這一句檔頭的有 6 支,
    其中只有 2 支真的自己讀寫 PNG。看起來是共用的檔頭抄過來時沒逐支核對。)
   「不需要安裝任何套件」那半句本來就是對的:本檔 import 的全是 Python 自己就附的模組。

授權:MIT(見檔尾完整條款)。本站教學文字另採 CC BY 4.0。
"""
TOOL_DATE = '2026-09-26'  # 這一版工具的日期
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
#    各管道要不要帳號寫在那一頁。管道有變動只會改那一頁。
# ─────────────────────────────────────────────────────────

import os
import re
import sys
import signal
import struct
import shutil
import tempfile
import argparse

# ── 備份的原子性(2026-08-29 上線前稽核加)────────────────────────────
# 原本是直接 shutil.copy2(遊戲檔, .bak)。複製途中被中斷(磁碟滿、外接碟拔掉、
# Windows 上按 Ctrl-C)會留下一個**半截的 .bak**;下一次執行看到它「存在」
# 就印「備份已存在,保留最早那一份」繼續改遊戲檔,之後 --restore
# 會拿那個半截檔覆蓋掉正本。
#
# 實測(2026-08-29):把 2,665,562 bytes 的備份截成 300,000 bytes,
# 本站防護最嚴的那支還原指令三道把關全過、印「✓ 已從備份還原」、exit code 0,
# 2.66 MB 的遊戲檔當場被 300 KB 蓋掉。magic 只看開頭,看不出後面少了多少。

# 「有沒有真的動到玩家的遊戲檔」。
# 用途只有一個:被 Ctrl-C 打斷的時候,說得出「還沒動到」還是「已經改了」。
# 沒有它就只能含糊地印「已中斷」,而使用者最想知道的正是「我的遊戲檔還能用嗎」。
#
# ⚠️ 2026-09-06 第三輪訂正,兩件事:
#   (1) 原本是一個布林 _MUTATED,而它是在 os.replace **回來之後**才被設起來的。
#       Ctrl-C 剛好落在那兩行中間的話,收尾會照舊的值講話 —— 檔案已經換掉了,
#       螢幕上卻寫「還沒有動到任何檔案」。現在是三態:
#         idle       還沒動過
#         replacing  正在換某一個檔(_NoInterrupt 裝得上的話幾乎看不到,它是保險)
#         replaced   至少換過一個了
#   (2) 「換名 + 登記」被 _NoInterrupt 包成不可中斷的一段,所以 (1) 那個縫
#       幾乎不會被踩到;三態是踩到時的保險,兩道一起才算數。
_STATE = {'phase': 'idle', 'target': None, 'replaced': []}


def _mark_replacing(path):
    """進入不可中斷段之前登記「正在換 X」。真的落在縫裡時,收尾會說實話。"""
    _STATE['phase'], _STATE['target'] = 'replacing', path


def _mark_replaced(path):
    """os.replace 已經回來了才可以呼叫。這一行在 _NoInterrupt 區塊裡面。"""
    _STATE['phase'], _STATE['target'] = 'replaced', path
    if path not in _STATE['replaced']:
        _STATE['replaced'].append(path)


def _unmark_replacing():
    """**確定 os.replace 沒有發生**的時候才可以呼叫,把「正在換」收回去。

    ⚠️ 不可以無條件收回:換名做完了才撤銷登記,就是 2026-09-06 這一輪要修的
       那種謊話。呼叫端只在「暫存檔還在、換名確定沒成」那一條路上用它。
       前面已經有別的檔換成功時,狀態要停在 replaced 而不是 idle。
    """
    if _STATE['phase'] == 'replacing':
        if _STATE['replaced']:
            _STATE['phase'], _STATE['target'] = 'replaced', _STATE['replaced'][-1]
        else:
            _STATE['phase'], _STATE['target'] = 'idle', None


class _NoInterrupt(object):
    """把「os.replace + 登記」包起來,這段期間不讓 Ctrl-C 插隊。

    收到 SIGINT 先記著,離開這一段之後再照常丟出 KeyboardInterrupt。
    這樣收尾看到的登記一定跟磁碟上的狀態一致,不會出現「檔案換掉了但程式
    還以為沒換」的那一瞬間。

    ⚠️ signal.signal 只有主執行緒裝得上,裝不上就退回原本的行為 ——
       不會比以前更糟,而且外面那個 replacing 狀態就是為這種情形留的:
       真的落在縫裡,收尾會誠實說「不確定換好了沒有」,不會說「沒動到」。
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


def _refuse_symlink(path, role):
    """要寫的地方是符號連結就停下來,不跟著它走到別的地方去。

    ⚠️ 用 os.path.islink 而不是 os.path.exists:連結指到的檔不存在時
       exists() 回 False,等於整個看不見它(dangling symlink);
       islink() 看的是連結本身,兩種都擋得住。
    """
    if os.path.islink(path):
        raise DataError(
            '%s 是一個符號連結:\n'
            '    %s\n'
            '  不敢跟著它寫下去 —— 連結可能指到遊戲資料夾外面的東西。\n'
            '  請把它換成真正的檔案,或改用沒有連結的路徑。' % (role, path))


def _new_temp_beside(dst):
    """在 dst 的**同一個資料夾**裡開一個名字獨一無二的暫存檔,回傳 (fd, 路徑)。

    2026-09-05 上線前稽核抓到的:暫存檔原本叫「目的檔 + .part」,是個**猜得到
    的固定名字**。事先在那個資料夾放一個叫 models.big.unibak.part 的符號連結
    指到資料夾外面的檔,shutil.copy2() 會跟著連結把外面那個檔先截成 0 再寫;
    後面的 os.replace() 雖然只換掉連結本身,但外面那個檔在那之前就沒了。
    mkstemp() 走的是 O_CREAT|O_EXCL,名字已經被佔就直接失敗,而且名字每次
    都不一樣 —— 沒有人事先知道要佔哪一個。

    一定要同一個資料夾,os.replace() 才是同一個檔案系統內的改名(原子的);
    跨磁碟的 replace 在 Windows 上會直接失敗。
    """
    d = os.path.dirname(os.path.abspath(dst)) or '.'
    # 開頭那個 . 是為了在 Unix 上不礙眼;真正保證不衝突的是 mkstemp 自己。
    return tempfile.mkstemp(dir=d, prefix='.' + os.path.basename(dst) + '.part-')


def _atomic_copy(src, dst, marks_mutation=False):
    """把 src 完整複製到 dst —— dst 這個名字上只會有「原來那份」或「完整的新份」。

    順序是固定的:同資料夾開暫存檔 → 寫完 flush + fsync → 對權限
    → **逐位元組驗過** → os.replace 換上去。驗在換之前,所以驗不過的時候
    dst 還是原本那一份,一個位元組都沒被動到。

    marks_mutation:這一次換掉的是不是玩家的遊戲檔。是的話換上去之前先記下來,
    Ctrl-C 才說得出「已經改了,請 --restore」。備份(dst 是 .unibak)不算。

    ⚠️ 本站有些腳本用 pathlib.Path 存路徑,有些用字串。
       2026-08-29 第一版寫成 dst + '.part',在 Path 上直接 TypeError,
       等於所有備份都失敗 —— 而且「半截備份被擋下來」那個測試照樣是綠的。
       是陰性對照(先證明正常流程真的會產生備份)抓到的。
    """
    # 先統一成字串路徑:下面每一步都是 os.path 的函式,Path 物件混進來
    # 容易在某一步上爆炸(見上面那段訂正)。
    src, dst = os.fspath(src), os.fspath(dst)
    _refuse_symlink(dst, '要寫入的目標')
    fd, tmp = _new_temp_beside(dst)
    # 換名成功之後 tmp 這個名字已經不存在了,收尾不可以再去刪它
    # (刪掉的會是別人剛好取到同一個名字的檔)。
    swapped = False
    try:
        with os.fdopen(fd, 'wb') as fout:
            with open(src, 'rb') as fin:
                shutil.copyfileobj(fin, fout, 1 << 20)
            fout.flush()
            # fsync:把資料交給作業系統寫下去,不要只留在程式自己的緩衝區裡。
            # (macOS 上要逼進碟片本身還得 F_FULLFSYNC,這裡不做 —— 對一份
            #  幾百 MB 的備份太貴,而且擋得住的是斷電,不是本段要防的中斷。)
            os.fsync(fout.fileno())
        # 權限與時間:目的檔已經在那裡就沿用它的(還原),否則沿用來源的(備份)。
        # mkstemp 開出來的檔是 0600,不處理的話還原之後的權限會跟原本不一樣。
        try:
            shutil.copystat(src, tmp)
            if os.path.exists(dst):
                shutil.copymode(dst, tmp)
        except OSError:
            pass                        # 權限對不上不值得讓整件事失敗
        # 換上去之前先逐位元組驗過。這一步是「已備份 / 已還原」那句話的憑據 ——
        # 沒有它,那句話只是從「複製沒有丟例外」推出來的,不是量到的。
        _verify_same(src, tmp)
        # ⚠️ 2026-09-06:換名與登記中間不可以有縫。原本是 os.replace 一行、
        #    登記在它後面一行,Ctrl-C 落在那兩行中間的話收尾會說「還沒有動到
        #    任何檔案」—— 而檔案已經換掉了。現在兩行被 _NoInterrupt 綁在一起,
        #    而且進來之前先登記「正在換」(真的落在縫裡時的保險)。
        if marks_mutation:
            _mark_replacing(dst)
        with _NoInterrupt():
            os.replace(tmp, dst)        # os.replace 是原子的
            swapped = True
            if marks_mutation:
                _mark_replaced(dst)
    except BaseException:
        # 接 BaseException 而不是 Exception:Ctrl-C(KeyboardInterrupt)
        # 正是最容易留下半截檔的情境,而它不是 Exception 的子類。
        #
        # ⚠️ 2026-09-11 第四輪修的那個縫:這裡原本只看 swapped 這個旗標,
        #    而它是在 os.replace **回來之後**才被設起來的 —— 跟 2026-09-06
        #    修掉的那個縫是同一種病,只是搬到了下一行。_NoInterrupt 擋得住
        #    SIGINT 訊號,但它裝不上的機器(非主執行緒)就沒有擋:那時候
        #    KeyboardInterrupt 落在「os.replace 已經回來、swapped = True 還沒
        #    跑到」中間,這裡會判「沒換成」,把登記收回 idle,收尾就對讀者說
        #    「已中斷。還沒有動到任何檔案。」—— 而檔案已經換掉了。
        #    (實測:用一個換完名就丟 KeyboardInterrupt 的 os.replace 跑一次,
        #     磁碟上是新內容,登記卻是 idle。)
        #    三態就是為這種機器留的保險,而它原本在這裡漏掉。
        #    改法是**不要問旗標,去問磁碟**:os.replace 成功之後 tmp 那個名字
        #    就不存在了,所以「tmp 還在」等於「換名沒發生」。這是量到的,
        #    不是從「有沒有走到某一行」推出來的。
        if not swapped:
            if os.path.exists(tmp):
                # 暫存檔還在 = 換名確定沒有發生。清掉它,把「正在換」收回去。
                try:
                    os.remove(tmp)
                except OSError:
                    pass
                if marks_mutation:
                    _unmark_replacing()
            elif marks_mutation:
                # 暫存檔不見了 = 換名其實做完了,只是登記那一行還沒跑到。
                # 這時候絕對不可以說「沒動到」。
                _mark_replaced(dst)
        # 清乾淨之後把原本的例外原封不動往上丟。
        # 清理失敗不可以蓋掉真正的錯誤原因(磁碟滿了要讓人看到「磁碟滿了」)。
        raise



def _stage_copy(live):
    """在正本**旁邊**開一個暫存檔,把正本原封不動複製進去,回傳暫存檔路徑。

    這是「複本上做、最後才換名」的第一步(2026-09-06 第三輪加的)。
    接下來所有的追加、目錄與檔頭改動都在這一份上做,正本在 os.replace 之前
    連開都不會被開來寫 —— 所以中途不管是失敗還是 Ctrl-C,
    「遊戲檔一個位元組都沒有動」這句話都是結構上成立的,不是推論出來的。

    一定要同一個資料夾:os.replace 只有在同一個檔案系統內才是原子的改名,
    跨磁碟在 Windows 上會直接失敗。

    代價要說清楚:這一步會多花一份跟正本一樣大的磁碟空間與一次完整複製的時間。
    models.big 有五百多 MB,所以裝球場上穿的那種球衣會比以前久
    (備份一次 + 工作複本一次)。換來的是「要嘛全裝、要嘛完全沒動」。
    """
    live = os.fspath(live)
    _refuse_symlink(live, '封裝檔 %s' % os.path.basename(live))
    fd, tmp = _new_temp_beside(live)
    try:
        with os.fdopen(fd, 'wb') as fout:
            with open(live, 'rb') as fin:
                shutil.copyfileobj(fin, fout, 1 << 20)
            fout.flush()
            os.fsync(fout.fileno())
        # 權限要跟著正本走。mkstemp 開出來的是 0600,不處理的話換名之後
        # 遊戲檔的權限會跟原本不一樣(本站的遊戲檔實測是 0700)。
        try:
            shutil.copymode(live, tmp)
        except OSError:
            pass
        # 複本先驗過才敢在上面動手。驗不過就代表這次複製本身有問題
        # (磁碟滿、外接碟拔掉),那時候正本還是原來那一份。
        _verify_same(live, tmp)
    except BaseException:
        try:
            os.remove(tmp)
        except OSError:
            pass
        raise
    return tmp


def _drop_temp(path):
    """把還沒換上去的暫存檔刪掉。刪不掉不算失敗,不可以蓋掉真正的錯誤原因。"""
    try:
        os.remove(path)
    except OSError:
        pass


def _restore_from_backup(bak, dst, verify_only=False):
    """還原之前先擋掉明顯壞掉的備份。

    verify_only=True 只驗不蓋(2026-09-05 加)。cmd_restore 用它先把每一份備份
    都驗過一遍,確定全部合格才開始覆蓋 —— 原本是一邊驗一邊蓋,第三份備份壞掉時
    前兩份已經還原了,使用者最後拿到「一半還原、一半沒還原」的混合狀態。

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
        raise DataError('找不到備份:%s' % bak)
    # 下面每一種格式的檢查都用它收尾:把「哪裡看出來壞了」接上同一段
    # 「多半是備份途中被中斷、請改用你自己留的那一份」。訊息一致,
    # 使用者不必分辨是哪種檔案格式才知道自己該做什麼。
    # ⚠️ 2026-09-05 訂正兩件事:
    #    (1) 這支函式原本定義在「0 bytes」那一關**後面**,所以只有它拿不到
    #        這段共用收尾 —— 最常見的一種壞備份,反而是訊息最少的那一種。
    #        提到前面來,四種判準共用同一段話。
    #    (2) 原本丟的是 SystemExit,不經過 main() 的出錯出口:實際 exit code
    #        是 1 而不是 main() 說明寫的 2,訊息也走 stderr、少了「停下來了:」
    #        前綴。改丟 DataError,跟這支腳本其他每一條停下來的路一致。
    def _stop(why):
        raise DataError(
            '這份備份是壞的,不敢拿它覆蓋 %s。\n'
            '  %s\n'
            '  多半是備份途中被中斷(磁碟滿、外接碟拔掉、按了 Ctrl-C)。\n'
            '  請改用你自己另外留的那一份備份。' % (dst, why))

    # 第一道:0 bytes。最便宜也最常見的一種壞備份。
    n = os.path.getsize(bak)
    if n == 0:
        _stop('備份是 0 bytes。')
    # 只讀開頭 8 個位元組認檔案類型。下面每一種類型各有自己的完整性判準,
    # 因為「怎麼看得出被截斷」這件事本來就是每種格式不一樣。
    with open(bak, 'rb') as _f:
        head = _f.read(8)

    # ── BIGF(封裝檔,也就是這一課會動到的那三個)──
    # 檔頭 +0x04 那一欄就是「這個檔應該有多大」。截斷的備份一定對不上,
    # 所以這一種不必用大小地板去猜,檔案自己就說得出答案。
    # ⚠️ 那一欄兩種位元組序都遇得到(見 size_field_order),所以兩種都算一次,
    #    任一種對得上就算過。
    if len(head) == 8 and head[:4] == b'BIGF':
        le = struct.unpack('<I', head[4:8])[0]
        be = struct.unpack('>I', head[4:8])[0]
        if le != n and be != n:
            _stop('檔頭說它應該是 %d bytes(或 %d),實際只有 %d bytes。' % (le, be, n))
        return None if verify_only else _do_copy(bak, dst)

    # ── 以下三種這一課用不到,是本站共用的還原防護 ──
    # 留著是因為這段程式碼被好幾支腳本共用,而 2026-08-30 那次稽核是
    # 六支腳本一起中招的。只擋 BIGF 等於只補了自己那一格。
    #
    # LOCH(語系檔):檔頭指到字串區 LOCL 的位移,再從那裡讀出字串條數與
    # 每一條的位移。被截斷的話,最後一條字串的位移一定會指到檔案外面。
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
        except DataError:
            raise
        except (struct.error, IndexError):
            _stop('讀不出語系檔的結構,它壞了。')

    # MZ(Windows 執行檔):走 DOS 檔頭 +0x3C 那個指標找到 PE 檔頭,
    # 再把節區表逐項掃過去,取「檔案裡的位移 + 長度」的最大值。
    # 那個最大值就是這個執行檔至少該有多大,比實際檔案大就是被截斷了。
    # 這一種最兇:還原一個半截的 mvp2005.exe,遊戲會完全開不起來。
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
        except DataError:
            raise
        except (struct.error, IndexError):
            _stop('讀不出執行檔的結構,它壞了。')

    # 通用地板 —— 非 BIGF 走到這裡
    if os.path.exists(dst):
        live = os.path.getsize(dst)
        if live > 0 and n * 2 < live:
            _stop('備份只有 %d bytes,而要被蓋掉的那個檔有 %d bytes ——'
                  '差太多了(不到一半)。' % (n, live))
    return None if verify_only else _do_copy(bak, dst)


# **還原**這條路上,真正覆蓋正本的唯一一個地方。
# 單獨拉成一支函式,是為了讓每一條還原路徑都非得經過 _restore_from_backup
# 的檢查才走得到這裡。哪天有人多加一種格式,少寫的檢查會很明顯。
# (安裝那條路覆蓋正本的地方是另一個:cmd_install 換名那一段。兩條路各一個,
#  沒有第三個 —— 除了它們兩個以外,沒有任何地方會開著正本寫下去。)
def _do_copy(bak, dst):
    # 2026-09-05 改成原子覆蓋(原本是直接 shutil.copy2(bak, dst))。
    # 直接覆蓋的話,還原途中被中斷(磁碟滿、外接碟拔掉、Ctrl-C)會留下一個
    # **半截的遊戲檔** —— 備份還在,可以再還原一次,但那一刻玩家手上的檔是壞的。
    # 走「暫存檔 + os.replace」之後,遊戲檔只有兩種狀態:還沒還原,或已經還原完。
    # 代價是還原途中要多一份暫存空間(跟備份時一樣多)。
    # ⚠️ 2026-09-05 再改一次:逐位元組比對現在在 _atomic_copy 裡面、**換上去
    #    之前**做。原本是換完才比,比不過的時候正本已經被那份可疑的資料蓋掉了
    #    —— 那正是這一步要防的事。現在驗不過就整個不換,正本原封不動。
    _atomic_copy(bak, dst, marks_mutation=True)


def _verify_same(a, b):
    """逐位元組比對兩個檔,不同就丟 DataError。

    ⚠️ 一定要比**完整長度**。用 zip() 兩邊一起走,短的那一邊走完就停,
       「一個檔是另一個的前半截」這種最要命的情形會整個測不出來。
       這裡先比大小,再一塊一塊往下讀到其中一邊讀完為止。
    """
    na, nb = os.path.getsize(a), os.path.getsize(b)
    if na != nb:
        raise DataError('寫出來的是 %d bytes,來源是 %d bytes —— 兩邊不一樣大,'
                        '沒有換上去。' % (nb, na))
    with open(a, 'rb') as fa, open(b, 'rb') as fb:
        while True:
            ba = fa.read(1 << 20)
            bb = fb.read(1 << 20)
            if ba != bb:
                raise DataError('寫出來的內容跟來源不同,沒有換上去。')
            if not ba:
                break




# 把輸出強制成 UTF-8。Windows 的主控台預設不是 UTF-8(繁中版是 cp950),
# 訊息裡的「✅」「→」這些字會讓 print 直接丟 UnicodeEncodeError,
# 也就是**工具明明做對了卻在印結果時當掉**。
# 舊版 Python 沒有 reconfigure,所以整段包在 try 裡,失敗就照原樣跑。
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass


class DataError(Exception):
    """檔案內容跟預期不符。一律當成「停下來問人」,不要猜。"""


# 兩個上限值。它們的用途不是「效能」,是**不要相信檔案自己說的數字**:
# 壞掉或被動過手腳的檔可以宣稱「我解壓出來有 4 GB」「我的目錄有兩千萬項」,
# 照著配置記憶體會直接把電腦吃垮。超過就當成檔案壞了,停下來。
MAX_UNCOMPRESSED = 64 * 1024 * 1024
MAX_BIG_ENTRIES = 200000
# 備份檔名的後綴。用本站專用的名字而不是通用的 .bak,
# 是為了跟其他工具留下的備份分得開,--restore 才不會撿到別人的。
BACKUP_SUFFIX = '.unibak'


# ─────────────────────────────────────────────────────────
#  QFS(EA 的壓縮格式,檔頭是 10 FB)
#
#  ⚠️ **這一課的流程用不到下面這兩支。** 球衣檔本身已經是遊戲格式,
#     腳本是原封不動接進封裝檔的,不解壓也不重新編碼。
#     留在這裡是因為它是本站解 EA 格式的共用範本(想自己改圖的人從這裡接手),
#     而且它們寫得出「QFS 到底長什麼樣」這件事,對讀者有用。
# ─────────────────────────────────────────────────────────
def qfs_decompress(data):
    """把一段 QFS 資料解開。不是 QFS 就原樣回傳(呼叫端不必先判斷)。

    格式(EA 內部叫 RefPack,社群文件多半叫 QFS):
      · 第 2 個位元組固定是 0xFB,那是辨識碼。第 1 個位元組帶旗標,
        常見的是 0x10。
      · **解壓後大小寫在檔頭,而且是 big-endian。** 第 1 個位元組的 bit 0
        如果是 1,檔頭比較長:大小放在 +6 佔 4 個位元組,資料從 +10 開始;
        否則大小放在 +2 佔 3 個位元組,資料從 +5 開始。
      · 之後是一串控制碼。每一個控制碼做兩件事:先照抄幾個位元組,
        再從**已經解出來的內容**往回抄一段(這就是壓縮的來源)。
        依第一個位元組落在哪一段,控制碼長 1、2、3 或 4 個位元組:
          < 0x80   2 個位元組:往回最多 1,024,抄 3 到 10
          < 0xC0   3 個位元組:往回最多 16,384,抄 4 到 67
          < 0xE0   4 個位元組:往回最多 131,072,抄 5 到 1,028
          < 0xFC   1 個位元組:只照抄 4 到 112,沒有反向參照
          >= 0xFC  結束,照抄最後 0 到 3 個位元組
      · 所有長度與位移都要 +1 或 +3 之類的偏移,因為 0 沒有意義,
        編碼時就把它讓給了更大的值。
    """
    if len(data) < 2 or data[1] != 0xFB:
        return data
    if data[0] & 0x01:
        if len(data) < 10:
            raise DataError('QFS 檔頭不完整')
        size = int.from_bytes(data[6:10], 'big'); pos = 10
    else:
        if len(data) < 5:
            raise DataError('QFS 檔頭不完整')
        size = int.from_bytes(data[2:5], 'big'); pos = 5
    # 檔頭宣稱的大小要先檢查再拿去用,理由見 MAX_UNCOMPRESSED 上面那段。
    if not 0 <= size <= MAX_UNCOMPRESSED:
        raise DataError('QFS 宣稱解壓尺寸異常:%d' % size)

    out = bytearray()
    end = len(data)

    def copy_back(offset, length):
        # 這一行擋的是「往回的距離」:至少要往回 1 個位元組,而且不能往回到
        # 還沒解出來的地方。它管的不是輸出總長度,總長度由下面那道擋。
        if not 0 < offset <= len(out):
            raise DataError('QFS 反向參照越界 offset=%d' % offset)
        src = len(out) - offset
        # ⚠️ 這裡**故意**一個位元組一個位元組抄,不可以改成切片一次接上去。
        #    length 可以大於 offset(例如往回 1 抄 50),那是合法的:
        #    邊抄邊長,等於把同一個位元組複製 50 次,連續色塊就是這樣壓的。
        #    切片會在複製前就把來源固定住,結果整個不一樣。
        for _ in range(length):
            out.append(out[src]); src += 1
        # ⚠️ 只檢查檔頭宣稱的大小是不夠的:那是「檔案自己說的」。
        #    一個惡意檔可以宣稱很小(通過上面那道),再用反向參照無限吐資料,
        #    把記憶體吃光。實際輸出也必須有上限,而且上限就是它自己宣稱的大小。
        if len(out) > size:
            raise DataError('QFS 解出來的資料超過檔頭宣稱的 %d 位元組' % size)

    while pos < end:
        b0 = data[pos]
        # 0xFC 以上:結束碼。後面只跟著 0 到 3 個照抄的位元組。
        if b0 >= 0xFC:
            n = b0 & 0x03; pos += 1
            out += data[pos:pos + n]; break
        # 0xE0 到 0xFB:純照抄一段(4 到 112 個位元組),沒有反向參照。
        if b0 >= 0xE0:
            n = ((b0 & 0x1F) << 2) + 4; pos += 1
            out += data[pos:pos + n]; pos += n; continue
        # 以下三段都是「照抄 n 個 + 往回抄 length 個」,差別只在
        # 位移與長度各用幾個位元(愈長的控制碼,往回抄得愈遠、抄得愈多)。
        if b0 >= 0xC0:
            b1, b2, b3 = data[pos + 1], data[pos + 2], data[pos + 3]; pos += 4
            n = b0 & 0x03
            length = ((b0 & 0x0C) << 6) + b3 + 5
            offset = ((b0 & 0x10) << 12) + (b1 << 8) + b2 + 1
        elif b0 >= 0x80:
            b1, b2 = data[pos + 1], data[pos + 2]; pos += 3
            n = (b1 >> 6) & 0x03
            length = (b0 & 0x3F) + 4
            offset = ((b1 & 0x3F) << 8) + b2 + 1
        else:
            b1 = data[pos + 1]; pos += 2
            n = b0 & 0x03
            length = ((b0 & 0x1C) >> 2) + 3
            offset = ((b0 & 0x60) << 3) + b1 + 1
        out += data[pos:pos + n]; pos += n
        copy_back(offset, length)
    # 切到檔頭宣稱的長度為止。最後一個控制碼可能會多抄出幾個位元組。
    return bytes(out[:size])


def qfs_compress_literal(data):
    """純 literal 編碼:不做字串比對,瞬間完成,格式一樣合法。

    壓出來比 EA 原本的大(大約等於原始大小),但因為我們是接到檔尾,
    大一點沒有影響。換來的是速度快上千倍,而且不可能壓錯。

    「不可能壓錯」的意思是:整段只用「照抄」那一類控制碼,完全不做反向參照,
    所以沒有位移算錯、抄過頭這些機會。輸出仍然是合法的 QFS,遊戲讀得動。
    """
    n = len(data)
    # 檔頭:10 FB + 3 個位元組的原始大小(**big-endian**,高位在前)。
    out = bytearray([0x10, 0xFB, (n >> 16) & 0xFF, (n >> 8) & 0xFF, n & 0xFF])
    # 照抄那一類控制碼一次只能抄 4 的倍數,所以先把尾巴不足 4 的零頭切出來,
    # 留給最後的結束碼(它剛好能帶 0 到 3 個位元組)。
    tail = n % 4
    body = n - tail
    pos = 0
    while pos < body:
        # 一次最多 112 個位元組。這不是隨便挑的:控制碼是 0xE0 | ((chunk-4)/4),
        # chunk = 112 剛好編成 0xFB,再大一格就撞進 0xFC 以上的結束碼區間了。
        chunk = min(112, body - pos)
        out.append(0xE0 | ((chunk - 4) // 4))
        out += data[pos:pos + chunk]
        pos += chunk
    # 結束碼:0xFC 加上還剩幾個位元組(0 到 3),後面直接跟著那幾個位元組。
    out.append(0xFC | tail)
    out += data[pos:]
    return bytes(out)


# ─────────────────────────────────────────────────────────
#  BIGF 封裝檔:讀目錄、接到檔尾
#
#  這一段才是這支腳本真正在做的事。BIGF 的長相:
#
#    位移  0   'BIGF'                    辨識碼
#          4   整個檔案的總大小          ⚠️ **位元組序不固定**,見下面那支
#          8   目錄有幾項                固定 big-endian
#         12   意義本站沒定案            本腳本沒有用到。在一份剛安裝好的原版
#                                        uniforms.big 上量到 9,369,而目錄實際
#                                        結束在 9,361、第一筆資料從 9,372 開始,
#                                        三個數字都不一樣,所以不寫死說法。
#         16   目錄開始
#             每一項 = 資料位移 4 bytes + 資料長度 4 bytes(都 big-endian)
#                      + 項目名稱,以一個 0x00 結尾,長度不固定
#             …一項接一項,中間沒有填補
#         之後 就是各項的資料本體
#
#  ⚠️ 目錄項目的位移與長度**一律 big-endian**,只有檔頭 +4 那一欄兩種都有。
#     這兩件事不一致,是本站踩過而且會靜默寫壞檔案的地方。
# ─────────────────────────────────────────────────────────
def size_field_order(path):
    """檔頭 +0x04 的「檔案總大小」是 little 還是 big endian。

    ⚠️ 這一欄兩種順序都遇得到,不能寫死,也不能照檔名或檔案大小猜。
       「哪個檔是哪一種」不是這個格式天生的性質,是看你手上這一份
       被誰重新打包過。
       本站以 BIGF 檔頭(不是副檔名)認過四份 data 資料夾:剛安裝好的原版
       英文版 207 個封裝檔、剛安裝好的原版繁體中文版 205 個、PK 版 205 個、
       打過中文更新檔的那一份 205 個。這四份全部是 little-endian,big-endian
       一個都沒有,連裡面最大的 models.big(172,992,803 個位元組)與
       frontend/portrait.big(109,291,217 個位元組)也是。
       只有本站測試機那份疊過模組的 data 資料夾出現 big-endian:384 個封裝檔
       裡有 10 個,而且集中在 7 個檔名上(models.big、frontend/portrait.big、
       audio 底下的 pnamedat.big 與 pnamehdr.big,以及球場夜間檔
       coornite.big / dodgnite.big / wrignite.big;夜間那三個是因為測試機有
       兩份 stadium 資料夾,所以各出現兩次)。這 7 個檔名在上面四份裡
       都是 little-endian。
       所以不要照檔名或檔案大小記,讀出來是哪一種就照哪一種寫回去。
    """
    n = os.path.getsize(path)
    with open(path, 'rb') as f:
        raw = f.read(8)
    if len(raw) < 8:
        raise DataError('%s 太小,不像封裝檔' % os.path.basename(path))
    if struct.unpack('<I', raw[4:8])[0] == n:
        return '<'
    if struct.unpack('>I', raw[4:8])[0] == n:
        return '>'
    raise DataError('%s 的檔頭大小欄位跟實際檔案大小對不上 —— 這個檔可能已經損毀'
                    % os.path.basename(path))


def big_entries(path):
    """回傳 [(名稱, 目錄欄位位置, 資料 offset, 資料長度)]。

    目錄欄位位置留著,是為了之後只改那 8 個位元組,不必重寫整個目錄。
    """
    try:
        with open(path, 'rb') as f:
            head = f.read(16)
            if len(head) < 16 or head[:4] != b'BIGF':
                raise DataError('%s 的開頭不是 BIGF,這不是封裝檔' % os.path.basename(path))
            count = int.from_bytes(head[8:12], 'big')
            if not 0 < count < MAX_BIG_ENTRIES:
                raise DataError('%s 的目錄項目數異常(%d)' % (os.path.basename(path), count))
            # 只讀「檔頭 + 估計的目錄長度」,不把整個檔吃進記憶體:
            # models.big 有 536 MB,而我們要的東西全在最前面幾 KB。
            # 每項抓 80 個位元組是寬估(8 個位元組欄位 + 名稱),再加 8 KB 餘裕。
            blob = head + f.read(count * 80 + 8192)
    except OSError as e:
        raise DataError('讀不到 %s:%s' % (path, e))

    items = []
    pos = 16
    for _ in range(count):
        if pos + 8 > len(blob):
            break                                   # 目錄比預估長,已讀到的就夠用
        # field 記的是「這一項在檔案裡的位置」。之後要改這一項時,
        # 就只覆寫從這裡開始的 8 個位元組,不必重寫整個目錄
        # (重寫目錄會讓長度變動,後面所有資料都得搬,那就是重新打包了)。
        field = pos
        off = int.from_bytes(blob[pos:pos + 4], 'big')
        size = int.from_bytes(blob[pos + 4:pos + 8], 'big')
        pos += 8
        # 名稱長度不固定,以 0x00 結尾,所以只能一項一項往下走,不能跳著算。
        end = blob.find(b'\x00', pos)
        if end < 0:
            break
        # latin-1 + 'replace':名稱理論上是 ASCII,但這裡的目的只是拿來比對檔名,
        # 遇到奇怪的位元組寧可換成替代字元也不要整支腳本丟例外。
        items.append((blob[pos:end].decode('latin-1', 'replace'), field, off, size))
        pos = end + 1
    return items


# 照目錄說的位移與長度,把某一項的資料本體撈出來。
# 讀到的長度跟目錄說的不一樣就丟例外,不回傳半截資料。
# ⚠️ 這一支目前這三個指令都沒有呼叫(複驗那一段是自己開檔 seek 的)。
#    它是給想接手做「讀出來改一改再放回去」的人用的。
def read_entry(path, off, size):
    with open(path, 'rb') as f:
        f.seek(off)
        data = f.read(size)
    if len(data) != size:
        raise DataError('目錄說這一項有 %d 個位元組,實際只讀到 %d' % (size, len(data)))
    return data


def append_entry(path, field_pos, blob):
    """把 blob 接到檔尾,只改該項目的目錄 8 bytes 與檔頭的 4 bytes。

    原本的資料一個位元組都不動 —— 所以就算新資料是壞的,舊資料還在檔案裡。

    它總共只寫三個地方:
      1. 檔尾接上新資料
      2. 目錄裡那一項的 8 個位元組(改成指向新位置與新長度)
      3. 檔頭 +4 的總大小 4 個位元組
    舊那一份資料還躺在原地,只是沒有人指向它了。

    ⚠️ **path 一律是工作複本,不是玩家的遊戲檔**(2026-09-06 第三輪改的)。
       以前這一支是直接對正本 r+b 寫下去的,那有兩個縫:寫到一半被中斷,
       正本會停在「目錄已經指到新位置、檔頭的總大小還是舊的」這種自相矛盾的
       狀態 —— 本腳本自己的 size_field_order 讀到它就會說「這個檔可能已經損毀」;
       而且多件球衣是一件一件寫進去的,中途失敗就留下半套。
       現在 cmd_install 先把正本複製到旁邊的暫存檔,這一支只對那一份動手,
       全部做完驗完才 os.replace 一次換名。**遊戲檔只有兩種狀態:全裝好,或完全沒動。**
       所以這裡不再登記 _STATE —— 登記的地方改到 os.replace 那一行旁邊,
       它才是真的會動到遊戲檔的那一刻。
    """
    # ⚠️ 位元組序一定要在**還沒動檔案之前**量。改完之後檔案大小已經變了,
    #    size_field_order 是拿檔頭那一欄跟實際大小比對來判斷的,那時候會判錯。
    order = size_field_order(path)          # 一定要在改檔案之前先量
    # 新資料要接在目前的檔尾,所以現在的檔案大小就是它的位移。
    new_off = os.path.getsize(path)
    # 'r+b':就地讀寫,**不截斷**。用 'wb' 會把整個封裝檔清空。
    with open(path, 'r+b') as f:
        f.seek(0, os.SEEK_END)
        f.write(blob)
        total = f.tell()
        f.seek(field_pos)
        f.write(struct.pack('>II', new_off, len(blob)))     # 目錄一律 big-endian
        # 檔頭那一欄用原檔那一種位元組序。寫錯的話檔案大小欄位會變成
        # 一個天文數字,而遊戲跟本腳本的檢查都會判定這個檔壞了。
        f.seek(4)
        f.write(struct.pack(order + 'I', total))
        # fsync:逼作業系統真的寫進碟。這一步之後才敢說「已經寫好了」。
        f.flush()
        os.fsync(f.fileno())
    return new_off


# ─────────────────────────────────────────────────────────
#  FSH(SHPI 容器):找到那張圖、換掉像素
#
#  ⚠️ **這一段這一課也用不到。** 裝球衣是把整個 .fsh 原封不動接進封裝檔,
#     不會拆開來看裡面的圖。留著的理由跟 QFS 那段一樣:它寫得出格式,
#     而且下面那張格式對照表是本站上線前一致性檢查會讀的東西。
#
#  FSH 的長相:
#    位移  0   'SHPI'
#          8   裡面有幾張圖(little-endian)
#         16   目錄開始,每一項 8 個位元組 = 4 個字的標籤 + 4 個位元組的位移
#    每一張圖自己的檔頭:
#          +0  格式代號(下面那張表)
#          +1  這一塊的長度,3 個位元組 little-endian。
#              ≤ 16 代表這裡沒給長度,要靠下一張圖的位移(或檔尾)去推
#          +4  寬、+6 高,各 2 個位元組 little-endian
#         +16  像素資料開始
#
#  ⚠️ **SHPI 內部是 little-endian,而外層的 BIGF 目錄是 big-endian。**
#     同一個檔案裡兩種順序並存,這是最容易寫錯的地方。
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
    """回傳 (格式代號, 寬, 高, 像素起點, 像素終點)。只看第一筆記錄。"""
    if len(data) < 16 or data[:4] != b'SHPI':
        raise DataError('不是 SHPI 檔(開頭是 %r)' % data[:4])
    num = struct.unpack_from('<I', data, 8)[0]
    if num < 1:
        raise DataError('這個 SHPI 裡一張圖都沒有')
    # 目錄第 0 項的位移欄。16 是目錄起點,0*8 是第 0 項,+4 跳過那 4 個字的標籤。
    off = struct.unpack_from('<I', data, 20)[0]         # 16 + 0*8 + 4
    if off + 16 > len(data):
        raise DataError('圖片記錄的檔頭不完整')
    # 認不得的格式代號一律停下來。**這裡寧可誤擋也不要猜**:
    # 猜錯格式會讓下面算出來的像素範圍是錯的,而換像素是會寫進檔案的動作。
    code = data[off]
    if code not in FSH_FORMATS:
        raise DataError('沒見過的格式代號 0x%02X' % code)
    block_size = data[off + 1] | (data[off + 2] << 8) | (data[off + 3] << 16)
    width = struct.unpack_from('<H', data, off + 4)[0]
    height = struct.unpack_from('<H', data, off + 6)[0]
    # 尺寸上限 4096:再大就不像是這個年代的遊戲貼圖,多半是把別的位元組
    # 當成寬高在讀。當成「檔案壞了」處理。
    if not (0 < width <= 4096 and 0 < height <= 4096):
        raise DataError('圖片尺寸異常 %dx%d' % (width, height))
    # 像素從圖片檔頭再過 16 個位元組開始(本站在原版的 128x128 ARGB32 上量過:
    # 檔頭在 96、像素從 112 起、到 65648 止,剛好 128×128×4 = 65,536 個位元組)。
    start = off + 16
    # 終點三種來源,由可靠到將就:
    #   1. 這一塊自己宣告的長度(最可靠)
    #   2. 沒宣告的話,用下一張圖的起點當這一張的終點
    #   3. 只有一張圖就一路到檔尾
    # 三種都再跟 len(data) 取小,免得壞檔把終點指到檔案外面。
    if block_size > 16:
        end = min(off + block_size, len(data))
    elif num > 1:
        end = min(struct.unpack_from('<I', data, 16 + 8 + 4)[0], len(data))
    else:
        end = len(data)
    return code, width, height, start, end


# 換掉像素區,前後的位元組原樣接回去。
# **長度必須一模一樣才肯做。** 差一個位元組就代表尺寸或格式跟原圖不同,
# 而 FSH 的檔頭與目錄都記著位移,長度一變後面每一項都會對不準。
# 要換不同尺寸的圖,就不是「換像素」而是「重做整個 FSH」,那不是這支的工作。
def fsh_replace_pixels(data, start, end, new_pixels):
    if len(new_pixels) != end - start:
        raise DataError('新像素有 %d 個位元組,原本是 %d —— 尺寸或格式不一致,拒絕寫入'
                        % (len(new_pixels), end - start))
    return data[:start] + new_pixels + data[end:]



# ─────────────────────────────────────────────────────────
#  一套球衣分裝到哪三個封裝檔
#
#  規則來自實測:把球衣檔的名字攤開來看,只有三種形狀。
#  ⚠️ 分類靠**檔名**,而檔名是社群訂的慣例,不是遊戲強制的。
#     所以腳本不會只信檔名 —— 分完類還會去封裝檔裡確認真的有同名項目,
#     沒有就跳過。這樣就算某個球衣包用了別的命名,也不會裝錯地方。
# ─────────────────────────────────────────────────────────
ARCHIVES = (
    ('models',   os.path.join('data', 'models.big'),               '球場上穿的'),
    ('uniforms', os.path.join('data', 'frontend', 'uniforms.big'), '選單裡看到的'),
    ('logos',    os.path.join('data', 'frontend', 'logos.big'),    '隊徽'),
)

# 三條檔名規則。共同的形狀是「三碼球隊代號 + 一個可有可無的字母」,
# 那個字母是第幾套球衣(a、b、c…);差別只在前面掛什麼字首:
#   u 或 f 開頭 → 球場上穿的        l 開頭 → 隊徽        沒有字首 → 選單裡的
# 三條都用 ^ 與 $ 夾住,而且第一個字元互斥,所以彼此不會搶,列的順序不影響結果。
# re.I 是因為有些球衣包的檔名是大寫的。
PATTERNS = (
    (re.compile(r'^[uf]\d{3}[a-z]?\.fsh$', re.I), 'models'),
    (re.compile(r'^l\d{3}[a-z]?\.fsh$',    re.I), 'logos'),
    (re.compile(r'^\d{3}[a-z]?\.fsh$',     re.I), 'uniforms'),
)


# 看檔名決定該進哪一個封裝檔;三條規則都不合就回 None(交給呼叫端說「看不出來」)。
# ⚠️ 這只是**第一關**。檔名是社群訂的慣例,不是遊戲強制的,所以 plan() 還會
#    再去封裝檔裡確認真的有同名項目。只信檔名就會把東西裝到錯的地方。
def classify(filename):
    for pat, target in PATTERNS:
        if pat.match(filename):
            return target
    return None


# 把三個封裝檔的完整路徑組出來,順便當成「你給的是不是遊戲資料夾」的檢查。
# 缺一個就停:三個檔在同一份安裝裡本來就該同時存在,少一個代表路徑給錯了,
# 這時候繼續往下做只會在更晚的地方失敗,訊息還更難懂。
def archive_paths(gamedir):
    out = {}
    for key, rel, _ in ARCHIVES:
        p = os.path.join(gamedir, rel)
        if not os.path.isfile(p):
            raise DataError('找不到 %s\n'
                            '  請確認你給的是遊戲資料夾(裡面看得到 mvp2005.exe 跟 data)' % p)
        out[key] = p
    return out


# 遞迴撿出球衣包底下所有 .fsh。
# 用 os.walk 往下找,是因為社群的壓縮檔解開後常常還包著一層甚至兩層資料夾,
# 而要求使用者「自己把檔案搬到最外層」是本站的禁區(退休球員不必做這種事)。
def collect(moddir):
    if not os.path.isdir(moddir):
        raise DataError('找不到資料夾 %s' % moddir)
    found = []
    for root, dirs, files in os.walk(moddir):
        # sorted:讓每次執行的列表順序一樣,不然作業系統給的順序會變,
        # 使用者拿兩次輸出對照時會以為東西不一樣。
        # ⚠️ 2026-09-05 補 dirs.sort():原本只排了檔名,**沒有排資料夾**,
        #    所以上面那句保證只做到一半 —— 球衣包分兩層時,子資料夾的先後
        #    是作業系統給的順序。本機實測建了 zzz/aaa/mmm/bbb 四個資料夾,
        #    os.walk 回報的順序是 mmm、bbb、aaa、zzz,既不是字母序也不是
        #    建立順序。dirs 要**就地**排序(sort() 不是 sorted()),
        #    os.walk 才會照著走。
        dirs.sort()
        for f in sorted(files):
            if f.lower().endswith('.fsh'):
                found.append((os.path.join(root, f), f, classify(f)))
    if not found:
        raise DataError('%s 底下一個 .fsh 都沒有。\n'
                        '  球衣包通常要先解壓縮,而且裡面可能還有一層資料夾。' % moddir)
    return found


def plan(gamedir, moddir):
    """算出完整的動作清單,回傳 (三個封裝檔的路徑, 裝得進去的, 裝不進去的)。

    **三個指令都先呼叫它**,--scan 與預覽只印它的結果,--apply 才照著做。
    「先全部算完再動手」是刻意的:邊算邊寫會在中途發現問題時留下半套球衣。
    完全唯讀。
    """
    paths = archive_paths(gamedir)
    # 一次把三個封裝檔的目錄讀成「小寫檔名 -> 目錄項目」。
    # 轉小寫是因為球衣包的檔名大小寫不一定跟封裝檔裡的一樣,
    # 而 Windows 的檔案系統本來就不分大小寫,使用者看不出差別。
    toc = {k: {it[0].lower(): it for it in big_entries(p)} for k, p in paths.items()}
    ok, bad = [], []
    for full, name, target in collect(moddir):
        # 第一關沒過:檔名不符合三條規則,不知道該裝哪裡。不猜。
        if target is None:
            bad.append((name, '檔名看不出該裝到哪裡'))
            continue
        # 第二關:封裝檔裡真的有同名項目嗎。
        # 這一關才是「只能換不能加」那條鐵律的執行點:沒有同名項目就只能新增,
        # 而新增會讓目錄變長、後面所有資料位移,那等於重新打包
        # (實測 uniforms.big 有 25.1%、logos.big 有 45.9% 的位元組不在目錄範圍內,
        #  重新打包會把那些資料弄丟)。所以跳過,並且把原因說給使用者聽。
        entry = toc[target].get(name.lower())
        if entry is None:
            bad.append((name, '%s 裡沒有同名項目,只能新增而不能替換'
                        % os.path.basename(paths[target])))
            continue
        # entry 是 big_entries() 的 (名稱, 目錄欄位位置, 資料位移, 資料長度)。
        # 這裡只留 [1] 目錄欄位位置(等一下要覆寫的那 8 個位元組)
        # 與 [3] 原本的長度(給 --scan 印「目前幾 bytes → 換成幾 bytes」)。
        ok.append((full, name, target, entry[1], entry[3]))

    # ── 同一個名字在球衣包的兩個子資料夾裡各有一份 ──
    # 社群包常常附一個「original」「舊版」之類的資料夾,裡面是同名的檔。
    # 兩份都接進去的話,封裝檔的目錄只會指向最後寫的那一份,而複驗會拿
    # 第一份去比,於是印「讀回來的位元組跟來源不同」、叫人 --restore。
    # 那是**假的失敗**:球衣其實裝好了,而使用者會把一個好好的遊戲還原掉,
    # 還去回報一個不存在的問題(2026-09-05 實測重現過)。
    # 這裡只留最後找到的那一份(也就是原本真的會生效的那一份),
    # 並且把被略過的那一份說給使用者聽 —— 上面 dirs.sort() 之後,
    # 「最後找到的」是固定的,不會這次執行選 A、下次選 B。
    keep = {}
    for row in ok:
        keep[row[1].lower()] = row
    if len(keep) != len(ok):
        for row in ok:
            if keep.get(row[1].lower()) is not row:
                bad.append((row[1],
                            '球衣包裡有兩個同名的檔;略過 %s 底下這一份,'
                            '裝 %s 底下那一份'
                            % (os.path.dirname(row[0]) or '.',
                               os.path.dirname(keep[row[1].lower()][0]) or '.')))
        ok = [r for r in ok if keep.get(r[1].lower()) is r]
    return paths, ok, bad


# ─────────────────────────────────────────────────────────
#  各種動作
# ─────────────────────────────────────────────────────────
def cmd_scan(gamedir, moddir):
    """--scan:只清點,不做任何事。

    為什麼要有這個指令:球衣包裡有幾個檔裝不進去是**正常的**(遊戲裡那個位置
    本來就不存在)。先讓人看到「哪些會裝、哪些會跳過、為什麼」,
    等一下真的裝的時候才不會把跳過訊息當成失敗。
    """
    paths, ok, bad = plan(gamedir, moddir)
    print('  球衣包 %s' % moddir)
    print('  找到 %d 個 .fsh' % (len(ok) + len(bad)))
    print()
    # 照封裝檔分組再印。使用者的心智模型是「這一套球衣要分裝到三個地方」,
    # 照那三個地方分組列出來,對得上他正在做的事。
    by = {}
    for full, name, target, field, oldsize in ok:
        by.setdefault(target, []).append((name, os.path.getsize(full), oldsize))
    for key, rel, desc in ARCHIVES:
        rows = by.get(key, [])
        print('  ── %s(%s)── %d 個' % (os.path.basename(paths[key]), desc, len(rows)))
        for name, newsz, oldsz in rows:
            print('     %-12s 目前 %8d → 換成 %8d bytes' % (name, oldsz, newsz))
        if not rows:
            print('     (沒有要裝的)')
    if bad:
        print()
        print('  ⚠️ 這 %d 個裝不進去:' % len(bad))
        for name, why in bad:
            print('     %-12s %s' % (name, why))
        print()
        print('     裝不進去不代表球衣包壞了,上面每一行後面寫的就是各自的原因。')
        print('     最常見的一種是:那支球隊在遊戲裡本來就只有一套球衣,那個位置')
        print('     不存在;硬要新增就得整包重新打包,而重新打包會弄丟目錄沒指到的')
        print('     資料,所以本站不做。另一種是球衣包裡附了同名的兩份,只裝一份。')
    print()
    print('  以上只是清點,還沒有動到任何檔案。')
    print('  要裝的話:把 --scan 換成 --install')


def _rename_in_message(msg, staged, paths):
    """把錯誤訊息裡工作複本那個臨時名字換回使用者認得的封裝檔名。

    ⚠️ 2026-09-06 實測抓到的:改成在複本上做之後,底層那幾支解析器
       (size_field_order / big_entries)報錯時印的是 os.path.basename(它拿到的路徑),
       而它拿到的是 .uniforms.big.part-9op790tn 這種臨時名字。
       畫面上就變成「.uniforms.big.part-9op790tn 的檔頭大小欄位跟實際大小對不上」——
       讀者手上根本沒有那個檔,這句話對他毫無意義。他要看到的是 uniforms.big。
       (不改那幾支解析器的簽章,是因為它們也是課程頁面在講的東西。)

    ⚠️ 2026-09-11:呼叫端從「只有 DataError」擴到「OSError 也算」。
       OSError 的臨時名字不是本腳本組出來的訊息,是作業系統回報的檔名欄位,
       所以那一條是改 filename / filename2 / strerror 三個欄位,不是改字串。
    """
    # ⚠️ 2026-09-11 覆驗抓到:OSError 的 filename 在少數情況會是 bytes
    #    (作業系統回報 bytes 路徑時)。對 bytes 做 str 的 replace 會丟 TypeError,
    #    把真正的錯誤訊息整個蓋掉 —— 讀者看到的會是一句跟他的問題無關的話。
    #    目前全檔的路徑都經過 os.fspath 變成 str,所以打不到;
    #    但這道守門只有兩行,不要等哪天有人改了路徑處理才發現。
    if not isinstance(msg, str):
        return msg
    for key, tmp in staged.items():
        msg = msg.replace(os.path.basename(tmp), os.path.basename(paths[key]))
    return msg


def _recheck_archive(archive, rows, shown):
    """重新讀一次目錄,三層複驗這一個封裝檔。回傳沒過的項目數(❌ 直接印出來)。

    三層各守一件事:
      1. 目錄裡那一項的長度,要等於來源檔的大小
      2. 照目錄說的位移與長度把資料撈出來,跟來源檔逐位元組比
         (長度對不代表內容對,所以第一層過了還要做這一層)
      3. 檔頭 +4 的總大小要等於檔案實際大小 —— 這一項守的是「位元組序有沒有
         寫對」;寫反了這裡會變成一個天文數字。兩種順序都認,因為原檔本來就
         兩種都有(見 size_field_order)。

    ⚠️ 一定要**重新讀一次目錄**,不能拿記憶體裡那份來比 —— 拿寫之前的資料
       去驗寫之後的結果,等於自己驗自己,永遠會過。

    archive 是要讀的那個檔(換名之前是工作複本,換名之後是玩家的遊戲檔);
    shown 是要印在畫面上的名字 —— 使用者認得的是 uniforms.big,
    不是工作複本那個臨時取的名字。
    """
    bad = 0
    toc = {it[0].lower(): it for it in big_entries(archive)}
    for full, name in rows:
        it = toc.get(name.lower())
        want = os.path.getsize(full)
        if it is None or it[3] != want:
            print('  ❌ %s 複驗失敗(目錄說 %s,應該是 %d bytes)'
                  % (name, it[3] if it else '沒有這一項', want))
            bad += 1
            continue
        with open(archive, 'rb') as f:
            f.seek(it[2]); got = f.read(it[3])
        with open(full, 'rb') as f:
            if got != f.read():
                print('  ❌ %s 複驗失敗(讀回來的位元組跟來源不同)' % name)
                bad += 1
    n = os.path.getsize(archive)
    with open(archive, 'rb') as f:
        h = f.read(8)
    if struct.unpack('<I', h[4:8])[0] != n and struct.unpack('>I', h[4:8])[0] != n:
        print('  ❌ %s 的檔頭大小欄位跟實際大小對不上' % shown)
        bad += 1
    return bad


def cmd_install(gamedir, moddir, apply_it):
    """--install:預覽,加了 --apply 才真的寫。

    apply_it 為假時**在印完預覽就 return**,底下備份與寫入那幾段完全不會執行。
    這是本站每一支會改遊戲檔的腳本共同的形狀:預設安全,危險要自己開口要。

    真的寫的時候順序是:先把每一個來源檔的開頭認過一遍(有一個不像球衣檔就
    整批停下,那時候一個位元組都還沒寫)→ 備份這次會動到的那幾個封裝檔
    → 把每個封裝檔各複製一份工作複本到它旁邊 → 整批球衣全部接到複本的檔尾
    → 讀複本複驗一輪(沒過就整批不換,遊戲檔沒動)→ 一次把複本全部換上去
    → 讀真正的遊戲檔再複驗一輪 → 有一項不對才叫人 --restore。

    ⚠️ 2026-09-06 第三輪改的重點在中間那幾步:以前是對正本 r+b 直接追加,
       多件球衣一件一件寫,第三件失敗時前兩件已經在遊戲檔裡了。現在整批套在
       同一份工作複本上,遊戲檔要嘛全部裝好、要嘛完全沒動。
    """
    paths, ok, bad = plan(gamedir, moddir)
    if not ok:
        raise DataError('沒有一個檔裝得進去。先用 --scan 看原因。')
    print('  準備裝 %d 個檔%s' % (len(ok), ('，跳過 %d 個' % len(bad)) if bad else ''))
    for full, name, target, field, oldsize in ok:
        print('     %-12s → %s' % (name, os.path.basename(paths[target])))
    if bad:
        print('  跳過:%s' % '、'.join(n for n, _ in bad))
    if not apply_it:
        print()
        print('  以上是預覽,還沒有動到任何檔案。')
        print('  確定要裝的話,在剛才那一行最後面加上 --apply')
        return

    # ── 寫任何東西之前,先把每一個來源檔的開頭都認過一遍 ──
    # 這一關原本只寫在下面的寫入迴圈裡。第 3 個檔不是球衣檔時,前兩個已經
    # 接進封裝檔了 —— 正是 plan() 那句「先全部算完再動手」要避免的半套狀態,
    # 而畫面上只印「不敢裝進去」,一個字都沒說「已經裝了兩個」。
    # 2026-09-05 在複本上實測重現過:一好一壞兩個檔,好的那個已經接進
    # uniforms.big 才停下來。提到動手之前做,失敗時一個位元組都還沒寫。
    # 下面迴圈裡那一關留著沒關係,它到時候只會再確認一次。
    for full, name, target, field, oldsize in ok:
        with open(full, 'rb') as f:
            head4 = f.read(4)
        if head4[:2] != b'\x10\xfb' and head4[:4] != b'SHPI':
            raise DataError('%s 的開頭既不是 QFS(10 FB)也不是 SHPI，\n'
                            '  這不像遊戲的圖檔,不敢裝進去。\n'
                            '  還沒有動到任何檔案。' % name)

    # ── 只備份「這一次真的會動到」的封裝檔 ──
    # touched 是這批球衣實際會寫到的那幾個。models.big 有 536 MB,
    # 沒有要動它就不要花那十幾秒去複製它。
    touched = sorted({t for _, _, t, _, _ in ok})
    print()
    for key in touched:
        p = paths[key]
        backup = p + BACKUP_SUFFIX
        # 動手之前先確認這兩個名字都不是符號連結。封裝檔本身是連結的話,
        # 等一下工作複本會跟著它換到別的地方去;備份那個名字是連結的話,
        # 寫備份就等於蓋掉連結指到的東西。連結不必是壞人放的 ——
        # 自己搬過資料夾、做過整理,都可能留下一個。
        _refuse_symlink(p, '封裝檔 %s' % os.path.basename(p))
        _refuse_symlink(backup, '備份檔 %s' % os.path.basename(backup))
        # 已經有備份就不覆蓋。那一份才是「你第一次動手之前的樣子」;
        # 每次都重新備份的話,裝第二套球衣就等於把退路蓋掉了。
        if os.path.exists(backup):
            print('  備份已存在,保留最早那一份 → %s' % os.path.basename(backup))
            continue
        print('  正在備份 %s(%.0f MB)...' % (os.path.basename(p), os.path.getsize(p) / 1048576.0))
        _atomic_copy(p, backup)
        print('  已備份 → %s' % os.path.basename(backup))

    # 哪幾個來源檔要進哪一個封裝檔。複驗兩次(換名前、換名後)都要用到。
    rows_by_key = {}
    for full, name, target, field, oldsize in ok:
        rows_by_key.setdefault(target, []).append((full, name))

    # ── 從這裡開始,所有改動都做在「工作複本」上,不碰正本 ──
    # 2026-09-06 第三輪改的。以前是對正本 r+b 直接追加,有兩個縫:
    #   · 寫到一半被中斷,正本會停在「目錄已經指到新位置、檔頭的總大小還是舊的」
    #     這種自相矛盾的狀態 —— 本腳本自己的 size_field_order 讀到它就會說
    #     「這個檔可能已經損毀」。
    #   · 多件球衣是一件一件寫進去的,第三件失敗時前兩件已經在正本裡了(半套)。
    # 現在整批球衣全部套到同一份工作複本上,驗完才 os.replace 一次換名。
    # **遊戲檔只有兩種狀態:全部裝好,或完全沒動。**
    staged = {}                 # key -> 工作複本路徑(還沒換上去的那些)
    keeps = {}                  # key -> 回頭路,換名中途失敗時靠它把已換的換回來
    swapped = []                # 已經換上去的 [(key, 正本路徑)]
    try:
        print()
        for key in touched:
            p = paths[key]
            print('  正在準備 %s 的工作複本(%.0f MB)...'
                  % (os.path.basename(p), os.path.getsize(p) / 1048576.0))
            staged[key] = _stage_copy(p)

        # ── 逐檔接到工作複本的尾巴 ──
        # 這一整段(含下面換名前的複驗)如果停下來,訊息裡可能夾著工作複本那個
        # 臨時名字。往上丟之前先換回使用者認得的封裝檔名(見 _rename_in_message)。
        try:
            print()
            for full, name, target, field, oldsize in ok:
                with open(full, 'rb') as f:
                    blob = f.read()
                # 球衣檔本身已經是遊戲格式,原封不動接進去。
                # 開頭 10 FB 代表 QFS 壓縮過,SHPI 代表沒壓縮,兩種遊戲都讀得動。
                # 這是**第二道**:同一件事上面備份之前已經全部認過一遍了。
                # 留著是因為「上面認過」跟「現在讀進來的這串位元組」是兩件事
                # (檔案可能在這中間被別的程式換掉)。走到這裡才發現的話,
                # 動的還是工作複本,遊戲檔仍然一個位元組都沒有被動到。
                if blob[:2] == b'\x10\xfb':
                    kind = 'QFS '
                elif blob[:4] == b'SHPI':
                    kind = 'SHPI'
                else:
                    raise DataError('%s 的開頭既不是 QFS(10 FB)也不是 SHPI，\n'
                                    '  這不像遊戲的圖檔,不敢裝進去。\n'
                                    '  改動都還在工作複本上,遊戲檔一個位元組都沒有動。'
                                    % name)
                # 位移印的是它在工作複本裡的位置。工作複本是正本逐位元組的複製,
                # 換名之後這個位移在遊戲檔裡完全一樣。
                new_off = append_entry(staged[target], field, blob)
                print('  %-12s %s %8d bytes → 接在 %s 第 %d 個位元組'
                      % (name, kind, len(blob), os.path.basename(paths[target]), new_off))

            # ── 換名之前:先用本腳本自己的解析器把每一份工作複本重讀一遍 ──
            # 這一關過不了就整批不換,遊戲檔連開都沒有被開來寫過。
            print()
            bad_check = 0
            for key in touched:
                bad_check += _recheck_archive(staged[key], rows_by_key.get(key, []),
                                              os.path.basename(paths[key]))
            if bad_check:
                raise DataError(
                    '工作複本複驗有 %d 項沒過,所以**沒有換上去**。\n'
                    '  你的遊戲檔一個位元組都沒有動,不必 --restore。\n'
                    '  請把上面每一行 ❌ 的訊息回報給本站。' % bad_check)
        except DataError as _e:
            raise DataError(_rename_in_message(str(_e), staged, paths))
        except OSError as _e:
            # ⚠️ 2026-09-11 補的:上面那一條只換了 DataError,而**最常見的一種
            #    失敗是 OSError** —— 封裝檔被設成唯讀時,工作複本會繼承那個唯讀
            #    權限(_stage_copy 會照抄正本的權限),接下來 append_entry 用
            #    r+b 開它就是 Permission denied,而作業系統回報的檔名正是
            #    .logos.big.part-cqb_mbz_ 這種臨時名字。實測(把 logos.big
            #    chmod 444 再 --apply)畫面上印的就是那個名字 —— 讀者手上根本
            #    沒有那個檔,而課程頁面那一列教的正是這種情形。
            #    這裡不換新的例外物件(換掉會丟掉 PermissionError 這種子類別),
            #    只把它兩個字串欄位裡的臨時名字換成使用者認得的封裝檔名;
            #    OSError 的 str() 是照這些欄位現算的,改了就跟著變。
            if getattr(_e, 'filename', None):
                _e.filename = _rename_in_message(_e.filename, staged, paths)
            if getattr(_e, 'filename2', None):
                _e.filename2 = _rename_in_message(_e.filename2, staged, paths)
            if getattr(_e, 'strerror', None):
                _e.strerror = _rename_in_message(_e.strerror, staged, paths)
            raise

        # ── 回頭路:讓「全有或全無」在多個封裝檔之間也成立 ──
        # 硬連結不佔空間也不複製資料,只是幫「現在的正本」多留一個名字;
        # os.replace 換掉的是目錄裡的名字,舊那一份還靠這個名字活著。
        # 換名中途失敗時,已經換上去的那幾個就靠它換回來。
        # ⚠️ exFAT / FAT32 這種不支援硬連結的磁碟做不出來。那就沒有回頭路,
        #    下面的收尾會誠實逐檔列出「已改 / 沒改」,不假裝退得回去。
        for key in touched:
            p = paths[key]
            try:
                kfd, kpath = _new_temp_beside(p)
                os.close(kfd)
                os.remove(kpath)            # mkstemp 先佔位子,再讓給 os.link
                os.link(p, kpath)
                keeps[key] = kpath
            except (OSError, AttributeError, NotImplementedError):
                keeps.pop(key, None)        # 做不出來就是沒有,這不算失敗

        # ── 換名。到這一行為止,遊戲檔一個位元組都沒有被動過 ──
        try:
            for key in touched:
                p = paths[key]
                # 登記在前、換名與登記綁成不可中斷的一段(見 _NoInterrupt)。
                # ⚠️ swapped 這一行**一定要在 with 裡面**。2026-09-06 下餌抓到:
                #    它原本在 with 外面,而下面回滾那一段是照著 swapped 決定
                #    「哪幾個要換回去」的。Ctrl-C 落在 os.replace 與 swapped.append
                #    中間時,logos.big 已經換掉了而 swapped 還是空的 —— 回滾
                #    什麼都沒做,螢幕上卻印「遊戲檔一個位元組都沒有動」。
                #    (實測:那一版印「沒改」,而磁碟上 logos.big 的 sha256 變了。)
                #    _STATE 當時是對的,錯的是這個給回滾看的登記。
                _mark_replacing(p)
                with _NoInterrupt():
                    os.replace(staged[key], p)
                    _mark_replaced(p)
                    swapped.append((key, p))
                    del staged[key]         # 換上去了,收尾不可以再刪這個名字
        except BaseException:
            # 換名中途失敗,或 Ctrl-C 剛好落在兩次換名中間。
            # 有回頭路就把已經換上去的換回來 —— 這樣「全有或全無」才成立。
            stuck = []
            for key, live in swapped:
                keep = keeps.get(key)
                try:
                    if keep is None:
                        raise OSError('這個磁碟做不出回頭路')
                    _mark_replacing(live)
                    with _NoInterrupt():
                        os.replace(keep, live)
                    keeps.pop(key, None)
                except (OSError, KeyboardInterrupt):
                    stuck.append(live)
            if stuck:
                _STATE['replaced'] = list(stuck)
                _mark_replaced(stuck[-1])
            else:
                # 全部換回來了,遊戲檔真的回到動手之前的樣子
                _STATE.update(phase='idle', target=None, replaced=[])
            del swapped[:]
            print()
            print('  ⚠️ 換名中途停下來了。逐檔說明:')
            for key in touched:
                nm = os.path.basename(paths[key])
                print('     %-14s %s' % (nm, '已改' if paths[key] in stuck else '沒改'))
            if stuck:
                print('  要退回去:')
                print('    python3 mvp_install_uniform.py "%s" --restore' % gamedir)
            else:
                print('  遊戲檔一個位元組都沒有動,不必 --restore。')
            raise
    finally:
        # 沒換上去的工作複本與沒用到的回頭路,一律清掉,不留垃圾。
        for _tmp in list(staged.values()):
            _drop_temp(_tmp)
        for _keep in list(keeps.values()):
            _drop_temp(_keep)

    # ── 換名之後再驗一次:這一次讀的是玩家真正的遊戲檔 ──
    # 「工作複本是對的」跟「換上去的那一份是對的」是兩件事。
    # (上面那個 print() 留的空行就是這一段的,換名前那一關過了就不印東西。)
    bad_check = 0
    for key in touched:
        bad_check += _recheck_archive(paths[key], rows_by_key.get(key, []),
                                      os.path.basename(paths[key]))
    if bad_check:
        raise DataError(
            '複驗有 %d 項沒過。舊資料還在封裝檔裡,還原得回來:\n'
            '    python3 mvp_install_uniform.py "%s" --restore\n'
            '  還原之後請把上面每一行 ❌ 的訊息回報給本站。\n'
            '  ⚠️ 這裡**不會**自動幫你還原:備份留的是「你第一次動手之前」的樣子,\n'
            '     你如果先前已經裝過別套球衣,自動還原會連那一套一起退掉。\n'
            '     那個決定要你自己做。' % (bad_check, gamedir))
    print('  複驗:%d 個檔全部逐位元組相符，%d 個封裝檔的檔頭都正確。' % (len(ok), len(touched)))
    print('  完成。進遊戲看看那支球隊。')


def cmd_restore(gamedir):
    """--restore:把三個封裝檔從備份還原。

    三個一起處理,而且**沒有備份的就跳過**(那個檔本來就沒被動過)。
    還原完備份留著不刪:救回來就把救命的那份丟掉,是在賭下一次不會出事。

    順序是「全部驗完才開始蓋」,跟 --install 同一個道理:
      1. 每一份備份都先驗完不完整(見 _restore_from_backup)。有一份不合格就
         整支停下來,那時候一個位元組都還沒覆蓋。
      2. 全部合格才逐檔覆蓋,而且每一檔各自走「同資料夾的暫存檔 + os.replace」,
         **跟備份逐位元組比對過才換上去** —— 比不過就整個不換,正本原封不動。
    ⚠️ 2026-09-05 之前是一邊驗一邊蓋:三份裡第三份壞掉時,前兩份已經還原了,
       使用者最後拿到「一半還原、一半沒還原」的混合狀態(實測重現過)。
    """
    paths = archive_paths(gamedir)
    todo = []
    for key, rel, desc in ARCHIVES:
        p = paths[key]
        backup = p + BACKUP_SUFFIX
        # lexists 而不是 exists:備份那個名字如果是指到不存在的地方的符號連結,
        # exists() 會說「沒有備份」而整個跳過它 —— 使用者明明看得到那個檔在那裡,
        # 卻被告知「找不到備份」。lexists() 看得見連結本身。
        if not os.path.lexists(backup):
            continue
        _refuse_symlink(backup, '備份檔 %s' % os.path.basename(backup))
        _refuse_symlink(p, '封裝檔 %s' % os.path.basename(p))
        _restore_from_backup(backup, p, verify_only=True)   # 只驗,不蓋
        todo.append((p, backup))
    if not todo:
        raise DataError('三個封裝檔都找不到備份,沒有東西可以還原。')
    for p, backup in todo:
        print('  正在還原 %s(%.0f MB)...' % (os.path.basename(p), os.path.getsize(backup) / 1048576.0))
        _restore_from_backup(backup, p)
    print('  已還原 %d 個封裝檔,每一個都跟備份逐位元組相符。備份檔留著沒刪。' % len(todo))


def main():
    """指令分派 + 統一的出錯出口。

    分派順序是刻意的:--selftest 排最前面(它不需要遊戲資料夾,手上還沒有
    遊戲的人也該能先驗這支腳本自己),再來是 --restore,因為那是「東西壞了要
    救回來」的人最急的一件事,不該被別的參數擋住。接著是唯讀的 --scan,
    最後才是 --install。什麼都沒給就印說明,不動任何檔案。

    回傳值就是 exit code:0 正常、1 是沒給遊戲資料夾(只印了說明)、
    2 是停下來了(資料有問題,或作業系統不讓讀寫)、130 是被 Ctrl-C。
    DataError 與 OSError 都在這裡接住印成人話,不讓使用者看到一整片 traceback。
    ⚠️ 130 那一條**不會**是 0:被中斷的執行不算成功,而寫腳本串起來的人
       是看 exit code 決定要不要繼續往下做的。
    ⚠️ 2026-09-05 補 OSError:原本只接 DataError,遊戲裝在需要系統管理員權限的
       位置、封裝檔被設成唯讀、磁碟滿、外接碟被拔掉,使用者拿到的都是一整片
       traceback —— 而這段說明正寫著「不讓使用者看到一整片 traceback」。
       (實測把 logos.big 設成 444 再 --apply,原本吐五層 traceback、exit=1。)
    """
    EPILOG = (
        "\n例子(照順序做):\n\n"
        "  1. 先清點:哪些裝得進去、哪些裝不進去\n"
        "     python3 mvp_install_uniform.py \"<遊戲資料夾>\" --scan \"<球衣包資料夾>\"\n\n"
        "  2. 預覽要做什麼(還是不會動到檔案)\n"
        "     python3 mvp_install_uniform.py \"<遊戲資料夾>\" --install \"<球衣包資料夾>\"\n\n"
        "  3. 確定了才真的裝\n"
        "     python3 mvp_install_uniform.py \"<遊戲資料夾>\" --install \"<球衣包資料夾>\" --apply\n\n"
        "  出問題就還原(三個封裝檔一起):\n"
        "     python3 mvp_install_uniform.py \"<遊戲資料夾>\" --restore\n"
    )
    ap = argparse.ArgumentParser(
        description='把一套球衣裝進 MVP Baseball 2005',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=EPILOG)
    ap.add_argument('gamedir', nargs='?',
                    help='遊戲資料夾(裡面看得到 mvp2005.exe 跟 data)')
    ap.add_argument('--scan', metavar='球衣包資料夾', help='清點,不做任何事')
    ap.add_argument('--install', metavar='球衣包資料夾', help='裝進去(沒加 --apply 就只是預覽)')
    ap.add_argument('--apply', action='store_true', help='真的寫入')
    ap.add_argument('--restore', action='store_true', help='把三個封裝檔從備份還原')
    ap.add_argument('--selftest', action='store_true', help='自我測試,不碰任何遊戲檔')
    args = ap.parse_args()

    if args.selftest:
        return selftest()
    if not args.gamedir:
        ap.print_help()
        return 1

    try:
        if args.restore:
            cmd_restore(args.gamedir)
        elif args.scan:
            cmd_scan(args.gamedir, args.scan)
        elif args.install:
            cmd_install(args.gamedir, args.install, args.apply)
        else:
            ap.print_help()
    except DataError as e:
        print('\n  停下來了:%s\n' % e)
        return 2
    except OSError as e:
        # 作業系統層級的失敗(唯讀、要管理員權限、磁碟滿、外接碟拔掉)。
        # DataError 跟 OSError 互不隸屬,分成兩條寫不是為了先後順序,
        # 是為了讓「檔案內容不對」跟「作業系統不讓碰」給出不一樣的話 ——
        # 使用者要做的事完全不同(一個是換檔案,一個是改權限或換安裝位置)。
        print('\n  停下來了:作業系統不讓我讀寫這個檔。\n'
              '  %s\n'
              '  常見原因:遊戲裝在需要系統管理員權限的位置(例如 Program Files)、\n'
              '  檔案被設成唯讀、磁碟空間不夠、或外接碟被拔掉。' % e)
        # ⚠️ 2026-09-06:這裡原本一律印「已經印過『已備份』的話可以 --restore」。
        #    改成複本上做之後,絕大多數的 OSError 都發生在換名之前 —— 那時候
        #    遊戲檔一個位元組都沒有動,叫人去還原是多餘的,還會把他先前裝好的
        #    別套球衣一起退掉。照登記講話才不會多此一舉。
        if _STATE['phase'] == 'idle':
            print('  你的遊戲檔一個位元組都沒有動,不必 --restore。\n')
        else:
            print('  封裝檔已經換過了。要退回去:\n'
                  '    python3 mvp_install_uniform.py "%s" --restore\n' % args.gamedir)
        return 2
    except KeyboardInterrupt:
        # 「什麼都沒動到」這句話要有憑據。_STATE 是三態的,而且「換名 + 登記」
        # 被 _NoInterrupt 綁成不可中斷的一段,所以這裡看到的登記一定跟磁碟上的
        # 狀態一致 —— 分不出來就只能含糊地說「已中斷」,而使用者最需要知道的
        # 正是「我現在的遊戲檔還能不能用」。
        if _STATE['phase'] == 'replaced':
            print('\n  已中斷 —— 但封裝檔已經動過了。要退回去:\n'
                  '    python3 mvp_install_uniform.py "%s" --restore\n' % args.gamedir)
        elif _STATE['phase'] == 'replacing':
            # 只有在 signal.signal 裝不上(非主執行緒)的機器上才可能走到這裡。
            # 不確定就說不確定,不可以猜「沒動到」。
            print('\n  已中斷 —— 中斷時正在替換:\n'
                  '    %s\n'
                  '  不確定換好了沒有。請用下面這一行還原,或自己跟 %s 備份比對:\n'
                  '    python3 mvp_install_uniform.py "%s" --restore\n'
                  % (_STATE['target'], BACKUP_SUFFIX, args.gamedir))
        else:
            print('\n  已中斷。還沒有動到任何檔案。\n')
        return 130
    return 0


# ─────────────────────────────────────────────────────────
#  自我測試(--selftest)
#
#  ⚠️ 這一段一個遊戲檔都不碰。它在系統暫存資料夾裡自己造幾個最小的封裝檔,
#     然後**故意去踩**下面那 70 個反向餌寫著的情況,看它有沒有真的擋下來。
#  ⚠️ 量法與結果(2026-09-26 重量):把自我測試以外、「下一行是 raise」的 if
#     逐一改成永遠不成立(一次只拆一道)再跑 --selftest,看它會不會變紅。
#     這樣數到 28 道,28 道單拆都會紅,而且逐一看過是對準它的那個餌紅的。
#     2026-09-24 用同一個量法時只有 1 道會紅(那時候還沒有餌 18 到 70;
#     當時記的是 29 道,2026-09-26 在當時那個版本上重數是 28 道,差的那 1 道沒查出來)。
#  ⚠️ 上面那個量法只數一種形狀。2026-09-26 另外用一套更寬的拆法再量一次,
#     多數六種:下一行是 _stop(...) 的 if(還原前檢查那 9 道)、下一行印 ❌ 的 if
#     (複驗那 3 層)、接住錯誤再改用讀者看得懂的話說出來的 except(8 處,拆法是讓它接不到)、
#     沒有 if 包著的 raise(2 處:size_field_order 最後那一行、寫入迴圈 else 後面那一行)、
#     呼叫 _refuse_symlink / _verify_same / 只驗不蓋的 _restore_from_backup 的那一行(9 處,
#     拆法是拿掉那次呼叫)、_NoInterrupt 離開時補丟的 Ctrl-C(1 處)。兩套合計 60 處。
#     補餌 47 到 67 之前,單拆還是全綠的有 22 處;補完之後剩 1 處:
#     _stage_copy 開頭那次 _refuse_symlink。cmd_install 在備份之前已經對同一個路徑叫過
#     一次,只有封裝檔在那兩次中間被換成連結才輪得到它,沒有替它下餌。
#  ⚠️ 兩套量法都只數「會停下來或報失敗」的那幾種形狀。不停下來、只是換一條路走的
#     保護(「備份已經在就不再備份」底下是 continue、「沒加 --apply 就只預覽」底下是
#     return)兩套都數不到。所以 2026-09-26 又量了第三次:自我測試以外、if 底下那一層
#     直接有 return / continue / break 的(return 1、2 那種已經算在第一套裡)共 16 處,
#     一樣一次拆一處。補餌 68 之前單拆全綠 6 處,其中一處就是「沒加 --apply 就只預覽」——
#     拆掉它,沒加 --apply 的 --install 會真的備份、改寫封裝檔、印「完成」,當時的自我測試照樣全綠。
#     補完剩 5 處,逐一看過:qfs_decompress 開頭「不是 QFS 就原樣回傳」、size_field_order
#     認大端序的那一行、big_entries 讀目錄讀到資料盡頭就停的兩行 —— 這 4 處是分辨格式
#     與讀檔的分支,不是擋東西的守門;剩下 1 處是 _rename_in_message 開頭的型別檢查,
#     它自己的註解寫著目前的程式走不到它,沒有替它下餌。
#     其他寫法的保護(例如迴圈條件、三元運算式)沒有逐一找過,所以這不等於每一道守門都有餌。
#  ⚠️ 叫讀者還原的那幾句話也不在任何一套量法裡(它們是 print 與訊息字串,不是 if)。
#     2026-09-26 另外逐一拆過:換上去之後複驗沒過、換名到一半失敗的逐檔說明、
#     main() 接住 OSError 與 Ctrl-C 之後那幾段,各自把還原指令改成「不必 --restore」
#     或整行拿掉,餌 27、28、52 分別會紅;換名之前複驗沒過那一句多印一行還原指令,餌 26 會紅。
#     main() 接 Ctrl-C 時「中斷時正在替換、不確定換好了沒有」那一句沒有替它下餌
#     (那一段的註解說只有裝不上訊號處理器的機器才走得到它,這一點本站沒有另外驗)。
#  ⚠️ 反過來,叫讀者「不必 --restore」的那幾句也逐一拆過(2026-09-26,補餌 69、70 那一次)。
#     共拆 8 種:換名之前複驗沒過、換名到一半失敗但全部換回來了的逐檔說明、main() 接住
#     OSError 時照登記說的那一句,各自整行拿掉或改成叫人還原;另外把 main() 照登記分兩路的
#     那個 if 改成永遠走「封裝檔已經換過了」、把逐檔說明那個 if 改成永遠給還原指令。
#     補餌 69、70 之前 8 種裡 6 種單拆全綠(只有換名之前複驗那一句有餌 26 守著);
#     補完 8 種都會紅,逐一看過紅的是餌 26、69、70 裡對準它的那一個。
# ─────────────────────────────────────────────────────────
class _Mute(object):
    """把一段程式的 print 吃掉,只給 --selftest 用。

    反向餌 12 會跑一次完整的安裝與還原,那兩支本來就會印十幾行給使用者看的字。
    自我測試的畫面上只該留最後那兩行 —— 課程頁面就是這樣教的:
    「印出別的東西就不要拿它去動遊戲檔,直接回報」。多印的東西會讓人以為出事了。
    """

    def __enter__(self):
        self._old = sys.stdout
        sys.stdout = self
        return self

    def write(self, s):
        return len(s)

    def flush(self):
        pass

    def __exit__(self, exc_type, exc, tb):
        sys.stdout = self._old
        return False


def _fake_big(items):
    """用 [(名稱, 資料)] 組一個最小但合法的 BIGF,只給 --selftest 用。

    照的是上面那張格式表:檔頭 16 個位元組 + 目錄(每項 8 個位元組的位移與
    長度 + 以 0x00 結尾的名稱)+ 各項資料本體。目錄一律 big-endian,
    檔頭 +4 的總大小這裡寫 little-endian(兩種本腳本都認,見 size_field_order)。
    """
    toc = b''
    for name, blob in items:
        toc += b'\x00' * 8 + name.encode('latin-1') + b'\x00'
    out = bytearray(b'BIGF' + b'\x00' * 4 + len(items).to_bytes(4, 'big')
                    + b'\x00' * 4 + toc)
    pos, off = 16, len(out)
    for name, blob in items:
        out[pos:pos + 4] = off.to_bytes(4, 'big')
        out[pos + 4:pos + 8] = len(blob).to_bytes(4, 'big')
        pos += 8 + len(name) + 1
        off += len(blob)
    for _, blob in items:
        out += blob
    out[4:8] = struct.pack('<I', len(out))
    return bytes(out)


# ── 反向餌 18 到 59 與 68 到 70 共用的小工具(2026-09-26 加)─────────────
# 為什麼要有它們:2026-09-24 把自我測試以外的守門逐一拆掉(那一個 if 改成永遠
# 不成立)再跑 --selftest,單拆一道就會紅的只有 1 道。讀者最常撞到的那幾道
# (路徑給錯、球衣包沒解壓、封裝檔壞了、沒有備份就按 --restore…)拆掉了也照樣全綠。
# 下面這幾支讓餌能照「讀者在命令列打的樣子」跑一次,再驗三件事:
# 畫面上那句中文、結束碼、檔案有沒有被動到。
def _selftest_snap(root):
    """把 root 底下每一個檔讀成 {相對路徑: 位元組},只給 --selftest 用。

    前後各拍一次、兩份要完全相等,才算「一個位元組都沒變,也沒有多出任何檔」——
    多出一份 .unibak 備份或留下一個 .part- 暫存檔,兩份就不相等。
    """
    out = {}
    for base, dirs, files in os.walk(root):
        dirs.sort()
        for fn in sorted(files):
            p = os.path.join(base, fn)
            with open(p, 'rb') as f:
                out[os.path.relpath(p, root)] = f.read()
    return out


def _selftest_game(parent, name):
    """組一個假的遊戲資料夾(三個封裝檔各一項),回傳 (資料夾, {鍵: 封裝檔路徑})。

    內容跟反向餌 12 用的那一份一樣:models.big 有 u001.fsh、uniforms.big 有 001.fsh、
    logos.big 有 l001.fsh。只給 --selftest 用。
    """
    g = os.path.join(parent, name)
    os.makedirs(os.path.join(g, 'data', 'frontend'))
    slots = {'models': os.path.join(g, 'data', 'models.big'),
             'uniforms': os.path.join(g, 'data', 'frontend', 'uniforms.big'),
             'logos': os.path.join(g, 'data', 'frontend', 'logos.big')}
    for key, item, ch in (('models', 'u001.fsh', b'M'),
                          ('uniforms', '001.fsh', b'U'),
                          ('logos', 'l001.fsh', b'L')):
        with open(slots[key], 'wb') as f:
            f.write(_fake_big([(item, b'\x10\xfb' + ch * 30)]))
    return g, slots


def _selftest_pack(parent, name, files):
    """組一個假的球衣包資料夾。files 是 [(檔名, 位元組)]。只給 --selftest 用。"""
    m = os.path.join(parent, name)
    os.makedirs(m)
    for fn, blob in files:
        with open(os.path.join(m, fn), 'wb') as f:
            f.write(blob)
    return m


def _selftest_run_main(argv):
    """照讀者在命令列打的樣子跑一次 main(),回傳 (結束碼, 畫面上印的字)。只給 --selftest 用。

    不直接呼叫 cmd_install 那幾支,是因為讀者看到的是 main() 印的那句
    「停下來了:…」跟結束碼 —— 反向餌要驗的正是這兩樣。
    main() 沒接住的例外(在讀者那裡會變成一整片 traceback)回傳成「例外 …」字串,
    呼叫端 assert 結束碼是 2 的那一行就會紅。
    """
    import contextlib
    import io
    buf = io.StringIO()
    old_argv = sys.argv
    sys.argv = ['mvp_install_uniform.py'] + list(argv)
    try:
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
            try:
                rc = main()
            except SystemExit as e:
                rc = e.code
            except Exception as e:
                rc = '例外 %r' % (e,)
    finally:
        sys.argv = old_argv
    return rc, buf.getvalue()


def _selftest_shpi(code=0x7D, width=2, height=2, num=1, magic=b'SHPI', img_off=24):
    """組一個只有一張圖的最小 SHPI,只給 --selftest 用。

    照上面 FSH 那張格式表:'SHPI' + 總長 + 圖數(little-endian)+ 4 個字的目錄代號,
    目錄第 0 項(4 個字的標籤 + 圖片記錄的位移)從 16 開始,圖片記錄從 24 開始,
    像素從 24 + 16 = 40 開始。像素一律照 4 bytes/像素 填(ARGB32 的大小)。
    """
    rec = (bytes([code, 0, 0, 0]) + struct.pack('<HH', width, height) + b'\x00' * 8
           + b'\x11' * (width * height * 4))
    out = (magic + b'\x00' * 4 + struct.pack('<I', num) + b'GIMX'
           + b'0000' + struct.pack('<I', img_off) + rec)
    return out[:4] + struct.pack('<I', len(out)) + out[8:]


def _selftest_loch(locl=b'LOCL', count=2):
    """組一個最小的假語系檔(LOCH),只給 --selftest 用(反向餌 60 到 63,2026-09-26 加)。

    只放還原前檢查會讀的那幾格:檔頭 +16 是字串區的位移(這裡是 32);
    字串區開頭是 'LOCL',+12 是字串條數,+16 起每條 4 個位元組的位移
    (相對於字串區開頭)。兩條字串,最後一條從字串區 +30 開始,整個檔 68 個位元組。
    """
    out = bytearray(b'LOCH' + b'\x00' * 28)
    out[16:20] = struct.pack('<I', 32)
    out += locl + b'\x00' * 8 + struct.pack('<I', count)
    out += struct.pack('<II', 24, 30)
    out += b'ABCDE\x00' + b'FGHIJ\x00'
    return bytes(out)


def _selftest_mz(pe=b'PE\x00\x00', nsec=1, raw_size=0x100):
    """組一個最小的假執行檔(MZ),只給 --selftest 用(反向餌 64 到 67,2026-09-26 加)。

    只放還原前檢查會讀的那幾格:DOS 檔頭 +0x3C 指到 PE 檔頭(這裡是 0x40);
    PE 檔頭 +6 是節區數、+20 是選用檔頭長度(這裡是 0,所以節區表從 0x58 開始);
    節區表每項 40 個位元組,+16 是資料長度、+20 是資料位移。
    整個檔 0x200 個位元組,唯一那個節區從 0x100 開始、長 raw_size。
    """
    out = bytearray(0x200)
    out[0:2] = b'MZ'
    out[0x3C:0x40] = struct.pack('<I', 0x40)
    out[0x40:0x44] = pe
    out[0x46:0x48] = struct.pack('<H', nsec)
    out[0x58 + 16:0x58 + 24] = struct.pack('<II', raw_size, 0x100)
    return bytes(out)


# ── 反向餌的記帳簿(2026-09-11 第四輪加)──────────────────────────
# 為什麼要有它:課程頁面叫讀者拿畫面上那個數字去對照,對不上就「不要拿它去
# 動遊戲檔,直接回報」。而餌 1、2、8(2026-09-26 起再加 56 到 59)需要這台機器
# 做得出符號連結,餌 10、13 需要裝得上 Ctrl-C 的訊號處理器 —— 兩件事都有機器做不到:
#   · Windows 沒開開發人員模式(也不是系統管理員)就做不出符號連結,
#     那幾個餌會整段跳過;
#   · 不在主執行緒時 signal.signal 裝不上,那兩個餌會整段跳過。
# 舊版不管實際跑了幾個,結尾都印同一個寫死的數字。實測模擬這兩種機器:
# 做不出連結時只有 10 個餌真的踩過、非主執行緒時 11 個,畫面上都還是印 13。
# 那個數字正是頁面要讀者核對的東西,所以它說謊的代價是讀者拿一支「其實只驗了
# 十分之七」的工具去動遊戲檔,還以為全驗過了。
# 現在改成「跑到哪一個就記哪一個」,結尾照記錄簿講話,跳過的要講出來。
_BAIT_LOG = {'ran': [], 'skipped': []}


def _bait_ran(n):
    """第 n 個反向餌**真的踩過了**才可以呼叫(擺在那一段最後一行 assert 後面)。"""
    if n not in _BAIT_LOG['ran']:
        _BAIT_LOG['ran'].append(n)


def _bait_skipped(n, why):
    """這台機器做不到,所以第 n 個反向餌整段跳過。理由要能讓讀者判斷是不是自己這台。"""
    if n not in [x for x, _ in _BAIT_LOG['skipped']]:
        _BAIT_LOG['skipped'].append((n, why))


def _bait_summary(log):
    """把記錄簿變成畫面上那一到兩行字。回傳一串字串(每個元素一行)。

    刻意寫成「吃一本記錄簿、吐出字串」的純函式,反向餌 14 才踩得到它:
    拿掉一個餌再算一次,印出來的字一定要跟著變 —— 不然那個數字又是寫死的了。
    """
    ran = sorted(log['ran'])
    lines = ['自我測試:全部通過(含 %d 個反向餌)' % len(ran)]
    grouped = {}
    for n, why in log['skipped']:
        grouped.setdefault(why, []).append(n)
    for why in sorted(grouped):
        ns = '、'.join(str(x) for x in sorted(grouped[why]))
        lines.append('  ⚠️ 另外 %d 個反向餌沒有跑到(第 %s 個):%s'
                     % (len(grouped[why]), ns, why))
    return lines


# 兩種「這台機器做不到」的理由,兩個地方都要用同一份字,讀者才比得出來。
_WHY_NO_SYMLINK = '這台做不出符號連結(Windows 要開發人員模式或系統管理員才做得出來)'
_WHY_NO_SIGNAL = '這台裝不上 Ctrl-C 的訊號處理器(要在主執行緒才裝得上)'


def selftest():
    """不碰任何遊戲檔的自我測試,全部在系統暫存資料夾裡做(跑完不刪,方便自己進去看)。

    重點不是「有沒有通過」,是裡面有 **70 個反向餌**:先證明「答案錯的時候它
    真的會叫」。只驗正向的測試會一路綠燈,卻在功能整個壞掉時照樣綠燈,
    那種測試比沒有更危險(這是本站 2026-08-29 那一輪的教訓)。

    ⚠️ 其中 9 個有機器做不到:餌 1、2、8、56、57、58、59 要做得出符號連結
       (Windows 沒開開發人員模式就做不出來),餌 10、13 要裝得上 Ctrl-C 的訊號處理器
       (要在主執行緒)。做不到就整段跳過,**而且畫面上會講出來**——
       所以最後那一行的數字在有些機器上會小於 70,那不是壞掉。
       (2026-09-26 補完餌 70 之後模擬過這兩種機器:做不出符號連結時印 63、
        非主執行緒時印 68,底下各多一行說明跳過了哪幾個。)

    70 個反向餌:
      1. 目的檔是符號連結 → 要拒絕,而且連結指到的那個檔不可以被動到
      2. 固定暫存名被先佔(事先放一個 <目的檔>.part 連結指到資料夾外面)
         → 正常備份照樣要成功,而外面那個檔要原封不動
      3. 換上去那一步失敗(把 os.replace 換成會丟例外的)→ 正本原封不動,
         而且不可以留下暫存垃圾
      4. 半截的檔不可以被 _verify_same 判成「相同」(zip() 的陷阱)
      5. 0 bytes 的備份不可以通過還原前的檢查
      6. 檔頭宣稱的長度對不上的備份不可以通過
      7. 換名之後,登記必須已經是「已換」—— Ctrl-C 的收尾不可以說「沒動到」
      8. 指到不存在的地方的備份連結,不可以被 exists() 當成「沒有備份」而放過
      9. 寫出來的內容跟來源不同時,正本**不可以已經被換掉**(驗要在換之前)
     10. _NoInterrupt 區塊裡收到 Ctrl-C:區塊裡的每一行都要跑完,
         而且離開之後一定要把 KeyboardInterrupt 丟出來(不可以吞掉)
     11. append_entry 寫的是工作複本,正本一個位元組都不可以變
     12. 多個封裝檔換名到一半失敗 → 已經換上去的要被換回去,
         三個檔全部回到動手之前的樣子,而且不留暫存垃圾
     13. Ctrl-C 落在「換名做完了、登記還沒做完」那一瞬間 → 一樣要全部換回去
         (餌 12 抓不到這個:它丟的是 OSError,登記那一行照樣跑得到)
     14. 最後那一行報的餌數必須是**真的踩過的那些**,不可以是寫死的數字;
         被機器條件跳過的餌一定要出現在畫面上
     15. 動手途中的 OSError,訊息裡不可以留著工作複本那個臨時名字 ——
         讀者手上沒有那個檔
     16. Ctrl-C 落在「換名回來了、旗標還沒設起來」那一瞬間 → 收尾要去問磁碟
         (暫存檔還在不在),不可以問旗標而說出「還沒有動到任何檔案」
     17. 假裝開了 -O(把 _optimize_level 換成回傳 1)→ 自我測試必須拒跑、結束碼 2;
         換回原本那一支之後守門要照樣放行(陰性對照)。2026-09-24 補的
    18 到 46 是 2026-09-26 補的,每一個只對準一道守門。18 到 28、45、46 照讀者在
    命令列打的樣子跑 main(),驗畫面上那句中文、結束碼 2,以及遊戲檔有沒有被動到:
    停在動手之前的那些,整個假遊戲資料夾要一個位元組都沒變(沒有多出備份或暫存檔);
    26 只驗三個封裝檔沒變(那時候備份已經做了);27、28 是換上去之後才出事,
    驗的是照它教的 --restore 跑一次會回到原樣。其餘的直接呼叫那一支函式,驗那句話。
     18. 給的資料夾不是遊戲資料夾 → 要說「請確認你給的是遊戲資料夾」
     19. 球衣包資料夾的路徑不存在 → 要說「找不到資料夾」
     20. 球衣包裡一個 .fsh 都沒有(多半是還沒解壓縮)→ 不可以印「找到 0 個」就結束
     21. 球衣包裡沒有一個檔裝得進去 → 不可以一路印到「完成」
     22. 球衣包裡混了一個不是遊戲圖檔的 .fsh → 整批停下,**連備份都還沒做**
     23. 封裝檔開頭不是 BIGF(開頭被改掉,或只剩 8 個位元組)→ 不可以照樣裝進去
     24. 封裝檔目錄說它有 0 項 → 不可以把它當成空的而跳過,其他照裝
     25. 從來沒裝過(沒有任何備份)就 --restore → 不可以印「已還原 0 個」
     26. 換名之前那一輪複驗沒過 → 整批不換,並且告訴讀者不必 --restore
         (也不可以同時印出還原指令)
     27. 換上去之後那一輪複驗沒過 → 要印出那一整行還原指令,不可以印「完成」,
         也不可以說「不必 --restore」;照它教的 --restore 跑一次,
         三個封裝檔要回到動手之前(陰性對照)
     28. 做不出硬連結的磁碟(exFAT / FAT32)上換名到一半失敗 → 逐檔說「已改 / 沒改」、
         逐檔說明那一段與最後「封裝檔已經換過了」那一段都要給那一整行還原指令、
         結束碼 2,不可以變成一整片 traceback,也不可以說「不必 --restore」
         (27、28 在 2026-09-26 第三次補的時候收緊過:原本只驗畫面上有「--restore」
          這個字,而「不必 --restore」裡也有這個字)
     29. 備份途中少寫了 → 訊息要說出兩邊不一樣大,而不只是「內容不同」
     30. 寫出來的長度一樣、內容不一樣 → 不可以被當成相同而換上去
     31. 還原前檢查拿到不存在的備份 → 要說「找不到備份」(直接呼叫,--restore 碰不到)
     32. 封裝檔不到 8 個位元組 → 要說「太小」(直接呼叫,--install 會先被餌 23 那道擋下)
     33 到 44. 這一課不會呼叫的共用函式(給想自己改圖的人接手用的):
         QFS 長檔頭不完整、短檔頭不完整、宣稱的解壓大小超過上限、反向參照越界、
         解出來超過宣稱的大小;read_entry 讀不滿;不是 SHPI、SHPI 裡 0 張圖、
         圖片記錄指到檔案外面、沒見過的格式代號、圖片寬度 0;換像素長度不同。
         每一個都要停下來、而且說的是對的那句話。
     45. 0 bytes 的備份 → --restore 要說「備份是 0 bytes」,不可以只被後面那道地板接住
     46. 開頭被蓋掉(不是 BIGF)又只剩不到一半的備份 → --restore 不可以拿它蓋遊戲檔
    47 到 67 也是 2026-09-26 補的(第二次),補的是另一套更寬的拆法才數得到的那幾處
    (見「自我測試(--selftest)」那個分隔註解)。47 到 59 照命令列跑 main();60 到 67 直接呼叫。
     47. 封裝檔尾巴被截掉 → --install --apply 要停在「檔頭大小欄位跟實際檔案大小對不上」,
         而且訊息裡是 uniforms.big,不是工作複本的臨時名字
     48. 接上去之後目錄那一項的長度不對 → 換名前複驗第一層要說「目錄說 N,應該是 M」
     49. 接上去之後檔頭的總大小沒寫進去 → 換名前複驗第三層要擋下來,不可以印「完成」
     50. 兩次開頭檢查中間,球衣檔被換成 PNG → 寫入迴圈裡那第二道要擋下來
     51. 封裝檔讀不到(作業系統不讓讀)→ 要說「讀不到 <哪一個檔>」
     52. 動手途中按 Ctrl-C → 結束碼 130;換名之前要說「還沒有動到任何檔案」,
         換名之後要說「已經動過了」並給那一整行還原指令(照它教的還原一次要回到原樣)
     53. 工作複本複製得不對而且沒有報錯 → 不可以在它上面動手
     54. --restore 時一份備份好、一份壞 → 一份都不可以先還原
     55. 連裝兩套球衣 → 第一次動手之前的備份不可以被蓋掉(--restore 要回到兩套都沒裝)
     56 到 59. 遊戲資料夾裡有符號連結:--install 時封裝檔或備份那個名字是連結、
         --restore 時備份或封裝檔是連結 → 都要在動任何一個檔之前停下來
     60 到 67. 還原前檢查裡給語系檔(LOCH)與執行檔(MZ)用的 8 道:這一課的備份都是
         封裝檔,走 --restore 碰不到,所以直接呼叫,先做格式完整的陰性對照
    68 是 2026-09-26 第三次補的,照命令列跑 main():
     68. 沒加 --apply 的 --install → 只印預覽、結束碼 0,整個假遊戲資料夾一個位元組都不變
         (沒有備份、沒有暫存檔);同一行加上 --apply 要真的裝進去(陰性對照)。
         那道守門底下是 return 不是 raise,前兩套量法都數不到,而這之前自我測試裡
         每一次 --install 都帶著 --apply —— 補這個餌之前把它拆掉,自我測試照樣全綠。
    69、70 是 2026-09-26 第四次補的,照命令列跑 main(),驗的是叫讀者「不必 --restore」的那幾句:
     69. 接到工作複本時作業系統不讓寫(封裝檔唯讀最常見的樣子)→ 結束碼 2,畫面上要說
         「你的遊戲檔一個位元組都沒有動,不必 --restore」,不可以印還原指令或
         「封裝檔已經換過了」;三個封裝檔一個位元組都不變、不留工作複本
     70. 換上去換到一半被拒絕(第二個封裝檔被別的程式開著)、回頭路做得出來 → 逐檔說明
         兩行都說「沒改」並說不必還原,main() 最後那一段也照登記說不必還原,結束碼 2,
         不可以印還原指令;三個封裝檔都回到動手之前的樣子
         餌 15、12 走的是同一條路,但它們直接呼叫 cmd_install 而且把畫面吃掉,
         看不到讀者拿來決定要不要還原的那幾句 —— 補這兩個餌之前,把那幾句拿掉或改成
         叫人還原,自我測試照樣全綠。
    ⚠️ 第 18 到 46 個為什麼要補:2026-09-24 把守門逐一拆掉再跑自我測試,
       單拆一道就會紅的只有 1 道 —— 讀者最常撞到的那幾道拆掉了照樣全綠。
       而且只驗「有沒有停下來」不夠:拆掉一道,後面常常還有別道接住,
       只是說的話不對(例如餌 18,拆掉之後印的是英文的 No such file),
       所以每一個餌都驗那句話。
    ⚠️ 第 9 個是 2026-09-05 補的,補的理由值得寫下來:前 8 個餌都在的時候,
       我把「逐位元組比對」搬到 os.replace **後面**去,自我測試照樣全綠 ——
       一個測不到「驗在換之前」的測試,等於沒有在測這件事。
    ⚠️ 第 14 個是 2026-09-11 補的。舊版結尾印的是寫死的「13」,而餌 1、2、8
       在做不出符號連結的機器上會整段跳過 —— 實測那種機器只有 10 個餌真的
       踩過,畫面上還是印 13。課程頁面正叫讀者拿那個數字決定「要不要拿這支
       工具去動遊戲檔」,所以那是一句會影響讀者決定的假話。
    ⚠️ 第 7 個 2026-09-06 換了測法。它原本測的是「append_entry 之後旗標要變 True」,
       而 append_entry 現在寫的是工作複本、根本不該動那個旗標 —— 照原樣留著
       就是在測一件已經不成立的事。現在它測的是真正會動到遊戲檔的那一刻。
    其餘是正向檢查,沒有算進來。
    """
    # python -O 會把 assert 整個拿掉 —— 上面那些餌有一大半是靠 assert 站著的,
    # 在 -O 下會一路走到「全部通過」而其實什麼都沒驗。寧可不跑也不要假綠。
    if _optimize_level():
        print('--selftest 不能在 python -O 下跑:-O 會把 assert 全部拿掉,測試會假綠')
        return 2
    # 這一行要緊接在守門後面:_optimize_bait() 的陰性對照靠它收工(見那個函式)。
    _opt = _optimize_bait(selftest)
    _BAIT_LOG['ran'], _BAIT_LOG['skipped'] = [], []
    # ── 反向餌 17:最上面那道 -O 守門(開頭那一行 _optimize_bait() 已經量好了,這裡只記帳) ──
    assert _opt[0], '假裝開了 -O(把 _optimize_level 換成回傳 1),自我測試竟然沒有拒跑'
    assert _opt[1], '陰性對照:沒開 -O 守門也擋,或是換回原本那一支沒換成功'
    _bait_ran(17)
    d = tempfile.mkdtemp(prefix='mvp_install_uniform_selftest_')
    big = os.path.join(d, 'uniforms.big')
    body = _fake_big([('001.fsh', b'\x10\xfb' + b'A' * 30),
                      ('002.fsh', b'SHPI' + b'B' * 28)])
    with open(big, 'wb') as f:
        f.write(body)
    # 正向:自己造的檔要讀得出兩項,而且長度對得上(不然下面全部沒有意義)
    items = big_entries(big)
    assert [it[0] for it in items] == ['001.fsh', '002.fsh'], '自造的封裝檔讀不出來:%r' % (items,)
    assert size_field_order(big) == '<', '自造的封裝檔檔頭大小欄位不對'

    # ── 反向餌 11:append_entry 寫的是工作複本,正本一個位元組都不可以變 ──
    # 陰性對照在後面:同一個 append 真的要在複本上生效(不然「沒變」是因為
    # 什麼都沒做,而不是因為隔離有效)。
    assert _STATE['phase'] == 'idle', '什麼都還沒做,登記就已經不是 idle 了'
    live_before = open(big, 'rb').read()
    work = _stage_copy(big)
    new_off = append_entry(work, items[0][1], b'\x10\xfb' + b'C' * 60)
    assert open(big, 'rb').read() == live_before, \
        'append_entry 動到了正本 —— 它應該只碰工作複本'
    assert _STATE['phase'] == 'idle', \
        '只動了工作複本,登記卻說動過遊戲檔了(Ctrl-C 會叫人做不必要的還原)'
    # 正向(陰性對照):接上去的那一項在**工作複本**裡讀回來要一模一樣,
    # 而且原本的第二項不受影響。這一段證明上面那個「正本沒變」不是假象。
    got = {it[0]: it for it in big_entries(work)}
    assert got['001.fsh'][2] == new_off and got['001.fsh'][3] == 62, '目錄沒有指到新資料'
    with open(work, 'rb') as f:
        f.seek(got['001.fsh'][2]); assert f.read(62) == b'\x10\xfb' + b'C' * 60, '接進去的位元組不對'
        f.seek(got['002.fsh'][2]); assert f.read(32) == b'SHPI' + b'B' * 28, '別人的資料被動到了'
    _bait_ran(11)

    # ── 反向餌 7:換名之後,登記必須已經是「已換」──
    # 這一段模擬真正會動到遊戲檔的那一刻:os.replace 把工作複本換上去。
    _mark_replacing(big)
    with _NoInterrupt():
        os.replace(work, big)
        _mark_replaced(big)
    assert _STATE['phase'] == 'replaced', \
        '已經換上去了,登記卻還不是 replaced —— Ctrl-C 會謊稱「還沒有動到任何檔案」'
    assert big in _STATE['replaced'], '換過的檔沒有被記進清單'
    _STATE.update(phase='idle', target=None, replaced=[])   # 驗完放回去
    _bait_ran(7)

    # ── 反向餌 10:_NoInterrupt 區塊裡的 Ctrl-C 不可以插隊,也不可以被吞掉 ──
    # 在區塊裡對自己送一個 SIGINT:區塊裡後面那幾行還是要跑完(不可以被打斷),
    # 而離開區塊之後 KeyboardInterrupt 一定要被丟出來(吞掉的話使用者以為成功了)。
    # signal.signal 裝不上的環境(非主執行緒)就跳過,那時候本來就退回原本行為。
    try:
        signal.signal(signal.SIGINT, signal.default_int_handler)
        _can_signal = True
    except (ValueError, OSError):
        _can_signal = False
    if _can_signal:
        _ran_to_end = False
        try:
            with _NoInterrupt():
                os.kill(os.getpid(), signal.SIGINT)
                _ran_to_end = True         # 這一行被跳過就代表 Ctrl-C 插進來了
        except KeyboardInterrupt:
            pass
        else:
            raise AssertionError('_NoInterrupt 把 Ctrl-C 吞掉了 —— '
                                 '離開區塊之後一定要再丟出來')
        assert _ran_to_end, '_NoInterrupt 沒擋住 Ctrl-C,區塊裡的登記那一行被跳過了'
        _bait_ran(10)
    else:
        # 裝不上就整段跳過(這是刻意的),但**要講出來** —— 不講的話畫面上那個
        # 數字會把「沒跑到」算成「跑過了」,而頁面正叫讀者拿那個數字做決定。
        _bait_skipped(10, _WHY_NO_SIGNAL)
        _bait_skipped(13, _WHY_NO_SIGNAL)

    # ── 反向餌 4:半截的檔不可以被判成「相同」 ──
    whole, half = os.path.join(d, 'whole.bin'), os.path.join(d, 'half.bin')
    with open(whole, 'wb') as f:
        f.write(b'A' * 2000)
    with open(half, 'wb') as f:
        f.write(b'A' * 1000)
    _verify_same(whole, whole)             # 正向:同一個檔要過
    try:
        _verify_same(whole, half)
    except DataError:
        pass
    else:
        raise AssertionError('半截的檔竟然被判成跟完整的相同')
    _bait_ran(4)

    # ── 正向 + 陰性對照:正常備份真的會產生備份,而且不留暫存垃圾 ──
    # 先證明這條路是通的,不然下面「守門擋下來了」那些結果無法解釋
    # (2026-08-29 就是漏了這一步,一個全部失敗的備份看起來也像全綠)。
    bak = big + BACKUP_SUFFIX
    _atomic_copy(big, bak)
    assert os.path.getsize(bak) == os.path.getsize(big), '備份大小跟正本不一樣'
    assert not [n for n in os.listdir(d) if '.part-' in n], '備份完還留著暫存檔'

    # ── 反向餌 2:固定的暫存名被先佔 ──
    outside = os.path.join(d, 'outside.txt')
    with open(outside, 'wb') as f:
        f.write('別人的心血'.encode('utf-8'))
    big2 = os.path.join(d, 'models.big')
    with open(big2, 'wb') as f:
        f.write(body)
    trap = big2 + BACKUP_SUFFIX + '.part'          # 2026-09-05 之前就叫這個名字
    try:
        os.symlink(outside, trap)
    except (OSError, NotImplementedError, AttributeError):
        trap = None                                # Windows 沒開開發人員模式就做不出連結
    _atomic_copy(big2, big2 + BACKUP_SUFFIX)
    if trap:
        with open(outside, 'rb') as f:
            assert f.read() == '別人的心血'.encode('utf-8'), \
                '備份跟著 .part 連結把資料夾外面那個檔蓋掉了'
        _bait_ran(2)
    else:
        _bait_skipped(2, _WHY_NO_SYMLINK)

    # ── 反向餌 1:目的檔自己是符號連結 ──
    if trap:
        link = os.path.join(d, 'link_target.big')
        os.symlink(outside, link)
        try:
            _atomic_copy(big, link)
        except DataError:
            pass
        else:
            raise AssertionError('目的檔是符號連結,竟然照樣寫下去了')
        with open(outside, 'rb') as f:
            assert f.read() == '別人的心血'.encode('utf-8'), '守門擋了卻還是動到連結指到的檔'
        _bait_ran(1)
        # ── 反向餌 8:指到不存在的地方的連結,exists() 看不見 ──
        dangling = os.path.join(d, 'dangling' + BACKUP_SUFFIX)
        os.symlink(os.path.join(d, '這個檔不存在'), dangling)
        assert os.path.exists(dangling) is False, 'exists() 竟然看得見斷掉的連結'
        assert os.path.lexists(dangling) is True, 'lexists() 應該看得見連結本身'
        try:
            _refuse_symlink(dangling, '備份檔')
        except DataError:
            pass
        else:
            raise AssertionError('斷掉的備份連結竟然過關了')
        _bait_ran(8)
    else:
        _bait_skipped(1, _WHY_NO_SYMLINK)
        _bait_skipped(8, _WHY_NO_SYMLINK)

    # ── 反向餌 3:換上去那一步失敗,正本要原封不動 ──
    victim = os.path.join(d, 'victim.big')
    with open(victim, 'wb') as f:
        f.write(b'ORIGINAL' * 100)
    before = open(victim, 'rb').read()
    real_replace = os.replace

    def _boom(a, b):
        raise OSError(28, '磁碟沒有空間了(這是 --selftest 故意製造的)')

    os.replace = _boom
    try:
        _atomic_copy(big, victim, marks_mutation=True)
    except OSError:
        pass
    else:
        raise AssertionError('換檔那一步失敗了,竟然沒有往上報')
    finally:
        os.replace = real_replace
    assert open(victim, 'rb').read() == before, '還原失敗了,正本卻已經被動過'
    assert not [n for n in os.listdir(d) if '.part-' in n], '失敗之後留下了暫存檔'
    _bait_ran(3)
    # 換名確定沒有發生,登記就要收回「還沒動」。停在「正在換」的話,
    # 收尾會叫使用者去做一次不必要的還原。
    assert _STATE['phase'] == 'idle', \
        '換名確定沒有發生,登記卻沒有收回來'

    # ── 反向餌 9:寫出來的內容不對時,正本不可以已經被換掉 ──
    # 模擬「沒有報錯的短寫」(磁碟寫到一半、網路磁碟斷線,都可能少寫而不丟例外)。
    victim2 = os.path.join(d, 'victim2.big')
    with open(victim2, 'wb') as f:
        f.write(b'KEEPME' * 100)
    before2 = open(victim2, 'rb').read()
    real_copy = shutil.copyfileobj

    def _short_write(fin, fout, length=0):
        fout.write(fin.read()[:-1])        # 少寫一個位元組,而且不丟例外

    shutil.copyfileobj = _short_write
    try:
        _atomic_copy(big, victim2, marks_mutation=True)
    except DataError:
        pass
    else:
        raise AssertionError('寫出來的東西跟來源不一樣,竟然沒被擋下來')
    finally:
        shutil.copyfileobj = real_copy
    assert open(victim2, 'rb').read() == before2, \
        '內容驗不過,正本卻已經被換掉了 —— 逐位元組比對必須在 os.replace 之前'
    assert not [n for n in os.listdir(d) if '.part-' in n], '驗不過之後留下了暫存檔'
    _bait_ran(9)
    # 換名確定沒有發生,登記就要收回「還沒動」。停在「正在換」的話,
    # 收尾會叫使用者去做一次不必要的還原。
    assert _STATE['phase'] == 'idle', \
        '換名確定沒有發生,登記卻沒有收回來'

    # ── 反向餌 16:Ctrl-C 落在「換名回來了、旗標還沒設起來」那一瞬間 ──
    # 這是 2026-09-06 修掉的那個縫搬到下一行的樣子。_NoInterrupt 擋得住 SIGINT,
    # 但它裝不上的機器(非主執行緒)沒有擋 —— 那時候收尾如果只看 swapped 這個
    # 旗標,會判「沒換成」而對讀者說「已中斷。還沒有動到任何檔案。」,
    # 而檔案已經換掉了。收尾要去問磁碟(暫存檔還在不在),不是問旗標。
    # 下餌的方式:一個「換完名就丟 KeyboardInterrupt」的 os.replace ——
    # 直接丟出來的例外 _NoInterrupt 本來就攔不住,那正是那個縫的樣子。
    gap_src = os.path.join(d, 'gap_new.big')
    gap_live = os.path.join(d, 'gap_live.big')
    with open(gap_src, 'wb') as f:
        f.write(b'NEW' * 100)
    with open(gap_live, 'wb') as f:
        f.write(b'OLD' * 100)
    real_replace4 = os.replace

    def _gap(a, b):
        r = real_replace4(a, b)            # 換名真的做完了
        raise KeyboardInterrupt            # …登記那一行還沒跑到

    os.replace = _gap
    try:
        _atomic_copy(gap_src, gap_live, marks_mutation=True)
    except KeyboardInterrupt:
        pass
    else:
        raise AssertionError('Ctrl-C 落在換名回來那一瞬間,竟然一路跑完了')
    finally:
        os.replace = real_replace4
    # 陰性對照:先確認換名**真的**做完了。不做這一步的話,下面「登記說已換」
    # 有可能只是因為根本沒換而剛好對(2026-08-29 那一輪的教訓)。
    assert open(gap_live, 'rb').read() == b'NEW' * 100, \
        '餌根本沒被踩到 —— 換名沒有做完,這一輪什麼都沒測到'
    assert _STATE['phase'] == 'replaced', \
        '檔案已經換掉了,登記卻說沒動到 —— 收尾會叫讀者放心,而他的遊戲檔已經變了'
    assert not [n for n in os.listdir(d) if '.part-' in n], '這一段留下了暫存檔'
    _bait_ran(16)
    _STATE.update(phase='idle', target=None, replaced=[])

    # ── 反向餌 5、6:壞掉的備份不可以拿來蓋正本 ──
    zero = os.path.join(d, 'zero' + BACKUP_SUFFIX)
    open(zero, 'wb').close()
    try:
        _restore_from_backup(zero, big, verify_only=True)
    except DataError:
        pass
    else:
        raise AssertionError('0 bytes 的備份竟然通過了')
    _bait_ran(5)
    trunc = os.path.join(d, 'trunc' + BACKUP_SUFFIX)
    with open(trunc, 'wb') as f:
        f.write(body[:len(body) // 2])     # 檔頭還說著原本的長度
    try:
        _restore_from_backup(trunc, big, verify_only=True)
    except DataError:
        pass
    else:
        raise AssertionError('被截斷的備份竟然通過了')
    _bait_ran(6)
    # 正向:完整的備份要通過,而且 verify_only 不可以動到正本
    live_now = open(big, 'rb').read()
    _restore_from_backup(bak, big, verify_only=True)
    assert open(big, 'rb').read() == live_now, 'verify_only 竟然動到了正本'

    # ── 反向餌 12:多個封裝檔換名到一半失敗,已經換上去的要被換回去 ──
    # 這是整支腳本最貴的一條路,所以在這裡跑一次完整的 --install --apply:
    # 造一個假的遊戲資料夾(三個封裝檔)+ 一個假的球衣包(兩件,分屬兩個封裝檔),
    # 讓**第二次** os.replace 失敗,然後要求三個封裝檔全部回到動手之前的樣子。
    g = os.path.join(d, 'fakegame')
    os.makedirs(os.path.join(g, 'data', 'frontend'))
    slots = {'models': os.path.join(g, 'data', 'models.big'),
             'uniforms': os.path.join(g, 'data', 'frontend', 'uniforms.big'),
             'logos': os.path.join(g, 'data', 'frontend', 'logos.big')}
    with open(slots['models'], 'wb') as f:
        f.write(_fake_big([('u001.fsh', b'\x10\xfb' + b'M' * 30)]))
    with open(slots['uniforms'], 'wb') as f:
        f.write(_fake_big([('001.fsh', b'\x10\xfb' + b'U' * 30)]))
    with open(slots['logos'], 'wb') as f:
        f.write(_fake_big([('l001.fsh', b'\x10\xfb' + b'L' * 30)]))
    before_all = {k: open(v, 'rb').read() for k, v in slots.items()}
    mod = os.path.join(d, 'fakepack')
    os.makedirs(mod)
    for nm, ch in (('001.fsh', b'X'), ('l001.fsh', b'Y')):
        with open(os.path.join(mod, nm), 'wb') as f:
            f.write(b'\x10\xfb' + ch * 90)

    # 陰性對照:先證明「沒有餌的時候這條路是綠的」。不先做這一步,
    # 下面「三個檔都沒變」有可能只是因為它本來就整支失敗(2026-08-29 的教訓)。
    with _Mute():
        cmd_install(g, mod, True)
    after_ok = {k: open(v, 'rb').read() for k, v in slots.items()}
    assert after_ok['uniforms'] != before_all['uniforms'], '正常安裝沒有動到 uniforms.big'
    assert after_ok['logos'] != before_all['logos'], '正常安裝沒有動到 logos.big'
    assert after_ok['models'] == before_all['models'], \
        '球衣包裡沒有 u###/f###,models.big 不該被碰'
    assert not [n for n in os.listdir(os.path.join(g, 'data', 'frontend'))
                if '.part-' in n], '正常安裝留下了暫存檔'
    _STATE.update(phase='idle', target=None, replaced=[])
    # 還原回動手之前,好讓下面那次帶餌的執行從同一個起點出發
    with _Mute():
        cmd_restore(g)
    for k, v in slots.items():
        assert open(v, 'rb').read() == before_all[k], '還原之後 %s 跟動手之前不一樣' % k
        if os.path.exists(v + BACKUP_SUFFIX):
            os.remove(v + BACKUP_SUFFIX)    # 讓帶餌那次從「還沒備份過」開始
    _STATE.update(phase='idle', target=None, replaced=[])

    # 下餌:換第二個封裝檔的時候丟 OSError(第一個已經換上去了)。
    # ⚠️ 只對「換到正本身上」那幾次動手腳:備份自己也走 os.replace,
    #    不分清楚的話餌會在備份階段就爆掉,測到的根本不是換名中途失敗。
    # ⚠️ 踩到一次之後就放行,不然回頭路自己那幾次 os.replace 也會被擋 ——
    #    那樣測到的是「回頭路壞了」,不是「回頭路有沒有用」。
    real_replace2 = os.replace
    live_paths = set(slots.values())
    trip = {'hits': 0, 'done': False}

    def _boom_second(a, b):
        if not trip['done'] and os.fspath(b) in live_paths:
            trip['hits'] += 1
            if trip['hits'] >= 2:
                trip['done'] = True
                raise OSError(28, '磁碟沒有空間了(這是 --selftest 故意製造的)')
        return real_replace2(a, b)

    os.replace = _boom_second
    try:
        with _Mute():
            cmd_install(g, mod, True)
    except OSError:
        pass
    else:
        raise AssertionError('換名中途失敗了,竟然沒有往上報')
    finally:
        os.replace = real_replace2
    assert trip['done'], '餌根本沒被踩到 —— 這一輪什麼都沒測到'
    for k, v in slots.items():
        assert open(v, 'rb').read() == before_all[k], \
            '換名中途失敗,%s 卻沒有被換回動手之前的樣子(全有或全無沒做到)' % k
    assert _STATE['phase'] == 'idle', \
        '全部換回來了,登記卻還說動過遊戲檔(會叫使用者做不必要的還原)'
    for sub in (os.path.join(g, 'data'), os.path.join(g, 'data', 'frontend')):
        assert not [n for n in os.listdir(sub) if '.part-' in n], \
            '換名失敗之後留下了暫存檔或回頭路:%s' % sub
    _bait_ran(12)
    _STATE.update(phase='idle', target=None, replaced=[])

    # ── 反向餌 13:Ctrl-C 落在「換名已經做完、登記還沒做完」那一瞬間 ──
    # 這是 2026-09-06 這一輪唯一一個**真的抓到活錯誤**的餌,所以留在這裡:
    # 給回滾看的那份登記(swapped)原本寫在 _NoInterrupt 區塊**外面**,
    # Ctrl-C 落在中間時 logos.big 已經換掉了而登記還是空的 —— 回滾什麼都沒做,
    # 螢幕上卻印「遊戲檔一個位元組都沒有動」。實測那一版:訊息說沒改,
    # 而磁碟上 logos.big 的 sha256 變了。
    # ⚠️ 餌 12 抓不到這個(它是丟 OSError,登記那一行照樣跑得到)。
    #    一個守門要配一個真的踩得到它的餌,不能靠別的餌順便。
    if _can_signal:
        for k, v in slots.items():
            if os.path.exists(v + BACKUP_SUFFIX):
                os.remove(v + BACKUP_SUFFIX)
        real_replace3 = os.replace
        trip2 = {'done': False}

        def _sigint_inside_with(a, b):
            # 先真的換過去,再對自己送 Ctrl-C —— 此時人還在 _NoInterrupt 區塊裡,
            # 所以區塊裡剩下的登記那幾行**一定要跑完**,離開才丟 KeyboardInterrupt。
            r = real_replace3(a, b)
            if not trip2['done'] and os.fspath(b) in live_paths:
                trip2['done'] = True
                os.kill(os.getpid(), signal.SIGINT)
            return r

        os.replace = _sigint_inside_with
        try:
            with _Mute():
                cmd_install(g, mod, True)
        except KeyboardInterrupt:
            pass
        else:
            raise AssertionError('Ctrl-C 落在換名中間,竟然一路跑完了')
        finally:
            os.replace = real_replace3
        assert trip2['done'], '餌根本沒被踩到 —— 這一輪什麼都沒測到'
        for k, v in slots.items():
            assert open(v, 'rb').read() == before_all[k], \
                'Ctrl-C 落在換名中間,%s 卻沒有被換回去 —— ' \
                '給回滾看的登記一定要在 _NoInterrupt 區塊裡面' % k
        assert _STATE['phase'] == 'idle', \
            '全部換回來了,登記卻還說動過遊戲檔'
        _bait_ran(13)
        _STATE.update(phase='idle', target=None, replaced=[])

    # ── 反向餌 15:OSError 的訊息裡不可以留著工作複本那個臨時名字 ──
    # 為什麼要有它:封裝檔被設成唯讀時,工作複本會照抄那個唯讀權限,
    # 接下來 append_entry 用 r+b 開它就是 Permission denied,而作業系統回報的
    # 檔名是 .logos.big.part-cqb_mbz_ 這種每次都不一樣的臨時名字。
    # 讀者手上沒有那個檔,那句話對他毫無意義 —— 而課程頁面「作業系統不讓我
    # 讀寫這個檔」那一列教的正是這種情形。(本站實測 chmod 444 重現過。)
    # 下餌的方式:讓 append_entry 丟一個帶著工作複本路徑的 OSError,
    # 往上傳到 cmd_install 外面時,那個臨時名字一定要已經被換成封裝檔名。
    for _k, _v in slots.items():
        if os.path.exists(_v + BACKUP_SUFFIX):
            os.remove(_v + BACKUP_SUFFIX)
    _real_append = append_entry
    _leak = {}

    def _append_boom(path, field_pos, blob):
        _leak['tmp'] = os.path.basename(path)
        _e = OSError(13, 'Permission denied')
        _e.filename = path
        raise _e

    globals()['append_entry'] = _append_boom
    try:
        with _Mute():
            cmd_install(g, mod, True)
    except OSError as _oe:
        _said = str(_oe)
    else:
        raise AssertionError('append_entry 丟了 OSError,竟然沒有往上報')
    finally:
        globals()['append_entry'] = _real_append
    assert _leak.get('tmp'), '餌根本沒被踩到 —— 這一輪什麼都沒測到'
    assert '.part-' in _leak['tmp'], '工作複本竟然不是臨時名字'
    assert _leak['tmp'] not in _said, \
        '訊息裡留著工作複本那個臨時名字(%s)—— 讀者手上根本沒有那個檔' % _leak['tmp']
    assert 'uniforms.big' in _said or 'logos.big' in _said, \
        '換完名之後訊息裡連封裝檔名都不見了,讀者不知道是哪一個檔出事'
    for _k, _v in slots.items():
        assert open(_v, 'rb').read() == before_all[_k], \
            'append 那一步失敗,%s 卻被動到了(它應該只動工作複本)' % _k
    for _sub in (os.path.join(g, 'data'), os.path.join(g, 'data', 'frontend')):
        assert not [n for n in os.listdir(_sub) if '.part-' in n], \
            'append 失敗之後留下了工作複本:%s' % _sub
    _bait_ran(15)
    _STATE.update(phase='idle', target=None, replaced=[])

    # ═══ 反向餌 18 到 46(2026-09-26 補;45、46 寫在餌 31 後面)═══════════
    # 2026-09-24 把自我測試以外、下一行是 raise 的 if 逐一改成永遠不成立再跑
    # --selftest,單拆一道就會紅的只有 1 道。讀者最常撞到的那些 —— 路徑給錯、
    # 球衣包還沒解壓、封裝檔壞了、沒有備份就按 --restore —— 拆掉了照樣全綠。
    # 下面每一個餌只對準一道守門。一定驗那句中文(不是只驗「有停下來」:
    # 拆掉一道,後面常常還有別道接住,只是說的話不對);照命令列跑的那幾個
    # 另外驗結束碼 2 與遊戲檔有沒有被動到(各餌上面寫著驗到什麼程度)。
    # 一律用自己造的假檔,不需要遊戲。
    _q = b'\x10\xfb'                         # 球衣檔開頭(QFS 壓縮過的那一種)
    _pack_ok = [('001.fsh', _q + b'X' * 90), ('l001.fsh', _q + b'Y' * 90)]

    def _must_stop(what, must_say, fn, *args):
        # 呼叫 fn(*args),它一定要丟 DataError,而且那句話裡要有 must_say。
        # 丟別種例外(IndexError、struct.error…)就讓它直接往上冒,自我測試會紅 ——
        # 那在讀者那裡就是一整片 traceback。
        try:
            fn(*args)
        except DataError as e:
            said = str(e)
        else:
            raise AssertionError('%s:竟然沒有停下來' % what)
        assert must_say in said, '%s:停是停了,但說的不是「%s」,而是:%s' % (what, must_say, said)

    def _must_exit2(what, must_say, argv):
        # 照讀者打的指令跑一次 main():結束碼一定要是 2,畫面上一定要有 must_say。
        rc, out = _selftest_run_main(argv)
        assert rc == 2, '%s:結束碼應該是 2,實際是 %r。畫面上印的是:\n%s' % (what, rc, out)
        assert must_say in out, '%s:畫面上沒有「%s」。印的是:\n%s' % (what, must_say, out)
        return out

    def _restore_cmd(g):
        # 畫面上教讀者還原的那一整行(開頭的 python3 不算在內)。2026-09-26 加:
        # 餌 27、28 原本只驗畫面上有沒有「--restore」這個字,而相反的指示
        # 「不必 --restore」裡也有這個字 —— 把還原指令換成「不必 --restore」,
        # 那兩個餌照樣過。改成驗那一整行,另外驗畫面上沒有叫人不必還原。
        return 'mvp_install_uniform.py "%s" --restore' % g

    # ── 反向餌 18:給的資料夾不是遊戲資料夾 ──
    # 讀者最常犯的第一個錯。拆掉這道,後面讀封裝檔那一關會接住,
    # 但印的是「讀不到 …/data/models.big:[Errno 2] No such file or directory」
    # (2026-09-26 拆掉實測)—— 沒有告訴他「你給錯資料夾了」。
    _notgame = os.path.join(d, 'b18_notgame')
    os.makedirs(_notgame)
    _pk = _selftest_pack(d, 'b18_pack', _pack_ok)
    _must_exit2('餌 18 不是遊戲資料夾', '請確認你給的是遊戲資料夾',
                [_notgame, '--install', _pk, '--apply'])
    assert _selftest_snap(_notgame) == {}, '餌 18:給錯資料夾,卻在那個資料夾裡留下了東西'
    _bait_ran(18)

    # ── 反向餌 19:球衣包資料夾的路徑給錯(不存在)──
    _g, _slots = _selftest_game(d, 'b19_game')
    _before = _selftest_snap(_g)
    _must_exit2('餌 19 球衣包路徑不存在', '找不到資料夾',
                [_g, '--scan', os.path.join(d, 'b19_沒有這個資料夾')])
    assert _selftest_snap(_g) == _before, '餌 19:遊戲資料夾被動到了'
    _bait_ran(19)

    # ── 反向餌 20:球衣包還沒解壓縮(資料夾裡一個 .fsh 都沒有)──
    # 拆掉這道,--scan 會印「找到 0 個 .fsh」然後結束碼 0,讀者以為沒事。
    _pk = _selftest_pack(d, 'b20_pack', [('readme.txt', b'read me'), ('jersey.png', b'\x89PNG')])
    _must_exit2('餌 20 沒有 .fsh', '一個 .fsh 都沒有', [_g, '--scan', _pk])
    assert _selftest_snap(_g) == _before, '餌 20:遊戲資料夾被動到了'
    _bait_ran(20)

    # ── 反向餌 21:球衣包裡沒有一個檔裝得進去 ──
    # 拆掉這道,--install --apply 會一路走到「複驗:0 個檔全部逐位元組相符」
    # 「完成。進遊戲看看那支球隊。」、結束碼 0 —— 什麼都沒裝卻說完成了。
    _pk = _selftest_pack(d, 'b21_pack', [('999.fsh', _q + b'Z' * 90), ('l999.fsh', _q + b'Z' * 90),
                                         ('shirt.fsh', _q + b'Z' * 90)])
    _out = _must_exit2('餌 21 一個都裝不進去', '沒有一個檔裝得進去',
                       [_g, '--install', _pk, '--apply'])
    assert '進遊戲看看' not in _out, '餌 21:什麼都沒裝,卻印了「完成」'
    assert _selftest_snap(_g) == _before, '餌 21:一個都裝不進去,遊戲資料夾卻被動到了(或多了備份檔)'
    _bait_ran(21)

    # ── 反向餌 22:球衣包裡混了一個不是遊戲圖檔的 .fsh ──
    # 拆掉這道,後面寫入迴圈裡的第二道還是會擋下來,遊戲檔也還是沒動 ——
    # 但那時候已經先做了備份,資料夾裡多出兩份 .unibak;訊息也變成「改動都還在工作複本上」。
    # 這一道的承諾是「有一個不是就整批停下來,那時候一個位元組都還沒寫」。
    _pk = _selftest_pack(d, 'b22_pack', [('001.fsh', _q + b'X' * 90),
                                         ('l001.fsh', b'\x89PNG\r\n\x1a\n' + b'Y' * 90)])
    _out = _must_exit2('餌 22 混了一個不是圖檔的', '還沒有動到任何檔案',
                       [_g, '--install', _pk, '--apply'])
    # ⚠️ 2026-09-26 訂正:這一行原本只驗 'l001.fsh' 有沒有出現在畫面上 —— 而停下來之前
    #    預覽那一段已經印過「l001.fsh → logos.big」,所以錯誤訊息就算不提檔名它也照樣過
    #    (拿掉訊息裡的檔名實測,自我測試照樣全綠)。改成只有那句錯誤訊息才會有的字串。
    assert 'l001.fsh 的開頭既不是' in _out, '餌 22:停下來的那句話沒說出是哪一個檔不對'
    assert _selftest_snap(_g) == _before, \
        '餌 22:來源檔有一個不像圖檔,卻已經寫了東西(多半是先做了備份)'
    _bait_ran(22)

    # ── 反向餌 23:封裝檔的開頭不是 BIGF(被別的工具存壞,或只剩半截)──
    # 拆掉這道,開頭改過的檔照樣被當成封裝檔讀,球衣會被接進一個不是封裝檔的檔裡。
    _pk = _selftest_pack(d, 'b23_pack', _pack_ok)
    for _i, (_tag, _mangle) in enumerate((('開頭被改成 BIG4', lambda b: b'BIG4' + b[4:]),
                                          ('只剩 8 個位元組', lambda b: b[:8]))):
        _g, _slots = _selftest_game(d, 'b23_game_%d' % _i)
        with open(_slots['uniforms'], 'rb') as f:
            _raw = f.read()
        with open(_slots['uniforms'], 'wb') as f:
            f.write(_mangle(_raw))
        _before = _selftest_snap(_g)
        _must_exit2('餌 23 %s' % _tag, '開頭不是 BIGF', [_g, '--install', _pk, '--apply'])
        assert _selftest_snap(_g) == _before, '餌 23 %s:遊戲資料夾被動到了' % _tag
    _bait_ran(23)

    # ── 反向餌 24:封裝檔目錄說它有 0 項 ──
    # 拆掉這道,那個封裝檔會被讀成「空的」,球衣包裡要進它的檔全部變成
    # 「沒有同名項目」而被跳過,其他封裝檔照樣裝 —— 結束碼 0,讀者不會知道檔壞了。
    _g, _slots = _selftest_game(d, 'b24_game')
    _pk = _selftest_pack(d, 'b24_pack', _pack_ok)
    with open(_slots['uniforms'], 'r+b') as f:
        f.seek(8)
        f.write(b'\x00\x00\x00\x00')
    _before = _selftest_snap(_g)
    _must_exit2('餌 24 目錄 0 項', '目錄項目數異常', [_g, '--install', _pk, '--apply'])
    assert _selftest_snap(_g) == _before, '餌 24:遊戲資料夾被動到了'
    _bait_ran(24)

    # ── 反向餌 25:從來沒裝過(沒有任何備份)就按 --restore ──
    # 拆掉這道,畫面上會印「已還原 0 個封裝檔」、結束碼 0 —— 讀者以為救回來了。
    _g, _slots = _selftest_game(d, 'b25_game')
    _before = _selftest_snap(_g)
    _out = _must_exit2('餌 25 沒有備份', '都找不到備份', [_g, '--restore'])
    assert '已還原' not in _out, '餌 25:一份備份都沒有,卻印了「已還原」'
    assert _selftest_snap(_g) == _before, '餌 25:遊戲資料夾被動到了'
    _bait_ran(25)

    # 下面三個餌要真的走到「寫」那一步,所以各自用一份新的假遊戲資料夾。
    def _archives(slots):
        got = {}
        for k, v in slots.items():
            with open(v, 'rb') as f:
                got[k] = f.read()
        return got

    def _no_parts(g):
        return not [n for n in _selftest_snap(g) if '.part-' in n]

    # ── 反向餌 26:換名之前那一輪複驗沒過 → 整批不換 ──
    # 下餌:讓 append_entry 接上去之後,把工作複本最後一個位元組翻掉
    # (模擬「寫進去了、但寫的不對、而且沒有報錯」)。
    # 拆掉這道,壞掉的工作複本會照樣被換上去,換上去之後那一輪才抓到 ——
    # 那時候遊戲檔已經變了,讀者得自己 --restore。
    _g, _slots = _selftest_game(d, 'b26_game')
    _pk = _selftest_pack(d, 'b26_pack', _pack_ok)
    _arch0 = _archives(_slots)
    _real_append26 = append_entry
    _hit26 = {'n': 0}

    def _append_then_rot(path, field_pos, blob):
        r = _real_append26(path, field_pos, blob)
        with open(path, 'r+b') as f:
            f.seek(-1, os.SEEK_END)
            last = f.read(1)
            f.seek(-1, os.SEEK_END)
            f.write(bytes([last[0] ^ 0xFF]))
        _hit26['n'] += 1
        return r

    globals()['append_entry'] = _append_then_rot
    try:
        _out = _must_exit2('餌 26 換名前複驗沒過', '工作複本複驗', [_g, '--install', _pk, '--apply'])
    finally:
        globals()['append_entry'] = _real_append26
    assert _hit26['n'] >= 1, '餌 26 根本沒被踩到 —— 這一輪什麼都沒測到'
    assert '不必 --restore' in _out, '餌 26:遊戲檔沒動,卻沒有告訴讀者不必還原'
    # 反過來也要成立:遊戲檔沒動,就不可以同時印出還原指令(2026-09-26 加)。
    # 照著跑的話,他先前裝好的別套球衣會被一起退掉。
    assert _restore_cmd(_g) not in _out, '餌 26:遊戲檔沒動,畫面上卻印了還原指令'
    assert _archives(_slots) == _arch0, '餌 26:換名前就驗出壞了,遊戲檔卻已經被換掉'
    assert _no_parts(_g), '餌 26:留下了工作複本'
    assert _STATE['phase'] == 'idle', '餌 26:什麼都沒換,登記卻說動過遊戲檔'
    _bait_ran(26)

    # ── 反向餌 27:換上去之後那一輪複驗沒過 → 一定要叫讀者 --restore,不可以說「完成」──
    # 下餌:os.replace 換到遊戲檔身上之後,把那個遊戲檔最後一個位元組翻掉
    # (模擬「換上去之後才壞掉」)。拆掉這道,畫面上會印「複驗:… 全部逐位元組相符」
    # 「完成」、結束碼 0,而遊戲檔裡的球衣是壞的。
    # 陰性對照在後面:照畫面上教的 --restore 跑一次,三個封裝檔要全部回到動手之前。
    _g, _slots = _selftest_game(d, 'b27_game')
    _pk = _selftest_pack(d, 'b27_pack', _pack_ok)
    _arch0 = _archives(_slots)
    _live27 = set(_slots.values())
    _real_replace27 = os.replace
    _hit27 = {'n': 0}

    def _replace_then_rot(a, b):
        r = _real_replace27(a, b)
        if os.fspath(b) in _live27:
            with open(b, 'r+b') as f:
                f.seek(-1, os.SEEK_END)
                last = f.read(1)
                f.seek(-1, os.SEEK_END)
                f.write(bytes([last[0] ^ 0xFF]))
            _hit27['n'] += 1
        return r

    os.replace = _replace_then_rot
    try:
        # 驗的是還原指令那一整行,不是「--restore」這個字(見 _restore_cmd)
        _out = _must_exit2('餌 27 換名後複驗沒過', _restore_cmd(_g), [_g, '--install', _pk, '--apply'])
    finally:
        os.replace = _real_replace27
    assert _hit27['n'] >= 1, '餌 27 根本沒被踩到 —— 這一輪什麼都沒測到'
    assert '複驗有' in _out and '進遊戲看看' not in _out, \
        '餌 27:換上去的遊戲檔跟來源不一樣,畫面上卻沒有說複驗沒過(或說了完成)'
    assert '不必 --restore' not in _out and '一個位元組都沒有動' not in _out, \
        '餌 27:遊戲檔已經換上去了,畫面上卻說沒動到、不必還原:\n%s' % _out
    _STATE.update(phase='idle', target=None, replaced=[])
    _rc, _out = _selftest_run_main([_g, '--restore'])
    assert _rc == 0, '餌 27 陰性對照:照畫面上教的 --restore 跑,結束碼是 %r:\n%s' % (_rc, _out)
    assert _archives(_slots) == _arch0, '餌 27 陰性對照:--restore 之後沒有回到動手之前的樣子'
    _STATE.update(phase='idle', target=None, replaced=[])
    _bait_ran(27)

    # ── 反向餌 28:做不出硬連結的磁碟(exFAT / FAT32 隨身碟)上,換名到一半失敗 ──
    # 下餌:os.link 一律失敗(那種磁碟就是這樣),再讓第二次換到遊戲檔身上的
    # os.replace 失敗。那時候第一個封裝檔已經換上去了,而沒有回頭路。
    # 腳本要誠實逐檔說「哪個已改、哪個沒改」並給還原指令,結束碼 2。
    # 拆掉這道,回頭路那一段會拿 None 去換名,丟出 TypeError —— 真正的原因被蓋掉,
    # 讀者看到一整片 traceback,也不知道哪個檔已經改了。
    _g, _slots = _selftest_game(d, 'b28_game')
    _pk = _selftest_pack(d, 'b28_pack', _pack_ok)
    _arch0 = _archives(_slots)
    _live28 = set(_slots.values())
    _real_replace28, _real_link28 = os.replace, getattr(os, 'link', None)
    _trip28 = {'hits': 0, 'done': False, 'links': 0}

    def _no_link(a, b):
        _trip28['links'] += 1
        raise OSError(1, '這個磁碟做不出硬連結(這是 --selftest 故意製造的)')

    def _boom_second28(a, b):
        if not _trip28['done'] and os.fspath(b) in _live28:
            _trip28['hits'] += 1
            if _trip28['hits'] >= 2:
                _trip28['done'] = True
                raise OSError(28, '磁碟沒有空間了(這是 --selftest 故意製造的)')
        return _real_replace28(a, b)

    os.link, os.replace = _no_link, _boom_second28
    try:
        _out = _must_exit2('餌 28 沒有回頭路', _restore_cmd(_g), [_g, '--install', _pk, '--apply'])
    finally:
        os.replace = _real_replace28
        if _real_link28 is None:
            del os.link
        else:
            os.link = _real_link28
    assert _trip28['done'] and _trip28['links'] >= 1, '餌 28 根本沒被踩到 —— 這一輪什麼都沒測到'
    _lines28 = _out.splitlines()
    assert [ln for ln in _lines28 if 'logos.big' in ln and '已改' in ln], \
        '餌 28:logos.big 已經換上去了,畫面上卻沒有說「已改」:\n%s' % _out
    assert [ln for ln in _lines28 if 'uniforms.big' in ln and '沒改' in ln], \
        '餌 28:uniforms.big 沒換成,畫面上卻沒有說「沒改」:\n%s' % _out
    # 畫面上有兩段話各自要給還原指令(2026-09-26 加):逐檔說明那一段,
    # 以及 main() 接住 OSError 之後照登記說的那一段(從「停下來了:作業系統…」開始)。
    # 只驗整個畫面上有沒有那一行,其中一段改成「不必 --restore」或整行拿掉都驗不出來。
    # (分段要用後面那半句:逐檔說明的標題「換名中途停下來了」裡也有「停下來了」四個字。)
    _pre28, _sep28, _post28 = _out.partition('停下來了:作業系統不讓我讀寫這個檔')
    assert _sep28, '餌 28:畫面上沒有「停下來了:作業系統不讓我讀寫這個檔」那一段:\n%s' % _out
    assert _restore_cmd(_g) in _pre28, '餌 28:逐檔說明那一段沒有給還原指令:\n%s' % _out
    assert '封裝檔已經換過了' in _post28 and _restore_cmd(_g) in _post28, \
        '餌 28:最後那一段沒有照登記說「封裝檔已經換過了」並給還原指令:\n%s' % _out
    assert '不必 --restore' not in _out and '一個位元組都沒有動' not in _out, \
        '餌 28:logos.big 已經換上去了,畫面上卻說沒動到、不必還原:\n%s' % _out
    _now28 = _archives(_slots)
    assert _now28['logos'] != _arch0['logos'], '餌 28:logos.big 應該已經換上去了(不然這一輪沒測到東西)'
    assert _now28['uniforms'] == _arch0['uniforms'] and _now28['models'] == _arch0['models'], \
        '餌 28:沒換成的封裝檔被動到了'
    assert _no_parts(_g), '餌 28:留下了工作複本'
    _STATE.update(phase='idle', target=None, replaced=[])
    _rc, _out = _selftest_run_main([_g, '--restore'])
    assert _rc == 0 and _archives(_slots) == _arch0, \
        '餌 28 陰性對照:照畫面上教的 --restore 跑,沒有回到動手之前的樣子:\n%s' % _out
    _STATE.update(phase='idle', target=None, replaced=[])
    _bait_ran(28)

    # ── 反向餌 29:備份途中少寫了(沒有報錯的短寫)→ 訊息要講出兩邊各幾個位元組 ──
    # 反向餌 9 驗的是「正本沒被換掉」;這一個驗讀者看到的那句話。
    # 拆掉「長度不同」那道,後面「內容不同」還是會擋 —— 但讀者只看到「內容不同」,
    # 看不出是少寫了(磁碟滿、外接碟拔掉最常見的樣子)。
    _v29 = os.path.join(d, 'b29_victim.big')
    with open(_v29, 'wb') as f:
        f.write(b'KEEP29' * 50)
    _b29 = open(_v29, 'rb').read()
    _real_copy29 = shutil.copyfileobj

    def _short29(fin, fout, length=0):
        fout.write(fin.read()[:-1])        # 少寫一個位元組,而且不丟例外

    shutil.copyfileobj = _short29
    try:
        _must_stop('餌 29 短寫', '兩邊不一樣大', _atomic_copy, big, _v29)
    finally:
        shutil.copyfileobj = _real_copy29
    assert open(_v29, 'rb').read() == _b29, '餌 29:正本被換掉了'
    assert not [n for n in os.listdir(d) if '.part-' in n], '餌 29:留下了暫存檔'
    _bait_ran(29)

    # ── 反向餌 30:寫出來的長度一樣、內容不一樣 → 不可以換上去 ──
    # 2026-09-24 那一輪記下的缺口:「長度相同、內容不同的檔只有『內容不同』那一道
    # 擋得到,這種情況還沒有餌」。拆掉那一道,這種檔會被當成「相同」換上去。
    _v30 = os.path.join(d, 'b30_victim.big')
    with open(_v30, 'wb') as f:
        f.write(b'KEEP30' * 50)
    _b30 = open(_v30, 'rb').read()
    _real_copy30 = shutil.copyfileobj

    def _flip30(fin, fout, length=0):
        data = bytearray(fin.read())
        data[len(data) // 2] ^= 0xFF      # 長度一樣,中間一個位元組不一樣
        fout.write(bytes(data))

    shutil.copyfileobj = _flip30
    try:
        _must_stop('餌 30 長度同內容不同', '內容跟來源不同', _atomic_copy, big, _v30, True)
    finally:
        shutil.copyfileobj = _real_copy30
    assert open(_v30, 'rb').read() == _b30, '餌 30:內容不同的檔被換上去了'
    assert not [n for n in os.listdir(d) if '.part-' in n], '餌 30:留下了暫存檔'
    assert _STATE['phase'] == 'idle', '餌 30:沒換成,登記卻沒有收回來'
    _bait_ran(30)

    # ── 反向餌 31:還原前檢查拿到一個不存在的備份 ──
    # 走正常的 --restore 碰不到這一道(前面先用 lexists 篩過),所以直接呼叫。
    # 拆掉它,下一行量檔案大小會丟作業系統的錯,訊息變成英文的 No such file。
    _must_stop('餌 31 備份不存在', '找不到備份', _restore_from_backup,
               os.path.join(d, 'b31_沒有這份備份' + BACKUP_SUFFIX), big, True)
    _bait_ran(31)

    # ── 反向餌 45、46:還原前檢查備份的另外兩道(寫成 _stop(...) 的那幾道)──
    # 上面那套量法只數「下一行是 raise」的 if,數不到 _stop(...)。2026-09-26 用同樣的
    # 拆法去拆它們:拆掉「0 bytes」那一道,反向餌 5 照樣綠 —— 後面的「不到一半」
    # 地板會接住,只是讀者看到的是「差太多了」而不是「備份是 0 bytes」;
    # 拆掉那道地板,開頭被蓋掉(不是 BIGF)的半截備份會被拿去蓋遊戲檔。
    # 兩個餌都照讀者打的 --restore 跑,驗那句話、結束碼 2、遊戲資料夾沒被動到。
    for _n, _tag, _junk, _say in ((45, '0 bytes 的備份', b'', '備份是 0 bytes'),
                                  (46, '開頭被蓋掉又只剩半截的備份', b'\x00' * 10, '不到一半')):
        _g, _slots = _selftest_game(d, 'b%d_game' % _n)
        with open(_slots['uniforms'] + BACKUP_SUFFIX, 'wb') as f:
            f.write(_junk)
        _before = _selftest_snap(_g)
        _out = _must_exit2('餌 %d %s' % (_n, _tag), _say, [_g, '--restore'])
        assert '已還原' not in _out, '餌 %d:備份是壞的,卻印了「已還原」' % _n
        assert _selftest_snap(_g) == _before, '餌 %d:拿壞掉的備份動到了遊戲資料夾' % _n
        _bait_ran(_n)

    # ══ 反向餌 47 到 59(2026-09-26 第二次補)══════════════════════════
    # 為什麼還要補:18 到 46 補完之後再檢查一次,發現上面那套量法(只數「if 的下一行
    # 是 raise」)數不到的不只 _stop(...) 那幾道。另外用一套更寬的拆法再量(數哪些形狀
    # 見「自我測試(--selftest)」那個分隔註解),單拆還是全綠的有 22 處。
    # 這一段補讀者照課程走會碰到的那幾處;語系檔、執行檔那 8 處在反向餌 60 到 67。
    # 47 到 59 都照命令列跑 main();其中 56 到 59 要這台機器做得出符號連結。

    # ── 反向餌 47:封裝檔尾巴被截掉一段(複製或下載到一半中斷最常見的樣子)──
    # 開頭與目錄都還完整,--scan 看不出來,餌 23、24 那兩道也不會攔;要到接上去之前
    # 量檔頭大小欄位(size_field_order 最後那個 raise)才擋得下來。那個 raise 不在
    # if 底下,上面那套量法數不到它。拆掉它實測:截掉 5 個位元組的 uniforms.big 照樣
    # 被接上去、檔頭改成新的總長度,兩輪複驗全過,印「完成」、結束碼 0。
    # 它量的是工作複本,所以另外驗訊息裡寫的是 uniforms.big,不是工作複本的臨時名字。
    # 備份在這之前已經做了,所以跟餌 26 一樣只驗三個封裝檔沒變、沒留下工作複本。
    _g, _slots = _selftest_game(d, 'b47_game')
    _pk = _selftest_pack(d, 'b47_pack', _pack_ok)
    with open(_slots['uniforms'], 'rb') as f:
        _raw = f.read()
    with open(_slots['uniforms'], 'wb') as f:
        f.write(_raw[:-5])
    _arch0 = _archives(_slots)
    _out = _must_exit2('餌 47 封裝檔尾巴被截掉', 'uniforms.big 的檔頭大小欄位跟實際檔案大小對不上',
                       [_g, '--install', _pk, '--apply'])
    assert '.part-' not in _out, '餌 47:訊息裡留著工作複本的臨時名字 —— 讀者手上沒有那個檔'
    assert '進遊戲看看' not in _out, '餌 47:封裝檔是壞的,卻印了「完成」'
    assert _archives(_slots) == _arch0, '餌 47:封裝檔是壞的,遊戲檔卻被換掉了'
    assert _no_parts(_g), '餌 47:留下了工作複本'
    assert _STATE['phase'] == 'idle', '餌 47:什麼都沒換,登記卻說動過遊戲檔'
    _bait_ran(47)

    # ── 反向餌 48、49:換名前那一輪複驗的第一層與第三層 ──
    # 餌 26 對準的是第二層(撈出來的位元組跟來源不同);另外兩層單拆,自我測試原本照樣全綠。
    # 下餌跟餌 26 同一個做法:append_entry 照常接上去之後,再把工作複本改壞一處 ——
    #   48:目錄裡那一項的長度少寫 1(模擬「目錄寫錯了,沒有報錯」)。拆掉第一層,
    #       第二層還是會擋,只是說成「讀回來的位元組跟來源不同」,所以驗第一層那句話。
    #   49:檔頭 +4 的總大小改回接之前的值(模擬「檔頭那 4 個位元組沒寫進去」)。
    #       拆掉第三層,兩輪複驗都會過,印「完成」、結束碼 0。
    _real_append4849 = append_entry
    for _n, _tag, _spoil, _say in (
            (48, '目錄說的長度不對',
             lambda f, pos, blob, head: (f.seek(pos + 4), f.write(struct.pack('>I', len(blob) - 1))),
             '❌ 001.fsh 複驗失敗(目錄說 91,應該是 92 bytes)'),
            (49, '檔頭的總大小沒寫進去',
             lambda f, pos, blob, head: (f.seek(4), f.write(head[4:8])),
             '❌ uniforms.big 的檔頭大小欄位跟實際大小對不上')):
        _g, _slots = _selftest_game(d, 'b%d_game' % _n)
        _pk = _selftest_pack(d, 'b%d_pack' % _n, _pack_ok)
        _arch0 = _archives(_slots)
        _hit = {'n': 0}

        def _append_then_spoil(path, field_pos, blob, _spoil=_spoil, _hit=_hit):
            with open(path, 'rb') as f:
                head = f.read(8)
            r = _real_append4849(path, field_pos, blob)
            with open(path, 'r+b') as f:
                _spoil(f, field_pos, blob, head)
            _hit['n'] += 1
            return r

        globals()['append_entry'] = _append_then_spoil
        try:
            _out = _must_exit2('餌 %d %s' % (_n, _tag), _say, [_g, '--install', _pk, '--apply'])
        finally:
            globals()['append_entry'] = _real_append4849
        assert _hit['n'] >= 1, '餌 %d 根本沒被踩到 —— 這一輪什麼都沒測到' % _n
        assert '工作複本複驗' in _out and '不必 --restore' in _out, \
            '餌 %d:換名前就驗出壞了,卻沒有告訴讀者遊戲檔沒動、不必還原' % _n
        assert _archives(_slots) == _arch0, '餌 %d:換名前就驗出壞了,遊戲檔卻已經被換掉' % _n
        assert _no_parts(_g), '餌 %d:留下了工作複本' % _n
        assert _STATE['phase'] == 'idle', '餌 %d:什麼都沒換,登記卻說動過遊戲檔' % _n
        _bait_ran(_n)

    # ── 反向餌 50:兩次開頭檢查中間,球衣檔被換成別的東西 ──
    # 寫入迴圈裡還有第二道開頭檢查(else 後面那個 raise,不在 if 底下,量法數不到)。
    # 第一道在備份之前已經認過每一個檔,所以只有檔案在兩次檢查中間被換掉才輪得到它。
    # 下餌:「準備工作複本」那一步做完之後,把球衣包裡的 001.fsh 換成一張 PNG。
    # 拆掉這道,那張 PNG 會原封不動接進封裝檔;複驗拿的是換過之後的來源去比,
    # 當然相符 —— 印「完成」、結束碼 0。
    _g, _slots = _selftest_game(d, 'b50_game')
    _pk = _selftest_pack(d, 'b50_pack', _pack_ok)
    _arch0 = _archives(_slots)
    _real_stage50 = _stage_copy
    _hit50 = {'n': 0}

    def _stage_then_swap(live):
        r = _real_stage50(live)
        if not _hit50['n']:
            with open(os.path.join(_pk, '001.fsh'), 'wb') as f:
                f.write(b'\x89PNG\r\n\x1a\n' + b'X' * 84)
        _hit50['n'] += 1
        return r

    globals()['_stage_copy'] = _stage_then_swap
    try:
        _out = _must_exit2('餌 50 兩次檢查中間被換掉', '改動都還在工作複本上',
                           [_g, '--install', _pk, '--apply'])
    finally:
        globals()['_stage_copy'] = _real_stage50
    assert _hit50['n'] >= 1, '餌 50 根本沒被踩到 —— 這一輪什麼都沒測到'
    assert '001.fsh 的開頭既不是' in _out, '餌 50:停下來的那句話沒說出是哪一個檔不對'
    assert _archives(_slots) == _arch0, '餌 50:不是圖檔的東西被換進遊戲檔了'
    assert _no_parts(_g), '餌 50:留下了工作複本'
    assert _STATE['phase'] == 'idle', '餌 50:什麼都沒換,登記卻說動過遊戲檔'
    _bait_ran(50)

    # ── 反向餌 51:封裝檔讀不到(作業系統不讓讀)──
    # big_entries 把「打不開」翻成「讀不到 <哪一個檔>」。拆掉那個 except 實測,錯誤會一路
    # 冒到 main() 接作業系統錯誤的那個出口,改印「作業系統不讓我讀寫這個檔」那一段 ——
    # 一樣停得下來、結束碼一樣是 2,差別只在說法。所以這個餌守的是那句話,不是停不停得下來。
    # 下餌:讓打開 uniforms.big 丟 PermissionError
    # (不用 chmod:系統管理員身分與 Windows 上,chmod 擋不住讀)。
    import builtins
    _g, _slots = _selftest_game(d, 'b51_game')
    _pk = _selftest_pack(d, 'b51_pack', _pack_ok)
    _before = _selftest_snap(_g)
    _deny51 = os.path.abspath(_slots['uniforms'])
    _hit51 = {'n': 0}

    def _open_denied(file, *a, **k):
        if isinstance(file, str) and os.path.abspath(file) == _deny51:
            _hit51['n'] += 1
            raise PermissionError(13, '拒絕存取(這是 --selftest 故意製造的)', file)
        return builtins.open(file, *a, **k)

    assert 'open' not in globals(), '餌 51:這支腳本自己定義了 open,下面換回去的那一行會弄壞它'
    globals()['open'] = _open_denied
    try:
        _must_exit2('餌 51 封裝檔讀不到', '讀不到 %s' % _slots['uniforms'], [_g, '--scan', _pk])
    finally:
        del globals()['open']
    assert _hit51['n'] >= 1, '餌 51 根本沒被踩到 —— 這一輪什麼都沒測到'
    assert _selftest_snap(_g) == _before, '餌 51:遊戲資料夾被動到了'
    _bait_ran(51)

    # ── 反向餌 52:動手途中按 Ctrl-C → main() 要接住、照登記說話、結束碼 130 ──
    # 餌 7、13、16 驗的是登記本身;這一個驗讀者最後看到的那句話與結束碼。
    # 拆掉 main() 接 Ctrl-C 的那一段,讀者看到的是一整片 traceback,不知道遊戲檔動了沒有。
    #   (a) 落在換名之前(準備工作複本時)→ 要說「還沒有動到任何檔案」,不可以叫人 --restore
    #   (b) 落在換名之後(最後那一輪複驗時)→ 要說「封裝檔已經動過了」並給 --restore;
    #       照它教的 --restore 跑一次,三個封裝檔要回到動手之前(陰性對照)
    # Ctrl-C 是直接丟出 KeyboardInterrupt,不靠訊號處理器,所以哪一種機器都跑得到。
    _g, _slots = _selftest_game(d, 'b52_game')
    _pk = _selftest_pack(d, 'b52_pack', _pack_ok)
    _arch0 = _archives(_slots)
    _real_recheck52 = _recheck_archive
    _live52 = set(os.path.abspath(p) for p in _slots.values())

    def _stage_ctrl_c(live):
        raise KeyboardInterrupt

    def _recheck_ctrl_c(archive, rows, shown):
        if os.path.abspath(archive) in _live52:
            raise KeyboardInterrupt
        return _real_recheck52(archive, rows, shown)

    for _part, _name, _fake, _say, _not_say in (
            ('a', '_stage_copy', _stage_ctrl_c, '還沒有動到任何檔案', '--restore'),
            ('b', '_recheck_archive', _recheck_ctrl_c, '封裝檔已經動過了', '還沒有動到任何檔案')):
        _real = globals()[_name]
        globals()[_name] = _fake
        try:
            try:
                _rc, _out = _selftest_run_main([_g, '--install', _pk, '--apply'])
            except KeyboardInterrupt:
                raise AssertionError('餌 52(%s):Ctrl-C 沒有被 main() 接住 —— '
                                     '讀者會看到一整片 traceback' % _part)
        finally:
            globals()[_name] = _real
        assert _rc == 130, '餌 52(%s):結束碼應該是 130,實際是 %r:\n%s' % (_part, _rc, _out)
        assert _say in _out and _not_say not in _out, \
            '餌 52(%s):畫面上的話跟遊戲檔實際的狀態對不上:\n%s' % (_part, _out)
        assert _no_parts(_g), '餌 52(%s):留下了工作複本' % _part
        if _part == 'b':
            # 2026-09-26 加:只驗「封裝檔已經動過了」不夠,後面那一整行還原指令拿掉了照樣過。
            # 下面陰性對照跑的 --restore 就是這一行。
            assert _restore_cmd(_g) in _out and '不必 --restore' not in _out, \
                '餌 52(b):封裝檔已經換上去了,畫面上卻沒有給還原指令(或說了不必還原):\n%s' % _out
        if _part == 'a':
            assert _archives(_slots) == _arch0, '餌 52(a):說還沒動,遊戲檔卻變了'
            assert _STATE['phase'] == 'idle', '餌 52(a):什麼都沒換,登記卻說動過遊戲檔'
    assert _archives(_slots) != _arch0, '餌 52(b):遊戲檔應該已經換上去了(不然這一輪沒測到東西)'
    _STATE.update(phase='idle', target=None, replaced=[])
    _rc, _out = _selftest_run_main([_g, '--restore'])
    assert _rc == 0 and _archives(_slots) == _arch0, \
        '餌 52 陰性對照:照畫面上教的 --restore 跑,沒有回到動手之前的樣子:\n%s' % _out
    _STATE.update(phase='idle', target=None, replaced=[])
    _bait_ran(52)

    # ── 反向餌 53:工作複本複製得不對(而且沒有報錯)→ 不可以在它上面動手 ──
    # _stage_copy 複製完會先跟正本逐位元組比對。拆掉這一道,換名前後兩輪複驗都看不出來 ——
    # 它們只驗新接上去的那一項與檔頭,工作複本別的地方錯了會原封不動換到遊戲檔上,
    # 印「完成」、結束碼 0。
    # 下餌:先把兩份 .unibak 備份放好(這一次就跳過備份,只剩「準備工作複本」會複製),
    # 再讓複製的時候把最後一個位元組翻掉。
    _g, _slots = _selftest_game(d, 'b53_game')
    _pk = _selftest_pack(d, 'b53_pack', _pack_ok)
    for _k in ('uniforms', 'logos'):
        with open(_slots[_k], 'rb') as f:
            _raw = f.read()
        with open(_slots[_k] + BACKUP_SUFFIX, 'wb') as f:
            f.write(_raw)
    _before = _selftest_snap(_g)
    _real_copy53 = shutil.copyfileobj
    _hit53 = {'n': 0}

    def _copy_flip_last(fin, fout, length=0):
        data = bytearray(fin.read())
        data[-1] ^= 0xFF
        fout.write(bytes(data))
        _hit53['n'] += 1

    shutil.copyfileobj = _copy_flip_last
    try:
        _must_exit2('餌 53 工作複本複製得不對', '寫出來的內容跟來源不同',
                    [_g, '--install', _pk, '--apply'])
    finally:
        shutil.copyfileobj = _real_copy53
    assert _hit53['n'] >= 1, '餌 53 根本沒被踩到 —— 這一輪什麼都沒測到'
    assert _selftest_snap(_g) == _before, '餌 53:工作複本是壞的,遊戲資料夾卻被動到了(或留下了暫存檔)'
    assert _STATE['phase'] == 'idle', '餌 53:什麼都沒換,登記卻說動過遊戲檔'
    _bait_ran(53)

    # ── 反向餌 54:--restore 時一份備份好、一份壞 → 一份都不可以先還原 ──
    # cmd_restore 先把每一份備份都驗過(verify_only=True 那一輪)才開始蓋。拆掉那一輪,
    # 好的那一份會先被還原,輪到壞的那一份才停 —— 讀者拿到「一半還原、一半沒還原」的
    # 遊戲資料夾(2026-09-05 修掉的就是這個)。下餌:uniforms.big 的備份是好的、但跟現在
    # 的檔不一樣;logos.big 的備份是 0 bytes(uniforms 排在 logos 前面,拆掉那一輪時它會先被蓋)。
    _g, _slots = _selftest_game(d, 'b54_game')
    with open(_slots['uniforms'] + BACKUP_SUFFIX, 'wb') as f:
        f.write(_fake_big([('001.fsh', _q + b'V' * 30)]))
    with open(_slots['logos'] + BACKUP_SUFFIX, 'wb') as f:
        f.write(b'')
    _before = _selftest_snap(_g)
    _out = _must_exit2('餌 54 一好一壞的備份', '備份是 0 bytes', [_g, '--restore'])
    assert '已還原' not in _out, '餌 54:有一份備份是壞的,卻印了「已還原」'
    assert _selftest_snap(_g) == _before, '餌 54:有一份備份是壞的,另一份卻已經先還原了'
    _bait_ran(54)

    # ── 反向餌 55:裝第二套球衣,不可以把第一次動手之前的備份蓋掉 ──
    # 看到備份已經在就不再備份 —— 那一份才是「你第一次動手之前的樣子」。那個 if 底下
    # 不是 raise 而是 continue,兩套量法都數不到;拆掉它,自我測試原本照樣全綠,
    # 而裝第二套時備份會被換成「裝了第一套之後」的樣子,--restore 只退得回第一套。
    # 下餌:同一個遊戲資料夾連裝兩套不一樣的球衣,再 --restore,要回到兩套都還沒裝的樣子。
    _g, _slots = _selftest_game(d, 'b55_game')
    _arch0 = _archives(_slots)
    for _i, _pkx in enumerate((_selftest_pack(d, 'b55_packA', _pack_ok),
                               _selftest_pack(d, 'b55_packB', [('001.fsh', _q + b'P' * 90),
                                                               ('l001.fsh', _q + b'Q' * 90)]))):
        _rc, _out = _selftest_run_main([_g, '--install', _pkx, '--apply'])
        assert _rc == 0 and '進遊戲看看' in _out, \
            '餌 55:第 %d 套正常的球衣沒裝成功(這一輪什麼都沒測到):\n%s' % (_i + 1, _out)
        _STATE.update(phase='idle', target=None, replaced=[])
    assert '備份已存在,保留最早那一份' in _out, '餌 55:裝第二套時沒有說保留了最早那一份備份'
    _rc, _out = _selftest_run_main([_g, '--restore'])
    assert _rc == 0 and _archives(_slots) == _arch0, \
        '餌 55:連裝兩套之後 --restore,沒有回到兩套都還沒裝的樣子(第一次的備份被蓋掉了):\n%s' % _out
    _STATE.update(phase='idle', target=None, replaced=[])
    _bait_ran(55)

    # ── 反向餌 56 到 59:遊戲資料夾裡有符號連結(照命令列跑)──
    # 餌 1、8 驗的是 _refuse_symlink 這支函式本身;這四個驗 --install 與 --restore 在動手
    # 之前有沒有真的去叫它。單拆其中一處呼叫,自我測試原本照樣全綠:
    #   56 --install,封裝檔本身是連結 → 要在備份之前就停。拆掉的話,後面準備工作複本
    #      那一步還是會擋,說的話也一樣 —— 但那時候已經隔著連結做了兩份備份。
    #   57 --install,備份那個名字是連結、指到資料夾外面一個存在的檔 → 要停。拆掉的話,
    #      它被當成「備份已存在」,整批照裝,而退路是一個指到別處的連結。
    #   58 --restore,備份是連結 → 要停。拆掉的話,會照著連結把外面那個檔還原進來。
    #   59 --restore,封裝檔是連結 → 要在還原任何一份之前就停。拆掉的話,排在前面的
    #      uniforms.big 先被還原,輪到 logos.big 才被另一道擋下,變成一半還原。
    # 連結都指到遊戲資料夾外面同一個檔,另外驗那個檔一個位元組都沒變。
    # 做不出符號連結的機器整段跳過,並寫在畫面上(同餌 1、2、8)。
    _outside56 = os.path.join(d, 'b56_outside.big')
    with open(_outside56, 'wb') as f:
        f.write(_fake_big([('001.fsh', _q + b'O' * 30), ('l001.fsh', _q + b'O' * 30)]))
    with open(_outside56, 'rb') as f:
        _outside56_0 = f.read()
    try:
        os.symlink(_outside56, os.path.join(d, 'b56_probe_link'))
        _can_link = True
    except (OSError, NotImplementedError, AttributeError):
        _can_link = False
    if _can_link:
        # 56
        _g, _slots = _selftest_game(d, 'b56_game')
        _pk = _selftest_pack(d, 'b56_pack', _pack_ok)
        os.remove(_slots['logos'])
        os.symlink(_outside56, _slots['logos'])
        _before = _selftest_snap(_g)
        _must_exit2('餌 56 封裝檔是連結', '封裝檔 logos.big 是一個符號連結',
                    [_g, '--install', _pk, '--apply'])
        assert _selftest_snap(_g) == _before, '餌 56:封裝檔是連結,卻先隔著它做了備份(或動到了別的檔)'
        _bait_ran(56)
        # 57
        _g, _slots = _selftest_game(d, 'b57_game')
        _pk = _selftest_pack(d, 'b57_pack', _pack_ok)
        os.symlink(_outside56, _slots['logos'] + BACKUP_SUFFIX)
        _before = _selftest_snap(_g)
        _out = _must_exit2('餌 57 備份那個名字是連結', '備份檔 logos.big.unibak 是一個符號連結',
                           [_g, '--install', _pk, '--apply'])
        assert '進遊戲看看' not in _out, '餌 57:退路是一個連結,卻照樣裝完了'
        assert _selftest_snap(_g) == _before, '餌 57:備份是連結,遊戲資料夾卻被動到了'
        _bait_ran(57)
        # 58
        _g, _slots = _selftest_game(d, 'b58_game')
        os.symlink(_outside56, _slots['uniforms'] + BACKUP_SUFFIX)
        _before = _selftest_snap(_g)
        _out = _must_exit2('餌 58 還原時備份是連結', '備份檔 uniforms.big.unibak 是一個符號連結',
                           [_g, '--restore'])
        assert '已還原' not in _out, '餌 58:備份是連結,卻印了「已還原」'
        assert _selftest_snap(_g) == _before, '餌 58:照著連結把外面的檔還原進來了'
        _bait_ran(58)
        # 59
        _g, _slots = _selftest_game(d, 'b59_game')
        with open(_slots['uniforms'] + BACKUP_SUFFIX, 'wb') as f:
            f.write(_fake_big([('001.fsh', _q + b'V' * 30)]))
        with open(_slots['logos'], 'rb') as f:
            _raw = f.read()
        with open(_slots['logos'] + BACKUP_SUFFIX, 'wb') as f:
            f.write(_raw)
        os.remove(_slots['logos'])
        os.symlink(_outside56, _slots['logos'])
        _before = _selftest_snap(_g)
        _out = _must_exit2('餌 59 還原時封裝檔是連結', '封裝檔 logos.big 是一個符號連結',
                           [_g, '--restore'])
        assert '已還原' not in _out, '餌 59:有一個封裝檔是連結,卻印了「已還原」'
        assert _selftest_snap(_g) == _before, '餌 59:有一個封裝檔是連結,另一個卻已經先還原了'
        _bait_ran(59)
        with open(_outside56, 'rb') as f:
            assert f.read() == _outside56_0, '餌 56 到 59:連結指到的、遊戲資料夾外面的那個檔被動到了'
    else:
        for _n in (56, 57, 58, 59):
            _bait_skipped(_n, _WHY_NO_SYMLINK)

    # ── 反向餌 32:封裝檔小到連檔頭都裝不下(不到 8 個位元組)──
    # 走 --install 會先被「開頭不是 BIGF」那一道擋下(餌 23),所以直接呼叫。
    # 拆掉它,下一行會丟 struct.error —— 不是本腳本認得的錯,讀者會看到 traceback。
    _tiny = os.path.join(d, 'b32_tiny.big')
    with open(_tiny, 'wb') as f:
        f.write(b'BIGF')
    _must_stop('餌 32 封裝檔不到 8 bytes', '太小', size_field_order, _tiny)
    _bait_ran(32)

    # ── 反向餌 33 到 44:這一課不會呼叫的共用函式 ──
    # qfs_decompress、read_entry、fsh_first_image、fsh_replace_pixels 這四支,
    # 裝球衣的流程一支都沒用到(球衣檔是原封不動接進去的)。留著是給想自己
    # 改圖的人接手用的 —— 他拿去用的時候,守門要是真的會擋的。
    # 先做陰性對照:正常的資料要解得開、讀得出、換得了,不然下面的「擋下來了」
    # 可能只是因為那支函式本來就整個壞掉。
    assert qfs_decompress(qfs_compress_literal(b'MVP2005 uniform')) == b'MVP2005 uniform', \
        '陰性對照:純照抄的 QFS 解不回原樣'
    assert qfs_decompress(b'\x10\xfb\x00\x00\x04' + b'\x01\x00' + b'A') == b'AAAA', \
        '陰性對照:帶反向參照的 QFS 解不回 AAAA'
    _must_stop('餌 33 QFS 長檔頭不完整', 'QFS 檔頭不完整', qfs_decompress, b'\x11\xfb\x00\x00\x00')
    _bait_ran(33)
    _must_stop('餌 34 QFS 短檔頭不完整', 'QFS 檔頭不完整', qfs_decompress, b'\x10\xfb\x00')
    _bait_ran(34)
    _must_stop('餌 35 QFS 宣稱的解壓大小超過上限', '解壓尺寸異常', qfs_decompress,
               b'\x11\xfb\x00\x00\x00\x00' + (MAX_UNCOMPRESSED + 1).to_bytes(4, 'big'))
    _bait_ran(35)
    # 照抄 1 個 A 之後往回 10 個位元組抄 —— 可是手上只有 1 個位元組。
    _must_stop('餌 36 QFS 反向參照越界', '反向參照越界', qfs_decompress,
               b'\x10\xfb\x00\x00\x10' + b'\x01\x09' + b'A')
    _bait_ran(36)
    # 檔頭說解開是 2 個位元組,控制碼卻吐出 4 個。
    _must_stop('餌 37 QFS 解出來超過宣稱的大小', '超過檔頭宣稱', qfs_decompress,
               b'\x10\xfb\x00\x00\x02' + b'\x01\x00' + b'A')
    _bait_ran(37)
    _p38 = os.path.join(d, 'b38.big')
    with open(_p38, 'wb') as f:
        f.write(_fake_big([('a.fsh', b'xyz')]))
    _it38 = big_entries(_p38)[0]
    assert read_entry(_p38, _it38[2], _it38[3]) == b'xyz', '陰性對照:read_entry 讀不出 xyz'
    _must_stop('餌 38 目錄說的長度比檔案剩下的多', '實際只讀到', read_entry,
               _p38, _it38[2], _it38[3] + 5)
    _bait_ran(38)
    _shpi = _selftest_shpi()
    assert fsh_first_image(_shpi) == (0x7D, 2, 2, 40, len(_shpi)), \
        '陰性對照:自造的 SHPI 讀不出來:%r' % (fsh_first_image(_shpi),)
    _must_stop('餌 39 不是 SHPI', '不是 SHPI', fsh_first_image, _selftest_shpi(magic=b'SHPX'))
    _bait_ran(39)
    _must_stop('餌 40 SHPI 裡 0 張圖', '一張圖都沒有', fsh_first_image, _selftest_shpi(num=0))
    _bait_ran(40)
    _must_stop('餌 41 圖片記錄的位移指到檔案外面', '檔頭不完整', fsh_first_image,
               _selftest_shpi(img_off=1000))
    _bait_ran(41)
    _must_stop('餌 42 沒見過的格式代號', '沒見過的格式代號', fsh_first_image, _selftest_shpi(code=0x55))
    _bait_ran(42)
    _must_stop('餌 43 圖片寬度是 0', '圖片尺寸異常', fsh_first_image, _selftest_shpi(width=0))
    _bait_ran(43)
    assert fsh_replace_pixels(_shpi, 40, 56, b'\x22' * 16) == _shpi[:40] + b'\x22' * 16, \
        '陰性對照:長度相同的像素換不進去'
    _must_stop('餌 44 新像素長度不同', '拒絕寫入', fsh_replace_pixels, _shpi, 40, 56, b'\x22' * 15)
    _bait_ran(44)

    # ── 反向餌 60 到 67:還原前檢查裡給語系檔(LOCH)與執行檔(MZ)用的那 8 道(2026-09-26 加)──
    # 這一課的備份都是封裝檔(BIGF),走 --restore 碰不到它們;留著是因為這段檢查是本站
    # 幾支腳本共用的(2026-08-30 那次是六支腳本一起中招),哪天有人拿去接手用,守門要是真的會擋。
    # 所以直接呼叫 _restore_from_backup(只驗不蓋),而目標檔故意不存在 ——
    # 不讓最後那道「不到一半」的地板插手,量到的才是對準的那一道。
    # 每一格各一個:6 道 if,加上 2 道「讀不出結構」的 except(檔案短到連該讀的那幾格都沒有)。
    # 先做陰性對照:格式完整的假語系檔與假執行檔要過得了,不然下面的「擋下來了」
    # 可能只是那段檢查本來就什麼都擋。
    _nodst = os.path.join(d, 'b60_沒有這個檔')

    def _loc_bak(tag, blob):
        p = os.path.join(d, 'b%s%s' % (tag, BACKUP_SUFFIX))
        with open(p, 'wb') as f:
            f.write(blob)
        return p

    assert _restore_from_backup(_loc_bak('60ok', _selftest_loch()), _nodst, True) is None, \
        '陰性對照:格式完整的假語系檔過不了還原前檢查'
    assert _restore_from_backup(_loc_bak('64ok', _selftest_mz()), _nodst, True) is None, \
        '陰性對照:格式完整的假執行檔過不了還原前檢查'
    for _n, _tag, _blob, _say in (
            (60, '語系檔的 LOCL 不在該在的地方', _selftest_loch(locl=b'XXXX'), '那裡不是 LOCL'),
            (61, '語系檔的位移表被截斷', _selftest_loch(count=1000), '位移表被截斷了'),
            (62, '語系檔最後一條字串超出檔尾', _selftest_loch()[:62], '超出檔案結尾'),
            (63, '語系檔短到讀不出結構', b'LOCH' + b'\x00' * 12, '讀不出語系檔的結構'),
            (64, '執行檔的 PE 檔頭不對', _selftest_mz(pe=b'PX\x00\x00'), 'PE 檔頭不在它該在的地方'),
            (65, '執行檔的節區表被截斷', _selftest_mz(nsec=100), '節區表被截斷了'),
            (66, '執行檔的節區指到檔尾外面', _selftest_mz(raw_size=0x200), '節區指到'),
            (67, '執行檔短到讀不出結構', b'MZ' + b'\x00' * 30, '讀不出執行檔的結構')):
        _must_stop('餌 %d %s' % (_n, _tag), _say, _restore_from_backup, _loc_bak(_n, _blob), _nodst, True)
        _bait_ran(_n)

    # ── 反向餌 68:沒加 --apply 的 --install 只能預覽,一個位元組都不可以寫(2026-09-26 加)──
    # 這是整支工具「預設不寫」的根本,也是課程頁面「預覽」那一步讀者一定會跑的那一行。
    # 守門是 cmd_install 裡的 `if not apply_it:`,底下是 return 而不是 raise,前兩套量法都數不到
    # (第三套才數得到,見「自我測試(--selftest)」那個分隔註解);
    # 而這之前自我測試裡每一次 --install 都帶著 --apply。把那一行拆掉(或讓 main() 把
    # args.apply 換成 True),當時的自我測試照樣全綠,而沒加 --apply 的 --install 會真的做備份、
    # 改寫兩個封裝檔、印「完成」、結束碼 0(2026-09-26 在假遊戲資料夾上實測)。
    # 下餌:照讀者打的樣子跑一次不加 --apply 的 --install。球衣包用裝得進去的那一種,
    # 不然它會先被餌 21 那一道擋下來,測不到這一道。
    # 陰性對照在後面:同一行加上 --apply 再跑一次,遊戲資料夾要真的變了 ——
    # 不然「沒變」可能只是這個球衣包本來就裝不進去。
    _g, _slots = _selftest_game(d, 'b68_game')
    _pk = _selftest_pack(d, 'b68_pack', _pack_ok)
    _before = _selftest_snap(_g)
    _rc, _out = _selftest_run_main([_g, '--install', _pk])
    assert _rc == 0, '餌 68:沒加 --apply 的預覽,結束碼應該是 0,實際是 %r:\n%s' % (_rc, _out)
    assert '以上是預覽,還沒有動到任何檔案' in _out, \
        '餌 68:沒加 --apply,畫面上卻沒有說這只是預覽:\n%s' % _out
    assert '已備份' not in _out and '進遊戲看看' not in _out, \
        '餌 68:沒加 --apply,卻做了備份或印了「完成」:\n%s' % _out
    assert _selftest_snap(_g) == _before, \
        '餌 68:沒加 --apply,遊戲資料夾卻被動到了(或多了備份檔、暫存檔)'
    assert _STATE['phase'] == 'idle', '餌 68:什麼都沒寫,登記卻說動過遊戲檔'
    _rc, _out = _selftest_run_main([_g, '--install', _pk, '--apply'])
    assert _rc == 0 and '進遊戲看看' in _out and _selftest_snap(_g) != _before, \
        '餌 68 陰性對照:同一行加上 --apply 卻沒有裝進去(這一輪什麼都沒測到):\n%s' % _out
    _STATE.update(phase='idle', target=None, replaced=[])
    _bait_ran(68)

    # ── 反向餌 69:接到工作複本時作業系統不讓寫(封裝檔被設成唯讀最常見的樣子)(2026-09-26 加)──
    # 為什麼要有它:這時候遊戲檔一個位元組都還沒動,main() 接住作業系統錯誤之後要照登記說
    # 「不必 --restore」—— 課程頁面「停下來了:作業系統不讓我讀寫這個檔」那一列,教讀者看的
    # 正是這一句。餌 15 走的是同一條路,但它直接呼叫 cmd_install 而且把畫面吃掉,看不到 main()
    # 最後印的那一段。補這個餌之前實測:把 main() 裡照登記分兩路的那個 if 改成永遠不成立
    # (永遠印「封裝檔已經換過了」加還原指令),或把「不必 --restore」那一行拿掉,自我測試照樣全綠。
    # 讀者照著那行指令還原,會把他先前裝好的別套球衣一起退掉。
    # 下餌:跟餌 15 一樣讓 append_entry 丟一個帶著工作複本路徑的 PermissionError
    # (不用 chmod:系統管理員身分與 Windows 上,chmod 擋不住寫)。
    _g, _slots = _selftest_game(d, 'b69_game')
    _pk = _selftest_pack(d, 'b69_pack', _pack_ok)
    _arch0 = _archives(_slots)
    _real_append69 = append_entry
    _hit69 = {'tmp': ''}

    def _append_denied(path, field_pos, blob):
        _hit69['tmp'] = os.path.basename(path)
        raise PermissionError(13, '拒絕存取(這是 --selftest 故意製造的)', path)

    globals()['append_entry'] = _append_denied
    try:
        _out = _must_exit2('餌 69 接到工作複本時被拒絕', '停下來了:作業系統不讓我讀寫這個檔',
                           [_g, '--install', _pk, '--apply'])
    finally:
        globals()['append_entry'] = _real_append69
    assert '.part-' in _hit69['tmp'], '餌 69 根本沒被踩到 —— 這一輪什麼都沒測到'
    assert '你的遊戲檔一個位元組都沒有動,不必 --restore' in _out, \
        '餌 69:遊戲檔沒動,畫面上卻沒有告訴讀者不必還原:\n%s' % _out
    assert _restore_cmd(_g) not in _out and '封裝檔已經換過了' not in _out, \
        '餌 69:遊戲檔沒動,畫面上卻叫讀者還原:\n%s' % _out
    assert _hit69['tmp'] not in _out, '餌 69:畫面上留著工作複本那個臨時名字(讀者手上沒有那個檔)'
    assert _archives(_slots) == _arch0, '餌 69:接到工作複本那一步就失敗了,遊戲檔卻被動到了'
    assert _no_parts(_g), '餌 69:留下了工作複本'
    assert _STATE['phase'] == 'idle', '餌 69:什麼都沒換,登記卻說動過遊戲檔'
    _bait_ran(69)

    # ── 反向餌 70:換上去換到一半被拒絕,而回頭路做得出來(2026-09-26 加)──
    # 例如第二個封裝檔正被別的程式開著(Windows 上遊戲沒關就是這樣)。已經換上去的那一個
    # 會靠回頭路換回來,所以遊戲檔一個位元組都沒動,畫面上兩段話都要說不必還原:
    # 逐檔說明那一段(「換名中途停下來了」底下)與 main() 接住作業系統錯誤之後那一段。
    # 餌 12 走的是同一條路,但它直接呼叫 cmd_install 而且把畫面吃掉,只驗三個封裝檔換回來了;
    # 補這個餌之前實測:把逐檔說明那一段的「不必 --restore」換成還原指令,自我測試照樣全綠。
    # 下餌:os.link 照常(回頭路做得出來),讓換到第二個封裝檔身上的 os.replace 丟 PermissionError。
    # 跟餌 12 一樣,要系統暫存資料夾做得出硬連結(2026-09-26 模擬過做不出來的機器:兩個都會紅)。
    # 反過來那一面是餌 28:同一條路做不出回頭路時,兩段都要改口給還原指令。
    _g, _slots = _selftest_game(d, 'b70_game')
    _pk = _selftest_pack(d, 'b70_pack', _pack_ok)
    _arch0 = _archives(_slots)
    _live70 = set(_slots.values())
    _real_replace70 = os.replace
    _trip70 = {'hits': 0, 'done': False}

    def _locked_second(a, b):
        if not _trip70['done'] and os.fspath(b) in _live70:
            _trip70['hits'] += 1
            if _trip70['hits'] >= 2:
                _trip70['done'] = True
                raise PermissionError(13, '檔案正被別的程式使用(這是 --selftest 故意製造的)', b)
        return _real_replace70(a, b)

    os.replace = _locked_second
    try:
        _out = _must_exit2('餌 70 換到一半被拒絕', '停下來了:作業系統不讓我讀寫這個檔',
                           [_g, '--install', _pk, '--apply'])
    finally:
        os.replace = _real_replace70
    assert _trip70['done'], '餌 70 根本沒被踩到 —— 這一輪什麼都沒測到'
    # 分段跟餌 28 一樣用後面那半句(逐檔說明的標題「換名中途停下來了」裡也有「停下來了」)。
    _pre70, _sep70, _post70 = _out.partition('停下來了:作業系統不讓我讀寫這個檔')
    _rows70 = [ln.strip() for ln in _pre70.splitlines()
               if ln.strip().endswith('已改') or ln.strip().endswith('沒改')]
    assert '換名中途停下來了' in _pre70 and len(_rows70) == 2 \
        and all(ln.endswith('沒改') for ln in _rows70), \
        '餌 70:兩個封裝檔都換回來了,逐檔說明卻沒有兩行都說「沒改」:\n%s' % _out
    assert '不必 --restore' in _pre70, \
        '餌 70:逐檔說明那一段沒有告訴讀者不必還原:\n%s' % _out
    assert '你的遊戲檔一個位元組都沒有動,不必 --restore' in _post70, \
        '餌 70:最後那一段沒有照登記說不必還原:\n%s' % _out
    assert _restore_cmd(_g) not in _out and '封裝檔已經換過了' not in _out, \
        '餌 70:遊戲檔都換回來了,畫面上卻叫讀者還原:\n%s' % _out
    assert _archives(_slots) == _arch0, '餌 70:換到一半被拒絕,封裝檔卻沒有全部回到動手之前的樣子'
    assert _no_parts(_g), '餌 70:留下了工作複本或回頭路'
    assert _STATE['phase'] == 'idle', '餌 70:全部換回來了,登記卻說動過遊戲檔'
    _bait_ran(70)

    # ── 反向餌 14:印出來的餌數必須是「真的踩過的那些」,不可以寫死 ──
    # 這一個踩的是記帳簿自己。上面那些餌裡有 9 個會因為機器做不到而整段
    # 跳過(餌 1、2、8、56 到 59 要做得出符號連結,餌 10、13 要裝得上訊號處理器),
    # 而舊版(那時候一共 13 個餌)不管跑了幾個都印同一個數字。實測模擬那兩種機器:只有 10 個 / 11 個
    # 餌真的踩過,畫面上還是印 13 —— 頁面卻叫讀者拿那個數字決定要不要動遊戲檔。
    # 下餌的方式有兩面:
    #   (a) 從記錄簿裡拿掉一個跑過的餌,那一行字一定要跟著變(數字寫死就不會變);
    #   (b) 把它改記成「跳過」,畫面上一定要出現跳過的說明(不說就等於沒說謊也沒說實話)。
    _bait_ran(14)
    _real = _bait_summary(_BAIT_LOG)
    _one_less = {'ran': [n for n in _BAIT_LOG['ran'] if n != 4],
                 'skipped': list(_BAIT_LOG['skipped'])}
    assert _bait_summary(_one_less) != _real, \
        '少跑一個反向餌,印出來的那一行竟然一模一樣 —— 那個數字是寫死的'
    _moved = {'ran': _one_less['ran'],
              'skipped': list(_BAIT_LOG['skipped']) + [(4, '假裝跳過(反向餌 14 造的)')]}
    assert any('假裝跳過' in ln for ln in _bait_summary(_moved)), \
        '跳過的反向餌沒有被寫在畫面上 —— 讀者會以為每一個都跑過了'
    assert _bait_summary(_BAIT_LOG) == _real, '記錄簿被反向餌 14 自己改壞了'

    for _line in _bait_summary(_BAIT_LOG):
        print(_line)
    print('  測試用的檔留在 %s' % d)
    return 0


# ─────────────────────────────────────────────────────────
#  「-O 拒跑」那道守門的餌(2026-09-24 加)
#
#  自我測試一開頭有一道守門:在 python -O 底下拒跑(-O 會把 assert 整段拿掉,
#  測試會變成一片假的綠燈)。那一行以前直接問 sys.flags.optimize,
#  而 sys.flags 是唯讀的,同一個程序裡沒辦法把 -O 打開又關掉 ——
#  所以那道守門一直沒有餌:哪天被拆掉,自我測試照樣全綠,沒有人會發現。
#  現在守門改問 _optimize_level(),自我測試就能暫時把它換掉來下餌。
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
