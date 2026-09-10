#!/bin/bash
#
# ─────────────────────────────────────────────────────────
#  法律與免責(每一支本站腳本都帶著這一段)
#
#  · 本工具與 Electronic Arts 無任何官方關聯,也未經其授權或背書。
#    MVP Baseball 2005 為 Electronic Arts 之作品與商標。
#  · 本工具為原創程式碼,**不含任何 EA 的程式碼或資產**。
#  · 本工具不提供、不教學、也不包含任何規避技術保護措施的功能。
#    它只設兩個環境變數(WINEDEBUG 與 WINEPREFIX)並把畫面訊息錄成一份 log,
#    腳本自己不寫入遊戲資料夾裡的任何檔案。
#  · 使用者應僅對自己合法取得的遊戲副本使用本工具,並自行承擔風險。
#    使用前請自行確認你與遊戲發行商之間的使用者授權合約(EULA)。
#  · 本工具按「現狀」提供,不附任何明示或默示的擔保。
#  · 授權:MIT(見檔尾)。教學文字另採 CC BY 4.0。
#  · 回報與下架:https://toniliumvp.github.io/MVPBaseball/report.html
#    三條管道,其中「直接向 GitHub 提出」不需經過維護者;
#    留言區那條不需要任何帳號。管道有變動只會改那一頁。
# ─────────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════
#  mvp_wine_log.sh — 用 Wine 啟動遊戲,並把「遊戲自己送出的除錯訊息」錄下來
#
#  MVP Baseball 2005 內建了一套除錯訊息,走 Windows 的 OutputDebugStringA 送出去。
#  在 Windows 上要用 DebugView 才看得到。在 Mac 的 Wine 底下,照理說把
#  WINEDEBUG 設成 +debugstr 就會印出來 —— 但本站實測攔不到:11 次實跑的 log,
#  debugstr 這個頻道一行都沒有(其中 10 份的 seh 有 68~102 行,代表旗標本身有生效)。
#  課程頁第 ⑨ 節寫了原因:debugstr 這個頻道掛在 kernel32.dll,
#  而真正實作 OutputDebugStringA 的是 kernelbase.dll。
#  所以這支腳本現在的用處是收 +seh 的當機現場,不要指望它讀得到字串內容。
#
#  平常的啟動腳本設的是 WINEDEBUG="-all"(全部關掉),所以連 seh 都看不到。
#  這支腳本只設環境變數並把訊息錄成一份 log,自己不寫入遊戲資料夾裡的任何檔案。
#
#  用法(遊戲資料夾是必填,把資料夾拖進終端機就會自動填):
#    bash mvp_wine_log.sh "<遊戲資料夾>"
#    bash mvp_wine_log.sh "<遊戲資料夾>" "<執行檔檔名>"
#    bash mvp_wine_log.sh --help
#    bash mvp_wine_log.sh --selftest     ← 只驗自己的守門,不會啟動遊戲
#
#  log 寫到桌面,檔名是 mvp_debug_<年月日_時分秒>.log;
#  桌面不存在就改寫到家目錄,同一秒內跑第二次會自動加序號,不會蓋掉前一份。
#  ⚠️ log 裡會有你的家目錄、帳號名稱與遊戲資料夾的完整路徑(Wine 自己印的)。
#  所以跑完會**另外**產一份遮蔽版 mvp_debug_<...>_可回報.log:家目錄、帳號名稱、
#  Windows 使用者資料夾都換成代號。要貼到網路上請貼那一份,原始那份留在自己電腦。
#  遮蔽版產完會自己複驗,只要還找得到家目錄或帳號名稱就刪掉它並以非 0 離開。
#
#  想換 Wine 的除錯旗標,跑之前設 WINEDEBUG_MODE,例如
#    WINEDEBUG_MODE=+seh bash mvp_wine_log.sh "<遊戲資料夾>"
#  啟動遊戲時會先 cd 進遊戲資料夾(跟本站啟動器同一個條件),
#  而且只有遊戲資料夾底下懶人包那一層裡真的有 wineprefix 時,才設 WINEPREFIX。
#
#  安全:遊戲資料夾裡懶人包那一層的 .wine_path 是「別人做的懶人包也可能夾帶」的設定檔,
#  它的內容會被當成程式執行。所以這裡不只看檔名,還要求解開符號連結之後的
#  絕對路徑落在下面那張白名單裡(Homebrew / MacPorts / /usr/bin /
#  Wine 或 CrossOver 或 Whisky 的 app 套件 / Linux 的 wine 套件目錄),
#  而且那個檔必須是「一般檔案、有執行位元」。
#  腳本自己寫死的那張自動搜尋清單走的是同一道關卡 —— 不是「寫死的就免驗」。
#  .wine_path 不合格就整條忽略,改用自動搜尋清單。
#
#  ⚠️ 這道關卡只看三件事:路徑前綴、檔名、是不是可以執行的一般檔案。
#     它**不驗簽章、也不看檔案內容**。如果有人有辦法把東西放進
#     /opt/homebrew/bin/ 並且取名叫 wine,這裡照樣會執行它。
#     它擋的是「別人做的懶人包夾帶一個 .wine_path」,不是「系統已經被入侵」。
#
#  寫檔:這支腳本只在桌面(桌面不在就家目錄)建兩個檔 —— 原始 log 與遮蔽版。
#  兩個都用 O_EXCL 新建,不覆蓋既有檔;目的檔如果是符號連結就直接停下來,
#  不跟著連結去寫別的地方。中斷(Ctrl+C)時照三態說話:還沒建 / 正在建 X /
#  已經建好 X,不會在「檔案已經建好、但還沒登記」的那個空檔說成「什麼都還沒建立」。
#
#  MIT License · Copyright (c) 2026 toni
# ═══════════════════════════════════════════════════════════════

set -u

# ═══ 小工具:路徑守門與安全建檔 ═══════════════════════════════
# 這一段只做判斷,不執行任何東西,也不寫入遊戲資料夾。
# 每一條守門在 --selftest 裡都有一個「餌」在測它會不會真的擋下來。

# 允許被當成 Wine 執行的檔名(要完全相同,不是「wine 開頭」)。
WINE_BASENAMES="wine wine64 wine32 wine32on64 wine-stable wine-devel wine-staging wine-preview wine-crossover"

WINE_REJECT_REASON=""
WINE_VALIDATED=""
EXE_REJECT_REASON=""
# create_new_file 為什麼失敗:symlink / exists / cannot-create。
# 有這個才分得出「同名的是你上一輪跑出來的檔」跟「同名的是別人放的符號連結」,
# 這兩種的處置不一樣(前者換序號,後者停下來)。
CREATE_FAIL_REASON=""

# ── 狀態登記:還沒建 / 正在建 X / 建好但還沒複驗 / 已經建好而且驗過 ────────
# 這支腳本不寫遊戲資料夾,但它會在桌面建兩個檔。「檔案建好」跟「登記建好」
# 是兩個動作,Ctrl+C 剛好落在中間的話,收尾就會照舊的登記說「什麼都還沒建立」——
# 那是說謊,桌面上其實已經多了一個檔。所以每個檔各有三態,
# 而且「建檔 + 登記」整段包在不可中斷區裡(begin_uninterruptible)。
LOG=""
LOG_CAND=""
LOG_STATE=none
LOG_CREATED=0
SHARE=""
SHARE_CAND=""
SHARE_STATE=none
GAME_STARTED=0
# 遊戲「開過」跟遊戲「跑完了」是兩件事。分不開的話,遊戲結束之後才按的 Ctrl+C
# 會被說成「收到一半的 log、分析也沒跑」—— 那時候 log 其實是完整的。
GAME_DONE=0

# 不可中斷區:進到區裡才收到的 Ctrl+C 先記著,離開區之後再照常處理。
# 這樣中斷收尾看到的登記,一定跟磁碟上的狀態一致。
INT_DEFER=0
INT_PENDING=0
begin_uninterruptible() { INT_DEFER=1; INT_PENDING=0; }
end_uninterruptible() {
    INT_DEFER=0
    if [ "$INT_PENDING" -eq 1 ]; then
        INT_PENDING=0
        on_interrupt
    fi
}

# 中斷時要講的話。三態各有各的說法,不可以一律說「什麼都還沒動」。
# 順序有意義:「正在建遮蔽版」要排在「遊戲已經啟動」前面 ——
# 遮蔽版是遊戲跑完才建的,兩個條件會同時成立,排錯就永遠說不到遮蔽版那一句。
interrupt_report() {
    echo ""
    echo "  ⚠️  你按了 Ctrl+C,這一輪中斷。"
    if [ "$SHARE_STATE" = "created" ]; then
        echo "     兩份檔都已經產生完了,被中斷的只是最後的整理。"
        echo "     原始 log(含本機路徑,自己留):$LOG"
        echo "     回報用(已遮蔽,複驗過了):$SHARE"
    elif [ "$SHARE_STATE" = "unverified" ]; then
        echo "     遮蔽版已經產生,但還沒跑完複驗就被中斷了:$SHARE"
        echo "     ⚠️ 沒驗過的那一份不要直接貼出去,裡面可能還留著家目錄或帳號名稱。"
        echo "     原始 log 在:$LOG"
    elif [ "$SHARE_STATE" = "creating" ]; then
        echo "     中斷時正在建立遮蔽版:$SHARE_CAND"
        echo "     那個檔可能已經建好了(內容可能只有一半),自己看一眼再決定要不要刪。"
        echo "     原始 log 在:$LOG"
    elif [ "$GAME_DONE" -eq 1 ]; then
        echo "     遊戲已經結束了,log 收完整了:$LOG"
        echo "     被中斷的是後面的整理,所以還沒有可以貼出去的遮蔽版 ——"
        echo "     這一份裡面有你的家目錄與帳號名稱,要給別人請自己先遮掉。"
    elif [ "$GAME_STARTED" -eq 1 ]; then
        echo "     遊戲已經啟動過了,收到一半的 log 留在:$LOG"
        echo "     那份不完整,分析也沒跑,不要拿它下結論。"
    elif [ "$LOG_STATE" = "created" ] || [ "$LOG_CREATED" -eq 1 ]; then
        echo "     遊戲還沒啟動,只有一個空的 log 檔:$LOG"
    elif [ "$LOG_STATE" = "creating" ]; then
        echo "     中斷時正在建立 log 檔:$LOG_CAND"
        echo "     那個檔可能已經建好了(是空的),自己看一眼再決定要不要刪。"
    else
        echo "     什麼都還沒建立。"
    fi
    echo "     這支腳本從頭到尾都沒有寫入遊戲資料夾裡的任何檔案。"
    echo ""
}

on_interrupt() {
    if [ "$INT_DEFER" -eq 1 ]; then
        # 正在不可中斷區裡:先記著,等 end_uninterruptible 再處理。
        INT_PENDING=1
        return 0
    fi
    interrupt_report
    exit 130
}

# 把資料夾那一段解成真實絕對路徑(cd 進去再 pwd -P,連 .. 跟資料夾符號連結一起解掉)
canon_dir() {
    local d
    d=$(cd "$1" 2>/dev/null && pwd -P) || return 1
    [ -n "$d" ] || return 1
    printf '%s\n' "$d"
}

# 逐層解開最後一段的符號連結,最多 8 層;解不完(有循環)就失敗。
resolve_symlink() {
    local p="$1" n=0 target dir
    while [ -L "$p" ] && [ "$n" -lt 8 ]; do
        target=$(readlink "$p") || return 1
        case "$target" in
            /*) p="$target" ;;
            *)  dir=$(dirname "$p"); p="$dir/$target" ;;
        esac
        n=$((n + 1))
    done
    if [ -L "$p" ]; then return 1; fi
    printf '%s\n' "$p"
}

wine_basename_ok() {
    local b="$1" n
    for n in $WINE_BASENAMES; do
        if [ "$b" = "$n" ]; then return 0; fi
    done
    return 1
}

# 白名單:只認套件管理員與 Wine 系 app 套件的安裝位置。
# 遊戲資料夾、下載資料夾、隨身碟一律不在裡面 —— 那正是懶人包會夾帶東西的地方。
wine_dir_allowed() {
    local d="$1" app
    case "$d" in
        /opt/homebrew/*|/usr/local/*|/opt/local/*) return 0 ;;
        /usr/bin|/usr/bin/*) return 0 ;;
        /usr/lib/wine|/usr/lib/wine/*|/usr/lib64/wine|/usr/lib64/wine/*) return 0 ;;
        /opt/wine-stable/*|/opt/wine-devel/*|/opt/wine-staging/*) return 0 ;;
        "$HOME"/Library/"Application Support"/com.isaacmarovitz.Whisky/*) return 0 ;;
        "$HOME"/Library/"Application Support"/Whisky/*) return 0 ;;
        /Applications/*.app/*)
            # 只認名字裡有 wine / crossover / whisky 的 app 套件
            app="${d#/Applications/}"
            app="${app%%.app/*}"
            app=$(printf '%s' "$app" | tr '[:upper:]' '[:lower:]')
            case "$app" in
                *wine*|*crossover*|*whisky*) return 0 ;;
            esac
            return 1
            ;;
    esac
    return 1
}

# 收一條「宣稱是 Wine」的路徑,通過就把解析後的絕對路徑放進 WINE_VALIDATED,不通過就回非 0。
# 兩邊都要查:寫在檔案裡的那條路徑、以及解開符號連結之後真正會被執行的那個檔。
# 結果走全域變數不走 stdout —— 用 $(...) 接的話函式是在子行程裡跑,
# 被拒的理由會跟著子行程一起消失,畫面上就只剩一個冒號(這個坑實際踩過)。
validate_wine_bin() {
    local given="$1" resolved dir_given dir_real base_given base_real
    WINE_REJECT_REASON=""
    WINE_VALIDATED=""
    case "$given" in
        /*) ;;
        *) WINE_REJECT_REASON="不是絕對路徑"; return 1 ;;
    esac
    base_given=$(basename "$given")
    if ! wine_basename_ok "$base_given"; then
        WINE_REJECT_REASON="檔名不是 Wine 的執行檔名稱($base_given)"
        return 1
    fi
    dir_given=$(canon_dir "$(dirname "$given")") || {
        WINE_REJECT_REASON="那條路徑的資料夾不存在"
        return 1
    }
    if ! wine_dir_allowed "$dir_given"; then
        WINE_REJECT_REASON="不在允許的 Wine 安裝位置($dir_given)"
        return 1
    fi
    resolved=$(resolve_symlink "$given") || {
        WINE_REJECT_REASON="符號連結解不開(可能是循環)"
        return 1
    }
    base_real=$(basename "$resolved")
    if ! wine_basename_ok "$base_real"; then
        WINE_REJECT_REASON="符號連結指到的不是 Wine($base_real)"
        return 1
    fi
    dir_real=$(canon_dir "$(dirname "$resolved")") || {
        WINE_REJECT_REASON="符號連結指到的資料夾不存在"
        return 1
    }
    if ! wine_dir_allowed "$dir_real"; then
        WINE_REJECT_REASON="符號連結指到允許範圍外($dir_real)"
        return 1
    fi
    if [ ! -f "$dir_real/$base_real" ] || [ ! -x "$dir_real/$base_real" ]; then
        WINE_REJECT_REASON="不是可以執行的一般檔案"
        return 1
    fi
    WINE_VALIDATED="$dir_real/$base_real"
    return 0
}

# 第二個參數是「檔名」,不是路徑。帶 / 或 \ 或 .. 就有可能指到遊戲資料夾以外。
validate_exe_name() {
    local n="$1"
    EXE_REJECT_REASON=""
    case "$n" in
        "") EXE_REJECT_REASON="檔名是空的" ; return 1 ;;
        .|..) EXE_REJECT_REASON="「$n」不是檔名" ; return 1 ;;
        */*) EXE_REJECT_REASON="只能給檔名,不可以帶 /" ; return 1 ;;
        *\\*) EXE_REJECT_REASON="只能給檔名,不可以帶 \\" ; return 1 ;;
        *:*) EXE_REJECT_REASON="不可以帶磁碟機代號(:)" ; return 1 ;;
        -*) EXE_REJECT_REASON="不可以用 - 開頭" ; return 1 ;;
    esac
    return 0
}

# 建一個「一定是新的」檔:是符號連結就拒絕,已經存在也拒絕(set -C 走的是 O_EXCL,
# 不會跟著符號連結去截斷別的地方的檔案)。權限收成只有自己讀得到。
create_new_file() {
    local p="$1"
    CREATE_FAIL_REASON=""
    if [ -L "$p" ]; then CREATE_FAIL_REASON="symlink"; return 1; fi
    # 這個 -e 只是為了把「同名檔已經在」跟「建不出來」分開報,
    # 真正防搶跑的還是下面那個 set -C(O_EXCL);-e 本身是有空窗的。
    if [ -e "$p" ]; then CREATE_FAIL_REASON="exists"; return 1; fi
    ( set -C; : > "$p" ) 2>/dev/null || { CREATE_FAIL_REASON="cannot-create"; return 1; }
    chmod 600 "$p" 2>/dev/null || true
    return 0
}

# 真正要寫之前再看一眼目的檔是不是符號連結。
# 建檔時擋過一次,但從「建好」到「真的寫進去」中間還有一段時間,
# 而桌面是別人也碰得到的地方 —— 所以寫之前再確認一次。
assert_not_symlink() {
    local p="$1" what="$2"
    if [ -L "$p" ]; then
        echo ""
        echo "  ✗ ${what}是符號連結:$p"
        echo "     本工具不跟著連結寫,請把它換成真正的檔案。"
        echo ""
        return 1
    fi
    return 0
}

# 建 log 檔。檔名帶時間,同一秒內跑第二次會自動加序號。
# 兩種「同名」的處置不一樣:
#   · 同名的是一般檔案 → 換下一個序號(那是你自己上一輪跑出來的)
#   · 同名的是符號連結 → 直接停下來(那不是自己長出來的東西,不要繞過它)
# 建檔 + 登記包在不可中斷區裡,中斷時的說法才不會跟磁碟上的狀態對不上。
# 回傳:0 建好了 / 1 序號用完 / 2 遇到符號連結(訊息已經印出來了)
open_log_in() {
    local dir="$1" stamp="$2" seq=1 cand
    while [ "$seq" -le 50 ]; do
        if [ "$seq" -eq 1 ]; then
            cand="$dir/mvp_debug_$stamp.log"
        else
            cand="$dir/mvp_debug_${stamp}_$seq.log"
        fi
        LOG_CAND="$cand"
        LOG_STATE=creating
        begin_uninterruptible
        if create_new_file "$cand"; then
            LOG="$cand"
            LOG_CREATED=1
            LOG_STATE=created
        fi
        end_uninterruptible
        if [ "$LOG_STATE" = "created" ]; then return 0; fi
        LOG_STATE=none
        if [ "$CREATE_FAIL_REASON" = "symlink" ]; then
            assert_not_symlink "$cand" "log 檔"
            return 2
        fi
        seq=$((seq + 1))
    done
    LOG_STATE=none
    return 1
}

# 給 sed 用的跳脫(分隔符號用 |)
sed_escape() {
    printf '%s' "$1" | LC_ALL=C sed -e 's/[|\\.^$*[]/\\&/g'
}

# 產一份可以貼到網路上的遮蔽版:家目錄、帳號名稱、遊戲資料夾、
# Windows 的使用者資料夾都換成代號。原始那份不動。
sanitize_log() {
    local src="$1" dst="$2" gdir="$3"
    local user home_esc user_esc game_esc
    user=$(id -un 2>/dev/null || true)
    [ -n "$user" ] || user="${USER:-}"
    home_esc=$(sed_escape "$HOME")
    game_esc=$(sed_escape "$gdir")
    set -- -e "s|${game_esc}|<遊戲資料夾>|g" -e "s|${home_esc}|<家目錄>|g"
    # 帳號名稱太短就不換 —— 兩三個字母到處都是,換了會把 log 改得看不懂。
    if [ -n "$user" ] && [ ${#user} -ge 3 ]; then
        user_esc=$(sed_escape "$user")
        set -- "$@" -e "s|${user_esc}|<使用者>|g"
    fi
    set -- "$@" \
        -e 's|\([A-Za-z]:\\[Uu]sers\\\)[^\\ ]*|\1<使用者>|g' \
        -e 's|\([A-Za-z]:\\[Hh]ome\\\)[^\\ ]*|\1<使用者>|g' \
        -e 's|/Users/[^/ ]*|/Users/<使用者>|g' \
        -e 's|/home/[^/ ]*|/home/<使用者>|g'
    # 目的檔在真正寫入之前再確認一次不是符號連結(寫入一律不跟著連結走)。
    assert_not_symlink "$dst" "遮蔽版" || return 1
    LC_ALL=C sed "$@" "$src" >> "$dst" 2>/dev/null
}

# ═══ --selftest:每一道守門配一個餌,證明它真的會擋 ═══════════
# 這支是 shell,不是 Python:沒有 assert,也沒有「會把 assert 整個拿掉」的最佳化模式,
# 所以不存在「換個旗標跑就變假綠」的情況,也就沒有對應的守門可以加。
# 每一項都是明寫的 if / else,結果各自呼叫 st_ok / st_bad 累加 selftest_fail,
# 離開碼直接來自那個計數器 —— 沒有任何一項是「沒出聲就算過」。
selftest_fail=0
st_ok()   { printf '  ✅ %s\n' "$1"; }
st_bad()  { printf '  ❌ %s\n' "$1"; selftest_fail=$((selftest_fail + 1)); }
st_skip() { printf '  ⏭  %s\n' "$1"; }

# 靜態檢查小工具:某一行(整行逐字相同)在原始碼裡的行號。
# 用 grep -x -F(整行、當成固定字串)而不自己寫正規表示式:
# 這樣錨得死,而且呼叫它的那幾行自己(前面有縮排)不會被自己抓到。
# 找不到、或找到不只一行,都回非 0 並且什麼都不印 ——
# 「不只一行」代表這個錨已經不唯一,那種情況下比行號先後也沒意義。
src_line_no() {
    local want="$1" hits
    hits=$(grep -nxF "$want" "$0" 2>/dev/null | cut -d: -f1)
    [ -n "$hits" ] || return 1
    [ "$(printf '%s\n' "$hits" | wc -l | tr -d ' ')" = "1" ] || return 1
    printf '%s\n' "$hits"
}

run_selftest() {
    local sb marker out rc real_wine n state
    local fakehome_real whisky_bin
    local ln_guard ln_run ln_start ln_done ln_share ln_create
    sb=$(mktemp -d "${TMPDIR:-/tmp}/mvp_wine_log_selftest.XXXXXX") || return 1
    echo ""
    echo "  ═══ mvp_wine_log.sh 自我測試 ═══"
    echo "  沙盒:$sb"
    echo ""

    # ── 餌 1:資料夾外一支叫 wine-helper 的自製程式(舊版的 wine* 比對會放行)
    marker="$sb/BAIT_RAN"
    mkdir -p "$sb/evil"
    printf '#!/bin/sh\ntouch "%s"\n' "$marker" > "$sb/evil/wine-helper"
    chmod +x "$sb/evil/wine-helper"
    if validate_wine_bin "$sb/evil/wine-helper" >/dev/null 2>&1; then
        st_bad "餌 1:wine-helper 被放行了"
    else
        st_ok "餌 1:wine-helper 被擋($WINE_REJECT_REASON)"
    fi

    # ── 餌 2:名字剛好就叫 wine,但放在沙盒裡(舊版一樣會放行)
    cp "$sb/evil/wine-helper" "$sb/evil/wine"
    if validate_wine_bin "$sb/evil/wine" >/dev/null 2>&1; then
        st_bad "餌 2:沙盒裡的 wine 被放行了"
    else
        st_ok "餌 2:沙盒裡的 wine 被擋($WINE_REJECT_REASON)"
    fi

    # ── 餌 3:用 .. 從白名單裡穿出去
    if validate_wine_bin "/opt/homebrew/bin/../../..$sb/evil/wine" >/dev/null 2>&1; then
        st_bad "餌 3:.. 穿越被放行了"
    else
        st_ok "餌 3:.. 穿越被擋($WINE_REJECT_REASON)"
    fi

    # ── 餌 4:相對路徑
    if validate_wine_bin "wine" >/dev/null 2>&1; then
        st_bad "餌 4:相對路徑被放行了"
    else
        st_ok "餌 4:相對路徑被擋($WINE_REJECT_REASON)"
    fi

    # ── 餌 4b / 4c:白名單位置底下的東西,還要是「可以執行的一般檔案」
    # SPEC 第 7 節明寫的這道關卡,前面四個餌都測不到 —— 它們在「檔名 / 路徑前綴」
    # 就先被擋掉了,根本走不到 -f / -x 那一行(實測:把那個 if 整段刪掉,--selftest 照樣全綠)。
    # 做法:在沙盒的假 HOME 底下用 Whisky 那條白名單路徑,不需要碰任何系統目錄。
    # canon_dir 走的是 pwd -P,所以假 HOME 也要先解過一次 ——
    # macOS 的 $TMPDIR 在 /var/folders,而 /var 自己就是符號連結,不解會對不上白名單。
    mkdir -p "$sb/fakehome"
    fakehome_real=$(cd "$sb/fakehome" && pwd -P)
    whisky_bin="$fakehome_real/Library/Application Support/Whisky/Libraries/Wine/bin"
    mkdir -p "$whisky_bin"
    # 判斷結果走全域變數,所以用子行程時要自己把結果印出來再接。
    mkdir -p "$whisky_bin/wine64"
    out=$( HOME="$fakehome_real"
           if validate_wine_bin "$whisky_bin/wine64"; then printf 'PASS|%s' "$WINE_VALIDATED"
           else printf 'REJECT|%s' "$WINE_REJECT_REASON"; fi )
    case "$out" in
        REJECT*) st_ok "餌 4b:白名單裡一個叫 wine64 的「資料夾」被擋(${out#REJECT|})" ;;
        *)       st_bad "餌 4b:白名單裡叫 wine64 的資料夾被當成 Wine 放行了" ;;
    esac
    rmdir "$whisky_bin/wine64"
    printf '#!/bin/sh\ntouch "%s"\n' "$marker" > "$whisky_bin/wine64"
    chmod 644 "$whisky_bin/wine64"
    out=$( HOME="$fakehome_real"
           if validate_wine_bin "$whisky_bin/wine64"; then printf 'PASS|%s' "$WINE_VALIDATED"
           else printf 'REJECT|%s' "$WINE_REJECT_REASON"; fi )
    case "$out" in
        REJECT*) st_ok "餌 4c:白名單裡沒有執行位元的 wine64 被擋(${out#REJECT|})" ;;
        *)       st_bad "餌 4c:白名單裡 chmod 644 的 wine64 被放行了" ;;
    esac
    # 陰性對照:同一個位置、一般檔、有執行位元 → 必須通過,不然 4b / 4c 的綠是假的
    # (整道關卡壞死也會讓 4b / 4c 變綠)。
    chmod 755 "$whisky_bin/wine64"
    out=$( HOME="$fakehome_real"
           if validate_wine_bin "$whisky_bin/wine64"; then printf 'PASS|%s' "$WINE_VALIDATED"
           else printf 'REJECT|%s' "$WINE_REJECT_REASON"; fi )
    case "$out" in
        PASS*) st_ok "陰性對照:白名單裡可執行的一般檔通過 → ${out#PASS|}" ;;
        *)     st_bad "陰性對照:白名單裡正常的 wine64 被誤擋(${out#REJECT|})" ;;
    esac
    rm -f "$whisky_bin/wine64"
    # 這三項從頭到尾只做判斷。餌的內容是「跑起來就會留下記號」的,記號不可以出現。
    if [ -e "$marker" ]; then
        st_bad "餌 4b/4c:驗證過程中那支假 wine 被執行了"
    else
        st_ok "餌 4b/4c:整段只做判斷,那支假 wine 一次都沒有被執行"
    fi

    # ── 陰性對照:真的 Wine 必須通過(不然這道守門是把所有人都擋住)
    real_wine=""
    for n in /opt/homebrew/bin/wine64 /opt/homebrew/bin/wine \
             /usr/local/bin/wine64 /usr/local/bin/wine; do
        if [ -x "$n" ]; then real_wine="$n"; break; fi
    done
    if [ -z "$real_wine" ]; then
        st_skip "陰性對照:這台沒裝 Wine,跳過(不能因此說守門是對的)"
    elif validate_wine_bin "$real_wine"; then
        st_ok "陰性對照:$real_wine 通過 → $WINE_VALIDATED"
    else
        st_bad "陰性對照:真的 Wine 被擋了($WINE_REJECT_REASON)"
    fi

    # ── 執行檔檔名
    for n in "../mvp2005.exe" "..\\mvp2005.exe" "/etc/passwd" ".." "-rf" "C:mvp2005.exe" ""; do
        if validate_exe_name "$n"; then
            st_bad "檔名守門:「$n」被放行了"
        else
            st_ok "檔名守門:「$n」被擋($EXE_REJECT_REASON)"
        fi
    done
    for n in "mvp2005.exe" "mvp2005 - 4GB.exe"; do
        if validate_exe_name "$n"; then
            st_ok "檔名守門:「$n」通過(正常檔名不能被誤擋)"
        else
            st_bad "檔名守門:正常檔名「$n」被誤擋"
        fi
    done

    # ── 餌 5:log 目的檔先被換成指向沙盒外的符號連結
    printf 'OUTSIDE\n' > "$sb/outside.txt"
    ln -s "$sb/outside.txt" "$sb/link.log"
    if create_new_file "$sb/link.log"; then
        st_bad "餌 5:符號連結被當成新檔建立"
    elif [ "$(cat "$sb/outside.txt")" = "OUTSIDE" ]; then
        st_ok "餌 5:符號連結被擋,外面那個檔一個字都沒變"
    else
        st_bad "餌 5:外面那個檔被動到了"
    fi

    # ── 餌 6:已經存在的普通檔不可以被截斷
    printf 'KEEP\n' > "$sb/exists.log"
    if create_new_file "$sb/exists.log"; then
        st_bad "餌 6:既有檔被當成新檔"
    elif [ "$(cat "$sb/exists.log")" = "KEEP" ]; then
        st_ok "餌 6:既有檔沒被截斷"
    else
        st_bad "餌 6:既有檔被截斷了"
    fi

    # ── 正常建檔:要成功,而且權限 600
    if create_new_file "$sb/fresh.log"; then
        n=$(ls -l "$sb/fresh.log" | cut -c1-10)
        if [ "$n" = "-rw-------" ]; then
            st_ok "建檔:新檔建得起來,權限 $n"
        else
            st_bad "建檔:權限是 $n,不是 -rw-------"
        fi
    else
        st_bad "建檔:正常的新檔建不起來"
    fi

    # ── 遮蔽:家目錄與帳號名稱不可以留在可回報版裡
    # 家目錄故意設成沙盒裡的一個假路徑,不是真的家目錄 ——
    # 不然「把家目錄路徑換掉」那一條會順手把家目錄也蓋掉,這個餌就永遠亮不起來。
    # (反向測試證過:用真 $HOME 時把家目錄那一條拿掉,測試照樣全綠。)
    mkdir -p "$sb/fakehome"
    {
        printf 'wine: cannot find %s/Desktop/x\n' "$sb/fakehome"
        printf 'trace:C:\\users\\%s\\Temp\\a.log\n' "someoneelse"
        printf 'unix path /Users/%s/Games\n' "someoneelse"
        printf 'logged in as %s at boot\n' "$(id -un)"
        printf 'plain line without anything\n'
    } > "$sb/raw.log"
    : > "$sb/clean.log"
    ( HOME="$sb/fakehome"; sanitize_log "$sb/raw.log" "$sb/clean.log" "$sb/game" )
    if LC_ALL=C grep -qF "$sb/fakehome" "$sb/clean.log"; then
        st_bad "遮蔽:家目錄還在"
    elif LC_ALL=C grep -qF "$(id -un)" "$sb/clean.log"; then
        st_bad "遮蔽:帳號名稱還在"
    elif LC_ALL=C grep -qF "someoneelse" "$sb/clean.log"; then
        st_bad "遮蔽:Windows / Unix 使用者資料夾裡的名字還在"
    elif [ "$(wc -l < "$sb/raw.log")" != "$(wc -l < "$sb/clean.log")" ]; then
        st_bad "遮蔽:行數對不上(有整行被吃掉)"
    else
        st_ok "遮蔽:家目錄、帳號名稱、使用者資料夾都不見了,行數一樣"
    fi

    # ── 餌 11:遮蔽版的目的檔被換成指向沙盒外的符號連結 → 一個位元組都不可以寫過去
    printf 'OUTSIDE11\n' > "$sb/outside11.txt"
    ln -s "$sb/outside11.txt" "$sb/dst11.log"
    if ( sanitize_log "$sb/raw.log" "$sb/dst11.log" "$sb/game" ) >/dev/null 2>&1; then
        st_bad "餌 11:遮蔽版寫進了符號連結"
    elif [ "$(cat "$sb/outside11.txt")" != "OUTSIDE11" ]; then
        st_bad "餌 11:外面那個檔被寫到了"
    else
        st_ok "餌 11:遮蔽版拒絕寫進符號連結,外面那個檔一個字都沒變"
    fi
    # 陰性對照:目的檔是一般檔的時候,遮蔽版還是要寫得出來(不然餌 11 的綠是假的)
    : > "$sb/dst11ok.log"
    if ( sanitize_log "$sb/raw.log" "$sb/dst11ok.log" "$sb/game" ) >/dev/null 2>&1 \
       && [ -s "$sb/dst11ok.log" ]; then
        st_ok "陰性對照:目的檔是一般檔時遮蔽版寫得出來"
    else
        st_bad "陰性對照:一般檔也寫不出遮蔽版"
    fi

    # ── 端到端:整支腳本吃一個夾帶 .wine_path 的假遊戲資料夾
    if [ -r "$0" ]; then
        mkdir -p "$sb/game/launcher" "$sb/fakehome"
        _ld="$sb/game/launcher"; printf '%s\n' "$sb/evil/wine-helper" > "$_ld/.wine_path"
        rm -f "$marker"
        out=$(HOME="$sb/fakehome" bash "$0" "$sb/game" 2>&1); rc=$?
        if [ -e "$marker" ]; then
            st_bad "端到端:夾帶的程式被執行了"
        elif [ "$rc" -eq 0 ]; then
            st_bad "端到端:應該非 0 離開,實際是 0"
        elif ! printf '%s' "$out" | grep -q "不執行它"; then
            st_bad "端到端:離開碼 $rc,但沒印出「不執行它」"
        elif ! printf '%s' "$out" | grep -q "不合格:..*"; then
            # 冒號後面必須真的有理由。理由存在全域變數裡,一旦有人把呼叫改回
            # WINE_BIN=$(validate_wine_bin ...),函式就跑在子行程,理由會消失,
            # 畫面上只剩一個冒號 —— 這個坑實際踩過,所以留一個餌守著。
            st_bad "端到端:被拒了,但沒說理由(冒號後面是空的)"
        else
            st_ok "端到端:夾帶的 .wine_path 被拒(有寫理由),離開碼 $rc,餌沒被執行"
        fi

        # CLI 沒有被改壞
        HOME="$sb/fakehome" bash "$0" --help >/dev/null 2>&1
        if [ $? -eq 0 ]; then st_ok "CLI:--help 仍然是 0"; else st_bad "CLI:--help 不是 0"; fi
        HOME="$sb/fakehome" bash "$0" >/dev/null 2>&1
        if [ $? -eq 1 ]; then st_ok "CLI:沒給參數仍然是 1"; else st_bad "CLI:沒給參數不是 1"; fi
    else
        st_skip "端到端:讀不到自己($0),跳過"
    fi

    # ── 餌 7:桌面上先被放了一個同名的符號連結 → 整個建檔要停下來,不可以繞過去
    mkdir -p "$sb/desk"
    printf 'OUTSIDE7\n' > "$sb/outside7.txt"
    ln -s "$sb/outside7.txt" "$sb/desk/mvp_debug_BAIT7.log"
    out=$( ( open_log_in "$sb/desk" "BAIT7" ) 2>&1 ); rc=$?
    if [ "$rc" -eq 0 ]; then
        st_bad "餌 7:桌面上的符號連結被當成 log 檔用了"
    elif [ "$(cat "$sb/outside7.txt")" != "OUTSIDE7" ]; then
        st_bad "餌 7:外面那個檔被寫到了"
    elif ! printf '%s' "$out" | grep -q "符號連結"; then
        st_bad "餌 7:擋下來了,但沒說是符號連結"
    elif [ -e "$sb/desk/mvp_debug_BAIT7_2.log" ]; then
        st_bad "餌 7:繞過去用了下一個序號(應該停下來)"
    else
        st_ok "餌 7:桌面上的符號連結被擋(離開碼 $rc),外面那個檔沒變,也沒繞道"
    fi

    # ── 陰性對照:同一個資料夾、沒有餌的時候必須建得起來,而且權限 600
    out=$( ( open_log_in "$sb/desk" "BAIT7OK" ) 2>&1 ); rc=$?
    if [ "$rc" -ne 0 ]; then
        st_bad "陰性對照:沒有餌的時候 log 也建不起來(離開碼 $rc)"
    elif [ ! -f "$sb/desk/mvp_debug_BAIT7OK.log" ]; then
        st_bad "陰性對照:回報建好了,但檔案不在"
    else
        n=$(ls -l "$sb/desk/mvp_debug_BAIT7OK.log" | cut -c1-10)
        if [ "$n" = "-rw-------" ]; then
            st_ok "陰性對照:沒有餌的時候建得起來,權限 $n"
        else
            st_bad "陰性對照:權限是 $n,不是 -rw-------"
        fi
    fi

    # ── 餌 7b:同名的是「一般檔」→ 要自動加序號(既有行為不可以被改壞),而且不覆蓋
    printf 'KEEP7B\n' > "$sb/desk/mvp_debug_BAIT7B.log"
    out=$( ( open_log_in "$sb/desk" "BAIT7B" ) 2>&1 ); rc=$?
    if [ "$rc" -ne 0 ]; then
        st_bad "餌 7b:同名一般檔應該加序號,實際離開碼 $rc"
    elif [ "$(cat "$sb/desk/mvp_debug_BAIT7B.log")" != "KEEP7B" ]; then
        st_bad "餌 7b:同名的一般檔被覆蓋了"
    elif [ ! -f "$sb/desk/mvp_debug_BAIT7B_2.log" ]; then
        st_bad "餌 7b:沒有建出 _2 那一份"
    else
        st_ok "餌 7b:同名一般檔沒被動到,自動改用 _2"
    fi

    # ── 餌 7c:登記要跟磁碟上的狀態一致 —— 建好了就是 created,被擋下就是 none
    state=$( ( open_log_in "$sb/desk" "BAIT7C" >/dev/null 2>&1
               printf '%s|%s|%s' "$LOG_STATE" "$LOG_CREATED" "$LOG" ) )
    if [ "$state" != "created|1|$sb/desk/mvp_debug_BAIT7C.log" ]; then
        st_bad "餌 7c:建好之後的登記不對($state)"
    else
        state=$( ( open_log_in "$sb/desk" "BAIT7" >/dev/null 2>&1
                   printf '%s|%s' "$LOG_STATE" "$LOG_CREATED" ) )
        if [ "$state" != "none|0" ]; then
            st_bad "餌 7c:被符號連結擋下之後還登記成建過了($state)"
        else
            st_ok "餌 7c:登記跟磁碟一致(建好=created、被擋=none)"
        fi
    fi

    # ── 餌 8:不可中斷區真的把 Ctrl+C 押後(不是當場斷在「建好但還沒登記」中間)
    # 這一段在主行程裡跑,$$ 一定是自己;$BASHPID 在 bash 3.2 沒有,不能用。
    # 如果押後壞掉,on_interrupt 會當場 exit 130,整個 --selftest 直接死掉 ——
    # 那是很吵的紅,不是假綠。(拿變體檔實測過:把 begin_uninterruptible 改成
    # 空的,--selftest 就停在這裡、離開碼 130、印不出總結。)
    trap on_interrupt INT
    begin_uninterruptible
    kill -INT $$
    n=1                      # 走得到這一行,代表沒有當場中斷
    rc="$INT_PENDING"        # 而且訊號真的被記下來了
    INT_DEFER=0
    INT_PENDING=0
    trap - INT
    if [ "$n" = "1" ] && [ "$rc" = "1" ]; then
        st_ok "餌 8:不可中斷區裡的 Ctrl+C 被押後(記下來了,沒有當場斷)"
    else
        st_bad "餌 8:押後沒生效(到達=$n、記下=$rc)"
    fi

    # ── 餌 8b:離開不可中斷區之後,on_interrupt 要照常中斷 —— 離開碼 130 + 印報告
    out=$( ( LOG=""; LOG_CAND=""; LOG_STATE=none; LOG_CREATED=0
             GAME_STARTED=0; SHARE_STATE=none; INT_DEFER=0
             on_interrupt
             printf 'NOT_REACHED\n' ) 2>&1 ); rc=$?
    if [ "$rc" -ne 130 ]; then
        st_bad "餌 8b:中斷的離開碼是 $rc,不是 130"
    elif printf '%s' "$out" | grep -q "NOT_REACHED"; then
        st_bad "餌 8b:on_interrupt 沒有真的離開"
    elif ! printf '%s' "$out" | grep -q "什麼都還沒建立"; then
        st_bad "餌 8b:中斷了卻沒印出狀態報告"
    else
        st_ok "餌 8b:不在不可中斷區時照常中斷,離開碼 130 並印出報告"
    fi

    # ── 餌 9:三態 —— 「正在建立」不可以說成「什麼都還沒建立」
    out=$( ( LOG=""; LOG_CAND="$sb/desk/正在建.log"; LOG_STATE=creating
             LOG_CREATED=0; GAME_STARTED=0; SHARE_STATE=none
             interrupt_report ) 2>&1 )
    if printf '%s' "$out" | grep -q "什麼都還沒建立"; then
        st_bad "餌 9:正在建立的時候還是說「什麼都還沒建立」"
    elif ! printf '%s' "$out" | grep -qF "$sb/desk/正在建.log"; then
        st_bad "餌 9:沒有印出正在建立的那個檔名"
    else
        st_ok "餌 9:中斷時「正在建立」會照實說,而且印出檔名"
    fi

    # ── 餌 9b:遮蔽版那一態排在遊戲已啟動前面(兩個條件會同時成立,排錯就永遠說不到)
    out=$( ( LOG="$sb/desk/a.log"; LOG_CAND="$LOG"; LOG_STATE=created; LOG_CREATED=1
             GAME_STARTED=1
             SHARE_CAND="$sb/desk/a_可回報.log"; SHARE_STATE=creating
             interrupt_report ) 2>&1 )
    if ! printf '%s' "$out" | grep -qF "$sb/desk/a_可回報.log"; then
        st_bad "餌 9b:正在建遮蔽版,卻被「遊戲已經啟動」那一句蓋掉了"
    else
        st_ok "餌 9b:正在建遮蔽版時會照實說,並印出那個檔名"
    fi

    # ── 餌 9c:遮蔽版寫好了但還沒複驗就被中斷 —— 要講明「這一份沒驗過,別貼」
    out=$( ( LOG="$sb/desk/a.log"; LOG_CAND="$LOG"; LOG_STATE=created; LOG_CREATED=1
             GAME_STARTED=1
             SHARE="$sb/desk/a_可回報.log"; SHARE_CAND="$SHARE"; SHARE_STATE=unverified
             interrupt_report ) 2>&1 )
    if ! printf '%s' "$out" | grep -qF "$sb/desk/a_可回報.log"; then
        st_bad "餌 9c:沒驗過的遮蔽版被「遊戲已經啟動」那一句蓋掉了"
    elif ! printf '%s' "$out" | grep -q "不要直接貼出去"; then
        st_bad "餌 9c:有講到那個檔,但沒說它還沒驗過"
    else
        st_ok "餌 9c:中斷時會講明「遮蔽版還沒複驗,不要直接貼出去」"
    fi

    # ── 餌 9d:遊戲跑完了才中斷 —— 不可以再說「收到一半的 log」
    out=$( ( LOG="$sb/desk/a.log"; LOG_CAND="$LOG"; LOG_STATE=created; LOG_CREATED=1
             GAME_STARTED=1; GAME_DONE=1
             SHARE=""; SHARE_CAND=""; SHARE_STATE=none
             interrupt_report ) 2>&1 )
    if printf '%s' "$out" | grep -q "收到一半"; then
        st_bad "餌 9d:遊戲跑完了還說 log 只收到一半"
    elif ! printf '%s' "$out" | grep -q "log 收完整了"; then
        st_bad "餌 9d:沒說 log 是完整的"
    elif ! printf '%s' "$out" | grep -q "自己先遮掉"; then
        st_bad "餌 9d:沒提醒那一份還沒遮蔽"
    else
        st_ok "餌 9d:遊戲跑完後中斷,說法改成「log 完整、還沒遮蔽」"
    fi

    # ── 餌 9e:兩份都做完了才中斷 —— 要把兩個檔名都給出來,不可以說成半截
    out=$( ( LOG="$sb/desk/a.log"; LOG_CAND="$LOG"; LOG_STATE=created; LOG_CREATED=1
             GAME_STARTED=1; GAME_DONE=1
             SHARE="$sb/desk/a_可回報.log"; SHARE_CAND="$SHARE"; SHARE_STATE=created
             interrupt_report ) 2>&1 )
    if printf '%s' "$out" | grep -q "收到一半\|分析也沒跑"; then
        st_bad "餌 9e:兩份都做完了還說收到一半 / 分析沒跑"
    elif ! printf '%s' "$out" | grep -qF "$sb/desk/a_可回報.log"; then
        st_bad "餌 9e:沒把已經驗過的遮蔽版檔名給出來"
    else
        st_ok "餌 9e:兩份都完成時,中斷會照實說並給出兩個檔名"
    fi

    # ── 陰性對照:真的什麼都沒動的時候,還是要說「什麼都還沒建立」
    out=$( ( LOG=""; LOG_CAND=""; LOG_STATE=none; LOG_CREATED=0
             GAME_STARTED=0; GAME_DONE=0; SHARE_STATE=none
             interrupt_report ) 2>&1 )
    if printf '%s' "$out" | grep -q "什麼都還沒建立"; then
        st_ok "陰性對照:真的沒動的時候仍然說「什麼都還沒建立」"
    else
        st_bad "陰性對照:沒動的時候卻沒說「什麼都還沒建立」"
    fi

    # ── 餌 10:寫入前的符號連結複查
    ln -s "$sb/outside7.txt" "$sb/desk/link10"
    if assert_not_symlink "$sb/desk/link10" "測試檔" >/dev/null 2>&1; then
        st_bad "餌 10:符號連結被寫入前複查放行了"
    else
        printf 'x\n' > "$sb/desk/plain10"
        if assert_not_symlink "$sb/desk/plain10" "測試檔" >/dev/null 2>&1; then
            st_ok "餌 10:寫入前複查擋連結、放行一般檔"
        else
            st_bad "陰性對照:一般檔被寫入前複查誤擋"
        fi
    fi

    # ── 中斷處理:trap 有沒有裝在原始碼裡(這一條是靜態檢查,不是實際按 Ctrl+C)
    # 樣式錨在行首 —— 不錨的話,這一行自己就含著那串字,grep 會抓到自己而永遠是綠的
    # (反向測試證過:把真正那一行 trap 拿掉,不錨的版本照樣全綠)。
    if [ -r "$0" ] && grep -q '^trap on_interrupt INT$' "$0"; then
        st_ok "中斷:原始碼裡有裝 INT 的 trap(靜態檢查)"
    else
        st_bad "中斷:找不到 INT 的 trap"
    fi

    # ── 主流程的守門與登記:靜態位置檢查 ────────────────────────
    # 為什麼要有這一段:下面四行都在「真的啟動遊戲」那條路上,--selftest 走不到,
    # 所以把它們刪掉,前面每一個餌都還是綠的(實測過四個變體檔,--selftest 全部 rc=0、
    # 0 ❌)。它們各自的「行為」前面已經有餌驗過(符號連結守門是餌 10、
    # 三態說法是餌 9 / 9b / 9c / 9d / 9e),這裡補的是「主流程有沒有在對的位置呼叫它們」,
    # 所以比的是行號先後,不只是「有沒有這一行」。
    # ⚠️ 這是靜態檢查。它證明那一行還在、而且排在對的一邊;
    #    它不證明中間有沒有被塞進別的東西。真正的中斷行為要靠端到端中斷掃描,
    #    而那個需要遊戲資料夾與一支長得像 wine 的執行檔,塞不進 --selftest。
    if [ ! -r "$0" ]; then
        st_skip "主流程靜態檢查:讀不到自己($0),跳過"
    else
        ln_run=$(src_line_no '( cd "$GAME_DIR" && "$WINE_BIN" "$EXE" ) >> "$LOG" 2>&1')
        ln_guard=$(src_line_no 'assert_not_symlink "$LOG" "log 檔" || exit 1')
        ln_start=$(src_line_no 'GAME_STARTED=1')
        ln_done=$(src_line_no 'GAME_DONE=1')
        ln_share=$(src_line_no 'SHARE_STATE=creating')
        ln_create=$(src_line_no 'if create_new_file "$SHARE_CAND"; then')
        if [ -z "$ln_run" ]; then
            st_bad "主流程:找不到唯一一行「啟動遊戲」(不見了,或變成兩行以上),後面幾項沒辦法比位置"
        else
            if [ -z "$ln_guard" ]; then
                st_bad "主流程:找不到唯一一行寫 log 之前的 assert_not_symlink 守門(不見了,或變成兩行以上)"
            elif [ "$ln_guard" -ge "$ln_run" ]; then
                st_bad "主流程:符號連結守門在第 $ln_guard 行,沒有排在啟動遊戲(第 $ln_run 行)前面"
            else
                st_ok "主流程:寫 log 之前先擋符號連結(第 $ln_guard 行,在啟動遊戲第 $ln_run 行之前)"
            fi
            if [ -z "$ln_start" ]; then
                st_bad "主流程:找不到唯一一行 GAME_STARTED=1(不見了,或變成兩行以上)"
            elif [ "$ln_start" -ge "$ln_run" ]; then
                st_bad "主流程:GAME_STARTED=1 在第 $ln_start 行,沒有排在啟動遊戲(第 $ln_run 行)前面"
            else
                st_ok "主流程:啟動遊戲之前先登記 GAME_STARTED=1(第 $ln_start 行)"
            fi
            if [ -z "$ln_done" ]; then
                st_bad "主流程:找不到唯一一行 GAME_DONE=1(不見了,或變成兩行以上)—— 少了它,遊戲跑完才中斷會謊稱 log 只收到一半"
            elif [ "$ln_done" -le "$ln_run" ]; then
                st_bad "主流程:GAME_DONE=1 在第 $ln_done 行,沒有排在遊戲跑完(第 $ln_run 行)後面"
            else
                st_ok "主流程:遊戲跑完之後才登記 GAME_DONE=1(第 $ln_done 行)"
            fi
        fi
        if [ -z "$ln_share" ] || [ -z "$ln_create" ]; then
            st_bad "主流程:找不到唯一一行 SHARE_STATE=creating 或建遮蔽版那一行(不見了,或變成兩行以上)—— 少了前者,寫到一半被中斷會謊稱還沒有遮蔽版"
        elif [ "$ln_share" -ge "$ln_create" ]; then
            st_bad "主流程:SHARE_STATE=creating 在第 $ln_share 行,沒有排在建遮蔽版(第 $ln_create 行)前面"
        else
            st_ok "主流程:建遮蔽版之前先登記 SHARE_STATE=creating(第 $ln_share 行)"
        fi
    fi

    rm -rf "$sb"
    echo ""
    if [ "$selftest_fail" -eq 0 ]; then
        echo "  ✅ 全部通過。"
        echo ""
        return 0
    fi
    echo "  ❌ 有 $selftest_fail 項沒過。"
    echo ""
    return 1
}

if [ "${1:-}" = "--selftest" ]; then
    run_selftest
    exit $?
fi

if [ $# -lt 1 ] || [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
    echo ""
    echo "  用法:bash mvp_wine_log.sh \"<遊戲資料夾>\" [執行檔檔名]"
    echo ""
    echo "  例:"
    echo "    bash mvp_wine_log.sh \"$HOME/MVP Baseball 2005\""
    echo "    bash mvp_wine_log.sh \"$HOME/MVP Baseball 2005\" \"mvp2005 - 4GB.exe\""
    echo ""
    echo "  遊戲資料夾 = 裡面有 mvp2005.exe 的那一層。"
    echo "  把資料夾拖進終端機視窗就會自動填路徑。"
    echo ""
    echo "  第二個參數只能是檔名,不可以帶路徑(不會去遊戲資料夾以外找)。"
    echo ""
    echo "  log 會寫到桌面;桌面不存在就寫到家目錄。"
    echo "  同名的檔已經在,會自動加序號;同名的是符號連結,就直接停下來不寫。"
    echo "  另外會產一份遮蔽版 mvp_debug_<...>_可回報.log,要貼到網路上請貼那一份。"
    echo ""
    echo "  Wine 只認標準安裝位置(Homebrew / MacPorts / /usr/bin / Wine 系 app 套件),"
    echo "  而且只看路徑前綴與檔名、是不是可執行的一般檔案 —— 不驗簽章、不看內容。"
    echo "  想換除錯旗標:WINEDEBUG_MODE=+seh bash mvp_wine_log.sh \"<遊戲資料夾>\""
    echo "  只驗守門不啟動遊戲:bash mvp_wine_log.sh --selftest"
    echo ""
    # 沒給參數是「用錯了」,--help 是「問對了」,離開碼要分開。
    if [ $# -lt 1 ]; then exit 1; fi
    exit 0
fi

GAME_DIR="$1"
EXE_NAME="${2:-mvp2005.exe}"

if [ ! -d "$GAME_DIR" ]; then
    echo ""
    echo "  ✗ 找不到這個資料夾:$GAME_DIR"
    echo "     第一個參數要給「裡面有 mvp2005.exe 的那一層」。"
    echo ""
    exit 1
fi

# 轉成絕對路徑:等一下要 cd 進遊戲資料夾再啟動遊戲,
# 相對路徑在 cd 之後就指不到了。
GAME_DIR=$(cd "$GAME_DIR" && pwd -P)

# 第二個參數是檔名,不是路徑 —— 帶 ../ 或磁碟機代號就會跑到遊戲資料夾以外。
if ! validate_exe_name "$EXE_NAME"; then
    echo ""
    echo "  ✗ 執行檔參數不合格:$EXE_REJECT_REASON"
    echo "     只給檔名就好,例如:\"mvp2005 - 4GB.exe\""
    echo ""
    exit 1
fi

LAUNCHER_DIR="$GAME_DIR/launcher"
WINE_PATH_FILE="$LAUNCHER_DIR/.wine_path"
# log 放桌面;有些人把桌面關掉或改名,那就退到家目錄。
LOG_DIR="$HOME/Desktop"
[ -d "$LOG_DIR" ] || LOG_DIR="$HOME"

echo ""
echo "  ═══ MVP Baseball 除錯訊息錄影 ═══"
echo ""

# 中斷(Ctrl+C)要說實話:錄到哪裡就是哪裡,而且從頭到尾沒動過遊戲資料夾。
# 說實話的機制(三態登記 / 不可中斷區 / interrupt_report)定義在檔案上半部,
# 因為 --selftest 也要拿它們來測。這裡只是把 trap 裝上去。
trap on_interrupt INT

# ── 找 Wine ────────────────────────────────────────────────
WINE_BIN=""
if [ -f "$WINE_PATH_FILE" ]; then
    # 這個純文字檔是啟動器寫的,而它的內容會被當成執行檔跑起來。
    # 別人做的懶人包只要夾帶一個 .wine_path,就等於夾帶了「要跑哪支程式」。
    # 所以只取第一行,而且解開符號連結之後的絕對路徑必須落在白名單裡
    # (Homebrew / MacPorts / /usr/bin / Wine 系 app 套件 / Linux 的 wine 目錄),
    # 檔名也要完全等於 wine、wine64 這一類 —— 光是「wine 開頭」不算。
    CLAIMED=$(head -1 "$WINE_PATH_FILE" | tr -d "\r")
    if [ -n "$CLAIMED" ]; then
        if validate_wine_bin "$CLAIMED"; then
            WINE_BIN="$WINE_VALIDATED"
        else
            WINE_BIN=""
            echo "  ⚠️  $WINE_PATH_FILE 這條路徑不合格:$WINE_REJECT_REASON"
            echo "     它指的是:$CLAIMED"
            echo "     為了安全起見不執行它,改用自動搜尋。"
            echo ""
        fi
    fi
fi
if [ -z "$WINE_BIN" ]; then
    # 這張清單是腳本自己寫死的(跟本站啟動器同一份),不吃遊戲資料夾裡的設定。
    for p in /opt/homebrew/bin/wine64 /usr/local/bin/wine64 \
             /opt/homebrew/bin/wine /usr/local/bin/wine \
             /opt/local/bin/wine64 /opt/local/bin/wine \
             "/Applications/CrossOver.app/Contents/SharedSupport/CrossOver/bin/wine" \
             "$HOME/Library/Application Support/com.isaacmarovitz.Whisky/Libraries/Wine/bin/wine64" \
             /opt/homebrew/opt/game-porting-toolkit/bin/wine64 \
             /usr/local/opt/game-porting-toolkit/bin/wine64 \
             /usr/bin/wine64 /usr/bin/wine; do
        if [ -x "$p" ] && validate_wine_bin "$p"; then
            WINE_BIN="$WINE_VALIDATED"
            break
        fi
        WINE_BIN=""
    done
fi
if [ -z "$WINE_BIN" ] || [ ! -x "$WINE_BIN" ]; then
    echo "  ✗ 找不到 Wine。請先跑過「啟動器.command」把 Wine 裝好。"
    echo ""
    exit 1
fi

EXE="$GAME_DIR/$EXE_NAME"
if [ -L "$EXE" ]; then
    echo "  ✗ $EXE_NAME 是一個符號連結,不是真的執行檔。"
    echo "     為了安全起見不跑它(它可能指到遊戲資料夾以外)。"
    echo ""
    exit 1
fi
if [ ! -f "$EXE" ]; then
    echo "  ✗ 找不到執行檔:$EXE"
    echo ""
    echo "  這個資料夾裡有的是:"
    ls "$GAME_DIR"/mvp2005*.exe 2>/dev/null | sed 's|.*/|      |'
    echo ""
    exit 1
fi

# log 檔名帶時間;同一秒內跑第二次會加序號。
# 建檔一律走 O_EXCL(set -C),而且先擋掉符號連結 ——
# 桌面上如果先被放了一個同名的符號連結,舊寫法的 > 會跟著它去截斷別的地方的檔案。
LOG_STAMP=$(date +%Y%m%d_%H%M%S)
open_log_in "$LOG_DIR" "$LOG_STAMP"
case $? in
    0) ;;
    2) exit 1 ;;
    *)
        echo "  ✗ 在 $LOG_DIR 建不出 log 檔。"
        echo "     請確認那個資料夾存在、可以寫入,而且沒有同名的符號連結。"
        echo ""
        exit 1
        ;;
esac

echo "  Wine    : $WINE_BIN"
echo "  執行檔  : $EXE_NAME"
echo "  記錄到  : $LOG"
echo ""
echo "  遊戲要開起來了。請照平常的方式進到會當機的那個組合"
echo "  (中文語系 + 大球場),讓它當給我們看。"
echo ""
echo "  當機或關掉遊戲之後,這個視窗會自己整理結果。"
echo "  ──────────────────────────────────────────────"
echo ""

# wineprefix 不存在就不要設 —— 本站的啟動器也是這樣做的:它同樣先確認
# 那個資料夾在不在,不在就不設,讓 Wine 用預設環境。硬指到一個不存在的
# 路徑,Wine 會另外開一個全新環境,那就不是你平常玩的那個,量到的也對不上。
if [ -d "$LAUNCHER_DIR/wineprefix" ]; then
    export WINEPREFIX="$LAUNCHER_DIR/wineprefix"
else
    echo "  ⚠️  找不到 $LAUNCHER_DIR/wineprefix,這一輪會用 Wine 的預設環境。"
    echo "     那跟你平常玩的環境不一樣,結果不一定對得上。"
    echo ""
fi
export WINEDEBUG="${WINEDEBUG_MODE:-+seh,+debugstr}"

# cd 進遊戲資料夾再啟動:遊戲是用相對路徑去找 data\ 的,
# 本站啟動器的兩個啟動點也都把工作目錄設成遊戲資料夾。
# 工作目錄不一樣,重現的就不是同一個當機。
# 遊戲的除錯訊息走 stderr,兩條都收。
# 這裡用 >> 不用 > :log 檔剛剛才用 O_EXCL 建好,再用 > 去截斷等於把守門白做了。
# 從建好到現在中間隔了一段(顯示訊息、設環境變數),寫之前再確認一次它還是一般檔案。
assert_not_symlink "$LOG" "log 檔" || exit 1
GAME_STARTED=1
( cd "$GAME_DIR" && "$WINE_BIN" "$EXE" ) >> "$LOG" 2>&1
GAME_DONE=1

echo ""
echo "  ──────────────────────────────────────────────"
echo "  遊戲結束了。整理中..."
echo ""

TOTAL=$(wc -l < "$LOG" | tr -d ' ')
echo "  log 總行數:$TOTAL"
echo ""

show() {
    local label="$1" pat="$2"
    local n
    n=$(grep -ac "$pat" "$LOG" 2>/dev/null || true)
    n=${n:-0}
    printf '  %-38s %s\n' "$label" "$n 次"
    if [ "$n" -gt 0 ]; then
        grep -a "$pat" "$LOG" | head -6 | sed 's/^/        /'
    fi
}

echo "  ═══ 這一輪到底有沒有抓到東西 ═══"
# 這裡只能放「遊戲自己印出來的字串」。曾經把 40010006 也放進來 —— 那是 Wine 的
# seh 頻道自己印的例外碼,只證明遊戲丟了訊息,不證明我們讀到了內容;
# 放進來會把下面那道「這一輪不算數」的保險關掉,反而得出相反的結論。
GAMEMSG=$(grep -acE "IOP initialized|SKU Mem|Beast memory" "$LOG" 2>/dev/null || true)
GAMEMSG=${GAMEMSG:-0}
printf '  %-38s %s\n' "遊戲自己送出的訊息" "$GAMEMSG 次"
echo ""
echo "  ═══ 關鍵訊息 ═══"
show "⭐ 記憶體不夠(OUT OF MEMORY)" "OUT OF MEMORY"
show "⭐ 池子剩多少(total free mem)" "total free mem"
show "記憶體池建立完(SKU Mem)"      "SKU Mem"
show "BEAST 池"                      "Beast memory"
show "名稱管理員載入量"              "Name manager loaded"
show "球場配額警告"                  "quota exceeded"
echo ""

echo "  ═══ 當機現場 ═══"
show "頁面錯誤(寫入位址 0)" "page fault on write"
show "未處理例外"           "Unhandled exception"
echo ""
echo "  暫存器(如果有抓到,edx 是關鍵):"
grep -a -A4 -E "dispatch_exception .*c0000005|Register dump|page fault" "$LOG" 2>/dev/null | head -14 | sed 's/^/      /'
echo ""

# ── 產一份可以貼到網路上的遮蔽版 ─────────────────────────────
# Wine 的訊息裡會有你的家目錄、帳號名稱、遊戲資料夾完整路徑。
# 原始那份留著自己看,要給別人的貼這一份。
SHARE=""
SHARE_CAND="${LOG%.log}_可回報.log"
# 「建好」跟「登記建好」中間不可以被 Ctrl+C 拆開,不然收尾會說成沒建過。
# creating 這一態要一路涵蓋到「遮蔽內容寫完」為止 —— 寫到一半被中斷,
# 桌面上那份是半截的,收尾必須講出來。
SHARE_STATE=creating
begin_uninterruptible
if create_new_file "$SHARE_CAND"; then
    SHARE="$SHARE_CAND"
fi
end_uninterruptible
SANITIZED=0
if [ -n "$SHARE" ]; then
    if sanitize_log "$LOG" "$SHARE" "$GAME_DIR"; then SANITIZED=1; fi
    # 寫完了,但還沒複驗 —— 這一段被中斷的話,那份檔不可以被當成「可以貼出去」。
    SHARE_STATE=unverified
else
    SHARE_STATE=none
fi
SHARE_OK=0
if [ -n "$SHARE" ] && [ -f "$SHARE" ] && [ "$SANITIZED" -eq 1 ]; then
    # 複驗:遮蔽版裡不可以再找得到家目錄或帳號名稱,行數也要跟原始那份一樣。
    ME=$(id -un 2>/dev/null || true)
    SHARE_OK=1
    if LC_ALL=C grep -qF "$HOME" "$SHARE" 2>/dev/null; then SHARE_OK=0; fi
    if [ -n "$ME" ] && [ ${#ME} -ge 3 ] && LC_ALL=C grep -qF "$ME" "$SHARE" 2>/dev/null; then SHARE_OK=0; fi
    if [ "$(wc -l < "$SHARE" | tr -d ' ')" != "$TOTAL" ]; then SHARE_OK=0; fi
fi
if [ "$SHARE_OK" -eq 1 ]; then
    SHARE_STATE=created
    echo "  ═══ 可以貼出去的那一份 ═══"
    echo "  已產生遮蔽版(家目錄、帳號名稱、遊戲資料夾都換成代號):"
    echo "  $SHARE"
    echo "  要貼到網路上、傳給別人,請用這一份;原始那份留在自己電腦。"
    echo "  ⚠️ 遮蔽是機械式取代,貼出去之前還是自己看一眼。"
    echo ""
else
    echo "  ═══ 可以貼出去的那一份 ═══"
    if [ -z "$SHARE" ]; then
        if [ "$CREATE_FAIL_REASON" = "symlink" ]; then
            echo "  ❌ 產不出遮蔽版:$SHARE_CAND 是符號連結,"
            echo "     本工具不跟著連結寫,請把它換成真正的檔案。"
        else
            echo "  ❌ 產不出遮蔽版:$SHARE_CAND 這個檔名建不起來"
            echo "     (可能已經有同名的檔佔著,那種檔一律不覆蓋)。"
        fi
    else
        begin_uninterruptible
        rm -f "$SHARE"
        SHARE=""
        SHARE_STATE=none
        end_uninterruptible
        echo "  ❌ 遮蔽版沒有通過複驗,已經刪掉,不留一份「以為安全」的檔。"
    fi
    echo "     log 本身沒事(在 $LOG),但裡面有你的家目錄與帳號名稱,"
    echo "     要貼出去請自己先把那些換掉。"
    echo ""
fi

echo "  ═══ 結論 ═══"
if grep -aq "OUT OF MEMORY" "$LOG" 2>/dev/null; then
    echo "  ✅ 直接抓到 OUT OF MEMORY。把 log 留著,照課程頁的回報格式回報。"
elif grep -aqi "bb55bb55" "$LOG" 2>/dev/null; then
    echo "  ✅ 抓到 0xBB55BB55 這個指紋(全檔只有配置失敗那條路在用)。"
    echo "     把 log 留著,照課程頁的回報格式回報。"
elif [ "$GAMEMSG" -eq 0 ]; then
    echo "  ⚠️  這一輪【不算數】。"
    echo "     遊戲自己的訊息一行都沒收到(連開機就會印的都沒有),"
    echo "     代表是攔截方式沒對上,不是遊戲沒印。"
    echo "     ❌ 不可以據此判斷「記憶體不是原因」。把 log 留著回報 —— 攔截方式要換。"
else
    echo "  ℹ️  有收到遊戲訊息,但沒有 OUT OF MEMORY 也沒有那個指紋。"
    echo "     這才算是「記憶體池不是原因」的證據。把 log 留著,照課程頁的回報格式回報。"
fi
echo ""
echo "  log 檔(原始,含本機路徑,自己留):$LOG"
if [ "$SHARE_OK" -eq 1 ]; then
    echo "  回報用(已遮蔽):$SHARE"
fi
echo ""

# 遮蔽沒過就以非 0 離開 —— 不可以印個 ❌ 然後假裝一切正常。
if [ "$SHARE_OK" -ne 1 ]; then
    exit 1
fi


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
