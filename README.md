# 매크로 스튜디오 (Macro Studio)

마우스·키보드 입력을 **녹화 → 편집 → JSON 저장 → 재생**하는 한국어 UI 데스크톱 앱입니다.  
클라우드/텔레메트리 없음. 녹화는 **녹화 모드**에서만 동작합니다.

A small desktop macro recorder & editor: record mouse+keyboard, edit freely (cut/copy/paste), save/load unlimited slots, share as portable JSON code, and play back once (no infinite loop by default). Multi-monitor uses virtual-desktop absolute coordinates.

## 기능

1. **동적 슬롯 (개수 제한 없음)** — 왼쪽 스크롤 목록  
   - **슬롯 추가** / **슬롯 삭제** / **슬롯 비우기** / **슬롯 복제** (`(복사)` 접미사)  
   - 표시: `N번 매크로 — 이름` 또는 `(비어있음)`  
   - 저장: `macros/slot_01.json`, `slot_02.json`, … (100번 이상은 `slot_100.json`)  
   - **Ctrl+1 … Ctrl+0**: 목록 **앞쪽 1~10번째** 슬롯으로 빠른 이동 (있을 때만)
2. **녹화** — 클릭(버튼·좌표), 스크롤, 키, 지연 / 마우스 이동은 기본 OFF  
   - 단축키: **F9** 녹화 토글, **F10** 재생(재생 중이면 중단), **Esc** 중단  
   - 좌표는 **가상 데스크톱 절대좌표** (멀티 모니터). 이벤트에 모니터 인덱스 참고 기록 가능
3. **편집** — 동작 번호 1-based  
   - 필드 수정, 삭제, **범위 삭제**, ▲▼ 순서, 대기(Wait) 삽입  
   - **잘라내기 / 복사 / 붙여넣기** — 범위 지정 후 원하는 위치(선택 앞, 없으면 끝)에 붙이기  
   - **현재 마우스 위치로 X/Y 채우기** (레이아웃 변경 시 재타겟)  
   - **[슬롯 저장]**을 눌렀을 때만 디스크 기록
4. **공유 (코드)**  
   - **코드로 내보내기**: 펜스 JSON 스니펫 생성·복사  
   - **코드 붙여넣기**: 동일 스니펫 → 새 슬롯 생성 또는 현재 슬롯 덮어쓰기  
   - 왕복 시 이벤트 타입·지연·좌표·키 보존
5. **재생** — 3초 카운트다운, 기본 1회, **N번부터 재생**

## 멀티 모니터

- `pynput` 녹화/재생은 OS **가상 데스크톱 전역(절대) 좌표**를 사용합니다.
- UI 상단에 현재 마우스 `(x, y)`와 감지된 **모니터 번호**를 표시합니다 (`screeninfo`).
- 모니터 배치가 같으면 화면 1·2 어디서든 동일 좌표로 재생됩니다.
- 배치가 다르면 해당 동작을 선택한 뒤 **[현재 마우스 위치로 X/Y 채우기]**로 다시 맞추세요.
- 이벤트의 `monitor` 필드는 참고용이며, 재생은 절대 `x`/`y`를 따릅니다.

## 요구 사항

- Python **3.11+** (권장 3.11–3.13)
- `pynput`, `customtkinter`, `screeninfo` (`requirements.txt`)


## Python 없이 쓰기 (Windows exe)

Python을 설치하지 않아도 **GitHub Actions**가 만든 Windows 실행 파일로 매크로 스튜디오를 실행할 수 있습니다.

### Actions 아티팩트 다운로드

1. 저장소 **Actions** 탭 → 워크플로 **Build Windows exe** 선택
2. 최신 성공한 실행(초록 체크)을 연 뒤 **Artifacts**에서 `MacroStudio-windows-x64` 다운로드
3. zip을 풀어 `MacroStudio.exe` 실행  
   - 첫 실행 시 exe와 **같은 폴더**에 `macros/` 가 자동 생성됩니다 (매크로 JSON 저장 위치)
4. 태그 `v*` 를 푸시하면 Release에도 동일 zip이 첨부됩니다

직접 링크(저장소가 public/권한 있을 때):  
https://github.com/nonojin99/Macro/actions/workflows/build-windows.yml

### 로컬에서 Windows 빌드

Windows PC에서:

```bat
cd Macro
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements-build.txt
scripts\build_windows.bat
```

또는 PowerShell:

```powershell
.\scripts\build_windows.ps1
```

결과: `dist\MacroStudio\MacroStudio.exe` (one-folder).  
`dist/`·`build/` 는 git에 올리지 않습니다.

**왜 one-folder?** customtkinter·pynput 리소스 로딩이 안정적이고, one-file보다 시작이 빠르며 Windows Defender 오탐이 상대적으로 적은 편입니다.

### Windows Defender / SmartScreen 안내

서명되지 않은 exe라 **Windows가 차단·경고**할 수 있습니다.  
본인이 빌드했거나 Actions 아티팩트임을 확인한 뒤 “추가 정보 → 실행”으로 허용하세요.  
백신 오탐이 나면 해당 폴더를 예외로 두거나 소스에서 직접 빌드하세요.

### 멀티모니터·권한 노트 (exe 동일)

- 좌표는 **가상 데스크톱 절대좌표**입니다. 모니터 배치가 바뀌면 **[현재 마우스 위치로 X/Y 채우기]**로 다시 맞추세요.
- 일부 보안 소프트웨어·관리자 권한이 필요한 창에서는 입력 후킹/재생이 막힐 수 있습니다.
- 관리자 권한으로 뜬 앱을 제어하려면 MacroStudio도 관리자 권한으로 실행해야 할 수 있습니다.

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

또는:

```bash
pip install -e .
macro-studio
```

## 슬롯 저장 형식

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
      "action": "press",
      "monitor": 0
    }
  ]
}
```

이벤트 `type`: `click` | `scroll` | `key` | `move` | `wait`

### 사용 흐름 예

1. **슬롯 추가** → 이름 입력 → F9 녹화 → 목록 편집  
2. 동작 3~5번 **잘라내기** → 동작 1 선택 → **붙여넣기** (앞으로 이동)  
3. **슬롯 복제**로 변형본 만들기  
4. **코드로 내보내기** → 다른 PC에서 **코드 붙여넣기**  
5. [슬롯 저장] → `macros/slot_NN.json`

## OS 권한 (중요)

### macOS
- **손쉬운 사용**, **입력 모니터링** 허용 필요

### Windows
- UAC/보안 소프트웨어가 입력 후킹을 막을 수 있음

### Linux
- X11 권장 (Wayland에서는 `pynput` 제한 가능)

## 프로젝트 구조

```
Macro/
├── README.md
├── requirements.txt
├── requirements-build.txt     # + pyinstaller
├── pyproject.toml
├── macro_studio.spec          # Windows one-folder
├── run_macro_studio.py        # PyInstaller 진입점
├── scripts/build_windows.ps1 / .bat
├── .github/workflows/build-windows.yml
├── tests/test_frozen_paths.py
├── macros/
└── macro_studio/
    ├── app.py / app_hotkeys.py  # UI 셸
    ├── recorder.py / player.py
    ├── models.py / storage.py # 동적 슬롯 (+ frozen exe 경로)
    ├── monitors.py            # 멀티모니터 절대좌표
    ├── share.py               # 코드 내보내기/가져오기
    ├── ui_slots.py / ui_slots_ops.py / ui_share.py
    ├── ui_events.py / ui_events_edit.py / ui_clipboard.py
    └── __main__.py
```

## 단축키

| 키 | 동작 |
|----|------|
| F9 | 녹화 시작/중지 |
| F10 | 재생 / 재생 중이면 중단 |
| Esc | 재생 중단 |
| Ctrl+1 … Ctrl+0 | 목록 앞 1~10번째 슬롯 |

## 주의

- 본인 PC 자동화 용도. 타인 시스템·약관 위반·악성 자동화에 사용하지 마세요.
- 재생 중 마우스 이동 — **Esc** / **F10**으로 중단하세요.
