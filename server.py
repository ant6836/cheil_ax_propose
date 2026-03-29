"""
제일기획 AI 전략 인텔리전스 — Graph-RAG 백엔드
LLM 호출 패턴: 06_daily_summary.py (requests.post, Bearer Token)
실행: python server.py
"""

import os
import re
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import requests as req

load_dotenv()

app = Flask(__name__)
CORS(app)

BASE_URL = os.getenv("BASE_URL", "")
API_KEY = os.getenv("API_KEY", "")
MODEL = os.getenv("MODEL", "vertex_ai.anthropic.claude-sonnet-4-6")
HEADERS = {"Content-Type": "application/json", "Authorization": f"Bearer {API_KEY}"}

# ============================================================
# ONTOLOGY DATA (dashboard.html ONTOLOGY_DATA와 동기화)
# ============================================================
NODES = [
    # 강점
    {
        "id": "S1",
        "type": "strength",
        "label": "국내 과점 지위",
        "desc": "국내 광고대행 시장 점유율 1위. 삼성 계열 물량으로 형성된 진입장벽이 높은 구조적 강점.",
        "region": "all",
    },
    {
        "id": "S2",
        "type": "strength",
        "label": "현금 4,700억",
        "desc": "2024년 기준 순현금 4,700억원 보유. M&A 및 AI 투자에 즉시 활용 가능한 재무 기반.",
        "region": "all",
    },
    {
        "id": "S3",
        "type": "strength",
        "label": "M&A 디지털 자산",
        "desc": "McKinney(북미), Iris(유럽) 등 해외 자회사 및 AI 스타트업 지분 보유.",
        "region": "all",
    },
    {
        "id": "S4",
        "type": "strength",
        "label": "Copy Joe · Conti Joe",
        "desc": "국내 최초 광고 특화 생성형AI 도구. 텍스트·이미지 생성 영역에서 내부 생산성 증가.",
        "region": "all",
    },
    # 약점
    {
        "id": "W1",
        "type": "weakness",
        "label": "삼성 의존도 71%",
        "desc": "매출의 71%가 삼성 계열사에서 발생. 클라이언트 다변화 부재로 수익 구조 취약.",
        "region": "all",
    },
    {
        "id": "W2",
        "type": "weakness",
        "label": "AI 전략 실행 격차",
        "desc": "AI 전략 수립은 완료되었으나 실제 실행 속도가 경쟁사 대비 18개월 지연.",
        "region": "all",
    },
    {
        "id": "W3",
        "type": "weakness",
        "label": "가치사슬 AI 공백",
        "desc": "퍼포먼스 최적화·미디어 바잉·데이터 분석 등 핵심 가치사슬에 AI 도구 부재.",
        "region": "all",
    },
    {
        "id": "W4",
        "type": "weakness",
        "label": "AI 투자 실행 지연",
        "desc": "이사회 승인된 AI 투자 계획이 실행 단계에서 지연되는 거버넌스 이슈.",
        "region": "all",
    },
    # 기회
    {
        "id": "O1",
        "type": "opportunity",
        "label": "생성형AI 광고시장",
        "desc": "2032년 1,924억 달러 규모 전망. 현재 초기 시장 선점 가능한 황금 창(窓).",
        "region": "all",
    },
    {
        "id": "O2",
        "type": "opportunity",
        "label": "리테일 미디어",
        "desc": "Amazon·Walmart 등 리테일 미디어 시장 1,795억 달러 돌파. AI 자동화 수요 급증.",
        "region": "all",
    },
    {
        "id": "O3",
        "type": "opportunity",
        "label": "신흥시장 성장",
        "desc": "북미·유럽 비계열 광고주 시장 진입 기회. 해외 자회사를 통한 교두보 확보 가능.",
        "region": "북미",
    },
    {
        "id": "O5",
        "type": "opportunity",
        "label": "AI M&A 기회창",
        "desc": "AI 스타트업 밸류에이션 조정기. 생성형AI·미디어테크 분야 전략적 인수 적기.",
        "region": "all",
    },
    # 위협
    {
        "id": "T1",
        "type": "threat",
        "label": "WPP 경로 리스크",
        "desc": "WPP의 시총 87% 소멸은 AI 대응 지연 시 대형 에이전시도 몰락 가능함을 증명.",
        "region": "all",
    },
    {
        "id": "T2",
        "type": "threat",
        "label": "빅테크 직접 집행",
        "desc": "Google·Meta·Amazon이 광고주에게 직접 AI 광고 도구를 제공하며 에이전시 역할 잠식.",
        "region": "all",
    },
    {
        "id": "T3",
        "type": "threat",
        "label": "Publicis AI 독주",
        "desc": "Publicis의 AI 수주 실적이 WPP 대비 2배. 글로벌 AI 광고 표준을 선점 중.",
        "region": "all",
    },
    # 약신호
    {
        "id": "WS1",
        "type": "signal",
        "label": "생성형AI 광고",
        "desc": "소셜에서 AI 생성 광고 크리에이티브 관련 논의 급증. 광고주의 직접 도입 사례 증가.",
        "region": "all",
    },
    {
        "id": "WS2",
        "type": "signal",
        "label": "Retail Media AI",
        "desc": "에이전시의 수동 리테일 미디어 운영 한계에 대한 불만이 소셜·포럼에서 다수 감지.",
        "region": "북미",
    },
    {
        "id": "WS3",
        "type": "signal",
        "label": "EU AI법 시행",
        "desc": "EU AI법 크리에이티브 공개 의무화 시행 임박. 유럽 광고주의 컴플라이언스 수요 급증.",
        "region": "유럽",
    },
    {
        "id": "WS4",
        "type": "signal",
        "label": "취약성 마케팅",
        "desc": "Z세대 대상 불완전함을 드러내는 진정성 마케팅 트렌드. 기존 광고 대비 호감도 +43%.",
        "region": "all",
    },
    # 핵심 역량
    {
        "id": "CREATIVE",
        "type": "concept",
        "label": "크리에이티브 자동화",
        "desc": "생성형AI를 활용한 광고 크리에이티브 제작 자동화. 텍스트·이미지·영상 생성 포함.",
        "region": "all",
    },
    {
        "id": "AI_ADV",
        "type": "concept",
        "label": "AI 광고 플랫폼",
        "desc": "AI 기반 광고 집행·최적화 플랫폼. 퍼포먼스 마케팅과 크리에이티브 생성을 통합.",
        "region": "all",
    },
    {
        "id": "RETAIL_M",
        "type": "concept",
        "label": "리테일 미디어 AI",
        "desc": "Amazon·Walmart 등 리테일 미디어의 AI 자동화 바잉·최적화 서비스.",
        "region": "all",
    },
    {
        "id": "DATA_INT",
        "type": "concept",
        "label": "데이터 통합",
        "desc": "광고 성과 데이터·소비자 행동 데이터·미디어 집행 데이터를 통합 분석하는 인프라.",
        "region": "all",
    },
    {
        "id": "COMP_OBL",
        "type": "concept",
        "label": "AI 컴플라이언스",
        "desc": "EU AI법 등 규제 환경에서 광고 크리에이티브의 법적 요건 충족을 보장하는 서비스.",
        "region": "all",
    },
    {
        "id": "PERF_OPT",
        "type": "concept",
        "label": "퍼포먼스 최적화",
        "desc": "AI 기반 광고 입찰·예산 배분·타겟팅 자동화로 마케팅 ROI를 극대화하는 역량.",
        "region": "all",
    },
    {
        "id": "AUDIENCE",
        "type": "concept",
        "label": "오디언스 인텔리전스",
        "desc": "AI 기반 소비자 세분화·행동 예측·개인화 타겟팅 역량.",
        "region": "all",
    },
    {
        "id": "MKTG_ROI",
        "type": "concept",
        "label": "마케팅 ROI",
        "desc": "AI 광고 투자 대비 수익률을 실시간으로 측정하고 최적화하는 분석 역량.",
        "region": "all",
    },
    # 보유 자산
    {
        "id": "COPY JOE",
        "type": "asset",
        "label": "Copy Joe AI",
        "desc": "제일기획 자체 개발 텍스트 생성AI. 광고 카피 자동 생성. 현재 영상 생성 기능 부재.",
        "region": "all",
    },
    {
        "id": "MCKINNEY",
        "type": "asset",
        "label": "McKinney",
        "desc": "북미 시장 진입 교두보. AI 크리에이티브 파이프라인 구축 착수 중.",
        "region": "북미",
    },
    {
        "id": "IRIS",
        "type": "asset",
        "label": "Iris 유럽",
        "desc": "유럽 광고 시장 접근 자산. EU AI법 관련 규제 대응 서비스 제공 가능.",
        "region": "유럽",
    },
    # 전략 행동
    {
        "id": "A1",
        "type": "action",
        "label": "AI 크리에이티브 확장",
        "desc": "Copy Joe · Conti Joe를 영상 생성AI로 확장하고 생성형AI 광고 패키지 상품화. 목표: 2026 Q3.",
        "region": "all",
    },
    {
        "id": "A2",
        "type": "action",
        "label": "Retail AI 플랫폼",
        "desc": "McKinney 브랜드로 Retail Media AI 자동화 플랫폼 출시. Amazon/Walmart 광고주 타겟.",
        "region": "북미",
    },
    {
        "id": "A3",
        "type": "action",
        "label": "EU 컴플라이언스 서비스",
        "desc": "EU AI Act 준수 크리에이티브 가이드라인 수립 후 BYD 유럽 캠페인 시범 적용.",
        "region": "유럽",
    },
    {
        "id": "A4",
        "type": "action",
        "label": "AI M&A 실행",
        "desc": "2026 H2 AI 스타트업 인수 실행. 생성형AI 영상·미디어테크 분야 우선 타겟.",
        "region": "all",
    },
]

EDGES = [
    {"s": "S4", "t": "COPY JOE", "type": "보유함", "str": 1.0, "label": "보유"},
    {"s": "S2", "t": "O5", "type": "가능케함", "str": 0.85, "label": "투자 재원"},
    {"s": "S2", "t": "A4", "type": "가능케함", "str": 0.9, "label": "M&A 자금"},
    {"s": "S3", "t": "MCKINNEY", "type": "연결됨", "str": 0.9, "label": "해외 자산"},
    {"s": "S3", "t": "IRIS", "type": "연결됨", "str": 0.85, "label": "해외 자산"},
    {"s": "S1", "t": "O1", "type": "활용가능", "str": 0.7, "label": "시장 지위"},
    {"s": "W1", "t": "T1", "type": "유사패턴", "str": 0.9, "label": "과도한 의존"},
    {"s": "W2", "t": "T3", "type": "격차심화", "str": 0.8, "label": "실행 지연"},
    {"s": "W2", "t": "AI_ADV", "type": "공백발생", "str": 0.85, "label": "역량 부재"},
    {
        "s": "W3",
        "t": "CREATIVE",
        "type": "공백발생",
        "str": 0.9,
        "label": "자동화 미흡",
    },
    {
        "s": "W3",
        "t": "PERF_OPT",
        "type": "공백발생",
        "str": 0.85,
        "label": "AI 도구 부재",
    },
    {
        "s": "W3",
        "t": "RETAIL_M",
        "type": "공백발생",
        "str": 0.8,
        "label": "미디어 AI 부재",
    },
    {"s": "W4", "t": "O5", "type": "위험요인", "str": 0.75, "label": "창 좁아짐"},
    {"s": "O1", "t": "AI_ADV", "type": "성장동인", "str": 0.9, "label": "시장 확대"},
    {"s": "O2", "t": "RETAIL_M", "type": "성장동인", "str": 0.9, "label": "시장 확대"},
    {
        "s": "O3",
        "t": "MCKINNEY",
        "type": "진입경로",
        "str": 0.75,
        "label": "북미 교두보",
    },
    {"s": "O5", "t": "A4", "type": "연결됨", "str": 0.8, "label": "M&A 타이밍"},
    {"s": "T1", "t": "W2", "type": "경고함", "str": 0.85, "label": "선례 경고"},
    {"s": "T2", "t": "AI_ADV", "type": "경쟁함", "str": 0.9, "label": "직접 집행"},
    {"s": "T2", "t": "PERF_OPT", "type": "경쟁함", "str": 0.8, "label": "플랫폼 잠식"},
    {
        "s": "T3",
        "t": "CREATIVE",
        "type": "경쟁함",
        "str": 0.85,
        "label": "AI 크리에이티브",
    },
    {"s": "WS1", "t": "O1", "type": "감지됨", "str": 0.9, "label": "시장 신호"},
    {"s": "WS1", "t": "CREATIVE", "type": "감지됨", "str": 0.8, "label": "수요 신호"},
    {"s": "WS2", "t": "O2", "type": "감지됨", "str": 0.85, "label": "시장 신호"},
    {"s": "WS2", "t": "RETAIL_M", "type": "감지됨", "str": 0.9, "label": "수요 신호"},
    {"s": "WS3", "t": "COMP_OBL", "type": "촉발됨", "str": 0.95, "label": "규제 수요"},
    {"s": "WS3", "t": "IRIS", "type": "촉발됨", "str": 0.7, "label": "유럽 기회"},
    {
        "s": "WS4",
        "t": "AUDIENCE",
        "type": "감지됨",
        "str": 0.75,
        "label": "트렌드 신호",
    },
    {
        "s": "AI_ADV",
        "t": "CREATIVE",
        "type": "포함함",
        "str": 0.9,
        "label": "크리에이티브 통합",
    },
    {
        "s": "AI_ADV",
        "t": "DATA_INT",
        "type": "의존함",
        "str": 0.85,
        "label": "데이터 필요",
    },
    {"s": "AI_ADV", "t": "MKTG_ROI", "type": "제공함", "str": 0.8, "label": "ROI 측정"},
    {
        "s": "RETAIL_M",
        "t": "DATA_INT",
        "type": "의존함",
        "str": 0.8,
        "label": "데이터 연동",
    },
    {
        "s": "RETAIL_M",
        "t": "AUDIENCE",
        "type": "활용함",
        "str": 0.85,
        "label": "타겟팅",
    },
    {
        "s": "CREATIVE",
        "t": "AUDIENCE",
        "type": "활용함",
        "str": 0.75,
        "label": "개인화",
    },
    {
        "s": "AUDIENCE",
        "t": "PERF_OPT",
        "type": "강화함",
        "str": 0.8,
        "label": "타겟 정밀도",
    },
    {
        "s": "DATA_INT",
        "t": "PERF_OPT",
        "type": "가능케함",
        "str": 0.85,
        "label": "데이터 기반",
    },
    {
        "s": "PERF_OPT",
        "t": "MKTG_ROI",
        "type": "측정함",
        "str": 0.9,
        "label": "성과 측정",
    },
    {
        "s": "COPY JOE",
        "t": "CREATIVE",
        "type": "지원함",
        "str": 0.8,
        "label": "텍스트 생성",
    },
    {
        "s": "MCKINNEY",
        "t": "RETAIL_M",
        "type": "운영함",
        "str": 0.75,
        "label": "북미 리테일",
    },
    {"s": "IRIS", "t": "COMP_OBL", "type": "운영함", "str": 0.8, "label": "규제 대응"},
    {"s": "A1", "t": "W3", "type": "해결함", "str": 0.9, "label": "AI 역량 확충"},
    {"s": "A1", "t": "COPY JOE", "type": "확장함", "str": 0.85, "label": "영상AI 추가"},
    {
        "s": "A1",
        "t": "CREATIVE",
        "type": "강화함",
        "str": 0.9,
        "label": "크리에이티브 자동화",
    },
    {"s": "A2", "t": "RETAIL_M", "type": "구현함", "str": 0.9, "label": "플랫폼 구축"},
    {"s": "A2", "t": "MCKINNEY", "type": "활용함", "str": 0.85, "label": "북미 실행"},
    {
        "s": "A3",
        "t": "COMP_OBL",
        "type": "구현함",
        "str": 0.9,
        "label": "서비스 상품화",
    },
    {"s": "A3", "t": "IRIS", "type": "활용함", "str": 0.8, "label": "유럽 네트워크"},
    {"s": "A4", "t": "W2", "type": "해결함", "str": 0.85, "label": "AI 역량 내재화"},
    {"s": "A4", "t": "DATA_INT", "type": "강화함", "str": 0.75, "label": "인프라 확충"},
]

# 타입 키워드 매핑
TYPE_KEYWORDS = {
    "strength": ["강점", "장점", "우위"],
    "weakness": ["약점", "단점", "취약", "문제"],
    "opportunity": ["기회", "성장", "가능성"],
    "threat": ["위협", "위험", "리스크"],
    "signal": ["신호", "트렌드", "약신호"],
    "concept": ["역량", "능력", "핵심"],
    "asset": ["자산", "보유", "자회사"],
    "action": ["전략", "액션", "실행", "행동"],
}

NODE_MAP = {n["id"]: n for n in NODES}


# ============================================================
# GRAPH-RAG 핵심 함수
# ============================================================


def tokenize(text: str) -> set:
    """간단한 한국어+영문 토크나이저 (공백·특수문자 기준)"""
    text = text.upper()
    tokens = re.split(r"[\s\.,·\-\(\)\[\]\/]+", text)
    return {t for t in tokens if len(t) >= 2}


def score_node(question_tokens: set, node: dict) -> float:
    """질문과 노드 간 관련도 점수 (0~3)"""
    score = 0.0
    # 레이어1: 노드 ID 직접 언급 (가중치 3)
    if node["id"].upper() in question_tokens or node["id"] in " ".join(question_tokens):
        score += 3.0
    # 레이어2: label 토큰 overlap (가중치 2)
    label_tokens = tokenize(node["label"])
    overlap = question_tokens & label_tokens
    if overlap:
        score += 2.0 * len(overlap) / max(len(label_tokens), 1)
    # 레이어3: desc 토큰 overlap (가중치 1)
    desc_tokens = tokenize(node["desc"])
    desc_overlap = question_tokens & desc_tokens
    if desc_overlap:
        score += 1.0 * len(desc_overlap) / max(len(desc_tokens), 1)
    return score


def extract_subgraph(question: str, selected_node: str | None, region: str):
    """질문 기반 관련 서브그래프 추출"""
    question_tokens = tokenize(question)

    # 타입 키워드 매핑으로 추가 시드
    type_seeds = set()
    for ntype, keywords in TYPE_KEYWORDS.items():
        for kw in keywords:
            if kw in question:
                type_seeds.add(ntype)

    # 노드별 관련도 점수 계산
    scored = []
    for node in NODES:
        # 지역 필터 적용
        if region != "전체" and node["region"] not in ("all", region):
            continue
        s = score_node(question_tokens, node)
        if node["type"] in type_seeds:
            s += 1.5
        scored.append((s, node))

    scored.sort(key=lambda x: -x[0])

    # 시드 노드 선택 (score > 0 상위 4개, 없으면 selected_node 또는 전체)
    seed_ids = set()
    for s, n in scored[:4]:
        if s > 0:
            seed_ids.add(n["id"])

    if selected_node and selected_node in NODE_MAP:
        seed_ids.add(selected_node)

    # 시드가 없으면 지역 기반 전체 사용
    if not seed_ids:
        seed_ids = {
            n["id"] for n in NODES if region == "전체" or n["region"] in ("all", region)
        }

    # BFS 2홉 확장 (양방향)
    adj: dict[str, list[str]] = {n["id"]: [] for n in NODES}
    for e in EDGES:
        adj[e["s"]].append(e["t"])
        adj[e["t"]].append(e["s"])

    visited = set(seed_ids)
    frontier = set(seed_ids)
    for _ in range(2):
        next_frontier = set()
        for nid in frontier:
            for nbr in adj.get(nid, []):
                if nbr not in visited:
                    visited.add(nbr)
                    next_frontier.add(nbr)
        frontier = next_frontier

    # 지역 필터 재적용 + 최대 15노드 제한 (시드 우선)
    result_nodes = []
    for s, n in scored:
        if n["id"] in visited:
            result_nodes.append(n)
    # 15개 초과 시 점수 상위 우선 (시드는 반드시 포함)
    seed_nodes = [n for n in result_nodes if n["id"] in seed_ids]
    other_nodes = [n for n in result_nodes if n["id"] not in seed_ids]
    result_nodes = (seed_nodes + other_nodes)[:15]
    result_ids = {n["id"] for n in result_nodes}

    # 해당 노드 간 엣지만 선택 (strength >= 0.7, 최대 25개)
    result_edges = [
        e
        for e in EDGES
        if e["s"] in result_ids and e["t"] in result_ids and e["str"] >= 0.7
    ]
    result_edges.sort(key=lambda e: -e["str"])
    result_edges = result_edges[:25]

    return result_nodes, result_edges


def serialize_subgraph(nodes: list, edges: list) -> str:
    """서브그래프를 LLM 프롬프트용 텍스트로 직렬화"""
    type_label = {
        "strength": "강점",
        "weakness": "약점",
        "opportunity": "기회",
        "threat": "위협",
        "signal": "약신호",
        "concept": "핵심역량",
        "asset": "보유자산",
        "action": "전략행동",
    }
    lines = ["[관련 노드]"]
    for n in nodes:
        tl = type_label.get(n["type"], n["type"])
        lines.append(f"- {n['id']} ({tl}) | {n['label']} | {n['desc']}")

    lines.append("\n[관련 연결 관계]")
    for e in edges:
        src = NODE_MAP.get(e["s"], {}).get("label", e["s"])
        tgt = NODE_MAP.get(e["t"], {}).get("label", e["t"])
        lines.append(
            f"- {e['s']}({src}) --[{e['type']} | {e['label']} | 강도 {e['str']}]--> {e['t']}({tgt})"
        )

    return "\n".join(lines)


def build_system_prompt(subgraph_text: str, region: str) -> str:
    return f"""당신은 제일기획의 AI 전략 인텔리전스 어시스턴트입니다.
아래 제공된 전략 지식 그래프(온톨로지)를 기반으로 질문에 답변합니다.

## 답변 원칙
- 그래프에 포함된 노드와 엣지 정보를 최우선 근거로 사용할 것
- 노드 ID를 언급할 때는 반드시 레이블도 함께 표기 (예: W3 가치사슬 AI 공백)
- 전략적 인사이트 도출 시 연결 경로(엣지 타입·강도)를 논거로 활용할 것
- 답변 분량: 200~350자 내외, 경영진 보고에 적합한 간결하고 전문적인 톤
- 그래프에 없는 정보는 추측하지 말 것
- 노드의 id는 괄호로 표기할 것
- '##'와 같은 기호를 사용하지 말고, 텍스트 중심의 답변을 생성할 것

## 현재 그래프 컨텍스트 (질문 관련 서브그래프)
{subgraph_text}

## 메타 정보
- 총 노드: 34개 | 총 엣지: 59개 | 분석 기준: 2026년 3월
- 현재 지역 필터: {region}"""


# ============================================================
# LLM 호출 (06_daily_summary.py 패턴)
# ============================================================


def call_llm(messages: list) -> str:
    payload = {
        "model": MODEL,
        "input": messages,
        "stream": False,
        "temperature": 0.3,
    }
    resp = req.post(BASE_URL, headers=HEADERS, json=payload, timeout=60)
    resp.raise_for_status()
    result = resp.json()
    return result["output"][0]["content"][0]["text"]


# ============================================================
# 엔드포인트
# ============================================================


@app.route("/api/ontology/chat", methods=["POST"])
def ontology_chat():
    data = request.get_json(force=True)
    question = (data.get("question") or "").strip()
    history = data.get("history", [])[-6:]  # 최근 3턴(6메시지)
    selected_node = data.get("selected_node")
    region = data.get("region", "전체")

    if not question:
        return jsonify({"error": "질문이 비어 있습니다."}), 400

    nodes, edges = extract_subgraph(question, selected_node, region)
    subgraph_text = serialize_subgraph(nodes, edges)
    system_prompt = build_system_prompt(subgraph_text, region)

    # 메시지 구성 (06_daily_summary.py 스타일)
    messages = [{"role": "user", "content": system_prompt}]
    for h in history:
        if h.get("role") in ("user", "assistant") and h.get("content"):
            messages.append({"role": h["role"], "content": h["content"]})
    messages.append({"role": "user", "content": question})

    try:
        answer = call_llm(messages)
    except Exception as e:
        return jsonify({"error": f"LLM 호출 실패: {str(e)}"}), 500

    used_node_ids = [n["id"] for n in nodes]
    return jsonify(
        {
            "answer": answer,
            "referenced_nodes": used_node_ids,
        }
    )


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "model": MODEL})


if __name__ == "__main__":
    print(f"[server] 모델: {MODEL}")
    print(
        f"[server] BASE_URL: {BASE_URL[:40]}..."
        if len(BASE_URL) > 40
        else f"[server] BASE_URL: {BASE_URL}"
    )
    print("[server] http://localhost:5000 에서 실행 중")
    app.run(host="0.0.0.0", port=5000, debug=False)
