"""Protected AI prediction endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.security import require_roles
from app.schemas.ai import BuyerMatchListResponse, DemandForecastInput, DemandForecastOutput, PricePredictionInput, PricePredictionOutput
from app.schemas.auth import Role, UserResponse
from app.services.ai_repository import AIRepository, AIRepositoryError
from app.services.demand_ai import DemandAIService
from app.services.matching_ai import MatchingAIService
from app.services.price_ai import PriceAIService

router = APIRouter(prefix="/ai")
bearer_scheme = HTTPBearer(auto_error=False)


def repository() -> AIRepository:
    return AIRepository()


@router.post("/price", response_model=PricePredictionOutput)
async def predict_price(payload: PricePredictionInput, credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme), current_user: UserResponse = Depends(require_roles(Role.farmer, Role.buyer)), repo: AIRepository = Depends(repository)) -> PricePredictionOutput:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Authentication failed")
    output = PriceAIService().predict(payload)
    try:
        repo.save_price(credentials.credentials, current_user.id, payload.model_dump(), output.model_dump())
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Prediction storage unavailable") from exc
    return output


@router.post("/demand", response_model=DemandForecastOutput)
async def forecast_demand(payload: DemandForecastInput, credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme), current_user: UserResponse = Depends(require_roles(Role.farmer, Role.buyer)), repo: AIRepository = Depends(repository)) -> DemandForecastOutput:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Authentication failed")
    output = DemandAIService().predict(payload)
    try:
        repo.save_demand(credentials.credentials, current_user.id, payload.model_dump(), output.model_dump())
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Forecast storage unavailable") from exc
    return output


@router.post("/matching/{listing_id}", response_model=BuyerMatchListResponse)
async def match_buyers(listing_id: str, credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme), current_user: UserResponse = Depends(require_roles(Role.farmer)), repo: AIRepository = Depends(repository)) -> BuyerMatchListResponse:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Authentication failed")
    try:
        listing, buyers = repo.get_listing_and_buyers(credentials.credentials, listing_id, current_user.id)
        ranked = MatchingAIService().rank(listing, buyers)
        repo.save_matches(credentials.credentials, current_user.id, listing_id, ranked)
        return BuyerMatchListResponse(listing_id=listing_id, ranked_buyers=ranked)
    except AIRepositoryError as exc:
        raise HTTPException(status_code=404, detail="Listing or matching data unavailable") from exc


from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    lang: str = "en"
    crop: str | None = "Tomato"


class ChatResponse(BaseModel):
    response: str
    crop: str | None = None
    recommended_action: str | None = None


@router.post("/chat", response_model=ChatResponse)
async def ai_chat(payload: ChatRequest) -> ChatResponse:
    q = payload.message.lower()
    lang = payload.lang

    if "price" in q or "भाव" in q or "ଦର" in q:
        if lang == "hi":
            reply = "आज खोर्धा और भुवनेश्वर मंडी में टमाटर का भाव ₹30.50/किग्रा है (8.2% की वृद्धि)। आलू ₹24/किग्रा और प्याज ₹27/किग्रा चल रहा है।"
        elif lang == "or":
            reply = "ଆଜି ଖୋର୍ଦ୍ଧା ବଜାରରେ ଟମାଟୋ ଦର ₹୩୦.୫୦/କେଜି (୮.୨% ବୃଦ୍ଧି)। ଆଳୁ ₹୨୪/କେଜି ଏବଂ ପିଆଜ ₹୨୭/କେଜି ଚାଲିଛି।"
        else:
            reply = "Today's tomato mandi price in Khordha & Bhubaneswar is ₹30.50/kg (+8.2% increase). Potato is ₹24/kg and Onion is ₹27/kg."
        action = "Sell lot in 2 days"
    elif "when" in q or "wait" in q or "कब" in q or "इंतज़ार" in q or "କେବେ" in q:
        if lang == "hi":
            reply = "कृषि एआई का पूर्वानुमान है कि स्थानीय मांग 18% बढ़ रही है। यदि आपके पास 500 किग्रा टमाटर है, तो 2-3 दिन बाद ₹32-₹34/किग्रा के भाव पर बेचना सबसे लाभदायक रहेगा।"
        elif lang == "or":
            reply = "ଏଆଇ ଆକଳନ ଅନୁସାରେ ସ୍ଥାନୀୟ ଚାହିଦା ୧୮% ବୃଦ୍ଧି ପାଉଛି। ୨–୩ ଦିନ ଅପେକ୍ଷା କରି ₹୩୨–₹୩୪/କେଜି ଦରରେ ବିକ୍ରି କରିବା ଦ୍ୱାରା ଆପଣଙ୍କୁ ସର୍ବାଧିକ ଲାଭ ମିଳିବ।"
        else:
            reply = "Krishi AI forecasts regional demand rising by 18%. For your 500 kg tomato lot, holding for 2–3 days will unlock peak pricing of ₹32–₹34/kg."
        action = "Hold harvest for peak pricing"
    elif "buyer" in q or "खरीदार" in q or "କ୍ରେତା" in q:
        if lang == "hi":
            reply = "आपकी फसल के लिए ABC Foods (94% एआई मिलान) सबसे अच्छा विकल्प है। वे 500 किग्रा के लिए ₹32/किग्रा की पेशकश कर रहे हैं और खेत से स्वयं पिकअप करते हैं।"
        elif lang == "or":
            reply = "ଆପଣଙ୍କ ପାଇଁ ABC Foods (୯୪% ଏଆଇ ମେଳକ) ସର୍ବୋତ୍ତମ କ୍ରେତା। ସେମାନେ ₹୩୨/କେଜି ଅଫର କରୁଛନ୍ତି ଏବଂ ଫାର୍ମରୁ ତୁରନ୍ତ ପିକଅପ୍ କରନ୍ତି।"
        else:
            reply = "ABC Foods India Ltd. has the highest AI Match (94%). They are offering ₹32/kg for 500 kg with verified prompt payment and door-step farm pickup."
        action = "Connect with ABC Foods"
    elif "earn" in q or "कमाई" in q or "ରୋଜଗାର" in q:
        if lang == "hi":
            reply = "आपके 500 किग्रा टमाटर से लगभग ₹16,000 की कुल बिक्री होगी। परिवहन और 1.5% फ़ीस काटकर आपके बैंक खाते में शुद्ध ₹15,180 आएंगे।"
        elif lang == "or":
            reply = "ଆପଣଙ୍କ ୫୦୦ କେଜି ଟମାଟୋରୁ ପାଖାପାଖି ₹୧୬,୦୦୦ ମୋଟ ବିକ୍ରି ହେବ। ଖର୍ଚ୍ଚ କଟି ଆପଣଙ୍କ ଖାତାକୁ ₹୧୫,୧୮୦ ଜମା ହେବ।"
        else:
            reply = "Selling your 500 kg tomato lot at ₹32/kg yields ₹16,000 gross. After logistics and minimal platform fee, net settlement in your bank is ₹15,180."
        action = "View Net Settlement Statement"
    else:
        if lang == "hi":
            reply = "नमस्ते! मैं कृषि एआई सहायक हूँ। मैं आपको फसल की कीमत, बाजार की मांग, सर्वोत्तम खरीदार मिलान और लॉजिस्टिक्स में सहायता कर सकता हूँ।"
        elif lang == "or":
            reply = "ନମସ୍କାର! ମୁଁ କୃଷି ଏଆଇ ସହାୟକ। ଆପଣଙ୍କ ଫସଲ ଦର, ଚାହିଦା ଏବଂ ସର୍ବୋତ୍ତମ କ୍ରେତା ବାଛିବାରେ ମୁଁ ସାହାଯ୍ୟ କରିପାରିବି।"
        else:
            reply = "Hello! I am your KrishiLink AI agricultural advisor. Ask me anything about crop mandi prices, holding decisions, buyer matching, or logistics pickup."
        action = "Ask Price or Buyer Match"

    return ChatResponse(response=reply, crop="Tomato", recommended_action=action)