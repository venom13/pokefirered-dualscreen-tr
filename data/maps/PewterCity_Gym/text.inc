PewterCity_Gym_Text_BrockIntro::
    .string "Demek geldin. Ben BROCK.\n"
    .string "PEWTER'ın SALON LİDERİYİM.\p"
    .string "Kaya gibi sert irade gücüm\n"
    .string "POKéMON'larımda bile belli.\p"
    .string "POKéMON'larımın hepsi kaya gibi serttir\n"
    .string "ve gerçek bir azme sahiptir.\p"
    .string "Doğru, POKéMON'larımın hepsi KAYA\n"
    .string "türü!\p"
    .string "Fuhaha! Kaybedeceğini bile bile bana\n"
    .string "meydan mı okuyacaksın?\p"
    .string "Seni bana meydan okumaya iten şey\n"
    .string "EĞİTMEN onurun.\p"
    .string "Pekala o zaman!\n"
    .string "En iyini göster!{PLAY_BGM}{MUS_ENCOUNTER_GYM_LEADER}$"

@ NOTE: This defeat text actually causes a buffer overflow. It's too long for the gDisplayedStringBattle
@ buffer that it's put into, and it stomps all over the gBattleTextBuffs after, as well as the otherwise
@ unused array after that, sFlickerArray. Perhaps that's the reason why said array exists.
PewterCity_Gym_Text_BrockDefeat::
    .string "Seni hafife aldım, bu yüzden kaybettim.\p"
    .string "Zaferinin kanıtı olarak sana bunu\n"
    .string "veriyorum…resmi POKéMON LİGİ KAYA\l"
    .string "ROZETİ.\p"
    .string "{FONT_NORMAL}{PLAYER}, BROCK'tan KAYA ROZETİ'ni\n"
    .string "aldı!{PAUSE_MUSIC}{PLAY_BGM}{MUS_OBTAIN_BADGE}{PAUSE 0xFE}{PAUSE 0x56}{RESUME_MUSIC}\p"
    .string "{FONT_MALE}KAYA ROZETİ'ne sahip olmak bile\n"
    .string "POKéMON'larını güçlendirir.\p"
    .string "Ayrıca savaş dışında FLAŞ hareketini\n"
    .string "kullanmanı sağlar.\p"
    .string "Tabii ki POKéMON'un kullanmak için FLAŞ\n"
    .string "hareketini bilmeli.$"

PewterCity_Gym_Text_TakeThisWithYou::
    .string "Dur!\n"
    .string "Bunu da yanına al.$"

PewterCity_Gym_Text_ReceivedTM39FromBrock::
    .string "{PLAYER}, BROCK'tan TM39 aldı.$"

PewterCity_Gym_Text_ExplainTM39::
    .string "TM, yani Teknik Makine, POKéMON için\n"
    .string "bir teknik içerir.\p"
    .string "TM kullanmak içindeki hareketi bir\n"
    .string "POKéMON'a öğretir.\p"
    .string "Bir TM yalnızca bir kez kullanılabilir.\p"
    .string "Bu yüzden kullanırken POKéMON'u\n"
    .string "dikkatle seç.\p"
    .string "Neyse…\n"
    .string "TM39'da KAYA MEZARI var.\p"
    .string "Rakibe kayalar fırlatır ve HIZINI\n"
    .string "düşürür.$"

PewterCity_Gym_Text_BrockPostBattle::
    .string "Bu koca dünyamızda her türlü EĞİTMEN\n"
    .string "var.\p"
    .string "POKéMON EĞİTMENİ olarak çok yetenekli\n"
    .string "görünüyorsun.\p"
    .string "O yüzden sana bir önerim var.\p"
    .string "CERULEAN'daki SALON'a git ve\n"
    .string "yeteneklerini sına.$"

PewterCity_Gym_Text_DontHaveRoomForThis::
    .string "Buna yerin yok.$"

PewterCity_Gym_Text_LiamIntro::
    .string "Olduğun yerde dur, ufaklık!\p"
    .string "BROCK'la yüzleşmekten on bin ışık yılı\n"
    .string "uzaksın!$"

PewterCity_Gym_Text_LiamDefeat::
    .string "Hay aksi!\p"
    .string "Işık yılı zaman değil…\n"
    .string "Mesafe ölçer!$"

PewterCity_Gym_Text_LiamPostBattle::
    .string "Epey ateşlisin.\n"
    .string "…Ama BROCK kadar değil!$"

PewterCity_Gym_Text_LetMeTakeYouToTheTop::
    .string "Selam!\n"
    .string "Büyük hayaller kurmak ister misin?\p"
    .string "POKéMON şampiyonu olmayı hayal etmeye\n"
    .string "cesaretin var mı?\p"
    .string "EĞİTMEN değilim ama nasıl kazanacağın\n"
    .string "konusunda tavsiye verebilirim.\p"
    .string "Seni zirveye taşıyayım!$"

PewterCity_Gym_Text_LetsGetHappening::
    .string "Pekala!\n"
    .string "Hadi başlayalım!$"

PewterCity_Gym_Text_TryDifferentPartyOrders::
    .string "Bir maçta ilk çıkan POKéMON, POKéMON\n"
    .string "LİSTESİ'nin en başındakidir.\p"
    .string "POKéMON'ların sırasını değiştirerek\n"
    .string "avantaj kazanabilirsin.\p"
    .string "Rakibinin takımına göre farklı\n"
    .string "sıralamalar dene.$"

PewterCity_Gym_Text_ItsFreeLetsGetHappening::
    .string "Ücretsiz hizmet!\n"
    .string "Hadi başlayalım!$"

PewterCity_Gym_Text_YoureChampMaterial::
    .string "Tam düşündüğüm gibi!\n"
    .string "Sende POKéMON şampiyonu cevheri var!$"

PewterCity_Gym_Text_GymStatue::
    .string "PEWTER POKéMON SALONU\n"
    .string "LİDER: BROCK\p"
    .string "KAZANAN EĞİTMENLER:\n"
    .string "{RIVAL}$"

PewterCity_Gym_Text_GymStatuePlayerWon::
    .string "PEWTER POKéMON SALONU\n"
    .string "LİDER: BROCK\p"
    .string "KAZANAN EĞİTMENLER:\n"
    .string "{RIVAL}, {PLAYER}$"

