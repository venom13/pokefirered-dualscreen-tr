#include "global.h"
#include "link_rfu.h"
#include "mystery_gift_server.h"
#include "mystery_gift_client.h"
#include "constants/union_room.h"

ALIGNED(4) const u8 gText_UR_EmptyString[] = _("");
ALIGNED(4) const u8 gText_UR_Colon[] = _(":");
ALIGNED(4) const u8 gText_UR_ID[] = _("{ID}");
ALIGNED(4) const u8 gText_UR_PleaseStartOver[] = _("Lütfen en baştan yeniden başla.");
ALIGNED(4) const u8 gText_UR_WirelessSearchCanceled[] = _("KABLOSUZ İLETİŞİM SİSTEMİ araması\niptal edildi.");
ALIGNED(4) static const u8 sText_AwaitingCommunucation2[] = _("ともだちからの れんらくを\nまっています");
ALIGNED(4) const u8 gText_UR_AwaitingCommunication[] = _("{STR_VAR_1}! Başka bir oyuncudan\niletişim bekleniyor.");
ALIGNED(4) const u8 gText_UR_AwaitingLinkPressStart[] = _("{STR_VAR_1}! Bağlantı bekleniyor!\nHerkes hazır olunca START'a bas.");

ALIGNED(4) static const u8 sText_SingleBattle[] = _("シングルバトルを かいさいする");
ALIGNED(4) static const u8 sText_DoubleBattle[] = _("ダブルバトルを かいさいする");
ALIGNED(4) static const u8 sText_MultiBattle[] = _("マルチバトルを かいさいする");
ALIGNED(4) static const u8 sText_TradePokemon[] = _("ポケモンこうかんを かいさいする");
ALIGNED(4) static const u8 sText_Chat[] = _("チャットを かいさいする");
ALIGNED(4) static const u8 sText_DistWonderCard[] = _("ふしぎなカードをくばる");
ALIGNED(4) static const u8 sText_DistWonderNews[] = _("ふしぎなニュースをくばる");
ALIGNED(4) static const u8 sText_DistMysteryEvent[] = _("ふしぎなできごとを かいさいする");
ALIGNED(4) static const u8 sText_HoldPokemonJump[] = _("なわとびを かいさいする");
ALIGNED(4) static const u8 sText_HoldBerryCrush[] = _("きのみマッシャーを かいさいする");
ALIGNED(4) static const u8 sText_HoldBerryPicking[] = _("きのみどりを かいさいする");
ALIGNED(4) static const u8 sText_HoldSpinTrade[] = _("ぐるぐるこうかんを かいさいする");
ALIGNED(4) static const u8 sText_HoldSpinShop[] = _("ぐるぐるショップを かいさいする");

// Unused
static const u8 *const sLinkGroupActionTexts[] = {
    sText_SingleBattle,
    sText_DoubleBattle,
    sText_MultiBattle,
    sText_TradePokemon,
    sText_Chat,
    sText_DistWonderCard,
    sText_DistWonderNews,
    sText_DistWonderCard,
    sText_HoldPokemonJump,
    sText_HoldBerryCrush,
    sText_HoldBerryPicking,
    sText_HoldBerryPicking,
    sText_HoldSpinTrade,
    sText_HoldSpinShop
};

static const u8 sText_1PlayerNeeded[] = _("1 oyuncu\ngerekli.");
static const u8 sText_2PlayersNeeded[] = _("2 oyuncu\ngerekli.");
static const u8 sText_3PlayersNeeded[] = _("3 oyuncu\ngerekli.");
static const u8 sText_4PlayersNeeded[] = _("あと4にん\nひつよう");
static const u8 sText_2PlayerMode[] = _("2 OYUNCULU\nMOD");
static const u8 sText_3PlayerMode[] = _("3 OYUNCULU\nMOD");
static const u8 sText_4PlayerMode[] = _("4 OYUNCULU\nMOD");
static const u8 sText_5PlayerMode[] = _("5 OYUNCULU\nMOD");

const u8 *const gTexts_UR_PlayersNeededOrMode[][5] = {
    { // 2 players required
        sText_1PlayerNeeded,
        sText_2PlayerMode
    },
    { // 4 players required
        sText_3PlayersNeeded,
        sText_2PlayersNeeded,
        sText_1PlayerNeeded,
        sText_4PlayerMode
    },
    { // 2-5 players required
        sText_1PlayerNeeded,
        sText_2PlayerMode,
        sText_3PlayerMode,
        sText_4PlayerMode,
        sText_5PlayerMode
    },
    { // 3-5 players required
        sText_2PlayersNeeded,
        sText_1PlayerNeeded,
        sText_3PlayerMode,
        sText_4PlayerMode,
        sText_5PlayerMode
    }
};

ALIGNED(4) const u8 gText_UR_BButtonCancel[] = _("{B_BUTTON}VAZGEÇ");
ALIGNED(4) static const u8 sText_SearchingForParticipants[] = _("ため\nさんかしゃ ぼしゅうちゅう です！");
ALIGNED(4) const u8 gText_UR_PlayerContactedYouForXAccept[] = _("{STR_VAR_2} seninle iletişime geçti:\n{STR_VAR_1}. Kabul?");
ALIGNED(4) const u8 gText_UR_PlayerContactedYouShareX[] = _("{STR_VAR_2} seninle iletişime geçti.\nPaylaşılsın mı: {STR_VAR_1}?");
ALIGNED(4) const u8 gText_UR_PlayerContactedYouAddToMembers[] = _("{STR_VAR_2} seninle iletişime geçti.\nÜyelere eklensin mi?");
ALIGNED(4) const u8 gText_UR_AreTheseMembersOK[] = _("{STR_VAR_1}!\nBu üyeler uygun mu?");
ALIGNED(4) const u8 gText_UR_CancelModeWithTheseMembers[] = _("Bu üyelerle {STR_VAR_1} MODU iptal\nedilsin mi?");
ALIGNED(4) const u8 gText_UR_AnOKWasSentToPlayer[] = _("Şu oyuncuya “TAMAM” gönderildi:\n{STR_VAR_1}.");

ALIGNED(4) static const u8 sText_OtherTrainerUnavailableNow[] = _("Diğer EĞİTMEN şu an müsait değil\ngibi görünüyor…\p");
ALIGNED(4) static const u8 sText_CantTransmitTrainerTooFar[] = _("Çok uzaktaki bir EĞİTMENLE iletişim\nkuramazsın.\p");
ALIGNED(4) static const u8 sText_TrainersNotReadyYet[] = _("Diğer EĞİTMEN(LER) henüz hazır\ndeğil.\p");

const u8 *const gTexts_UR_CantTransmitToTrainer[] = {
    sText_CantTransmitTrainerTooFar,
    sText_TrainersNotReadyYet
};

ALIGNED(4) const u8 gText_UR_ModeWithTheseMembersWillBeCanceled[] = _("Bu üyelerle {STR_VAR_1} MODU iptal\nedilecek.{PAUSE 90}");
ALIGNED(4) static const u8 sText_MemberNoLongerAvailable[] = _("Artık müsait kalamayacak bir üye\nvar.\p");

const u8 *const gTexts_UR_PlayerUnavailable[] = {
    sText_OtherTrainerUnavailableNow,
    sText_MemberNoLongerAvailable
};

ALIGNED(4) static const u8 sText_TrainerAppearsUnavailable[] = _("Diğer EĞİTMEN müsait değil gibi\ngörünüyor…\p");
ALIGNED(4) const u8 gText_UR_PlayerSentBackOK[] = _("{STR_VAR_1} bir “TAMAM” gönderdi!");
ALIGNED(4) const u8 gText_UR_PlayerOKdRegistration[] = _("{STR_VAR_1}, üyeliğini onayladı.");
ALIGNED(4) static const u8 sText_PlayerRepliedNo[] = _("{STR_VAR_1} şöyle cevap verdi:\p“Hayır…”\p");
ALIGNED(4) const u8 gText_UR_AwaitingOtherMembers[] = _("{STR_VAR_1}!\nDiğer üyeler bekleniyor!");
ALIGNED(4) const u8 gText_UR_QuitBeingMember[] = _("Üyelikten çıkılsın mı?");
ALIGNED(4) static const u8 sText_StoppedBeingMember[] = _("Üyelikten çıktın.\p");

const u8 *const gTexts_UR_PlayerDisconnected[] = {
    [RFU_STATUS_OK]                  = NULL,
    [RFU_STATUS_FATAL_ERROR]         = sText_MemberNoLongerAvailable,
    [RFU_STATUS_CONNECTION_ERROR]    = sText_TrainerAppearsUnavailable,
    [RFU_STATUS_CHILD_SEND_COMPLETE] = NULL,
    [RFU_STATUS_NEW_CHILD_DETECTED]  = NULL,
    [RFU_STATUS_JOIN_GROUP_OK]       = NULL,
    [RFU_STATUS_JOIN_GROUP_NO]       = sText_PlayerRepliedNo,
    [RFU_STATUS_WAIT_ACK_JOIN_GROUP] = NULL,
    [RFU_STATUS_LEAVE_GROUP_NOTICE]  = NULL,
    [RFU_STATUS_LEAVE_GROUP]         = sText_StoppedBeingMember
};

ALIGNED(4) const u8 gText_UR_WirelessLinkEstablished[] = _("KABLOSUZ İLETİŞİM SİSTEMİ\nbağlantısı kuruldu.");
ALIGNED(4) const u8 gText_UR_WirelessLinkDropped[] = _("KABLOSUZ İLETİŞİM SİSTEMİ\nbağlantısı koptu…");
ALIGNED(4) const u8 gText_UR_LinkWithFriendDropped[] = _("Arkadaşınla bağlantı koptu…");
ALIGNED(4) static const u8 sText_PlayerRepliedNo2[] = _("{STR_VAR_1} şöyle cevap verdi: “Hayır…”");

const u8 *const gTexts_UR_LinkDropped[] = {
    [RFU_STATUS_OK]                  = NULL,
    [RFU_STATUS_FATAL_ERROR]         = gText_UR_LinkWithFriendDropped,
    [RFU_STATUS_CONNECTION_ERROR]    = gText_UR_LinkWithFriendDropped,
    [RFU_STATUS_CHILD_SEND_COMPLETE] = NULL,
    [RFU_STATUS_NEW_CHILD_DETECTED]  = NULL,
    [RFU_STATUS_JOIN_GROUP_OK]       = NULL,
    [RFU_STATUS_JOIN_GROUP_NO]       = sText_PlayerRepliedNo2,
    [RFU_STATUS_WAIT_ACK_JOIN_GROUP] = NULL,
    [RFU_STATUS_LEAVE_GROUP_NOTICE]  = NULL,
    [RFU_STATUS_LEAVE_GROUP]         = NULL
};

ALIGNED(4) static const u8 sText_DoYouWantXMode[] = _("{STR_VAR_2} MODU istiyor musun?");
ALIGNED(4) static const u8 sText_DoYouWantXMode2[] = _("{STR_VAR_2} MODU istiyor musun?");

// Unused
static const u8 *const sDoYouWantModeTexts[] = {
    sText_DoYouWantXMode,
    sText_DoYouWantXMode2
};

ALIGNED(4) static const u8 sText_CommunicatingPleaseWait[] = _("はなしかけています…\nしょうしょう おまちください"); // Unused
ALIGNED(4) const u8 gText_UR_AwaitingPlayersResponseAboutTrade[] = _("Takas için şu oyuncunun cevabı\nbekleniyor: {STR_VAR_1}…");

ALIGNED(4) static const u8 sText_Communicating[] = _("İletişim kuruluyor{PAUSE 15}.{PAUSE 15}.{PAUSE 15}.{PAUSE 15}.{PAUSE 15}.\n{PAUSE 15}.{PAUSE 15}.{PAUSE 15}.{PAUSE 15}.{PAUSE 15}.{PAUSE 15}.{PAUSE 15}.{PAUSE 15}.{PAUSE 15}.{PAUSE 15}.{PAUSE 15}.{PAUSE 15}.{PAUSE 15}.{PAUSE 15}.{PAUSE 15}.{PAUSE 15}.{PAUSE 15}.{PAUSE 15}.");
ALIGNED(4) static const u8 sText_CommunicatingWithPlayer[] = _("İletişim: {STR_VAR_1}{PAUSE 15}.{PAUSE 15}.{PAUSE 15}.\n{PAUSE 15}.{PAUSE 15}.{PAUSE 15}.{PAUSE 15}.{PAUSE 15}.{PAUSE 15}.{PAUSE 15}.{PAUSE 15}.{PAUSE 15}.{PAUSE 15}.{PAUSE 15}.{PAUSE 15}.{PAUSE 15}.{PAUSE 15}.{PAUSE 15}.{PAUSE 15}.{PAUSE 15}.{PAUSE 15}.");
ALIGNED(4) static const u8 sText_PleaseWaitAWhile[] = _("Lütfen biraz bekle{PAUSE 15}.{PAUSE 15}.{PAUSE 15}.{PAUSE 15}.{PAUSE 15}.{PAUSE 15}.\n{PAUSE 15}.{PAUSE 15}.{PAUSE 15}.{PAUSE 15}.{PAUSE 15}.{PAUSE 15}.{PAUSE 15}.{PAUSE 15}.{PAUSE 15}.{PAUSE 15}.{PAUSE 15}.{PAUSE 15}.{PAUSE 15}.{PAUSE 15}.{PAUSE 15}.{PAUSE 15}.{PAUSE 15}.{PAUSE 15}.");

const u8 *const gTexts_UR_CommunicatingWait[] = {
    sText_Communicating,
    sText_CommunicatingWithPlayer,
    sText_PleaseWaitAWhile
};

ALIGNED(4) static const u8 sText_HiDoSomethingMale[] = _("Selam! Yapmak istediğin bir şey var\nmı?");
ALIGNED(4) static const u8 sText_HiDoSomethingFemale[] = _("Merhaba!\nBir şey yapmak ister misin?");
ALIGNED(4) static const u8 sText_HiDoSomethingAgainMale[] = _("{STR_VAR_1}: Selam, yine karşılaştık!\nBu sefer ne yapmak istersin?");
ALIGNED(4) static const u8 sText_HiDoSomethingAgainFemale[] = _("{STR_VAR_1}: Ah! {PLAYER}, merhaba!\nBir şey yapmak ister misin?");

const u8 *const gTexts_UR_HiDoSomething[][GENDER_COUNT] = {
    {
        sText_HiDoSomethingMale,
        sText_HiDoSomethingFemale
    }, {
        sText_HiDoSomethingAgainMale,
        sText_HiDoSomethingAgainFemale
    }
};

ALIGNED(4) static const u8 sText_DoSomethingMale[] = _("Bir şey yapmak ister misin?");
ALIGNED(4) static const u8 sText_DoSomethingFemale[] = _("Bir şey yapmak ister misin?");
ALIGNED(4) static const u8 sText_DoSomethingAgainMale[] = _("{STR_VAR_1}: Şimdi ne yapmak\nistersin?");
ALIGNED(4) static const u8 sText_DoSomethingAgainFemale[] = _("{STR_VAR_1}‘また なにかする？");

// Unused
static const u8 *const sDoSomethingTexts[][GENDER_COUNT] = {
    {
        sText_DoSomethingMale,
        sText_DoSomethingFemale
    }, {
        sText_DoSomethingAgainMale,
        sText_DoSomethingAgainMale // was probably supposed to be sText_DoSomethingAgainFemale
    }
};

ALIGNED(4) static const u8 sText_SomebodyHasContactedYou[] = _("Biri seninle iletişime geçti.{PAUSE 60}");
ALIGNED(4) static const u8 sText_PlayerHasContactedYou[] = _("{STR_VAR_1} seninle iletişime geçti.{PAUSE 60}");

const u8 *const gTexts_UR_PlayerContactedYou[] = {
    sText_SomebodyHasContactedYou,
    sText_PlayerHasContactedYou
};

ALIGNED(4) static const u8 sText_AwaitingResponseFromTrainer[] = _("Diğer EĞİTMENDEN cevap bekleniyor…");
ALIGNED(4) static const u8 sText_AwaitingResponseFromPlayer[] = _("Şu oyuncudan cevap bekleniyor:\n{STR_VAR_1}…");

const u8 *const gTexts_UR_AwaitingResponse[] = {
    sText_AwaitingResponseFromTrainer,
    sText_AwaitingResponseFromPlayer
};

ALIGNED(4) static const u8 sText_AwaitingResponseCancelBButton[] = _("あいての ていあんを まっています\nビーボタンで キャンセル");

ALIGNED(4) const u8 gText_UR_ShowTrainerCard[] = _("Diğer EĞİTMEN sana EĞİTMEN KARTI'nı\ngösterdi.\pSen de EĞİTMEN KARTI'nı göstermek\nister misin?");
ALIGNED(4) const u8 gText_UR_BattleChallenge[] = _("Diğer EĞİTMEN sana savaş için\nmeydan okuyor.\pMeydan okumayı kabul ediyor musun?");
ALIGNED(4) const u8 gText_UR_ChatInvitation[] = _("Diğer EĞİTMEN seni sohbete davet\nediyor.\pSohbet davetini kabul ediyor musun?");
ALIGNED(4) const u8 gText_UR_OfferToTradeMon[] = _("Kayıtlı Sv. {DYNAMIC 0} {DYNAMIC 1} için bir takas teklifi\nvar,\pkarşılığında: Sv. {DYNAMIC 2} {DYNAMIC 3}.\pBu takas teklifini kabul ediyor\nmusun?");
ALIGNED(4) const u8 gText_UR_OfferToTradeEgg[] = _("Kayıtlı YUMURTA'n için bir takas\nteklifi var.\lBu takas teklifini kabul ediyor\lmusun?");
ALIGNED(4) const u8 gText_UR_ChatDropped[] = _("Sohbet kesildi.\p");
ALIGNED(4) const u8 gText_UR_OfferDeclined1[] = _("Teklifi reddettin.\p");
ALIGNED(4) const u8 gText_UR_OfferDeclined2[] = _("Teklifi reddettin.\p");
ALIGNED(4) const u8 gText_UR_ChatEnded[] = _("Sohbet sona erdi.\p");

// Unused
static const u8 *const sInvitationTexts[] = {
    gText_UR_ShowTrainerCard,
    gText_UR_BattleChallenge,
    gText_UR_ChatInvitation,
    gText_UR_OfferToTradeMon
};

ALIGNED(4) static const u8 sText_JoinChatMale[] = _("Ah, selam! Şu an sohbet ediyoruz.\nBize katılmak ister misin?");
ALIGNED(4) static const u8 sText_PlayerJoinChatMale[] = _("{STR_VAR_1}: Selam, {PLAYER}!\nŞu an sohbet ediyoruz.\lBize katılmak ister misin?");
ALIGNED(4) static const u8 sText_JoinChatFemale[] = _("Ah, merhaba! Şu an sohbet ediyoruz.\nBize katılmak ister misin?");
ALIGNED(4) static const u8 sText_PlayerJoinChatFemale[] = _("{STR_VAR_1}: Ah, merhaba {PLAYER}!\nŞu an sohbet ediyoruz.\lBize katılmak ister misin?");

const u8 *const gTexts_UR_JoinChat[][GENDER_COUNT] = {
    {
        sText_JoinChatMale,
        sText_JoinChatFemale
    }, {
        sText_PlayerJoinChatMale,
        sText_PlayerJoinChatFemale
    }
};

ALIGNED(4) const u8 gText_UR_TrainerAppearsBusy[] = _("……\nEĞİTMEN meşgul görünüyor…\p");
ALIGNED(4) static const u8 sText_WaitForBattleMale[] = _("Savaş mı?\nPekala, bana biraz zaman ver.");
ALIGNED(4) static const u8 sText_WaitForChatMale[] = _("Sohbet mi istiyorsun?\nTabii, biraz bekle.");
ALIGNED(4) static const u8 sText_ShowTrainerCardMale[] = _("Tabii! “Selamlaşma” olarak işte\nEĞİTMEN KARTIM.");
ALIGNED(4) static const u8 sText_WaitForBattleFemale[] = _("Savaş mı? Tabii ama hazırlanmak için\nzamana ihtiyacım var.");
ALIGNED(4) static const u8 sText_WaitForChatFemale[] = _("Sohbet mi etmek istedin?\nTamam ama lütfen biraz bekle.");
ALIGNED(4) static const u8 sText_ShowTrainerCardFemale[] = _("Kendimi tanıtmak için sana EĞİTMEN\nKARTIMI göstereceğim.");

const u8 *const gTexts_UR_WaitOrShowCard[GENDER_COUNT][4] = {
    {
        sText_WaitForBattleMale,
        sText_WaitForChatMale,
        NULL,
        sText_ShowTrainerCardMale
    }, {
        sText_WaitForBattleFemale,
        sText_WaitForChatFemale,
        NULL,
        sText_ShowTrainerCardFemale
    }
};

ALIGNED(4) static const u8 sText_WaitForChatMale2[] = _("チャットだね！\nわかった ちょっと まってて！");
ALIGNED(4) static const u8 sText_DoneWaitingBattleMale[] = _("Beklediğin için teşekkürler!\nHaydi savaşa başlayalım!{PAUSE 60}");
ALIGNED(4) static const u8 sText_DoneWaitingChatMale[] = _("Pekala!\nHaydi sohbet edelim!{PAUSE 60}");
ALIGNED(4) static const u8 sText_DoneWaitingBattleFemale[] = _("Beklettiğim için özür dilerim!\nHaydi başlayalım!{PAUSE 60}");
ALIGNED(4) static const u8 sText_DoneWaitingChatFemale[] = _("Beklettiğim için özür dilerim!\nHaydi sohbet edelim.{PAUSE 60}");
ALIGNED(4) static const u8 sText_TradeWillBeStarted[] = _("Takas başlatılacak.{PAUSE 60}");
ALIGNED(4) static const u8 sText_BattleWillBeStarted[] = _("Savaş başlatılacak.{PAUSE 60}");
ALIGNED(4) static const u8 sText_EnteringChat[] = _("Sohbete giriliyor…{PAUSE 60}");

const u8 *const gTexts_UR_StartActivity[][GENDER_COUNT][3] = {
    {
        {
            sText_BattleWillBeStarted,
            sText_EnteringChat,
            sText_TradeWillBeStarted
        }, {
            sText_BattleWillBeStarted,
            sText_EnteringChat,
            sText_TradeWillBeStarted
        }
    }, {
        {
            sText_DoneWaitingBattleMale,
            sText_DoneWaitingChatMale,
            sText_TradeWillBeStarted
        }, {
            sText_DoneWaitingBattleFemale,
            sText_DoneWaitingChatFemale,
            sText_TradeWillBeStarted
        }
    }
};

ALIGNED(4) static const u8 sText_BattleDeclinedMale[] = _("Üzgünüm! POKéMON'larım şu an pek iyi\nhissetmiyor.\lBaşka zaman savaşalım.\p");
ALIGNED(4) static const u8 sText_BattleDeclinedFemale[] = _("Çok özür dilerim ama POKéMON'larım\niyi hissetmiyor…\pBaşka zaman savaşalım.\p");

const u8 *const gTexts_UR_BattleDeclined[GENDER_COUNT] = {
    sText_BattleDeclinedMale,
    sText_BattleDeclinedFemale
};

ALIGNED(4) static const u8 sText_ShowTrainerCardDeclinedMale[] = _("Ha? EĞİTMEN KARTIM…\nŞimdi nereye gitti?\lÜzgünüm! Başka zaman gösteririm!\p");
ALIGNED(4) static const u8 sText_ShowTrainerCardDeclinedFemale[] = _("Ah? EĞİTMEN KARTIMI nereye\nkoydum?…\lÜzgünüm! Sonra gösteririm!\p");

const u8 *const gTexts_UR_ShowTrainerCardDeclined[GENDER_COUNT] = {
    sText_ShowTrainerCardDeclinedMale,
    sText_ShowTrainerCardDeclinedFemale
};

ALIGNED(4) static const u8 sText_IfYouWantToDoSomethingMale[] = _("Benimle bir şey yapmak istersen\nseslenmen yeter!\p");
ALIGNED(4) static const u8 sText_IfYouWantToDoSomethingFemale[] = _("Benimle bir şey yapmak istersen\nçekinme.\p");

const u8 *const gTexts_UR_IfYouWantToDoSomething[GENDER_COUNT] = {
    sText_IfYouWantToDoSomethingMale,
    sText_IfYouWantToDoSomethingFemale
};

ALIGNED(4) const u8 gText_UR_TrainerBattleBusy[] = _("Eyvah! Üzgünüm ama başka bir şey\nyapmam gerekiyor.\lBaşka zaman, tamam mı?\p");
ALIGNED(4) const u8 gText_UR_NeedTwoMonsOfLevel30OrLower1[] = _("Savaşmak istiyorsan Sv. 30'un altında\niki POKéMON gerekiyor.\p");
ALIGNED(4) const u8 gText_UR_NeedTwoMonsOfLevel30OrLower2[] = _("Savaş için Sv. 30'un altında iki\nPOKéMON gerekiyor.\p");

ALIGNED(4) static const u8 sText_DeclineChatMale[] = _("Ah, peki.\nNe zaman istersen gel, tamam mı?\p");
ALIGNED(4) static const u8 stext_DeclineChatFemale[] = _("Ah…\nLütfen istediğin zaman uğra.\p");

// Response from partner when player declines chat
const u8 *const gTexts_UR_DeclineChat[GENDER_COUNT] = {
    sText_DeclineChatMale,
    stext_DeclineChatFemale
};

ALIGNED(4) static const u8 sText_ChatDeclinedMale[] = _("Ah, üzgünüm!\nŞu an hiç yapamam.\lBaşka zaman sohbet edelim.\p");
ALIGNED(4) static const u8 sText_ChatDeclinedFemale[] = _("Ah, özür dilerim.\nŞu an yapacak çok işim var.\lBaşka bir zaman sohbet edelim.\p");

// Response from partner when they decline chat
const u8 *const gTexts_UR_ChatDeclined[GENDER_COUNT] = {
    sText_ChatDeclinedMale,
    sText_ChatDeclinedFemale
};

ALIGNED(4) static const u8 sText_YoureToughMale[] = _("Vay!\nEpey güçlü olduğunu görebiliyorum!\p");
ALIGNED(4) static const u8 sText_UsedGoodMoveMale[] = _("O hareketi mi kullandın?\nBu iyi bir strateji!\p");
ALIGNED(4) static const u8 sText_BattleSurpriseMale[] = _("Aferin!\nBu göz açıcıydı!\p");
ALIGNED(4) static const u8 sText_SwitchedMonsMale[] = _("Ah! O durumda o POKéMON'u nasıl\nkullanabildin?\p");
ALIGNED(4) static const u8 sText_YoureToughFemale[] = _("O POKéMON…\nGerçekten çok iyi yetiştirilmiş!\p");
ALIGNED(4) static const u8 sText_UsedGoodMoveFemale[] = _("İşte bu!\nŞimdi doğru hareket bu!\p");
ALIGNED(4) static const u8 sText_BattleSurpriseFemale[] = _("Bu harika!\nBöyle de mi savaşılıyor?\p");
ALIGNED(4) static const u8 sText_SwitchedMonsFemale[] = _("POKéMON değiştirmede kusursuz bir\nzamanlaman var!\p");

const u8 *const gTexts_UR_BattleReaction[GENDER_COUNT][4] = {
    {
        sText_YoureToughMale,
        sText_UsedGoodMoveMale,
        sText_BattleSurpriseMale,
        sText_SwitchedMonsMale
    }, {
        sText_YoureToughFemale,
        sText_UsedGoodMoveFemale,
        sText_BattleSurpriseFemale,
        sText_SwitchedMonsFemale
    }
};

ALIGNED(4) static const u8 sText_LearnedSomethingMale[] = _("Ah, anlıyorum!\nBu çok öğretici!\p");
ALIGNED(4) static const u8 sText_ThatsFunnyMale[] = _("Artık komik bir şey söyleme!\nGülmekten karnım ağrıdı!\p");
ALIGNED(4) static const u8 sText_RandomChatMale1[] = _("Ah?\nÖyle bir şey olmuştu.\p");
ALIGNED(4) static const u8 sText_RandomChatMale2[] = _("Hmhm… Ne?\nYani bunu mu söylüyorsun?\p");
ALIGNED(4) static const u8 sText_LearnedSomethingFemale[] = _("Öyle mi?\nBunu bilmiyordum.\p");
ALIGNED(4) static const u8 sText_ThatsFunnyFemale[] = _("Ahaha!\nBu da ne demek?\p");
ALIGNED(4) static const u8 sText_RandomChatFemale1[] = _("Evet, aynen öyle!\nDemek istediğim buydu.\p");
ALIGNED(4) static const u8 sText_RandomChatFemale2[] = _("Başka bir deyişle…\nEvet! Doğru!\p");

const u8 *const gTexts_UR_ChatReaction[GENDER_COUNT][4] = {
    {
        sText_LearnedSomethingMale,
        sText_ThatsFunnyMale,
        sText_RandomChatMale1,
        sText_RandomChatMale2
    }, {
        sText_LearnedSomethingFemale,
        sText_ThatsFunnyFemale,
        sText_RandomChatFemale1,
        sText_RandomChatFemale2
    }
};

ALIGNED(4) static const u8 sText_ShowedTrainerCardMale1[] = _("Selamlaşma yolum olarak EĞİTMEN\nKARTIMI gösteriyorum.\p");
ALIGNED(4) static const u8 sText_ShowedTrainerCardMale2[] = _("Umarım seni daha iyi tanırım!\p");
ALIGNED(4) static const u8 sText_ShowedTrainerCardFemale1[] = _("Tanışmak için birbirimize EĞİTMEN\nKARTLARIMIZI gösteriyoruz.\p");
ALIGNED(4) static const u8 sText_ShowedTrainerCardFemale2[] = _("Tanıştığımıza memnun oldum.\nLütfen yabancı olma!\p");

const u8 *const gTexts_UR_TrainerCardReaction[GENDER_COUNT][2] = {
    {
        sText_ShowedTrainerCardMale1,
        sText_ShowedTrainerCardMale2
    }, {
        sText_ShowedTrainerCardFemale1,
        sText_ShowedTrainerCardFemale2
    }
};

ALIGNED(4) static const u8 sText_MaleTraded1[] = _("Yaşasın!\nBu POKéMON'u gerçekten istiyordum!\p");
ALIGNED(4) static const u8 sText_MaleTraded2[] = _("Sonunda bir takasla uzun zamandır\nistediğim POKéMON'u aldım.\p");
ALIGNED(4) static const u8 sText_FemaleTraded1[] = _("Şu an POKéMON takas ediyorum.\p");
ALIGNED(4) static const u8 sText_FemaleTraded2[] = _("Sonunda istediğim o POKéMON'u\ntakasla aldım!\p");

const u8 *const gTexts_UR_TradeReaction[GENDER_COUNT][4] = {
    {
        sText_MaleTraded1,
        sText_MaleTraded2
    }, {
        sText_FemaleTraded1,
        sText_FemaleTraded2
    }
};

const u8 gText_UR_XCheckedTradingBoard[] = _("{STR_VAR_1}, TAKAS PANOSU'na baktı.\p");
ALIGNED(4) const u8 gText_UR_RegisterMonAtTradingBoard[] = _("TAKAS PANOSU'na hoş geldin.\pPOKéMON'unu kaydedip takasa\nsunabilirsin.\pPOKéMON'larından birini kaydetmek\nister misin?");
ALIGNED(4) const u8 gText_UR_TradingBoardInfo[] = _("Bu TAKAS PANOSU, takas için POKéMON\nsunmakta kullanılır.\pTek yapman gereken takas için bir\nPOKéMON kaydetmek.\pBaşka bir EĞİTMEN karşılığında\ntakımından bir POKéMON sunabilir.\pUmarız POKéMON kaydedip pek çok\nEĞİTMENLE takas edersin.\pPOKéMON'larından birini kaydetmek\nister misin?");
ALIGNED(4) static const u8 sText_ThankYouForRegistering[] = _("こうかんけいじばん の とうろくが\nかんりょう しました\pごりよう ありがとう\nございました！\p");
ALIGNED(4) static const u8 sText_NobodyHasRegistered[] = _("けいじばんに だれも ポケモンを\nとうろく していません\p\n");
ALIGNED(4) const u8 gText_UR_ChooseRequestedMonType[] = _("Lütfen takasta istediğin POKéMON\ntürünü seç.\n");
ALIGNED(4) const u8 gText_UR_WhichMonWillYouOffer[] = _("Takımındaki hangi POKéMON'u takasa\nsunacaksın?\p");
ALIGNED(4) const u8 gText_UR_RegistrationCanceled[] = _("Kayıt iptal edildi.\p");
ALIGNED(4) const u8 gText_UR_RegistraionCompleted[] = _("Kayıt tamamlandı.\p");
ALIGNED(4) const u8 gText_UR_TradeCanceled[] = _("Takas iptal edildi.\p");
ALIGNED(4) const u8 gText_UR_CancelRegistrationOfMon[] = _("Sv. {STR_VAR_2} {STR_VAR_1} kaydı\niptal edilsin mi?");
ALIGNED(4) const u8 gText_UR_CancelRegistrationOfEgg[] = _("YUMURTA'nın kaydı iptal edilsin mi?");
ALIGNED(4) const u8 gText_UR_RegistrationCanceled2[] = _("Kayıt iptal edildi.\p");
ALIGNED(4) static const u8 sText_TradeTrainersWillBeListed[] = _("こうかんを きぼうしているひとを\nひょうじします");
ALIGNED(4) static const u8 sText_ChooseTrainerToTradeWith2[] = _("こうかん したい トレーナーを\nえらんで ください");
ALIGNED(4) const u8 gText_UR_AskTrainerToMakeTrade[] = _("Şu oyuncudan takas istensin mi:\n{STR_VAR_1}?");
ALIGNED(4) static const u8 sText_AwaitingResponseFromTrainer2[] = _("……\nあいての へんじを まっています");
ALIGNED(4) static const u8 sText_NotRegisteredAMonForTrade[] = _("あなたが こうかんにだす\nポケモンが とうろくされていません\p");
ALIGNED(4) const u8 gText_UR_DontHaveTypeTrainerWants[] = _("{STR_VAR_1} adlı oyuncunun istediği\n{STR_VAR_2} türü POKéMON sende yok.\p");
ALIGNED(4) const u8 gText_UR_DontHaveEggTrainerWants[] = _("{STR_VAR_1} adlı oyuncunun istediği\nYUMURTA sende yok.\p");

ALIGNED(4) static const u8 sText_PlayerCantTradeForYourMon[] = _("{STR_VAR_1} şu an POKéMON'un için\ntakas yapamıyor.\p");
ALIGNED(4) static const u8 sText_CantTradeForPartnersMon[] = _("Şu an şu oyuncunun POKéMON'u için\ntakas yapamazsın: {STR_VAR_1}.\p");

// Unused
static const u8 *const sCantTradeMonTexts[] = {
    sText_PlayerCantTradeForYourMon,
    sText_CantTradeForPartnersMon
};

ALIGNED(4) const u8 gText_UR_TradeOfferRejected[] = _("Takas teklifin reddedildi.\p");
ALIGNED(4) const u8 gText_UR_EggTrade[] = _("YUMURTA TAKASI");
ALIGNED(4) const u8 gText_UR_ChooseJoinCancel[] = _("{DPAD_UPDOWN}SEÇ  {A_BUTTON}KATIL  {B_BUTTON}VAZGEÇ");
ALIGNED(4) const u8 gText_UR_ChooseTrainer[] = _("Lütfen bir EĞİTMEN seç.");
ALIGNED(4) static const u8 sText_ChooseTrainerSingleBattle[] = _("Lütfen TEK SAVAŞ için bir EĞİTMEN\nseç.");
ALIGNED(4) static const u8 sText_ChooseTrainerDoubleBattle[] = _("Lütfen ÇİFT SAVAŞ için bir EĞİTMEN\nseç.");
ALIGNED(4) static const u8 sText_ChooseLeaderMultiBattle[] = _("Lütfen ÇOKLU SAVAŞ için LİDERİ seç.");
ALIGNED(4) static const u8 sText_ChooseTrainerToTradeWith[] = _("Lütfen takas yapılacak EĞİTMENİ\nseç.");
ALIGNED(4) static const u8 sText_ChooseTrainerToShareWonderCards[] = _("Lütfen HARİKA KART paylaşan\nEĞİTMENİ seç.");
ALIGNED(4) static const u8 sText_ChooseTrainerToShareWonderNews[] = _("Lütfen HARİKA HABER paylaşan\nEĞİTMENİ seç.");
ALIGNED(4) static const u8 sText_ChooseLeaderPokemonJump[] = _("Mini POKéMON'larla zıpla!\nLütfen LİDERİ seç.");
ALIGNED(4) static const u8 sText_ChooseLeaderBerryCrush[] = _("DUT EZME!\nLütfen LİDERİ seç.");
ALIGNED(4) static const u8 sText_ChooseLeaderBerryPicking[] = _("DODRIO DUT TOPLAMA!\nLütfen LİDERİ seç.");

const u8 *const gTexts_UR_ChooseTrainer[] = {
    [LINK_GROUP_SINGLE_BATTLE] = sText_ChooseTrainerSingleBattle,
    [LINK_GROUP_DOUBLE_BATTLE] = sText_ChooseTrainerDoubleBattle,
    [LINK_GROUP_MULTI_BATTLE]  = sText_ChooseLeaderMultiBattle,
    [LINK_GROUP_TRADE]         = sText_ChooseTrainerToTradeWith,
    [LINK_GROUP_POKEMON_JUMP]  = sText_ChooseLeaderPokemonJump,
    [LINK_GROUP_BERRY_CRUSH]   = sText_ChooseLeaderBerryCrush,
    [LINK_GROUP_BERRY_PICKING] = sText_ChooseLeaderBerryPicking,
    [LINK_GROUP_WONDER_CARD]   = sText_ChooseTrainerToShareWonderCards,
    [LINK_GROUP_WONDER_NEWS]   = sText_ChooseTrainerToShareWonderNews
};

ALIGNED(4) const u8 gText_UR_SearchingForWirelessSystemWait[] = _("KABLOSUZ İLETİŞİM SİSTEMİ\naranıyor. Bekle...");
ALIGNED(4) static const u8 sText_MustHaveTwoMonsForDoubleBattle[] = _("ダブルバトルでは 2ひき いじょうの\nポケモンが ひつようです\p");
ALIGNED(4) const u8 gText_UR_AwaitingPlayersResponse[] = _("Şu oyuncunun cevabı bekleniyor: {STR_VAR_1}…");
ALIGNED(4) const u8 gText_UR_PlayerHasBeenAskedToRegisterYouPleaseWait[] = _("{STR_VAR_1} adlı oyuncudan seni üye\nyapması istendi. Lütfen bekle.");
ALIGNED(4) const u8 gText_UR_AwaitingResponseFromWirelessSystem[] = _("KABLOSUZ İLETİŞİM SİSTEMİ'nden\ncevap bekleniyor.");
ALIGNED(4) static const u8 sText_PleaseWaitForOtherTrainersToGather[] = _("ほかの さんかしゃが そろうまで\nしょうしょう おまちください");

ALIGNED(4) static const u8 sText_NoCardsSharedRightNow[] = _("Şu an paylaşılan KART yok gibi\ngörünüyor.");
ALIGNED(4) static const u8 sText_NoNewsSharedRightNow[] = _("Şu an paylaşılan HABER yok gibi\ngörünüyor.");

const u8 *const gTexts_UR_NoWonderShared[] = {
    sText_NoCardsSharedRightNow,
    sText_NoNewsSharedRightNow
};

ALIGNED(4) const u8 gText_UR_Battle[] = _("SAVAŞ");
ALIGNED(4) const u8 gText_UR_Chat2[] = _("SOHBET");
ALIGNED(4) const u8 gText_UR_Greetings[] = _("SELAMLAŞMA");
ALIGNED(4) const u8 gText_UR_Exit[] = _("ÇIKIŞ");

ALIGNED(4) const u8 gText_UR_Exit2[] = _("ÇIKIŞ");
ALIGNED(4) const u8 gText_UR_Info[] = _("BİLGİ");
ALIGNED(4) const u8 gText_UR_NameWantedOfferLv[] = _("İSİM{CLEAR_TO 0x3C}İSTENEN{CLEAR_TO 0x6E}SUNULAN{CLEAR_TO 0xC6}SV.");

ALIGNED(4) const u8 gText_UR_SingleBattle[] = _("TEK SAVAŞ");
ALIGNED(4) const u8 gText_UR_DoubleBattle[] = _("ÇİFT SAVAŞ");
ALIGNED(4) const u8 gText_UR_MultiBattle[] = _("ÇOKLU SAVAŞ");
ALIGNED(4) const u8 gText_UR_PokemonTrades[] = _("POKéMON TAKASI");
ALIGNED(4) const u8 gText_UR_Chat[] = _("SOHBET");
ALIGNED(4) const u8 gText_UR_Cards[] = _("KARTLAR");
ALIGNED(4) const u8 gText_UR_WonderCards[] = _("HARİKA KARTLAR");
ALIGNED(4) const u8 gText_UR_WonderNews[] = _("HARİKA HABER");
ALIGNED(4) const u8 gText_UR_PokemonJump[] = _("POKéMON ZIPLAMA");
ALIGNED(4) const u8 gText_UR_BerryCrush[] = _("DUT EZME");
ALIGNED(4) const u8 gText_UR_BerryPicking[] = _("DUT TOPLAMA");
ALIGNED(4) const u8 gText_UR_Search[] = _("ARA");
ALIGNED(4) const u8 gText_UR_SpinTrade[] = _("ぐるぐるこうかん");
ALIGNED(4) const u8 gText_UR_ItemTrade[] = _("アイテムトレード");

ALIGNED(4) static const u8 sText_ItsNormalCard[] = _("Bu bir NORMAL KART.");
ALIGNED(4) static const u8 sText_ItsBronzeCard[] = _("Bu bir BRONZ KART!");
ALIGNED(4) static const u8 sText_ItsCopperCard[] = _("Bu bir BAKIR KART!");
ALIGNED(4) static const u8 sText_ItsSilverCard[] = _("Bu bir GÜMÜŞ KART!");
ALIGNED(4) static const u8 sText_ItsGoldCard[] = _("Bu bir ALTIN KART!");

const u8 *const gTexts_UR_CardColor[] = {
    sText_ItsNormalCard,
    sText_ItsBronzeCard,
    sText_ItsCopperCard,
    sText_ItsSilverCard,
    sText_ItsGoldCard
};

ALIGNED(4) const u8 gText_UR_TrainerCardInfoPage1[] = _("{DYNAMIC 0} {DYNAMIC 1} - EĞİTMEN KARTI…\n{DYNAMIC 2}\pPOKéDEX: {DYNAMIC 3}\nSÜRE:    {DYNAMIC 4}:{DYNAMIC 5}\p");
ALIGNED(4) const u8 gText_UR_TrainerCardInfoPage2[] = _("SAVAŞ: {DYNAMIC 0} GALİBİYET  {DYNAMIC 2} MAĞLUBİYET\nTAKAS:   {DYNAMIC 3} KEZ\p“{DYNAMIC 4} {DYNAMIC 5}\n{DYNAMIC 6} {DYNAMIC 7}”\p");
ALIGNED(4) static const u8 sText_GladToMeetYouMale[] = _("{DYNAMIC 1}: Tanıştığımıza memnun oldum!{PAUSE 60}");
ALIGNED(4) static const u8 sText_GladToMeetYouFemale[] = _("{DYNAMIC 1}: Memnun oldum!{PAUSE 60}");

const u8 *const gTexts_UR_GladToMeetYou[GENDER_COUNT] = {
    sText_GladToMeetYouMale,
    sText_GladToMeetYouFemale
};

ALIGNED(4) const u8 gText_UR_FinishedCheckingPlayersTrainerCard[] = _("EĞİTMEN KARTI incelendi: {DYNAMIC 1}{PAUSE 60}");
ALIGNED(4) static const u8 sText_CanceledReadingCard[] = _("Kartı okuma iptal edildi.");

static const struct MysteryGiftClientCmd sClientScript_DynamicError[] = {
    {CLI_RECV, MG_LINKID_DYNAMIC_MSG},
    {CLI_COPY_MSG},
    {CLI_SEND_READY_END},
    {CLI_RETURN, CLI_MSG_BUFFER_FAILURE}
};

const struct MysteryGiftServerCmd gServerScript_ClientCanceledCard[] = {
    {SVR_LOAD_CLIENT_SCRIPT, PTR_ARG(sClientScript_DynamicError)},
    {SVR_SEND},
    {SVR_LOAD_MSG, PTR_ARG(sText_CanceledReadingCard)},
    {SVR_SEND},
    {SVR_RECV, MG_LINKID_READY_END},
    {SVR_RETURN, SVR_MSG_CLIENT_CANCELED}
};
