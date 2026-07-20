"""Translation module — translates citizen-facing verdict and actions to Indian languages."""

import json
import logging
from typing import Dict, List
from backend.core.llm import get_llm
from langchain_core.messages import HumanMessage, SystemMessage

logger = logging.getLogger(__name__)

LANGUAGE_NAMES = {
    "en": "English",
    "hi": "Hindi",
    "ta": "Tamil",
    "bn": "Bengali",
    "te": "Telugu",
}

SUPPORTED_LANGUAGES = list(LANGUAGE_NAMES.keys())

TRANSLATION_PROMPT = """Translate the following scam alert text into {language_name} ({language_code}).
Translate naturally and clearly — this is a safety warning for Indian citizens.
Keep proper nouns, numbers, and phone numbers as-is.
Return ONLY a valid JSON object with this exact structure:
{{
  "translated_verdict": "translated verdict text",
  "translated_actions": ["translated action 1", "translated action 2"]
}}
No preamble, no explanation, no markdown fences."""

# Pre-defined translations for common verdicts (avoids LLM call for speed)
FALLBACK_VERDICTS = {
    "hi": {
        "digital_arrest": "यह डिजिटल अरेस्ट स्कैम है। कोई भी सरकारी एजेंसी वीडियो कॉल पर गिरफ्तारी नहीं करती। पैसे ट्रांसफर न करें।",
        "fake_kyc": "यह फर्जी KYC स्कैम है। आपका बैंक कभी OTP या पासवर्ड नहीं मांगता।",
        "fake_investment": "यह फर्जी निवेश स्कैम है। गारंटीशुदा ऊंचे रिटर्न हमेशा धोखाधड़ी होते हैं।",
        "fake_job": "यह फर्जी नौकरी स्कैम है। कानूनी नियोक्ता कभी रजिस्ट्रेशन फीस नहीं मांगते।",
        "fake_lottery": "यह फर्जी लॉटरी स्कैम है। आपने कोई पुरस्कार नहीं जीता है।",
        "impersonation": "यह प्रतिरूपण स्कैम है। कॉलर जिसका दावा कर रहा है वह वही नहीं है। तुरंत कॉल काटें।",
        "romance_scam": "यह रोमांस स्कैम है। ऑनलाइन मिला व्यक्ति असली नहीं है। पैसे न भेजें।",
    },
    "ta": {
        "digital_arrest": "இது டிஜிட்டல் கைது மோசடி. எந்த அரசு நிறுவனமும் வீடியோ அழைப்பில் கைது செய்யாது. பணம் அனுப்ப வேண்டாம்.",
        "fake_kyc": "இது போலி KYC மோசடி. உங்கள் வங்கி ஒருபோதும் OTP அல்லது கடவுச்சொல்லைக் கேட்காது.",
        "fake_investment": "இது போலி முதலீட்டு மோசடி. உத்தரவாதமான அதிக வருமானம் எப்போதும் மோசடியாகும்.",
        "fake_job": "இது போலி வேலை மோசடி. சட்டவிதியான நிறுவனங்கள் பதிவு கட்டணம் கேட்காது.",
        "fake_lottery": "இது போலி லாட்டரி மோசடி. நீங்கள் பரிசு வென்றிருக்கவில்லை.",
        "impersonation": "இது மித்திர மோசடி. அழைப்பவர் கூறுவது போல் இல்லை. உடனடியாக அழைப்பைத் துண்டியுங்கள்.",
        "romance_scam": "இது காதல் மோசடி. ஆன்லைனில் சந்தித்த நபர் உண்மையானவர் அல்ல. பணம் அனுப்ப வேண்டாம்.",
    },
    "bn": {
        "digital_arrest": "এটি ডিজিটাল আরেস্ট স্ক্যাম। কোনো সরকারি সংস্থা ভিডিয়ো কলে গ্রেফতার করে না। টাকা ট্রান্সফার করবেন না।",
        "fake_kyc": "এটি জাল KYC স্ক্যাম। আপনার ব্যাংক কখনও OTP বা পাসওয়ার্ড চাইবে না।",
        "fake_investment": "এটি জাল বিনিয়োগ স্ক্যাম। গ্যারান্টিযুক্ত উচ্চ রিটার্ন সবসময় প্রতারণা।",
        "fake_job": "এটি জাল চাকরি স্ক্যাম। আইনসম্মত নিয়োগদাতারা কখনও নিবন্ধন ফি চাইবে না।",
        "fake_lottery": "এটি জাল লটারি স্ক্যাম। আপনি কোনো পুরস্কার জিতেননি।",
        "impersonation": "এটি ছদ্ববেশী স্ক্যাম। কলকারী যা দাবি করছেন তা সত্য নয়। এখনই কল কাটুন।",
        "romance_scam": "এটি প্রেম স্ক্যাম। অনলাইনে দেখা ব্যক্তি আসল নয়। টাকা পাঠাবেন না।",
    },
    "te": {
        "digital_arrest": "ఇది డిజిటల్ అరెస్ట్ స్కామ్. ఏ ప్రభుత్వ సంస్థ వీడియో కాల్‌లో అరెస్ట్ చేయదు. డబ్బు ట్రాన్స్‌ఫర్ చేయవద్దు.",
        "fake_kyc": "ఇది నకిలీ KYC స్కామ్. మీ బ్యాంక్ ఎప్పుడూ OTP లేదా పాస్‌వర్డ్ అడగదు.",
        "fake_investment": "ఇది నకిలీ పెట్టుబడి స్కామ్. హామీ ఎక్కువ రిటర్న్స్ ఎల్లప్పుడూ మోసం.",
        "fake_job": "ఇది నకిలీ ఉద్యోగ స్కామ్. చట్టబద్ధ నియోక్తలు ఎప్పుడూ రిజిస్ట్రేషన్ ఫీజు అడగరు.",
        "fake_lottery": "ఇది నకిలీ లాటరీ స్కామ్. మీరు బహుమతి గెలవలేదు.",
        "impersonation": "ఇది మోసపూరిత స్కామ్. కాలర్ చెప్పేది నిజం కాదు. వెంటనే కాల్ కట్ చేయండి.",
        "romance_scam": "ఇది ప్రేమ స్కామ్. ఆన్‌లైన్‌లో కలిసిన వ్యక్తి నిజమైనవాడు కాదు. డబ్బు పంపవద్దు.",
    },
}


def translate_verdict(
    one_line_verdict: str,
    recommended_actions: List[str],
    target_language: str,
) -> dict:
    """
    Translate citizen-facing verdict and actions into target language.
    Uses LLM for translation. Falls back to pre-defined translations if available.
    Returns {translated_verdict, translated_actions}.
    """
    if target_language == "en" or target_language not in SUPPORTED_LANGUAGES:
        return {
            "translated_verdict": one_line_verdict,
            "translated_actions": recommended_actions,
        }

    lang_name = LANGUAGE_NAMES.get(target_language, target_language)

    # Try LLM translation first
    try:
        llm = get_llm(temperature=0.1)
        prompt = TRANSLATION_PROMPT.format(
            language_name=lang_name,
            language_code=target_language,
        )
        actions_text = "\n".join(f"- {a}" for a in recommended_actions[:3])
        user_msg = f"Verdict: {one_line_verdict}\n\nActions:\n{actions_text}"

        response = llm.invoke([
            SystemMessage(content=prompt),
            HumanMessage(content=user_msg),
        ])

        content = response.content.strip()
        # Clean markdown fences if present
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        content = content.strip()

        data = json.loads(content)
        return {
            "translated_verdict": data.get("translated_verdict", one_line_verdict),
            "translated_actions": data.get("translated_actions", recommended_actions[:3]),
        }

    except Exception as e:
        logger.warning(f"LLM translation failed for {target_language}: {e}")

    # Fallback: use pre-defined translations if available
    scam_type = None
    for stype in FALLBACK_VERDICTS.get(target_language, {}).keys():
        if stype in one_line_verdict.lower().replace(" ", "_"):
            scam_type = stype
            break

    if scam_type and target_language in FALLBACK_VERDICTS:
        translated = FALLBACK_VERDICTS[target_language][scam_type]
        return {
            "translated_verdict": translated,
            "translated_actions": recommended_actions[:3],
        }

    # Final fallback: return English with note
    return {
        "translated_verdict": f"[Translation unavailable for {lang_name}] {one_line_verdict}",
        "translated_actions": recommended_actions[:3],
    }
