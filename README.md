# 매크로 스튜디오 (Macro Studio)

마우스·키보드 입력을 **녹화 → 편집 → JSON 저장 → 재생**하는 한국어 UI 데스크톱 앱입니다.  
클라우드/텔레메트리 없음. 녹화는 **녹화 모드**에서만 동작합니다.

A small desktop macro recorder & editor: record mouse+keyboard, edit the event list after stop, save/load JSON into numbered slots, and play back once (no infinite loop by default).

## 기능

1. **번호 슬롯 (1번~10번)** — 왼쪽 패널에 고정 10개 슬롯  
   - 표시: `1번 매크로 — 이름` 또는 `1번 매크로 (비어있음)`  
   - 슬롯 선택 → 불러오기 (또는 더블클릭 / **Ctrl+1 … Ctrl+0**)  
   - **[슬롯 저장]** → `macros/slot_01.json` … `slot_10.json`  
   - 슬롯 비우기로 파일 삭제
2. **녹화** — 시작/중지, 클릭(버튼·좌표), 스크롤, 키 입력, 지연 시간 기록  
   - 마우스 **이동** 녹화는 기본 OFF (체크박스로 샘플링 ON)  
   - 녹화 중 표시등(●)  
   - 단축키: **F9** 녹화 토글, **F10** 재생(재생 중이면 중단)
3. **편집** — 중지 후 이벤트 목록(**동작 1, 동작 2…** 1-based)  
   - 필드 수정, 삭제, **범위 삭제 (A~B번)**, 위/아래 순서 변경, 대기(Wait) 삽입  
   - **현재 마우스 위치로 X/Y 채우기** (click/move/scroll 좌표 보정)  
   - **[슬롯 저장]**을 눌렀을 때만 디스크에 기록
4. **재생** — 3초 카운트다운, **Esc** 또는 **F10**으로 중단, 기본 1회 재생  
   - **N번부터 재생**: 시작 동작 번호 + 버튼 (이전 동작 건너뜀)

## 요구 사항

- Python **3.11+** (권장 3.11–3.13)
- `pynput`, `customtkinter` (자세한 버전은 `requirements.txt`)

## 설치 & 실행

```bash
cd /path/to/Macro
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
python -m macro_studio
```

또는 editable 설치 후:

```bash
pip install -e .
macro-studio
```

## 슬롯 저장 형식

각 슬롯은 `macros/slot_NN.json` 파일입니다 (NN = 01…10).

```json
{
  "name": "로그인 클릭",
  "description": "",
  "version": 1,
  "slot": 1,
  "events": [
    {
      "type": "click",
      "delay_ms": 500,
      "x": 100,
      "y": 200,
      "button": "left",
      "action": "press"
    }
  ]
}
```

이벤트 `type`: `click` | `scroll` | `key` | `move` | `wait`

### 슬롯 사용 흐름

1. 왼쪽에서 **3번 매크로** 선택 → [슬롯 불러오기] (비어 있으면 빈 템플릿)
2. F9로 녹화 → 목록에서 **동작 1, 2…** 편집
3. 필요 시 범위 삭제(예: 1~2번 삭제 → 옛 3번이 동작 1이 됨)
4. 좌표 보정: 이벤트 선택 → [현재 마우스 위치로 X/Y 채우기]
5. [슬롯 저장] → `macros/slot_03.json`
6. 재생: [▶ 재생] 전체, 또는 `5` + [N번부터 재생]

## OS 권한 (중요)

### macOS
- **시스템 설정 → 개인 정보 보호 및 보안**
  - **손쉬운 사용(Accessibility)**: 터미널/Python/앱에 허용 (입력 제어·재생)
  - **입력 모니터링(Input Monitoring)**: 키 녹화에 필요
- 권한 없이 실행하면 클릭/키가 기록·재생되지 않을 수 있습니다.

### Windows
- 관리자 권한이 필요한 창(UAC 등) 위에서는 입력이 막힐 수 있습니다.
- 백신/보안 소프트웨어가 입력 후킹을 차단하면 예외를 추가하세요.

### Linux
- X11에서는 대체로 바로 동작합니다. Wayland 환경에서는 `pynput` 제한이 있을 수 있어 X11 세션을 권장합니다.

## 프로젝트 구조

```
Macro/
├── README.md
├── requirements.txt
├── pyproject.toml
├── .gitignore
├── macros/
│   ├── .gitkeep
│   └── slot_01.json   # 저장된 슬롯 예
└── macro_studio/
    ├── __init__.py
    ├── __main__.py
    ├── app.py          # UI (슬롯·편집·재생)
    ├── recorder.py     # 녹화
    ├── player.py       # 재생 (start_index 지원)
    ├── models.py       # 데이터 모델 (+ slot)
    └── storage.py      # JSON I/O + 슬롯 API
```

## 단축키 요약

| 키 | 동작 |
|----|------|
| F9 | 녹화 시작/중지 |
| F10 | 재생 / 재생 중이면 중단 |
| Esc | 재생 중단 |
| Ctrl+1 … Ctrl+9, Ctrl+0 | 슬롯 1~10 불러오기 |

## 주의

- 본 도구는 **본인 PC의 자동화**용입니다. 타인 시스템·게임 약관 위반·악성 자동화에 사용하지 마세요.
- 재생 중 마우스가 움직이므로, 중단은 **Esc** / **F10**을 사용하세요.
