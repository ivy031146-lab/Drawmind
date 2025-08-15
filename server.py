# server.py
import os, math
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import httpx

# =========================
# CHANGED: Developers 키 사용
# =========================
# 방법 A) 코드에 직접 넣기 (테스트용)
DEV_CLIENT_ID = os.environ.get("NAVER_DEV_CLIENT_ID", "XVuSwfoOb_1PXLpsmjH2")          # ← 당신의 Developers Client ID
DEV_CLIENT_SECRET = os.environ.get("NAVER_DEV_CLIENT_SECRET", "여기에_전체_Secret_문자열")  # ← 당신의 Developers Secret "전체" 값

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://127.0.0.1:8000"],
    allow_methods=["*"], allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"ok": True}

def haversine_km(lat1, lon1, lat2, lon2):
    dLat = math.radians(lat2-lat1); dLon = math.radians(lon2-lon1)
    a = math.sin(dLat/2)**2 + math.cos(math.radians(lat1))*math.cos(math.radians(lat2))*math.sin(dLon/2)**2
    return 6371.0 * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

@app.get("/api/centers")
async def centers(lat: float, lng: float):
    headers = {
        # CHANGED: Developers 키 헤더
        "X-Naver-Client-Id": DEV_CLIENT_ID,
        "X-Naver-Client-Secret": DEV_CLIENT_SECRET,
    }
    params_base = {"query": "치매안심센터", "display": 5, "sort": "random"}
    items = []

    async with httpx.AsyncClient(timeout=10) as client:
        for start in (1, 6, 11):
            params = {**params_base, "start": start}
            r = await client.get("https://openapi.naver.com/v1/search/local.json",
                                 params=params, headers=headers)
            if r.status_code != 200:
                # 디버깅용: 인증 실패/쿼터 초과/파라미터 오류 등 메시지 확인
                return {"error": r.status_code, "detail": r.text}

            data = r.json()
            for it in data.get("items", []):
                try:
                    lon = float(it.get("mapx",0))/1e7   # 경도
                    lat_ = float(it.get("mapy",0))/1e7  # 위도
                except Exception:
                    continue
                if not lon or not lat_:
                    continue
                dist = haversine_km(lat, lng, lat_, lon)
                items.append({
                    "title": (it.get("title") or "").replace("<b>","").replace("</b>",""),
                    "address": it.get("address"),
                    "roadAddress": it.get("roadAddress"),
                    "telephone": it.get("telephone"),
                    "lat": lat_, "lng": lon,
                    "distance_km": dist
                })

    items.sort(key=lambda v: v["distance_km"])
    return {"items": items[:20]}
