# %%
import os
import re
import csv
import time
import requests
import pypdf
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# %%
# 설정
BASE_URL = "https://genai-sharedservice-americas.pwcinternal.com/v1/responses"
API_KEY = os.getenv("API_KEY")
HEADERS = {"Content-Type": "application/json", "Authorization": f"Bearer {API_KEY}"}

MODEL = "vertex_ai.anthropic.claude-sonnet-4-6"

PDF_FOLDER = os.path.join(os.path.dirname(__file__), "EG Daily Report")
MODELS_CSV = os.path.join(os.path.dirname(__file__), "Models.csv")
OUTPUT_CSV = os.path.join(os.path.dirname(__file__), "daily_summary.csv")

# Models.csv에서 단가 로드
models_df = pd.read_csv(MODELS_CSV).dropna(subset=["Public Model Name"])
price_map = {
    row["Public Model Name"]: {
        "input": row["Input Cost per 1M tokens ($)"],
        "output": row["Output Cost per 1M tokens ($)"],
    }
    for _, row in models_df.iterrows()
}
MODEL_PRICE = price_map.get(MODEL, {"input": 0, "output": 0})
print(
    f"모델 단가 — input: ${MODEL_PRICE['input']}/1M, output: ${MODEL_PRICE['output']}/1M"
)

DAYS_KO = ["월", "화", "수", "목", "금", "토", "일"]


# %%
# PDF 텍스트 추출
def extract_pdf_text(pdf_path):
    reader = pypdf.PdfReader(pdf_path)
    return "\n".join(page.extract_text() or "" for page in reader.pages)


# 파일명에서 날짜 파싱
# 우선순위: (YYYY.MM.DD) → (MM.DD) (연도는 파일 수정연도 사용)
def filename_to_date(fname, fallback_year=None):
    # (YYYY.MM.DD) 형식 시도
    m = re.search(r"\((\d{4})\.(\d{1,2})\.(\d{1,2})\)", fname)
    if m:
        year, month, day = int(m.group(1)), int(m.group(2)), int(m.group(3))
        return f"{year}-{month:02d}-{day:02d}"

    # (MM.DD) 형식 시도 — 연도는 fallback_year 또는 현재 연도
    m = re.search(r"\((\d{1,2})\.(\d{1,2})\)", fname)
    if m:
        year = fallback_year or datetime.now().year
        month, day = int(m.group(1)), int(m.group(2))
        return f"{year}-{month:02d}-{day:02d}"

    return None


def date_to_day_of_week(date_str):
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return DAYS_KO[dt.weekday()]  # 월=0 ... 일=6
    except ValueError:
        return ""


# %%
# 요약 프롬프트
SUMMARIZE_SYSTEM = """당신은 삼일회계법인(PwC Korea)의 글로벌 정세 분석 전문가입니다.
Eurasia Group의 Daily Brief 원문을 기반으로, 삼일회계법인 임원진(C-Level)이 담당 고객사(국내 50대 대기업)에 미치는 영향을 판단하는 데 활용할 수 있도록 일일 글로벌 정세 동향을 한국어로 요약합니다.

<absolute_rules>
- 입력된 원문에 명시적으로 기재된 내용만 사용할 것.
- AI가 사전 학습한 지식, 외부 정보, 추측, 의견을 절대 포함하지 말 것.
- 원문에 없는 수치·사실·인과관계를 임의로 생성하거나 추가하지 말 것.
- 확인되지 않는 내용은 쓰지 않는 것이 누락보다 나음.
</absolute_rules>

<content_rules>
- 리포트 상단의 "summary bullets"를 구조적 뼈대로 활용할 것. 각 bullet은 다뤄야 할 핵심 주제 하나에 해당함. 마지막 bullet은 다룬 지역·국가·섹터를 나열한 것(예: "Regions/countries and sectors covered in this edition include...")으로, 관련 행위자와 주제가 모두 포함되도록 키워드 참조용으로 활용할 것.
- 리포트 본문 전체에서 구체적인 수치(확률, 가격, 퍼센트, 날짜, 수치 목표)를 찾아 각 주제에 보강할 것 — summary bullets에만 의존하지 말 것.
- 동일 행위자·지역을 다루는 여러 bullet은 하나의 문장으로 통합할 것.
- 환율·금리·원자재 가격에 영향을 줄 수 있는 거시 변수를 우선 반영할 것.
- 분량: 3~5문장, 약 150~300자를 목표로 할 것.
</content_rules>

<style_rules>
- 한국어 요약 본문만 출력할 것. 제목, 날짜, 머리말("안녕하세요", "다음은 요약입니다" 등) 일체 금지.
- C-Level 보고에 적합한 간결하고 전문적인 톤 유지.
- 금지 표현: "기본 시나리오", "양보 가능" 등 영어 직역 표현. 자연스러운 한국어 표현으로 대체할 것.
- 문장 어미: "~습니다", "~입니다", "~했습니다" 등 완성형 서술어 종결 금지. 반드시 명사형·분석형 어미로 마칠 것 (예: ~전망, ~예정, ~우려, ~추진, ~전환, ~불가피, ~이어질 것으로 보임). 예시의 문장 종결 방식을 엄격히 따를 것.
- 인명 최초 등장 시 직함 병기 (예: 젤렌스키 대통령, 멜로니 총리).
- 논조: 사실 중심, 분석적, 핵심 수치가 밀도 있게 담긴 문체.
</style_rules>

<examples>
<example id="1">
이란전이 트럼프의 전략적 오판으로 귀결되는 양상이며 2~3주 내 협상 출구가 유력한 경로(60%). 중국은 성장목표를 4.5에서 5%로 하향하고 AI 및 부채 해소에 정책 우선순위 전환. 이란전 장기화 시 유럽은 에너지, 난민, 테러 삼중 리스크에 노출되며 러시아는 유가 상승분을 우크라이나전에 재투입할 전망. EU 메르코수르 협정 4월 잠정 발효 예정.
</example>
<example id="2">
미·중 트럼프 4월 방중에서 휴전 연장 및 중국의 미국산 농산물·에너지·항공기 구매 확대 합의는 가능하나 양국 관계의 본질적 변화는 어려울 것(휴전 유지 65%, 결렬 리스크 20%). 우크라이나 국민 여론상 불리한 조건의 평화보다 전쟁 지속을 지지하는 분위기로 젤렌스키 대통령의 협상 카드가 제한적(6월까지 휴전 합의 불발 65%). 이탈리아 멜로니 총리, 2027년 재선에 유리하도록 선거제도 개편 추진(통과 가능성 60%). 이란·러-우크라 지정학 리스크로 1분기 브렌트유 $60~70 유지 전망, 수요 둔화로 공급과잉 흐름이나 급락 가능성은 낮음.
</example>
</examples>

<final_reminder>제목·머리말 없이 요약 본문만 출력할 것. 분량을 준수할 것. summary bullets의 마지막 포인트를 제외한 모든 주제를 빠짐없이 다루고, 리포트 본문에서 수치를 보강하며, 사실 중심의 분석적 논조를 유지할 것. 모든 문장은 "~습니다/~입니다" 종결 없이 예시와 동일한 명사형·분석형 어미로 마칠 것.</final_reminder>"""


# %%
# API 호출
def call_api(messages, temperature=0.0):
    payload = {
        "model": MODEL,
        "input": messages,
        "stream": False,
        "temperature": temperature,
    }
    resp = requests.post(BASE_URL, headers=HEADERS, json=payload, timeout=120)
    resp.raise_for_status()
    result = resp.json()
    text = result["output"][0]["content"][0]["text"]
    usage = result.get("usage", {})
    return text, usage.get("input_tokens", 0), usage.get("output_tokens", 0)


def summarize(report_text):
    messages = [
        {"role": "user", "content": SUMMARIZE_SYSTEM},
        {"role": "user", "content": f"<report>\n{report_text}\n</report>"},
    ]
    return call_api(messages, temperature=0.0)


# %%
# 이미 처리된 날짜 로드 → 재시작 시 중복 방지
done_dates = set()
if os.path.exists(OUTPUT_CSV):
    existing_df = pd.read_csv(OUTPUT_CSV, encoding="utf-8-sig")
    done_dates = set(existing_df["date"].astype(str))
    print(f"기존 결과 {len(done_dates)}건 로드 (스킵 예정)")

# %%
# PDF 파일 목록 수집 및 날짜 파싱
pdf_files = sorted(f for f in os.listdir(PDF_FOLDER) if f.endswith(".pdf"))

items = []
for fname in pdf_files:
    fpath = os.path.join(PDF_FOLDER, fname)
    # 파일 수정연도를 연도 fallback으로 사용
    mtime_year = datetime.fromtimestamp(os.path.getmtime(fpath)).year
    date_str = filename_to_date(fname, fallback_year=mtime_year)
    if date_str:
        items.append({"filename": fname, "date": date_str})

print(f"PDF 총 {len(pdf_files)}개 중 날짜 파싱 성공: {len(items)}개")

# %%
# 일일 요약 실행
print(f"\n{'='*60}")
print(f"모델: {MODEL}")
print(f"{'='*60}")

for item in items:
    if item["date"] in done_dates:
        print(f"  [{item['date']}] 스킵 (이미 완료)")
        continue

    day_of_week = date_to_day_of_week(item["date"])
    print(f"  [{item['date']}({day_of_week})] {item['filename'][:50]} ...", end=" ")

    fpath = os.path.join(PDF_FOLDER, item["filename"])
    try:
        report_text = extract_pdf_text(fpath)
    except Exception as e:
        print(f"PDF 추출 실패: {e}")
        continue

    try:
        t0 = time.time()
        summary, in_tok, out_tok = summarize(report_text)
        elapsed = round(time.time() - t0, 2)
    except Exception as e:
        print(f"요약 실패: {e}")
        continue

    cost = (in_tok * MODEL_PRICE["input"] + out_tok * MODEL_PRICE["output"]) / 1_000_000

    row = {
        "date": item["date"],
        "day_of_week": day_of_week,
        "filename": item["filename"],
        "summary": summary,
        "elapsed_sec": elapsed,
        "input_tokens": in_tok,
        "output_tokens": out_tok,
        "cost_usd": round(cost, 6),
    }

    write_header = not os.path.exists(OUTPUT_CSV)
    with open(OUTPUT_CSV, "a", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(row.keys()))
        if write_header:
            writer.writeheader()
        writer.writerow(row)

    done_dates.add(item["date"])
    print(f"완료 | cost=${cost:.5f} | {elapsed}s")
    time.sleep(0.5)

# %%
# 결과 확인
if os.path.exists(OUTPUT_CSV):
    result_df = pd.read_csv(OUTPUT_CSV, encoding="utf-8-sig")
    print(f"\n총 {len(result_df)}건 저장 완료: {OUTPUT_CSV}")
    print(result_df[["date", "day_of_week", "summary"]].to_string())

# %%
