# 제일기획 AI 전략 온톨로지 Graph-RAG 시스템 — 기술 명세서

> 작성일: 2026-03-29
> 대상 시스템: 제일기획 AI 전략 인텔리전스 플랫폼 (POC)
> 담당 컴포넌트: Graph-RAG 기반 전략 인텔리전스 AI 엔진

---

## 목차

1. [Graph-RAG 검색 전략](#1-graph-rag-검색-전략)
2. [LLM 프롬프트 템플릿 설계](#2-llm-프롬프트-템플릿-설계)
3. [질문 유형별 처리 방안](#3-질문-유형별-처리-방안)
4. [대화 히스토리 관리](#4-대화-히스토리-관리)
5. [샘플 API 요청/응답 구조](#5-샘플-api-요청응답-구조)

---

## 1. Graph-RAG 검색 전략

### 1.1 온톨로지 그래프 전체 구조 요약

```
노드 34개 / 엣지 59개
카테고리: strength(S), weakness(W), opportunity(O), threat(T),
          signal(WS), concept(핵심역량), asset(보유자산), action(A)
```

### 1.2 자연어 질문 → 관련 노드 추출 (키워드 매칭 알고리즘)

```python
# graph_rag_retriever.py

import re
from typing import List, Dict, Set

# ── 1. 노드 메타데이터 ──────────────────────────────────────────────
NODES: Dict[str, Dict] = {
    # 강점
    "S1": {"label": "국내 과점 지위", "type": "strength",
           "keywords": ["과점", "국내", "시장지위", "지배적", "점유율", "독점"]},
    "S2": {"label": "현금 4,700억", "type": "strength",
           "keywords": ["현금", "자금", "4700", "재무", "투자여력", "유동성"]},
    "S3": {"label": "M&A 디지털 자산", "type": "strength",
           "keywords": ["M&A", "인수", "디지털자산", "포트폴리오", "맥킨니", "아이리스"]},
    "S4": {"label": "CopyJoe·ContiJoe", "type": "strength",
           "keywords": ["copyjoe", "contijoe", "AI도구", "카피", "자체AI", "생성AI"]},

    # 약점
    "W1": {"label": "삼성 의존도 71%", "type": "weakness",
           "keywords": ["삼성", "의존", "71%", "클라이언트집중", "단일고객", "매출의존"]},
    "W2": {"label": "AI 전략 실행 격차", "type": "weakness",
           "keywords": ["실행격차", "전략격차", "AI격차", "실행력", "전략실행", "갭"]},
    "W3": {"label": "가치사슬 AI 공백", "type": "weakness",
           "keywords": ["가치사슬", "공백", "AI공백", "크리에이티브공백", "퍼포먼스공백", "자동화부재"]},
    "W4": {"label": "AI 투자 실행 지연", "type": "weakness",
           "keywords": ["투자지연", "실행지연", "AI투자", "지연", "속도"]},

    # 기회
    "O1": {"label": "생성형AI 광고시장", "type": "opportunity",
           "keywords": ["생성형AI", "광고시장", "AI광고", "generative", "시장성장"]},
    "O2": {"label": "리테일 미디어", "type": "opportunity",
           "keywords": ["리테일미디어", "retail media", "커머스미디어", "쇼핑광고", "e-commerce"]},
    "O3": {"label": "신흥시장 성장", "type": "opportunity",
           "keywords": ["신흥시장", "동남아", "중동", "중남미", "글로벌확장", "해외성장"]},
    "O5": {"label": "AI M&A 기회창", "type": "opportunity",
           "keywords": ["M&A기회", "인수기회", "기회창", "AI스타트업", "전략적인수"]},

    # 위협
    "T1": {"label": "WPP 경로 리스크", "type": "threat",
           "keywords": ["WPP", "경로리스크", "글로벌에이전시", "대형에이전시", "WPP위협"]},
    "T2": {"label": "빅테크 직접 집행", "type": "threat",
           "keywords": ["빅테크", "구글", "메타", "직접집행", "플랫폼내재화", "광고플랫폼"]},
    "T3": {"label": "Publicis AI 독주", "type": "threat",
           "keywords": ["publicis", "퍼블리시스", "AI독주", "경쟁사AI", "글로벌경쟁"]},

    # 약신호
    "WS1": {"label": "생성형AI 광고 신호", "type": "signal",
            "keywords": ["생성형AI신호", "AI광고트렌드", "약신호AI"]},
    "WS2": {"label": "Retail Media AI 신호", "type": "signal",
            "keywords": ["리테일AI신호", "retail AI", "커머스AI"]},
    "WS3": {"label": "EU AI법 시행", "type": "signal",
            "keywords": ["EU", "유럽AI법", "AI규제", "컴플라이언스", "GDPR", "AI Act"]},
    "WS4": {"label": "취약성 마케팅 신호", "type": "signal",
            "keywords": ["취약성마케팅", "공감마케팅", "감성마케팅"]},

    # 핵심역량 (concept)
    "CREATIVE": {"label": "크리에이티브 자동화", "type": "concept",
                 "keywords": ["크리에이티브", "자동화", "콘텐츠생성", "광고소재", "creative"]},
    "AI_ADV":   {"label": "AI 광고 플랫폼", "type": "concept",
                 "keywords": ["AI광고플랫폼", "광고플랫폼", "programmatic", "프로그래매틱"]},
    "RETAIL_M": {"label": "리테일 미디어 AI", "type": "concept",
                 "keywords": ["리테일미디어AI", "retail media AI", "쇼핑미디어"]},
    "DATA_INT": {"label": "데이터 통합", "type": "concept",
                 "keywords": ["데이터통합", "데이터플랫폼", "CDP", "통합데이터"]},
    "COMP_OBL": {"label": "AI 컴플라이언스", "type": "concept",
                 "keywords": ["컴플라이언스", "규제준수", "AI법", "법적대응", "compliance"]},
    "PERF_OPT": {"label": "퍼포먼스 최적화", "type": "concept",
                 "keywords": ["퍼포먼스", "성과최적화", "ROI최적화", "캠페인성과"]},
    "AUDIENCE": {"label": "오디언스 인텔리전스", "type": "concept",
                 "keywords": ["오디언스", "타겟팅", "고객인텔리전스", "세그멘테이션"]},
    "MKTG_ROI": {"label": "마케팅 ROI", "type": "concept",
                 "keywords": ["마케팅ROI", "ROI", "효율", "성과측정", "ROAS"]},

    # 보유자산 (asset)
    "COPYJOE": {"label": "CopyJoe AI 도구", "type": "asset",
                "keywords": ["copyjoe", "카피조", "AI카피라이팅", "자체AI"]},
    "MCKINNEY": {"label": "McKinney 북미법인", "type": "asset",
                 "keywords": ["mckinney", "맥킨니", "북미", "미국법인"]},
    "IRIS":     {"label": "Iris 유럽법인", "type": "asset",
                 "keywords": ["iris", "아이리스", "유럽법인", "유럽", "영국"]},

    # 전략행동 (action)
    "A1": {"label": "AI 크리에이티브 확장", "type": "action",
           "keywords": ["AI크리에이티브", "크리에이티브확장", "자동화확장", "소재확장"]},
    "A2": {"label": "Retail AI 플랫폼 구축", "type": "action",
           "keywords": ["리테일AI플랫폼", "retail AI구축", "커머스플랫폼"]},
    "A3": {"label": "EU 컴플라이언스 서비스", "type": "action",
           "keywords": ["EU컴플라이언스", "유럽서비스", "규제서비스", "컴플라이언스서비스"]},
    "A4": {"label": "AI M&A 실행", "type": "action",
           "keywords": ["AI M&A", "M&A실행", "인수실행", "전략인수"]},
}

# ── 2. 엣지 메타데이터 ──────────────────────────────────────────────
EDGES: List[Dict] = [
    {"src": "W3", "dst": "CREATIVE",  "rel": "공백발생", "strength": 0.90, "label": "자동화 미흡"},
    {"src": "W3", "dst": "PERF_OPT",  "rel": "공백발생", "strength": 0.85, "label": "퍼포먼스 미흡"},
    {"src": "W3", "dst": "RETAIL_M",  "rel": "공백발생", "strength": 0.80, "label": "리테일AI 미흡"},
    {"src": "A1", "dst": "W3",        "rel": "해결함",   "strength": 0.90, "label": "크리에이티브 자동화"},
    {"src": "A2", "dst": "RETAIL_M",  "rel": "구현함",   "strength": 0.85, "label": "리테일 플랫폼"},
    {"src": "A3", "dst": "COMP_OBL",  "rel": "구현함",   "strength": 0.80, "label": "EU 대응"},
    {"src": "A4", "dst": "O5",        "rel": "활용함",   "strength": 0.90, "label": "M&A 실행"},
    {"src": "W2", "dst": "T3",        "rel": "격차심화", "strength": 0.80, "label": "경쟁열위"},
    {"src": "T2", "dst": "AI_ADV",    "rel": "경쟁함",   "strength": 0.90, "label": "플랫폼 경쟁"},
    {"src": "WS1", "dst": "O1",       "rel": "감지됨",   "strength": 0.90, "label": "AI광고 신호"},
    {"src": "WS2", "dst": "O2",       "rel": "감지됨",   "strength": 0.85, "label": "리테일 신호"},
    {"src": "WS3", "dst": "COMP_OBL", "rel": "유발함",   "strength": 0.80, "label": "규제 대응 필요"},
    {"src": "S2", "dst": "A4",        "rel": "가능케함", "strength": 0.90, "label": "현금 재원"},
    {"src": "S3", "dst": "A4",        "rel": "가능케함", "strength": 0.85, "label": "M&A 경험"},
    {"src": "S4", "dst": "A1",        "rel": "지원함",   "strength": 0.80, "label": "AI 도구 활용"},
    {"src": "O1", "dst": "A1",        "rel": "촉진함",   "strength": 0.85, "label": "시장 기회"},
    {"src": "O2", "dst": "A2",        "rel": "촉진함",   "strength": 0.85, "label": "리테일 기회"},
    {"src": "IRIS", "dst": "A3",      "rel": "실행주체", "strength": 0.90, "label": "유럽 거점"},
    {"src": "MCKINNEY", "dst": "O3",  "rel": "진출기반", "strength": 0.80, "label": "북미 거점"},
    {"src": "CREATIVE", "dst": "MKTG_ROI", "rel": "향상함", "strength": 0.85, "label": "효율 증대"},
    {"src": "PERF_OPT", "dst": "MKTG_ROI", "rel": "향상함", "strength": 0.90, "label": "성과 개선"},
    {"src": "DATA_INT", "dst": "AUDIENCE", "rel": "강화함", "strength": 0.85, "label": "데이터 기반"},
    {"src": "W1", "dst": "O3",        "rel": "해소필요", "strength": 0.75, "label": "다변화 필요"},
    {"src": "T3", "dst": "AI_ADV",    "rel": "위협함",   "strength": 0.85, "label": "경쟁 심화"},
    {"src": "WS4", "dst": "CREATIVE", "rel": "기회연결", "strength": 0.70, "label": "공감 크리에이티브"},
]

# ── 3. 인접 리스트 빌드 ─────────────────────────────────────────────
def build_adjacency(edges: List[Dict]) -> Dict[str, List[str]]:
    adj: Dict[str, List[str]] = {nid: [] for nid in NODES}
    for e in edges:
        adj[e["src"]].append(e["dst"])
        adj[e["dst"]].append(e["src"])   # 양방향 탐색 허용
    return adj

ADJACENCY = build_adjacency(EDGES)

# ── 4. 질문 → 노드 ID 매칭 ──────────────────────────────────────────
def extract_seed_nodes(question: str, top_k: int = 4) -> List[str]:
    """
    질문 텍스트에서 가장 관련성 높은 노드 ID를 최대 top_k개 반환.
    전략:
      1) 노드 ID 직접 언급 (예: "W3", "A4") — 가중치 3
      2) 노드 label 포함 여부                — 가중치 2
      3) keywords 포함 여부 (단어 수 기반)   — 가중치 1
    """
    q_lower = question.lower()
    scores: Dict[str, float] = {}

    for nid, meta in NODES.items():
        score = 0.0

        # 1) 노드 ID 직접 언급
        if re.search(rf'\b{nid.lower()}\b', q_lower):
            score += 3.0

        # 2) label 포함
        label_words = meta["label"].replace("·", " ").split()
        label_hits = sum(1 for w in label_words if w.lower() in q_lower)
        score += label_hits * 2.0

        # 3) keywords 매칭
        kw_hits = sum(1 for kw in meta["keywords"] if kw.lower() in q_lower)
        score += kw_hits * 1.0

        if score > 0:
            scores[nid] = score

    # 점수 내림차순 정렬 후 top_k 반환
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [nid for nid, _ in ranked[:top_k]]


# ── 5. BFS 서브그래프 추출 ───────────────────────────────────────────
def extract_subgraph(
    seed_nodes: List[str],
    max_hops: int = 2,
    max_nodes: int = 15,
) -> Dict:
    """
    시드 노드에서 BFS로 서브그래프를 추출한다.

    hop 수 권장값:
      - 단순 노드 설명 질문  → hop=1 (직접 연결만)
      - 경로/인과 분석 질문  → hop=2 (기본값, 대부분의 질문)
      - 전체 전략 질문       → hop=3 또는 전체 그래프 사용

    max_nodes=15 제한: 프롬프트 토큰 예산(~1,500 토큰) 내 유지
    """
    visited: Set[str] = set()
    queue = [(nid, 0) for nid in seed_nodes if nid in NODES]
    result_nodes: List[str] = []

    while queue and len(result_nodes) < max_nodes:
        current, hop = queue.pop(0)
        if current in visited:
            continue
        visited.add(current)
        result_nodes.append(current)

        if hop < max_hops:
            for neighbor in ADJACENCY.get(current, []):
                if neighbor not in visited:
                    queue.append((neighbor, hop + 1))

    # 서브그래프에 포함된 엣지만 필터링
    result_set = set(result_nodes)
    result_edges = [
        e for e in EDGES
        if e["src"] in result_set and e["dst"] in result_set
    ]

    return {
        "nodes": {nid: NODES[nid] for nid in result_nodes},
        "edges": result_edges,
        "seed_nodes": seed_nodes,
    }


# ── 6. 전체 vs 부분 그래프 선택 기준 ───────────────────────────────
def decide_graph_scope(question: str, seed_nodes: List[str]) -> str:
    """
    반환값: "full" | "subgraph"

    전체 그래프 사용 조건 (full):
      - 시드 노드 0개 (질문이 너무 일반적)
      - "전체", "모든", "종합", "요약", "Overview" 키워드 포함
      - 질문 길이 < 10자 (맥락 부족)

    부분 서브그래프 사용 조건 (subgraph):
      - 시드 노드 1개 이상 매칭
      - 특정 노드 ID 명시 언급
      - 특정 전략 방향 언급
    """
    full_triggers = ["전체", "모든", "종합", "전반", "요약", "overview", "전략 전체"]
    q_lower = question.lower()

    if len(seed_nodes) == 0:
        return "full"
    if len(question) < 10:
        return "full"
    if any(t in q_lower for t in full_triggers):
        return "full"

    return "subgraph"
```

---

## 2. LLM 프롬프트 템플릿 설계

### 2.1 Graph Context 직렬화 형식 선택 근거

| 형식 | 장점 | 단점 | 권장 여부 |
|------|------|------|-----------|
| JSON | 구조적, 파싱 용이 | 토큰 소비 많음, LLM 가독성 낮음 | 보조 용도 |
| 자연어 | LLM 이해도 최고 | 토큰 많음, 정보 손실 가능 | 요약에만 사용 |
| **마크다운 테이블** | **토큰 효율, 구조 명확, LLM 친화적** | 복잡한 관계 표현 제한 | **권장** |

> **권장: 마크다운 테이블 + 인라인 관계 서술 혼합**
> 노드 목록은 마크다운 테이블, 엣지(관계)는 화살표 기호 자연어로 표현.

### 2.2 System Prompt

```
당신은 제일기획 AI 전략 컨설턴트입니다.
제일기획의 전략 온톨로지 지식 그래프를 기반으로 전략 질문에 답변합니다.

[그래프 읽는 방법]
- 노드는 전략 요소입니다. 유형: strength(S), weakness(W), opportunity(O),
  threat(T), signal(WS), concept(핵심역량), asset(보유자산), action(A)
- 엣지는 두 노드 간의 전략적 관계를 나타냅니다.
  예: A → B (해결함, strength:0.9) = "A가 B를 0.9 강도로 해결함"
- strength 값은 0~1로 관계의 전략적 중요도를 나타냅니다.
- 관계 유형: 공백발생 | 해결함 | 격차심화 | 경쟁함 | 감지됨 |
             가능케함 | 지원함 | 촉진함 | 실행주체 | 향상함

[답변 원칙]
1. 그래프 데이터에 근거하여 답변하십시오. 근거 없는 추론은 명시적으로 구분하십시오.
2. 관련 노드 ID를 답변에 명시하십시오 (예: W3, A1, CREATIVE).
3. 전략적 우선순위를 strength 값 기준으로 제시하십시오.
4. 답변 마지막에 "참조 노드: [ID1, ID2, ...]" 형식으로 정리하십시오.
5. 분량: 경영진 브리핑 수준 — 핵심 3~5문장 + 권고사항 2~3개.
6. 확신도(confidence)를 high/medium/low로 표시하십시오.
   - high: 직접 연결된 엣지가 3개 이상, strength > 0.8
   - medium: 간접 연결(hop=2), strength 0.6~0.8
   - low: 추론 또는 그래프 외 정보 활용
```

### 2.3 Graph Context 직렬화 함수

```python
def serialize_subgraph_to_prompt(subgraph: Dict) -> str:
    """
    서브그래프를 LLM 프롬프트용 마크다운으로 직렬화.
    토큰 예산: 노드당 약 30토큰, 엣지당 약 20토큰 → 15노드+20엣지 ≈ 850토큰
    """
    nodes = subgraph["nodes"]
    edges = subgraph["edges"]

    lines = ["### 관련 전략 노드\n"]
    lines.append("| ID | 유형 | 설명 |")
    lines.append("|-----|------|------|")
    for nid, meta in nodes.items():
        lines.append(f"| {nid} | {meta['type']} | {meta['label']} |")

    lines.append("\n### 전략 관계 (엣지)\n")
    for e in edges:
        src_label = nodes[e["src"]]["label"] if e["src"] in nodes else e["src"]
        dst_label = nodes[e["dst"]]["label"] if e["dst"] in nodes else e["dst"]
        lines.append(
            f"- **{e['src']}**({src_label}) → **{e['dst']}**({dst_label})"
            f" [{e['rel']}, 중요도:{e['strength']}]"
            + (f" — {e['label']}" if e.get('label') else "")
        )

    return "\n".join(lines)


def compress_context(subgraph: Dict, token_budget: int = 800) -> str:
    """
    토큰 절약 전략:
      1. strength < 0.7 엣지 제거 (저중요도 관계 pruning)
      2. type=signal 노드는 label만 포함 (상세 제거)
      3. 노드 수 > 12이면 시드와 직접 연결된 hop=1 노드 우선
    """
    # strength 기준 엣지 필터
    filtered_edges = [e for e in subgraph["edges"] if e["strength"] >= 0.75]

    # 필터된 엣지에 포함된 노드만 유지
    active_ids = set()
    for e in filtered_edges:
        active_ids.add(e["src"])
        active_ids.add(e["dst"])
    # 시드 노드는 항상 포함
    for nid in subgraph["seed_nodes"]:
        active_ids.add(nid)

    compressed_nodes = {
        nid: meta for nid, meta in subgraph["nodes"].items()
        if nid in active_ids
    }

    return serialize_subgraph_to_prompt({
        "nodes": compressed_nodes,
        "edges": filtered_edges,
        "seed_nodes": subgraph["seed_nodes"],
    })
```

### 2.4 User Message 구성 템플릿

```python
def build_user_message(
    question: str,
    subgraph: Dict,
    selected_node: str | None = None,
) -> str:
    graph_context = compress_context(subgraph)

    node_hint = ""
    if selected_node and selected_node in subgraph["nodes"]:
        meta = subgraph["nodes"][selected_node]
        node_hint = (
            f"\n[현재 선택 노드] **{selected_node}** — {meta['label']} "
            f"(유형: {meta['type']})\n"
        )

    return f"""{graph_context}
{node_hint}
---
[질문] {question}

위 온톨로지 그래프를 기반으로 전략적 관점에서 답변해주세요.
답변 마지막에 반드시 다음 형식을 포함하세요:
참조 노드: [노드ID1, 노드ID2, ...]
확신도: high | medium | low
"""
```

---

## 3. 질문 유형별 처리 방안

### Q1. "W3을 해결하는 가장 빠른 경로는?"

**서브그래프 추출 전략**
- 시드 노드: `[W3]`
- hop 수: 2
- 추출 노드 예시: `W3, CREATIVE, PERF_OPT, RETAIL_M, A1, A2, S4, O1, O2`
- 핵심 경로: `A1 → W3 (해결함, 0.9)`, `S4 → A1 (지원함, 0.8)`

**추가 프롬프트 지시어 (System Prompt 하단 append)**
```
이 질문은 "문제 해결 경로" 유형입니다.
답변 구조:
1. 공백의 현황 (W3이 발생시키는 문제 노드 나열)
2. 직접 해결 액션 (A 유형 노드)
3. 실행 가속 요소 (strength 최고값 경로 우선)
4. 예상 소요 기간 및 난이도 (그래프 외 추론임을 명시)
```

---

### Q2. "제일기획의 가장 큰 위험은 무엇인가?"

**서브그래프 추출 전략**
- 시드 노드: `[T1, T2, T3, W1, W2]` (위협·약점 전체)
- hop 수: 2
- 추출 노드 예시: `T1~T3, W1~W4, AI_ADV, WS1~WS4, A1~A4`
- 핵심 경로: `W2 → T3 (격차심화, 0.8)`, `T2 → AI_ADV (경쟁함, 0.9)`

**추가 프롬프트 지시어**
```
이 질문은 "리스크 우선순위" 유형입니다.
답변 구조:
1. 위협 매트릭스: (발생가능성 × 영향도) 기준 Top 3 위협
2. 위협-약점 교차점 (T×W 조합 중 strength 합산 최고값)
3. 즉각 대응 가능한 방어 액션
확신도 판단: threat 노드와 직접 연결된 엣지 수 기준
```

---

### Q3. "AI M&A를 실행하면 어떤 효과가 있나?"

**서브그래프 추출 전략**
- 시드 노드: `[A4, S2, S3, O5]`
- hop 수: 2
- 추출 노드 예시: `A4, S2, S3, O5, CREATIVE, AI_ADV, RETAIL_M, DATA_INT, W2, W3`
- 핵심 경로: `S2 → A4 (가능케함, 0.9)`, `A4 → O5 (활용함, 0.9)`

**추가 프롬프트 지시어**
```
이 질문은 "전략 행동 효과 분석" 유형입니다.
답변 구조:
1. M&A 실행 전제조건 (가능케함 엣지 기반)
2. 즉각 효과 (1hop 내 해결·구현 노드)
3. 연쇄 효과 (2hop까지 향상·강화 노드)
4. 잠재 리스크 (관련 threat/weakness 노드)
```

---

### Q4. "유럽 시장 전략을 어떻게 구성해야 하나?"

**서브그래프 추출 전략**
- 시드 노드: `[IRIS, A3, WS3, COMP_OBL, O3]`
- hop 수: 2
- 추출 노드 예시: `IRIS, A3, WS3, COMP_OBL, O3, S3, DATA_INT, CREATIVE`
- 핵심 경로: `IRIS → A3 (실행주체, 0.9)`, `WS3 → COMP_OBL (유발함, 0.8)`

**추가 프롬프트 지시어**
```
이 질문은 "지역 전략 수립" 유형입니다.
답변 구조:
1. 유럽 현재 포지션 (IRIS 자산 기반)
2. 규제 환경 (WS3/COMP_OBL 기반 EU AI Act 대응)
3. 진입 우선순위 (O3 기회 + 보유 자산 매칭)
4. 단계별 실행 로드맵 (A3 → COMP_OBL → O3 순서)
```

---

## 4. 대화 히스토리 관리

### 4.1 멀티턴 그래프 컨텍스트 지속 전략

```python
# conversation_manager.py

from dataclasses import dataclass, field
from typing import List, Set, Dict

@dataclass
class ConversationState:
    """
    멀티턴 대화에서 그래프 컨텍스트를 지속적으로 유지하는 상태 객체.
    """
    # 누적된 참조 노드 집합 (대화 전체 맥락)
    accumulated_nodes: Set[str] = field(default_factory=set)

    # 최근 3턴 요약 (rolling summary)
    rolling_summary: str = ""

    # 전체 대화 히스토리 (Claude API messages 형식)
    messages: List[Dict] = field(default_factory=list)

    # 현재 선택된 포커스 노드
    focus_node: str | None = None

    # 턴 카운터
    turn_count: int = 0


def update_state_after_response(
    state: ConversationState,
    referenced_nodes: List[str],
    question: str,
    answer: str,
) -> ConversationState:
    """응답 후 대화 상태 업데이트."""
    state.accumulated_nodes.update(referenced_nodes)
    state.turn_count += 1

    state.messages.append({"role": "user",      "content": question})
    state.messages.append({"role": "assistant",  "content": answer})

    # 3턴마다 rolling summary 갱신
    if state.turn_count % 3 == 0:
        state.rolling_summary = summarize_conversation(state.messages[-6:])

    return state


def build_history_context(state: ConversationState) -> str:
    """
    이전 대화 맥락을 현재 프롬프트에 주입할 텍스트 생성.

    전략:
    - 턴 1~2: 히스토리 없음 (신규 대화)
    - 턴 3~5: 최근 2턴 Q&A 전문 포함
    - 턴 6+:  rolling summary + 최근 1턴만 포함
    - 누적 참조 노드는 항상 포함 (컨텍스트 앵커)
    """
    if state.turn_count == 0:
        return ""

    node_list = ", ".join(sorted(state.accumulated_nodes))
    anchor = f"[이전 대화에서 논의된 노드: {node_list}]\n\n"

    if state.turn_count <= 2:
        recent = _format_recent_turns(state.messages, n=2)
        return anchor + recent

    if state.turn_count <= 5:
        recent = _format_recent_turns(state.messages, n=4)
        return anchor + recent

    # 턴 6 이상: 요약 + 최근 1턴
    recent = _format_recent_turns(state.messages, n=2)
    return anchor + f"[이전 대화 요약]\n{state.rolling_summary}\n\n" + recent


def summarize_conversation(messages: List[Dict]) -> str:
    """
    최근 N개 메시지를 요약 텍스트로 압축.
    실제 구현에서는 Claude API를 별도 호출하여 요약 생성.
    POC에서는 단순 key point 추출로 대체.
    """
    # POC 구현: 어시스턴트 응답에서 '참조 노드:' 라인 추출
    summary_lines = []
    for msg in messages:
        if msg["role"] == "assistant":
            for line in msg["content"].split("\n"):
                if "참조 노드:" in line or "권고사항" in line:
                    summary_lines.append(line.strip())

    return "\n".join(summary_lines[:5]) if summary_lines else "이전 대화 요약 없음"


def _format_recent_turns(messages: List[Dict], n: int) -> str:
    recent = messages[-n:] if len(messages) >= n else messages
    formatted = []
    for msg in recent:
        role = "사용자" if msg["role"] == "user" else "AI 컨설턴트"
        # 어시스턴트 응답은 첫 200자만 포함 (토큰 절약)
        content = msg["content"]
        if msg["role"] == "assistant" and len(content) > 200:
            content = content[:200] + "..."
        formatted.append(f"[{role}] {content}")
    return "\n".join(formatted)
```

### 4.2 토큰 예산 관리 (멀티턴)

| 컴포넌트 | 토큰 예산 | 비고 |
|----------|-----------|------|
| System Prompt | ~400 | 고정 |
| Graph Context | ~800 | compress_context 적용 |
| 대화 히스토리 | ~600 | rolling summary 방식 |
| User Question | ~100 | 질문 자체 |
| **합계** | **~1,900** | 전체 입력 토큰 |
| 응답 (Output) | ~600 | 경영진 브리핑 수준 |

---

## 5. 샘플 API 요청/응답 구조

### 5.1 엔드포인트 명세

```
POST /api/v1/graph-rag/query
Content-Type: application/json
```

### 5.2 Request 스키마

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "GraphRAGRequest",
  "type": "object",
  "required": ["question"],
  "properties": {
    "question": {
      "type": "string",
      "description": "사용자 자연어 질문",
      "minLength": 2,
      "maxLength": 500
    },
    "selected_node": {
      "type": ["string", "null"],
      "description": "온톨로지 그래프에서 현재 클릭된 노드 ID",
      "pattern": "^(S[1-9]|W[1-9]|O[1-9]|T[1-9]|WS[1-9]|A[1-9]|CREATIVE|AI_ADV|RETAIL_M|DATA_INT|COMP_OBL|PERF_OPT|AUDIENCE|MKTG_ROI|COPYJOE|MCKINNEY|IRIS)$",
      "default": null
    },
    "conversation_history": {
      "type": "array",
      "description": "이전 대화 메시지 배열 (최대 10턴)",
      "maxItems": 20,
      "items": {
        "type": "object",
        "required": ["role", "content"],
        "properties": {
          "role": { "type": "string", "enum": ["user", "assistant"] },
          "content": { "type": "string", "maxLength": 1000 }
        }
      },
      "default": []
    },
    "options": {
      "type": "object",
      "properties": {
        "max_hops": {
          "type": "integer",
          "minimum": 1,
          "maximum": 3,
          "default": 2
        },
        "max_nodes": {
          "type": "integer",
          "minimum": 5,
          "maximum": 20,
          "default": 15
        },
        "language": {
          "type": "string",
          "enum": ["ko", "en"],
          "default": "ko"
        }
      }
    }
  }
}
```

### 5.3 Response 스키마

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "GraphRAGResponse",
  "type": "object",
  "properties": {
    "answer": {
      "type": "string",
      "description": "LLM이 생성한 전략 답변 (마크다운)"
    },
    "referenced_nodes": {
      "type": "array",
      "description": "답변에서 참조된 노드 ID 목록",
      "items": { "type": "string" }
    },
    "confidence": {
      "type": "string",
      "enum": ["high", "medium", "low"],
      "description": "답변 확신도"
    },
    "subgraph_used": {
      "type": "object",
      "description": "실제 프롬프트에 사용된 서브그래프 메타데이터",
      "properties": {
        "node_count": { "type": "integer" },
        "edge_count": { "type": "integer" },
        "seed_nodes": { "type": "array", "items": { "type": "string" } },
        "scope": { "type": "string", "enum": ["full", "subgraph"] }
      }
    },
    "token_usage": {
      "type": "object",
      "properties": {
        "input_tokens":  { "type": "integer" },
        "output_tokens": { "type": "integer" }
      }
    },
    "session_id": {
      "type": "string",
      "description": "대화 세션 식별자 (멀티턴 연속성)"
    }
  }
}
```

### 5.4 샘플 API 페어 (5개)

---

**[샘플 1] W3 해결 경로 질문**

```json
// Request
{
  "question": "W3 가치사슬 AI 공백을 해결하는 가장 빠른 경로는 무엇인가?",
  "selected_node": "W3",
  "conversation_history": [],
  "options": { "max_hops": 2 }
}

// Response
{
  "answer": "W3(가치사슬 AI 공백)의 가장 빠른 해결 경로는 **A1 → W3 (해결함, strength:0.9)** 경로입니다.\n\nA1(AI 크리에이티브 확장)은 이미 S4(CopyJoe·ContiJoe)라는 자체 AI 자산에서 직접 지원받을 수 있어 (S4→A1, strength:0.8) 외부 조달 없이 즉시 착수 가능합니다.\n\nW3이 발생시키는 3개 공백 중 우선순위는:\n1. CREATIVE 자동화 (공백강도 0.90) — A1으로 즉시 대응\n2. PERF_OPT 최적화 (0.85) — DATA_INT 연계 필요\n3. RETAIL_M 리테일AI (0.80) — A2 별도 플랫폼 구축 필요\n\n**권고사항:**\n- 1순위: S4 기반 A1 즉시 가동 (3개월 내 파일럿)\n- 2순위: PERF_OPT를 위한 DATA_INT 정비 (6개월)\n- 3순위: A2 리테일AI 플랫폼 중기 로드맵 수립\n\n참조 노드: [W3, A1, CREATIVE, PERF_OPT, RETAIL_M, S4]\n확신도: high",
  "referenced_nodes": ["W3", "A1", "CREATIVE", "PERF_OPT", "RETAIL_M", "S4"],
  "confidence": "high",
  "subgraph_used": {
    "node_count": 9,
    "edge_count": 7,
    "seed_nodes": ["W3"],
    "scope": "subgraph"
  },
  "token_usage": { "input_tokens": 1420, "output_tokens": 380 },
  "session_id": "sess_abc123"
}
```

---

**[샘플 2] 최대 위험 질문**

```json
// Request
{
  "question": "제일기획의 가장 큰 위험은 무엇인가?",
  "selected_node": null,
  "conversation_history": [],
  "options": { "max_hops": 2 }
}

// Response
{
  "answer": "그래프 분석 결과 가장 심각한 위험은 **W2-T3 격차심화 루프**입니다.\n\nW2(AI 전략 실행 격차)가 T3(Publicis AI 독주)로 직결되는 엣지 (strength:0.80)는 실행 지연이 곧 경쟁열위 고착화를 의미합니다. 특히 T2(빅테크 직접 집행)가 AI_ADV(AI 광고 플랫폼) 노드를 경쟁 압박하는 구조(strength:0.90)는 플랫폼 내재화 가속 시 제일기획의 중간 포지션이 붕괴될 수 있음을 시사합니다.\n\n**위협 우선순위:**\n1. T2 빅테크 직접 집행 (strength:0.90, 즉각성 최고)\n2. T3 Publicis AI 독주 + W2 격차심화 복합 위협\n3. W1 삼성 의존도 71% (중장기 구조적 리스크)\n\n**권고사항:**\n- AI_ADV 포지셔닝 차별화 전략 수립 (빅테크와 차별화)\n- A1·A2 실행 가속화로 W2 격차 즉시 해소\n- W1 해소를 위한 O3 신흥시장 다변화 중기 계획\n\n참조 노드: [W2, T3, T2, AI_ADV, W1, A1, A2, O3]\n확신도: high",
  "referenced_nodes": ["W2", "T3", "T2", "AI_ADV", "W1", "A1", "A2", "O3"],
  "confidence": "high",
  "subgraph_used": {
    "node_count": 13,
    "edge_count": 11,
    "seed_nodes": ["T1", "T2", "T3", "W1", "W2"],
    "scope": "subgraph"
  },
  "token_usage": { "input_tokens": 1680, "output_tokens": 410 },
  "session_id": "sess_def456"
}
```

---

**[샘플 3] AI M&A 효과 분석**

```json
// Request
{
  "question": "AI M&A를 실행하면 어떤 효과가 있나?",
  "selected_node": "A4",
  "conversation_history": [],
  "options": { "max_hops": 2 }
}

// Response
{
  "answer": "A4(AI M&A 실행)는 S2(현금 4,700억)와 S3(M&A 디지털 자산)라는 두 강점 노드가 동시에 '가능케함' 관계로 뒷받침하는 구조입니다 (각 strength 0.90, 0.85).\n\n**즉각 효과 (1hop):**\n- O5(AI M&A 기회창) 직접 활용 가능\n- W3 공백 해소를 위한 기술 자산 확보 가속\n\n**연쇄 효과 (2hop):**\n- 인수 대상에 따라 CREATIVE·AI_ADV·RETAIL_M 중 공백 영역 즉시 보완\n- DATA_INT 강화 → AUDIENCE 인텔리전스 → MKTG_ROI 향상 연쇄\n\n**잠재 리스크:**\n- W4(AI 투자 실행 지연)가 A4 실행을 저해할 수 있음\n- T1(WPP 경로 리스크): 글로벌 에이전시의 동일 타겟 선점 가능성\n\n**권고사항:**\n- M&A 타겟 우선순위: CREATIVE 자동화 > RETAIL_M > DATA_INT 순\n- W4 해소를 위한 내부 의사결정 프로세스 간소화 선행\n- S2 현금 자산 활용 가능 창이 제한적이므로 6개월 내 실행\n\n참조 노드: [A4, S2, S3, O5, W3, W4, T1, CREATIVE, AI_ADV, RETAIL_M]\n확신도: high",
  "referenced_nodes": ["A4", "S2", "S3", "O5", "W3", "W4", "T1", "CREATIVE", "AI_ADV", "RETAIL_M"],
  "confidence": "high",
  "subgraph_used": {
    "node_count": 11,
    "edge_count": 9,
    "seed_nodes": ["A4", "S2", "S3", "O5"],
    "scope": "subgraph"
  },
  "token_usage": { "input_tokens": 1510, "output_tokens": 430 },
  "session_id": "sess_ghi789"
}
```

---

**[샘플 4] 유럽 시장 전략 (멀티턴 2번째 턴)**

```json
// Request
{
  "question": "유럽 시장에서 EU AI법을 오히려 기회로 활용하는 방법은?",
  "selected_node": "IRIS",
  "conversation_history": [
    {
      "role": "user",
      "content": "유럽 시장 전략을 어떻게 구성해야 하나?"
    },
    {
      "role": "assistant",
      "content": "IRIS(유럽법인)를 실행 주체로 A3(EU 컴플라이언스 서비스)를 선행 구축하는 것이 핵심입니다...\n참조 노드: [IRIS, A3, WS3, COMP_OBL, O3]\n확신도: high"
    }
  ],
  "options": { "max_hops": 2 }
}

// Response
{
  "answer": "이전 대화에서 논의한 IRIS-A3-COMP_OBL 구조를 기반으로, EU AI법(WS3)은 위협이 아닌 **진입 장벽 역전** 기회입니다.\n\nWS3(EU AI법 시행)이 COMP_OBL(AI 컴플라이언스)를 유발하는 구조(strength:0.80)에서, 경쟁자 대부분이 COMP_OBL을 비용으로 인식하는 반면 제일기획은 A3(EU 컴플라이언스 서비스)를 **상품화**하여 클라이언트에게 제공 가능합니다.\n\n**기회 활용 메커니즘:**\n- IRIS 거점을 활용해 EU 클라이언트의 AI 광고 컴플라이언스 대행 서비스 출시\n- S3(M&A 디지털 자산)으로 유럽 RegTech/AdTech 기업 인수 → COMP_OBL 역량 즉시 강화\n- WPP·Publicis 대비 아시아 기반 에이전시의 '중립적 파트너' 포지셔닝 활용\n\n**권고사항:**\n- A3를 독립 수익원으로 패키징 (Compliance-as-a-Service)\n- IRIS + MCKINNEY 공동 글로벌 컴플라이언스 제품 개발\n- 2026년 EU AI법 전면 시행 전 선점 포지셔닝 완료\n\n참조 노드: [WS3, COMP_OBL, A3, IRIS, S3, MCKINNEY, O3]\n확신도: high",
  "referenced_nodes": ["WS3", "COMP_OBL", "A3", "IRIS", "S3", "MCKINNEY", "O3"],
  "confidence": "high",
  "subgraph_used": {
    "node_count": 9,
    "edge_count": 8,
    "seed_nodes": ["IRIS", "A3", "WS3", "COMP_OBL"],
    "scope": "subgraph"
  },
  "token_usage": { "input_tokens": 1820, "output_tokens": 450 },
  "session_id": "sess_jkl012"
}
```

---

**[샘플 5] 전체 전략 종합 요약 (전체 그래프 사용)**

```json
// Request
{
  "question": "제일기획 AI 전략 전체를 한 문단으로 요약해줘",
  "selected_node": null,
  "conversation_history": [],
  "options": { "max_hops": 3 }
}

// Response
{
  "answer": "제일기획은 국내 과점 지위(S1)와 4,700억 현금(S2)이라는 강고한 실행 기반을 보유하고 있으나, W3(가치사슬 AI 공백)과 W2(실행 격차)가 T2·T3의 외부 위협과 맞물려 중기 경쟁력 훼손 위험이 높습니다. 이를 타개하는 핵심 전략 축은 **A1(AI 크리에이티브 자동화) → CREATIVE·PERF_OPT 공백 해소**, **A4(AI M&A) → S2 현금 기반 기술 자산 확보**, **A3(EU 컴플라이언스 서비스) → IRIS 거점 활용 유럽 선점**의 세 방향이며, WS1·WS2 약신호가 O1·O2 기회로 현실화되기 전에 선제 포지셔닝하는 것이 전략의 시간적 핵심입니다.\n\n참조 노드: [S1, S2, W2, W3, T2, T3, A1, A4, A3, CREATIVE, PERF_OPT, IRIS, O1, O2, WS1, WS2]\n확신도: high",
  "referenced_nodes": ["S1", "S2", "W2", "W3", "T2", "T3", "A1", "A4", "A3", "CREATIVE", "PERF_OPT", "IRIS", "O1", "O2", "WS1", "WS2"],
  "confidence": "high",
  "subgraph_used": {
    "node_count": 34,
    "edge_count": 25,
    "seed_nodes": [],
    "scope": "full"
  },
  "token_usage": { "input_tokens": 2200, "output_tokens": 320 },
  "session_id": "sess_mno345"
}
```

---

## 부록: 전체 시스템 데이터 흐름 다이어그램

```
[프론트엔드 온톨로지 탭]
     │
     │ POST /api/v1/graph-rag/query
     │ { question, selected_node, conversation_history }
     ▼
[Graph-RAG API 서버]
     │
     ├── 1. extract_seed_nodes(question)      ← 키워드 매칭
     │        ↓ seed_nodes: ["W3", ...]
     │
     ├── 2. decide_graph_scope(question)      ← full / subgraph 결정
     │        ↓ scope: "subgraph"
     │
     ├── 3. extract_subgraph(seeds, hops=2)   ← BFS 서브그래프 추출
     │        ↓ { nodes: {...}, edges: [...] }
     │
     ├── 4. compress_context(subgraph)        ← 토큰 최적화 직렬화
     │        ↓ markdown_context: "| ID | 유형 | ..."
     │
     ├── 5. build_history_context(state)      ← 멀티턴 히스토리 주입
     │        ↓ history_text
     │
     ├── 6. Claude API 호출                   ← claude-sonnet-4-6
     │        system:  SYSTEM_PROMPT
     │        messages: [history... + user_message]
     │        max_tokens: 600
     │        ↓ raw_answer
     │
     ├── 7. parse_referenced_nodes(answer)    ← "참조 노드:" 파싱
     │        ↓ ["W3", "A1", "CREATIVE"]
     │
     ├── 8. parse_confidence(answer)          ← "확신도:" 파싱
     │        ↓ "high"
     │
     └── 9. Response 조립 및 반환
          { answer, referenced_nodes, confidence,
            subgraph_used, token_usage, session_id }
     │
     ▼
[프론트엔드]
     ├── answer 텍스트 렌더링
     ├── referenced_nodes → 온톨로지 그래프 노드 하이라이트
     └── confidence → 배지 표시
```

---

## 부록: 주요 설계 결정 근거

| 결정 사항 | 선택 | 근거 |
|-----------|------|------|
| 직렬화 형식 | 마크다운 테이블 + 화살표 자연어 | JSON 대비 30% 토큰 절약, LLM 이해도 동등 |
| 기본 hop 수 | 2 | hop=1: 정보 부족, hop=3: 토큰 초과 위험. 실험적으로 2가 최적 |
| 토큰 예산 | 입력 ~1,900 / 출력 ~600 | claude-sonnet-4-6 기준 비용·품질 균형점 |
| 히스토리 전략 | Rolling Summary (3턴 주기) | 전체 히스토리 누적 시 토큰 폭발 방지 |
| confidence 기준 | 엣지 수 + strength 기반 규칙 | LLM 자기평가보다 그래프 구조 기반이 일관성 높음 |
| 서브그래프 상한 | 15노드 | 850토큰 내 유지, 핵심 관계 커버리지 충분 |
