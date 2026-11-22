# Sleek Windows EXE 개발기: 배치 파일 없이 실행하기

2026-11-22 · `v1.1.0-rc.2` · [이전 성능 개선 및 rc.1 패키징 기록](2026-11-22-performance-windows.ko.md)

## 무엇이 달라졌나

첫 프리뷰는 Windows용 Python 런타임을 포함했지만 사용자가 직접 클릭해 실행하는 파일은 CMD였다. 이번 프리뷰는 두 방식 모두 CMD 없이 동작하도록 실행 파일을 제공한다.

| 자산 | 사용법 | 설치 대상 |
| --- | --- | --- |
| `*-Windows-x64-Setup.exe` | EXE 하나를 내려받아 실행한 뒤 시작 메뉴의 **Sleek Downloader**를 연다. | 현재 사용자, `%LOCALAPPDATA%\Programs\SleekDownloader` |
| `*-Windows-x64-Portable.zip` | 폴더를 전부 풀고 최상단 `SleekDownloader.exe`를 더블클릭한다. | 사용자가 압축을 푼 폴더. 설치 불필요 |
| `SHA256SUMS-v1.1.0-rc.2.txt` | 다운로드 받은 파일의 SHA-256을 대조한다. | 별도 설치 없음 |

설치용 EXE는 그 파일 하나에 전체 런타임과 앱을 담는다. 포터블 `SleekDownloader.exe` 단독 파일에는 런타임까지 들어 있지 않으므로 ZIP에서 함께 풀어야 한다. 두 방식 모두 Python을 따로 설치할 필요는 없다. FFmpeg는 MP3 변환 및 분리된 영상·음성 병합에 별도로 필요하다. 이 릴리즈는 서명되지 않은 Windows x64 프리뷰다.

## 실행기 설계

런처는 [Zig](https://ziglang.org/download/)로 x86-64 Windows PE를 교차 컴파일한 작은 C 프로그램이다. 실행 파일 자신의 위치에서 `runtime\python.exe`와 `app\launch.py`를 찾는다. 동작에 CMD나 PATH에 등록된 Python이 필요 없다. 실행 파일 경로를 Windows API에 별도로 전달하고 인자 경로를 각각 인용하므로 폴더 이름에 공백이 있어도 일반적인 경로와 같은 방식으로 실행된다. 새 임의 명령을 받을 필요가 없어 인자는 `--smoke-test` 하나만 받는다.

Python 앱은 기존 프리뷰와 같이 127.0.0.1에서만 서버를 열고, 서버 생성 후 기본 브라우저를 열려고 시도한다. 정상 시작·중지 및 오류를 확인할 수 있도록 콘솔을 유지한다. [NSIS](https://nsis.sourceforge.io/) 설치 패키지는 현재 사용자용 시작 메뉴 바로가기와 제거 항목을 만들며 관리자 권한을 요구하지 않는다. 제거용 목록은 빌드 때 동봉한 파일 이름만으로 만든다. 앱의 `config.json`과 사용자가 추가한 파일은 삭제 대상에 포함하지 않는다. 빈 디렉터리만 제거한다.

## 재현 절차

1. 기존 개발기의 절차로 공식 CPython 3.13.17 임베딩 ZIP, 고정된 Windows x64 wheel을 확보한다.
2. Zig 0.15.2와 NSIS 3.11을 설치한다. 단독 배포된 Debian NSIS를 추출해 쓸 경우 `NSISDIR`을 해당 패키지의 NSIS 공유 데이터 디렉터리로 지정한다.
3. 아래 빌더를 실행한다. 같은 이름의 파일이 이미 있으면 덮어쓰지 않는다.

```sh
python -m unittest discover -s tests -v
python scripts/build_windows_exe.py /tmp/sleek-win dist/windows \
  --zig zig --makensis makensis --version v1.1.0-rc.2
(cd dist/windows && sha256sum -c SHA256SUMS-v1.1.0-rc.2.txt)
```

첫 빌드에서 NSIS 제거 항목의 경로 인용이 경고를 냈다. 경고를 무시하지 않고, 제거 프로그램 경로를 값으로 올바르게 인용하도록 고쳤다. 설치 빌드는 경고를 오류로 취급한다. 다음으로 같은 입력의 설치 EXE를 두 번 만들었을 때 내부 파일 시각이 달라 체크섬이 바뀌는 것을 확인했다. 동봉 파일 시각을 고정하고 동일한 Linux 도구 및 TZ=UTC로 다시 두 번 빌드해 설치 EXE와 포터블 ZIP이 각각 바이트 단위로 일치함을 확인했다. 소스·테스트·설치 명세는 Git에만 두고 Windows 바이너리는 GitHub Release 자산으로 분리한다. 이전 프리뷰 자산 및 비활성 GitHub Actions 설정은 변경하지 않았다.

## 검증 범위와 남은 것

단위·Flask 테스트 12개, 두 배포 파일의 SHA-256, 포터블 ZIP 압축 무결성, 두 EXE의 PE32+ x86-64 헤더를 확인했다. NSIS 설치 파일도 7-Zip으로 실제로 풀었고, 포터블과 공통인 1,302개 파일의 SHA-256이 전부 일치했다. 포터블에서 추출한 코드와 라이브러리로 Linux에서 HTTP 루트·소개·설정·파비콘과 잘못된 분석 입력을 검사했다. Linux Wine에서 실행을 시도했지만 Wine 초기화가 중단되어 앱 실행까지 검증하지 못했다. Windows 실기기에서의 설치·삭제·폴더 대화상자 및 실제 미디어 변환은 별도 검증 대상이다. 실행 확인은 Windows 터미널에서 `SleekDownloader.exe --smoke-test` 또는 일반 더블클릭으로 할 수 있다.
