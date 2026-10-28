.equ GAVE_PROFILE,  VAR_TEMP_1

MysteryEventClub_EventScript_Woman::
	lock
	faceplayer
	goto_if_eq GAVE_PROFILE, TRUE, EventScript_AlreadyGaveProfile
	goto_if_set FLAG_SYS_SET_TRAINER_CARD_PROFILE, EventScript_GivenProfileBefore
	msgbox Text_IdLoveToHearYourProfile
	goto EventScript_AskForProfile
	end

EventScript_AlreadyGaveProfile:
	msgbox Text_TellMoreNextTime
	release
	end

EventScript_AskForProfile:
	message Text_TellMeWhatsYourProfile
	waitmessage
	multichoice 18, 6, MULTICHOICE_YES_NO_INFO_2, FALSE
	switch VAR_RESULT
	case 0, EventScript_AcceptGiveProfile
	case 1, EventScript_DeclineGiveProfile
	case 2, EventScript_ProfileInfo
	case SCR_MENU_CANCEL, EventScript_DeclineGiveProfile
	end

EventScript_ProfileInfo:
	msgbox Text_ExplainProfile
	goto EventScript_AskForProfile
	end

EventScript_AcceptGiveProfile:
	msgbox Text_WhatsYourProfile
	closemessage
	goto EventScript_GiveProfile
	end

EventScript_CancelGiveProfile:
	msgbox Text_DecidedNotTo
	release
	end

EventScript_GaveProfile:
	setvar GAVE_PROFILE, TRUE
	setvar VAR_0x8004, 0
	special ShowEasyChatMessage
	waitmessage
	delay 80
	msgbox Text_ProfileSaysSomethingAboutYou
	release
	end

EventScript_DeclineGiveProfile:
	msgbox Text_DontBeLikeThat
	release
	end

EventScript_GivenProfileBefore:
	msgbox Text_HiWeMeetAgain
	goto EventScript_AskForNewProfile
	end

EventScript_AskForNewProfile:
	message Text_ChangeYourProfile
	waitmessage
	multichoice 18, 6, MULTICHOICE_YES_NO_INFO_2, FALSE
	switch VAR_RESULT
	case 0, EventScript_AcceptGiveNewProfile
	case 1, EventScript_DeclineGiveNewProfile
	case 2, EventScript_ProfileInfo2
	case SCR_MENU_CANCEL, EventScript_DeclineGiveNewProfile
	end

EventScript_ProfileInfo2:
	msgbox Text_ExplainProfile
	goto EventScript_AskForNewProfile
	end

EventScript_AcceptGiveNewProfile:
	msgbox Text_WhatAreYouLikeNow
	closemessage
	goto EventScript_GiveProfile
	end

EventScript_DeclineGiveNewProfile:
	msgbox Text_LikeProfileWayItIs
	release
	end

EventScript_GaveSpecialProfile:
	setvar GAVE_PROFILE, TRUE
	setvar VAR_0x8004, 0
	special ShowEasyChatMessage
	waitmessage
	delay 80
	msgbox Text_HeardThatBefore
	release
	end

EventScript_GiveProfile:
	setvar VAR_0x8004, EASY_CHAT_TYPE_PROFILE
	call Common_ShowEasyChatScreen
	lock
	faceplayer
	goto_if_eq VAR_0x8004, 0, EventScript_GaveSpecialProfile
	goto_if_eq VAR_RESULT, FALSE, EventScript_CancelGiveProfile
	goto_if_eq VAR_RESULT, TRUE, EventScript_GaveProfile
	end

Text_IdLoveToHearYourProfile:
	.string "Selam, tanıştığımıza memnun oldum!\p"
	.string "…Bu hiç dostça değil.\n"
	.string "Sen de selam versene?\p"
	.string "Hadi, bana kendinden bahset.\p"
	.string "Profilini duymayı çok isterim!$"

Text_TellMeWhatsYourProfile:
	.string "Bana kendinle ilgili güzel bir şey\n"
	.string "söyle. Profilin ne?$"

Text_ExplainProfile:
	.string "Profil dört kelime ya da ifadeyle\n"
	.string "yazılır.\p"
	.string "Profilin için seçebileceğin pek çok\n"
	.string "kelime var.\p"
	.string "Kelimeler ve ifadeler birkaç kullanışlı\n"
	.string "gruba ayrılmıştır.\p"
	.string "Önce bir grup seç, sonra bir kelime ya\n"
	.string "da ifade seç.\p"
	.string "…Göründüğünden kolay.\n"
	.string "Neden denemiyorsun?$"

Text_WhatsYourProfile:
	.string "Profilin ne?$"

Text_DontBeLikeThat:
	.string "Of… Öyle yapma.\n"
	.string "Bana profilini söyleyebilirsin.$"

Text_DecidedNotTo:
	.string "Ah, vazgeçtin mi?\n"
	.string "Ne kadar kararsızsın, değil mi?$"

Text_HiWeMeetAgain:
	.string "Selam!\n"
	.string "Yine karşılaştık!$"

Text_ChangeYourProfile:
	.string "Profilini değiştirmek ister misin?$"

Text_WhatAreYouLikeNow:
	.string "Şimdi nasıl birisin?\n"
	.string "Gerçekten bilmek isterim.$"

Text_LikeProfileWayItIs:
	.string "Tamam, profilini olduğu gibi\n"
	.string "seviyorsun.\p"
	.string "Bence de güzel.$"

Text_ProfileSaysSomethingAboutYou:
	.string "Hmhm…\p"
	.string "Profilin gerçekten kim olduğun hakkında\n"
	.string "bir şeyler söylüyor.\p"
	.string "Seni daha iyi tanıdığıma göre artık her\n"
	.string "zamankinden daha iyi arkadaşız!$"

Text_HeardThatBefore:
	.string "Ah, bunu daha önce duymuştum…\p"
	.string "Sanırım uzakta yaşayan kuzenim hep\n"
	.string "böyle derdi.$"

Text_TellMoreNextTime:
	.string "Bir dahaki sefere bana kendinden daha\n"
	.string "çok bahset!$"
