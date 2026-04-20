"""
puzzle_data.py
──────────────
50 道謎題資料庫（敘事推理、邏輯算術、語言諧音）
"""

PUZZLES: list[dict] = [
    # ── 第一部分：敘事推理（海龜湯）1-20 ─────────────────────────────────────
    {
        "id": "01", "category": "narrative", "category_label": "敘事推理",
        "question": "男子喝了一碗海龜湯，覺得味道不對，問店員這是海龜肉嗎？店員說是，男子就自殺了。為什麼？",
        "hint": "他曾在海上漂流過，糧食耗盡時，同伴拿了某樣東西煮湯給他喝，騙他說是海龜湯。",
        "answer": "男子曾遭遇船難在海上漂流，糧食耗盡。船員割下已死同伴的肉煮湯騙他是「海龜湯」讓他存活。多年後他吃到真正的海龜湯，才驚覺當年吃的是人肉，愧疚自殺。",
        "key_points": ["人肉", "船難", "同伴", "human flesh", "shipwreck"],
    },
    {
        "id": "02", "category": "narrative", "category_label": "敘事推理",
        "question": "男子看完病重見光明，搭火車回程經過隧道時卻跳車自殺。為什麼？",
        "hint": "他剛治好眼疾。火車進隧道的那一刻，車廂裡發生了什麼事？他看見了什麼（或沒看見什麼）？",
        "answer": "男子原是盲人，剛治好眼疾。火車進隧道時車廂全黑，他以為眼疾復發再次失明，絕望之下跳車自殺。",
        "key_points": ["以為復發", "隧道", "失明", "thought blind again", "darkness"],
    },
    {
        "id": "03", "category": "narrative", "category_label": "敘事推理",
        "question": "男子跳河救女友失敗。幾年後回到原址，老人說這條河從不長草，男子隨即自殺。為什麼？",
        "hint": "當年搜救時，他在水中抓到了某樣東西，但放手了。他以為那是水草。",
        "answer": "當年搜救時男子曾抓到「水草」但放手了。得知河裡沒有水草後，意識到當年抓到的是女友的頭髮，他親手放棄了救她的機會。",
        "key_points": ["頭髮", "水草", "放手", "hair", "let go"],
    },
    {
        "id": "04", "category": "narrative", "category_label": "敘事推理",
        "question": "妹妹在母親葬禮上對一男子一見鍾情。一個月後，妹妹殺了姊姊。為什麼？",
        "hint": "她想再見到那個男子。在什麼樣的場合，那個男子才會再次出現？",
        "answer": "妹妹想再辦一次葬禮，希望那位男子（親友）能再次出席，讓她有機會見到對方。",
        "key_points": ["葬禮", "再見到", "男子", "funeral", "see him again"],
    },
    {
        "id": "05", "category": "narrative", "category_label": "敘事推理",
        "question": "男子死在沙漠中，身旁散落行李，手中緊抓半根火柴。發生了什麼事？",
        "hint": "他和一群人同行，交通工具超重，需要犧牲一個人。他們用某種方式決定誰去死。",
        "answer": "他與同伴搭熱氣球遇故障須減重，大家抽籤決定由誰犧牲，他抽中半根短火柴，被推下熱氣球摔死。",
        "key_points": ["熱氣球", "抽籤", "短火柴", "hot-air balloon", "drew lots"],
    },
    {
        "id": "06", "category": "narrative", "category_label": "敘事推理",
        "question": "女子看房時，發現牆上有個洞，往裡看總是紅色的。房東說隔壁住著有「紅眼症」的人。那紅色是什麼？",
        "hint": "鄰居同時也在看著這個洞。你看著他，他也看著你。",
        "answer": "她看到的紅色是鄰居充血的眼球。鄰居也正透過同一個洞口跟她「四目相對」。",
        "key_points": ["眼球", "鄰居", "四目相對", "eyeball", "looking back"],
    },
    {
        "id": "07", "category": "narrative", "category_label": "敘事推理",
        "question": "深夜聽到類似「牛吃草」的聲音與撞門聲。隔天發現鄰居女子死在門口。發生了什麼事？",
        "hint": "她已經沒有手臂了。想想她是如何移動的，以及她用嘴在做什麼。",
        "answer": "鄰居丈夫殺妻並砍斷其四肢，斷臂的女子咬著草爬行求救（發出像牛吃草的聲音），最後爬到門口撞門求救，失血過多而亡。",
        "key_points": ["斷臂", "爬行", "咬草求救", "no arms", "crawling"],
    },
    {
        "id": "08", "category": "narrative", "category_label": "敘事推理",
        "question": "老王去理髮，問理髮師「你剪得怎樣？」理髮師說：「我剪的是頭髮不是臉。」老王為何沉默？",
        "hint": "理髮師在暗示什麼？換了髮型能改變什麼，但改變不了什麼？",
        "answer": "理髮師在諷刺老王長得醜，就算換了再好的髮型，也沒辦法改變臉的問題。",
        "key_points": ["嘲諷", "長相", "臉", "insult", "face"],
    },
    {
        "id": "09", "category": "narrative", "category_label": "敘事推理",
        "question": "我躺在床上看漆黑的直播，畫面越來越亮，我看見了自己的天花板，然後我死了。為什麼？",
        "hint": "你房間裡不只有你。有人藏在你床的旁邊，手裡拿著鏡頭。",
        "answer": "兇手正躲在主角床後進行直播。畫面變亮是因為兇手慢慢走向主角並將鏡頭對準上方（天花板），隨後殺害了主角。",
        "key_points": ["兇手", "床後", "直播", "killer", "hiding"],
    },
    {
        "id": "10", "category": "narrative", "category_label": "敘事推理",
        "question": "大哥病死後，三弟把二哥殺了。為什麼？",
        "hint": "三弟患有精神病。他一直習慣睡在兩個哥哥中間。大哥死了之後，他的左邊空了。",
        "answer": "三弟有精神病，他把二哥的屍體切半放在自己左右兩邊，幻想大哥還活著陪著他。",
        "key_points": ["精神病", "幻覺", "切半", "mental illness", "delusion"],
    },
    {
        "id": "11", "category": "narrative", "category_label": "敘事推理",
        "question": "小明躲在床底逃過屠殺，看見全家福那一刻意識到完蛋了。為什麼？",
        "hint": "兇手還在找人。全家福上面有什麼？",
        "answer": "全家福上有全家人的照片，兇手正按圖索驥，他看了照片就知道還少了一個孩子沒找到。",
        "key_points": ["全家人", "按圖索驥", "沒找到", "family photo", "tracking"],
    },
    {
        "id": "12", "category": "narrative", "category_label": "敘事推理",
        "question": "我吃了大西瓜，第二天我就死了。為什麼？",
        "hint": "他把西瓜籽吞下去了，他迷信肚子裡會長出什麼，非常恐慌，決定自己動手解決。",
        "answer": "主角吞了西瓜籽，迷信肚子會長西瓜，極度恐懼之下自己剖腹取籽，失血過多而亡。",
        "key_points": ["西瓜籽", "剖腹", "迷信", "seeds", "cut open"],
    },
    {
        "id": "13", "category": "narrative", "category_label": "敘事推理",
        "question": "媽媽推著我進電梯，門關上後，我再也無法去上學了。為什麼？",
        "hint": "電梯的門關上之後，又開了。你當時在低頭滑手機，沒有注意到。",
        "answer": "電梯門再次開了，「我」低頭玩手機沒注意，抬頭看見門外的兇手把媽媽殺了，目睹後留下心理創傷。",
        "key_points": ["門再開", "目睹", "兇手殺媽媽", "doors reopened", "witnessed murder"],
    },
    {
        "id": "14", "category": "narrative", "category_label": "敘事推理",
        "question": "保險推銷員安慰掛鑰匙的女孩，隔天女孩赤裸死在街頭，鑰匙不見了。為什麼？",
        "hint": "他的職業是賣保險的。如果家長覺得住家不安全，他們會做什麼？",
        "answer": "保險員為了讓家長恐懼並購買保險，故意殺害女孩並拿走鑰匙，製造「家門不安全」的假象來推銷保險。",
        "key_points": ["推銷保險", "製造恐懼", "拿走鑰匙", "insurance", "staged fear"],
    },
    {
        "id": "15", "category": "narrative", "category_label": "敘事推理",
        "question": "盲人團體在荒野求生獲救後，吹完生日蠟燭時，主角殺了所有人。為什麼？",
        "hint": "他們曾約定：糧食耗盡時，每人各斷一條手臂供食。吹完蠟燭，大家開始鼓掌，主角聽出了不對勁。",
        "answer": "吹蠟燭時主角聽到大家拍掌都是兩隻手的聲音，才發現只有自己真的被騙斷了臂，憤而殺人。",
        "key_points": ["斷臂", "拍手聲", "被騙", "clapping", "one arm"],
    },
    {
        "id": "16", "category": "narrative", "category_label": "敘事推理",
        "question": "夫妻享用晚餐，嬰兒在旁睡覺，隔天母子都死了。為什麼？",
        "hint": "丈夫在湯裡放了東西。妻子吃完飯之後，做了一件很普通的媽媽會做的事。",
        "answer": "丈夫在湯裡下毒想殺妻，妻子喝完後去哺母乳，毒素透過母乳傳給嬰兒，母子雙亡。",
        "key_points": ["下毒", "母乳", "毒素傳嬰兒", "poison", "breastfed"],
    },
    {
        "id": "17", "category": "narrative", "category_label": "敘事推理",
        "question": "男子看報紙後衝到頂樓開燈，再跳下自殺。為什麼？",
        "hint": "他有一份非常重要的工作，負責在夜晚點亮某個燈，讓船隻能夠安全航行。",
        "answer": "男子是燈塔管理員，報紙上的新聞說因燈塔未點亮導致重大船難，他自責趕緊補開燈後，畏罪自殺。",
        "key_points": ["燈塔", "船難", "沒開燈", "lighthouse", "guilt"],
    },
    {
        "id": "18", "category": "narrative", "category_label": "敘事推理",
        "question": "父子車禍，父死子傷，外科醫生說：「這是我兒子，我不能開刀。」醫生是誰？",
        "hint": "不要先入為主地假設醫生的性別。",
        "answer": "外科醫生是傷者的母親。",
        "key_points": ["媽媽", "母親", "mother"],
    },
    {
        "id": "19", "category": "narrative", "category_label": "敘事推理",
        "question": "男子求一杯水，店員突然拿槍指他，男子說謝謝後離開。為什麼？",
        "hint": "男子有一種讓他很困擾的身體狀況，可以用突然的驚嚇來治好。",
        "answer": "男子有嚴重打嗝問題，店員拔槍是為了嚇他以治好打嗝，男子被嚇好後表示感謝。",
        "key_points": ["打嗝", "嚇治打嗝", "hiccups", "frightened"],
    },
    {
        "id": "20", "category": "narrative", "category_label": "敘事推理",
        "question": "男子淋雨全身濕透，但頭上沒有一根頭髮濕了。為什麼？",
        "hint": "仔細看他的頭。",
        "answer": "因為他是禿頭，頭上根本沒有頭髮。",
        "key_points": ["禿頭", "沒頭髮", "bald"],
    },

    # ── 第二部分：邏輯與算術 21-30 ───────────────────────────────────────────
    {
        "id": "21", "category": "logic", "category_label": "邏輯算術",
        "question": "門外有三個開關控制房間內同一盞燈，你只能進門一次，如何確認哪個開關控制那盞燈？",
        "hint": "燈泡不只會亮，開了一段時間之後也會變熱。利用這個特性可以區分三個開關。",
        "answer": "打開 1 號開關等 5 分鐘後關掉，再打開 2 號。進門：燈亮著是 2 號；燈不亮但燈泡熱的是 1 號；燈不亮且燈泡涼的是 3 號。",
        "key_points": ["熱燈泡", "開關一段時間再關", "warm bulb", "heat"],
    },
    {
        "id": "22", "category": "logic", "category_label": "邏輯算術",
        "question": "12 顆球中有 1 顆重量不同（不知輕重），用天平只能秤三次，如何找出它？",
        "hint": "先把球分成三組，各 4 顆。第一次秤兩組，結果會告訴你異球在哪一組。",
        "answer": "將球分三組各 4 顆，前兩組放上天平。若平衡，異球在第三組；若不平衡則縮小範圍，再利用排除法，3 次內可確定異球。",
        "key_points": ["分三組", "三次", "排除法", "three groups", "elimination"],
    },
    {
        "id": "23", "category": "logic", "category_label": "邏輯算術",
        "question": "四人過橋，速度分別為 1、2、5、10 分鐘，只有一隻手電筒，一次最多兩人。最快幾分鐘全部過橋？",
        "hint": "關鍵技巧：讓最慢的兩個人一起過，讓最快的人負責來回送手電筒。",
        "answer": "17 分鐘。步驟：1+2 過（2分）→ 1 回（1分）→ 5+10 過（10分）→ 2 回（2分）→ 1+2 過（2分），合計 17 分鐘。",
        "key_points": ["17", "17分鐘", "17 minutes"],
    },
    {
        "id": "24", "category": "logic", "category_label": "邏輯算術",
        "question": "盲人需要各吃一顆紅色和藍色藥丸保命，桌上混有 2 顆紅和 2 顆藍，如何確保各吃到一顆？",
        "hint": "不需要分辨顏色。試著把每一顆藥丸都切開。",
        "answer": "將每一顆藥丸都對半切開，分成兩堆，各吃一堆。這樣每堆都含有半顆紅和半顆藍，效果等同各吃一顆。",
        "key_points": ["對半切", "各切半", "分兩堆", "cut in half"],
    },
    {
        "id": "25", "category": "logic", "category_label": "邏輯算術",
        "question": "5 隻雞 5 天生 5 顆蛋，100 天要生 100 顆蛋，需要幾隻雞？",
        "hint": "先算出每隻雞每天的產蛋速率，答案可能出乎你意料地簡單。",
        "answer": "5 隻。每隻雞每 5 天生 1 顆蛋，速率不變，5 隻雞 100 天生 100 顆。",
        "key_points": ["5", "5隻", "5 hens"],
    },
    {
        "id": "26", "category": "logic", "category_label": "邏輯算術",
        "question": "10 公尺深的井，蝸牛白天爬 3 公尺，夜晚滑下 2 公尺，需要幾天才能爬出井口？",
        "hint": "注意：當蝸牛在白天到達井口時就出去了，那天晚上不會再滑下來。仔細算哪天會到達 10 公尺。",
        "answer": "8 天。前 7 天每天淨爬 1 公尺到達 7 公尺，第 8 天白天爬 3 公尺達到 10 公尺即出井，不再滑下。",
        "key_points": ["8", "8天", "8 days"],
    },
    {
        "id": "27", "category": "logic", "category_label": "邏輯算術",
        "question": "3 個人 3 分鐘吃 3 個蘋果，9 個人 9 分鐘可以吃幾個蘋果？",
        "hint": "先算出每個人每分鐘能吃幾個蘋果，再乘上人數和時間。",
        "answer": "27 個。每人每 3 分鐘吃 1 個，9 分鐘吃 3 個，9 人共吃 27 個。",
        "key_points": ["27"],
    },
    {
        "id": "28", "category": "logic", "category_label": "邏輯算術",
        "question": "狼、羊、白菜，只有人能划船且一次只載一樣，如何都安全送到對岸？（狼吃羊、羊吃白菜）",
        "hint": "第一步一定要先帶羊過去。途中你可能需要把某樣東西帶回來。",
        "answer": "帶羊過 → 回 → 帶狼（或白菜）過 → 帶羊回 → 帶白菜（或狼）過 → 回 → 帶羊過。",
        "key_points": ["先帶羊", "帶羊回來", "take sheep first"],
    },
    {
        "id": "29", "category": "logic", "category_label": "邏輯算術",
        "question": "時鐘的長針和短針一天內「完全」重疊幾次？",
        "hint": "注意題目說的是「完全」重疊。長針和短針的長度一樣嗎？",
        "answer": "0 次。因為長針和短針長度不同，永遠無法「完全」重疊，只能方向對齊，但不是完全重疊。",
        "key_points": ["0", "0次", "zero", "長度不同"],
    },
    {
        "id": "30", "category": "logic", "category_label": "邏輯算術",
        "question": "男子在一個沒有上鎖的房間裡使盡全力拉門，卻怎麼也打不開。為什麼？",
        "hint": "他一直在「拉」。如果拉不開，試試另一個方向？",
        "answer": "因為那是一扇推門，不是拉門。",
        "key_points": ["推門", "推開", "push door"],
    },

    # ── 第三部分：語言諧音與字謎 31-50 ──────────────────────────────────────
    {
        "id": "31", "category": "wordplay", "category_label": "語言諧音",
        "question": "小羊、小豬、小雞一起去便利商店，誰沒有被打？",
        "hint": "便利商店 24 小時「不打烊」，「烊」的台語念起來像哪個動物？",
        "answer": "小羊。因為便利商店 24 小時「不打烊（羊）」，「烊」諧音「羊」。",
        "key_points": ["不打烊", "小羊"],
    },
    {
        "id": "32", "category": "wordplay", "category_label": "語言諧音",
        "question": "蛤蠣放太久會變成什麼料理？",
        "hint": "「擺久」用台語講快一點，像什麼酒？",
        "answer": "白酒蛤蠣。「擺久（bái jiǔ）」諧音「白酒」。",
        "key_points": ["白酒", "擺久"],
    },
    {
        "id": "33", "category": "wordplay", "category_label": "語言諧音",
        "question": "為什麼鎖匠比大學生還有學問？",
        "hint": "鎖匠專門「研究鎖」，用中文說快一點，跟哪個學歷很像？",
        "answer": "因為鎖匠是「研究所（研究鎖）」的，諧音「研究所」畢業。",
        "key_points": ["研究所", "研究鎖"],
    },
    {
        "id": "34", "category": "wordplay", "category_label": "語言諧音",
        "question": "爸爸用 5G 網路，小明跟著用，小明變成了哪個成語？",
        "hint": "「學父 5G」念快一點，像哪個形容人學問淵博的四字成語？",
        "answer": "「學富五車（學父 5G）」。諧音成語「學富五車」。",
        "key_points": ["學富五車", "學父5G"],
    },
    {
        "id": "35", "category": "wordplay", "category_label": "語言諧音",
        "question": "為什麼警察都不是捲髮？",
        "hint": "警察的職責是「執法」，「執法」念起來像什麼髮型？",
        "answer": "因為警察是「執法（直髮）」人員，諧音「直髮」。",
        "key_points": ["執法", "直髮"],
    },
    {
        "id": "36", "category": "wordplay", "category_label": "語言諧音",
        "question": "天主睡不著的時候會數什麼？",
        "hint": "「天主數⋯⋯」念快一點，像什麼台灣知名的可愛動物動畫？",
        "answer": "數「車車」。「天主數車車」諧音「天竺鼠車車」（台灣知名動畫）。",
        "key_points": ["天竺鼠車車", "車車"],
    },
    {
        "id": "37", "category": "wordplay", "category_label": "語言諧音",
        "question": "獅子、老虎、斑馬，誰最愛亂買東西？",
        "hint": "台語說「隨便亂買」叫「黑白買」，哪個動物的外表剛好符合這兩個顏色？",
        "answer": "斑馬。台語「黑白買」就是斑馬的顏色（黑白條紋）。",
        "key_points": ["斑馬", "黑白買"],
    },
    {
        "id": "38", "category": "wordplay", "category_label": "語言諧音",
        "question": "第十一本書，猜一個成語。",
        "hint": "用英文念「Book eleven」，聽起來像哪個中文四字成語？",
        "answer": "「不可思議（Book 11）」。Book 11 → 不可思議。",
        "key_points": ["不可思議", "Book 11"],
    },
    {
        "id": "39", "category": "wordplay", "category_label": "語言諧音",
        "question": "看到英文字母 U 哭了，你會聯想到哪個品牌？",
        "hint": "把「U 你哭囉」念快一點，像哪個日本服飾品牌？",
        "answer": "Uniqlo（U 你哭囉）。",
        "key_points": ["Uniqlo", "U你哭囉"],
    },
    {
        "id": "40", "category": "wordplay", "category_label": "語言諧音",
        "question": "誰做的麵最失敗？",
        "hint": "「失敗的麵」用英文念念看，像哪位超級英雄？",
        "answer": "蜘蛛人（Spider-Man）。Spider-Man 諧音「失敗的麵」。",
        "key_points": ["蜘蛛人", "Spider-Man", "失敗的麵"],
    },
    {
        "id": "41", "category": "wordplay", "category_label": "語言諧音",
        "question": "鯊魚吃了綠豆會變成什麼？",
        "hint": "「鯊（shā）」和「沙（shā）」同音。綠豆加「沙」是什麼飲料？",
        "answer": "綠豆沙（殺）。鯊魚的「鯊」諧音「沙」，綠豆＋沙（鯊）＝綠豆沙。",
        "key_points": ["綠豆沙"],
    },
    {
        "id": "42", "category": "wordplay", "category_label": "語言諧音",
        "question": "狼掉進冰水裡會變成什麼？",
        "hint": "「冰狼（bīng láng）」念快一點，像什麼台灣常見的東西？",
        "answer": "「檳榔（冰狼）」。冰狼諧音檳榔。",
        "key_points": ["檳榔", "冰狼"],
    },
    {
        "id": "43", "category": "wordplay", "category_label": "語言諧音",
        "question": "忍者對池塘射了五支鏢，只中兩隻魚。為什麼？",
        "hint": "有三隻魚「閃鏢」了。「三支閃鏢」念快一點，像哪個台灣知名品牌？",
        "answer": "因為有三隻魚閃鏢（三支雨傘標），諧音知名品牌「三支雨傘標」。",
        "key_points": ["三支雨傘標", "閃鏢"],
    },
    {
        "id": "44", "category": "wordplay", "category_label": "語言諧音",
        "question": "有一隻熊（Bear）朝你走過來，猜一個成語。",
        "hint": "「有 Bear 而來」念成中文，像哪個描述做好準備的四字成語？",
        "answer": "「有備而來（有 Bear 而來）」。Bear 諧音「備」。",
        "key_points": ["有備而來"],
    },
    {
        "id": "45", "category": "wordplay", "category_label": "語言諧音",
        "question": "英文字母爆炸了會變成什麼？",
        "hint": "爆炸聲是「Boom」，「OK Boom」念快一點，像哪個常見的醫療用品？",
        "answer": "OK 繃（OK Boom）。Boom 諧音「繃」。",
        "key_points": ["OK繃", "OK Boom"],
    },
    {
        "id": "46", "category": "wordplay", "category_label": "字謎",
        "question": "七十二小時，猜一個中文字。",
        "hint": "一天有 24 小時，72 小時等於幾天？「日」的三疊字是什麼？",
        "answer": "「晶」字。72 小時 ÷ 24 = 3 天，三個「日」疊在一起就是「晶」。",
        "key_points": ["晶"],
    },
    {
        "id": "47", "category": "wordplay", "category_label": "字謎",
        "question": "有點自大，猜一個中文字。",
        "hint": "把「自」、「大」、「點」三個元素拼在一起，就是答案。",
        "answer": "「臭」字。由「自」在上、「大」在下，再加一個點，組成「臭」。",
        "key_points": ["臭"],
    },
    {
        "id": "48", "category": "wordplay", "category_label": "字謎",
        "question": "籠中鳥，猜一個古代人名。",
        "hint": "籠子代表被「關」住，鳥有「羽」毛，把這兩個字合起來。",
        "answer": "「關羽」。鳥（羽）被關在籠中 → 關＋羽＝關羽。",
        "key_points": ["關羽"],
    },
    {
        "id": "49", "category": "wordplay", "category_label": "語言諧音",
        "question": "Costco 鬧鬼，猜一個成語。",
        "hint": "Costco 的中文是「好市多」，鬧鬼要「磨」人，「好市多磨」念念看。",
        "answer": "「好事多磨（Costco 磨）」。好市多（Costco）＋磨＝好事多磨。",
        "key_points": ["好事多磨", "Costco磨"],
    },
    {
        "id": "50", "category": "wordplay", "category_label": "語言諧音",
        "question": "二、四、六、八跳下水，猜一個成語。",
        "hint": "2、4、6、8 全都是什麼數？這個數列中缺少了哪一種數？",
        "answer": "「無稽之談（無奇之談）」。2、4、6、8 全是偶數，沒有奇（稽）數。",
        "key_points": ["無稽之談", "沒有奇數", "no odd numbers"],
    },
]

# ── 查詢工具 ──────────────────────────────────────────────────────────────────
_id_map: dict = {p["id"]: p for p in PUZZLES}


def get_puzzle_by_id(puzzle_id: str):
    return _id_map.get(puzzle_id)


def get_all_ids() -> list:
    return [p["id"] for p in PUZZLES]
