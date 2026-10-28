@ These are event scripts. They should not be moved to C.

#include "constants/global.h"
#include "constants/flags.h"
#include "constants/moves.h"
#include "constants/songs.h"
#include "constants/species.h"
#include "constants/vars.h"
#include "constants/items.h"
#include "constants/region_map_sections.h"
	.include "asm/macros.inc"
	.include "asm/macros/event.inc"
	.include "constants/constants.inc"

	.section .rodata
	
	.align 2
MysteryEventScript_StampCard::
	setvaddress MysteryEventScript_StampCard
	setorcopyvar VAR_RESULT, 1
	specialvar VAR_0x8008, GetMysteryGiftCardStat
	setorcopyvar VAR_RESULT, 0
	specialvar VAR_0x8009, GetMysteryGiftCardStat
	subvar VAR_0x8008, VAR_0x8009
	buffernumberstring STR_VAR_1, VAR_0x8008
	lock
	faceplayer
	vmessage sText_MysteryGiftStampCard
	waitmessage
	waitbuttonpress
	release
	end

sText_MysteryGiftStampCard:
	.string "DAMGA KARTI Sistemini kullandığın için\n"
	.string "teşekkürler.\p"
	.string "DAMGA KARTI'nı doldurmak için toplaman\n"
	.string "gereken kalan sayı: {STR_VAR_1}$"

MysteryEventScript_SurfPichu::
	setvaddress MysteryEventScript_SurfPichu
	vgoto_if_unset FLAG_MYSTERY_GIFT_DONE, SurfPichu_GiveIfPossible
	returnram

SurfPichu_GiveIfPossible:
	specialvar VAR_EVENT_PICHU_SLOT, CalculatePlayerPartyCount
	vgoto_if_eq VAR_EVENT_PICHU_SLOT, PARTY_SIZE, SurfPichu_FullParty
	setflag FLAG_MYSTERY_GIFT_DONE
	vcall SurfPichu_GiveEgg
	lock
	faceplayer
	vmessage sText_MysteryGiftEgg
	waitmessage
	waitbuttonpress
	playfanfare MUS_OBTAIN_ITEM
	waitfanfare
	release
	end

SurfPichu_FullParty:
	lock
	faceplayer
	vmessage sText_FullParty
	waitmessage
	waitbuttonpress
	release
	end

SurfPichu_GiveEgg:
	giveegg SPECIES_PICHU
	setmonmodernfatefulencounter VAR_EVENT_PICHU_SLOT
	setmonmetlocation VAR_EVENT_PICHU_SLOT, METLOC_FATEFUL_ENCOUNTER
	vgoto_if_eq VAR_EVENT_PICHU_SLOT, 1, SurfPichu_Slot1
	vgoto_if_eq VAR_EVENT_PICHU_SLOT, 2, SurfPichu_Slot2
	vgoto_if_eq VAR_EVENT_PICHU_SLOT, 3, SurfPichu_Slot3
	vgoto_if_eq VAR_EVENT_PICHU_SLOT, 4, SurfPichu_Slot4
	vgoto_if_eq VAR_EVENT_PICHU_SLOT, 5, SurfPichu_Slot5
	return

SurfPichu_Slot1:
	setmonmove 1, 2, MOVE_SURF
	return

SurfPichu_Slot2:
	setmonmove 2, 2, MOVE_SURF
	return

SurfPichu_Slot3:
	setmonmove 3, 2, MOVE_SURF
	return

SurfPichu_Slot4:
	setmonmove 4, 2, MOVE_SURF
	return

SurfPichu_Slot5:
	setmonmove 5, 2, MOVE_SURF
	return

sText_MysteryGiftEgg:
	.string "GİZEMLİ HEDİYE Sistemini kullandığın\n"
	.string "için teşekkürler.\p"
	.string "POKéMON MERKEZİ'nden bir hediyemiz\n"
	.string "var: bir POKéMON YUMURTASI!\p"
	.string "Lütfen onu sevgi ve şefkatle büyüt.$"

sText_FullParty:
	.string "Ah, takımın dolu görünüyor.\p"
	.string "Bir POKéMON'u PC'de depoladıktan sonra\n"
	.string "yanıma gel.$"

MysteryEventScript_VisitingTrainer::
	setvaddress MysteryEventScript_VisitingTrainer
	special ValidateEReaderTrainer
	vgoto_if_eq VAR_RESULT, 0, MysteryEventScript_VisitingTrainerArrived
	lock
	faceplayer
	vmessage sText_MysteryGiftVisitingTrainer
	waitmessage
	waitbuttonpress
	release
	end

MysteryEventScript_VisitingTrainerArrived:
	lock
	faceplayer
	vmessage sText_MysteryGiftVisitingTrainer_2
	waitmessage
	waitbuttonpress
	release
	end

sText_MysteryGiftVisitingTrainer:
	.string "GİZEMLİ HEDİYE Sistemini kullandığın\n"
	.string "için teşekkürler.\p"
	.string "Bu HARİKA KART'ı taşıyarak bir POKéMON\n"
	.string "MARKET'teki ankete katılabilirsin.\p"
	.string "Bu anketlerle EĞİTMENLERİ SEVII\n"
	.string "ADALARI'na davet et.\p"
	.string "…Sana anket için gizli bir şifre\n"
	.string "vereyim:\p"
	.string "“GIVE ME\n"
	.string "AWESOME TRAINER”\p"
	.string "Bunu bir ankete yaz ve KABLOSUZ\n"
	.string "İLETİŞİM SİSTEMİ'ne gönder.$"

sText_MysteryGiftVisitingTrainer_2:
	.string "GİZEMLİ HEDİYE Sistemini kullandığın\n"
	.string "için teşekkürler.\p"
	.string "SEVII ADALARI'na seni arayan bir\n"
	.string "EĞİTMEN geldi.\p"
	.string "Ziyaretçi EĞİTMENLE savaşmanın keyfini\n"
	.string "çıkarmanı dileriz.\p"
	.string "Başka şifreler girerek başka\n"
	.string "EĞİTMENLER davet edebilirsin.\p"
	.string "İşe yarayabilecek başka şifreler\n"
	.string "aramayı dene.$"

MysteryEventScript_BattleCard::
	setvaddress MysteryEventScript_BattleCard
	vgoto_if_set FLAG_MYSTERY_GIFT_DONE, MysteryEventScript_BattleCardInfo
	setorcopyvar VAR_RESULT, 2
	specialvar VAR_0x8008, GetMysteryGiftCardStat
	vgoto_if_ne VAR_0x8008, 3, MysteryEventScript_BattleCardInfo
	lock
	faceplayer
	vmessage sText_MysteryGiftBattleCountCard_2
	waitmessage
	waitbuttonpress
	giveitem ITEM_POTION
	release
	setflag FLAG_MYSTERY_GIFT_DONE
	end

MysteryEventScript_BattleCardInfo:
	lock
	faceplayer
	vmessage sText_MysteryGiftBattleCountCard
	waitmessage
	waitbuttonpress
	release
	end

sText_MysteryGiftBattleCountCard:
	.string "GİZEMLİ HEDİYE Sistemini kullandığın\n"
	.string "için teşekkürler.\p"
	.string "SAVAŞ SAYACI KARTI'n aynı KARTA sahip\n"
	.string "EĞİTMENLERE karşı savaş kaydını tutar.\p"
	.string "Seninle aynı KARTA sahip EĞİTMENLERİ\n"
	.string "bul ve onlarla savaş.\p"
	.string "HABERLER'i okuyarak genel sıralamaya\n"
	.string "bakabilirsin.\p"
	.string "Lütfen bir dene!$"

sText_MysteryGiftBattleCountCard_2:
	.string "GİZEMLİ HEDİYE Sistemini kullandığın\n"
	.string "için teşekkürler.\p"
	.string "Tebrikler!\p"
	.string "Üç savaş kazandığın için bir ödül\n"
	.string "kazandın!\p"
	.string "Daha çok savaşmak için ilham almanı\n"
	.string "dileriz.$"

MysteryEventScript_AuroraTicket::
	setvaddress MysteryEventScript_AuroraTicket
	lock
	faceplayer
	vgoto_if_set FLAG_RECEIVED_AURORA_TICKET, AuroraTicket_Obtained
	vgoto_if_set FLAG_FOUGHT_DEOXYS, AuroraTicket_Obtained
	checkitem ITEM_AURORA_TICKET, 1
	vgoto_if_eq VAR_RESULT, TRUE, AuroraTicket_Obtained
	vmessage sText_AuroraTicket1
	waitmessage
	waitbuttonpress
	checkitemspace ITEM_AURORA_TICKET, 1
	vgoto_if_eq VAR_RESULT, FALSE, AuroraTicket_NoBagSpace
	giveitem ITEM_AURORA_TICKET
	setflag FLAG_ENABLE_SHIP_BIRTH_ISLAND
	setflag FLAG_RECEIVED_AURORA_TICKET
	vmessage sText_AuroraTicket2
	waitmessage
	waitbuttonpress
	release
	end

AuroraTicket_NoBagSpace:
	vmessage sText_AuroraTicketNoPlace
	waitmessage
	waitbuttonpress
	release
	end

AuroraTicket_Obtained:
	vmessage sText_AuroraTicketGot
	waitmessage
	waitbuttonpress
	release
	end

sText_AuroraTicket1:
	.string "GİZEMLİ HEDİYE Sistemini kullandığın\n"
	.string "için teşekkürler.\p"
	.string "Sen {PLAYER} olmalısın.\n"
	.string "Burada senin için bir bilet var.$"

sText_AuroraTicket2:
	.string "VERMILION ŞEHRİ limanında kullanılacak\n"
	.string "gibi görünüyor.\p"
	.string "Neden denemiyor ve ne işe yaradığını\n"
	.string "görmüyorsun?$"

sText_AuroraTicketGot:
	.string "GİZEMLİ HEDİYE Sistemini kullandığın\n"
	.string "için teşekkürler.$"

sText_AuroraTicketNoPlace:
	.string "Ah, üzgünüm {PLAYER}. ÇANTANIN ÖNEMLİ\n"
	.string "EŞYALAR CEBİ dolu.\p"
	.string "Lütfen PC'nde bir şey depola, sonra\n"
	.string "bunun için geri gel.$"

MysteryEventScript_MysticTicket::
	setvaddress MysteryEventScript_MysticTicket
	lock
	faceplayer
	vgoto_if_set FLAG_RECEIVED_MYSTIC_TICKET, MysticTicket_Obtained
	vgoto_if_set FLAG_FOUGHT_LUGIA, MysticTicket_Obtained
	vgoto_if_set FLAG_FOUGHT_HO_OH, MysticTicket_Obtained
	checkitem ITEM_MYSTIC_TICKET, 1
	vgoto_if_eq VAR_RESULT, TRUE, MysticTicket_Obtained
	vmessage sText_MysticTicket2
	waitmessage
	waitbuttonpress
	checkitemspace ITEM_MYSTIC_TICKET, 1
	vgoto_if_eq VAR_RESULT, FALSE, MysticTicket_NoBagSpace
	giveitem ITEM_MYSTIC_TICKET
	setflag FLAG_ENABLE_SHIP_NAVEL_ROCK
	setflag FLAG_RECEIVED_MYSTIC_TICKET
	vmessage sText_MysticTicket1
	waitmessage
	waitbuttonpress
	release
	end

MysticTicket_NoBagSpace:
	vmessage sText_MysticTicketNoPlace
	waitmessage
	waitbuttonpress
	release
	end

MysticTicket_Obtained:
	vmessage sText_MysticTicketGot
	waitmessage
	waitbuttonpress
	release
	end

sText_MysticTicket2:
	.string "GİZEMLİ HEDİYE Sistemini kullandığın\n"
	.string "için teşekkürler.\p"
	.string "Sen {PLAYER} olmalısın.\n"
	.string "Burada senin için bir bilet var.$"

sText_MysticTicket1:
	.string "VERMILION ŞEHRİ limanında kullanılacak\n"
	.string "gibi görünüyor.\p"
	.string "Neden denemiyor ve ne işe yaradığını\n"
	.string "görmüyorsun?$"

sText_MysticTicketGot:
	.string "GİZEMLİ HEDİYE Sistemini kullandığın\n"
	.string "için teşekkürler.$"

sText_MysticTicketNoPlace:
	.string "Ah, üzgünüm {PLAYER}. ÇANTANIN ÖNEMLİ\n"
	.string "EŞYALAR CEBİ dolu.\p"
	.string "Lütfen PC'nde bir şey depola, sonra\n"
	.string "bunun için geri gel.$"

MysteryEventScript_AlteringCave::
	setvaddress MysteryEventScript_AlteringCave
	addvar VAR_ALTERING_CAVE_WILD_SET, 1
	vgoto_if_ne VAR_ALTERING_CAVE_WILD_SET, 10, MysteryEventScript_AlteringCave_
	setvar VAR_ALTERING_CAVE_WILD_SET, 0
MysteryEventScript_AlteringCave_:
	lock
	faceplayer
	vmessage sText_MysteryGiftAlteringCave
	waitmessage
	waitbuttonpress
	release
	end

sText_MysteryGiftAlteringCave:
	.string "GİZEMLİ HEDİYE Sistemini kullandığın\n"
	.string "için teşekkürler.\p"
	.string "Son zamanlarda nadir POKéMON\n"
	.string "görüldüğüne dair söylentiler var.\p"
	.string "Söylentiler SÜRGÜN ADASI'ndaki DEĞİŞEN\n"
	.string "MAĞARA hakkında.\p"
	.string "Neden oraya gidip söylentilerin doğru\n"
	.string "olup olmadığına bakmıyorsun?$"
