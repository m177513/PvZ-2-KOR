# PvZ 2 KOR

[베타 ZIP 다운로드](https://github.com/m177513/PvZ-2-KOR/releases/download/beta1-20260911/pvz2-ko-13.4.1-beta1-20260911.zip) · [릴리스 안내](https://github.com/m177513/PvZ-2-KOR/releases/tag/beta1-20260911)

Android ROW `com.ea.game.pvz2_row` **13.4.1 / versionCode 1055** 전용입니다. 게임 APK와 전체 OBB는 포함하지 않습니다. 설치된 원본 리소스에서 한글판을 만듭니다. 버전이 같아도 리소스 해시가 다르면 적용하지 않습니다.

## 준비

Windows PC, Python 3.11 이상, Android Platform-Tools의 adb, USB 케이블, PC 여유 공간 4GB 이상을 준비하세요. ZIP을 로컬 NTFS 드라이브의 폴더에 모두 풀어 주세요. Python 외 추가 pip 패키지는 필요 없습니다.

- Python 공식 다운로드: https://www.python.org/downloads/windows/
- ADB 공식 다운로드: https://developer.android.com/tools/releases/platform-tools

폰에서 게임을 설치하고 필요한 리소스 다운로드를 마친 뒤 게임을 닫습니다. USB 디버깅을 켜고 PC 연결을 허용하세요. 설치가 끝날 때까지 게임을 직접 실행하거나 폰을 조작하지 마세요. 앱 데이터 초기화·재설치는 필요 없습니다.

## 설치

준비가 끝났으면 `INSTALL.cmd`를 더블클릭해 설치할 수 있습니다. ADB를 찾지 못하면 adb.exe의 전체 경로를 입력하세요. 여러 폰이 연결돼 있으면 목록에서 선택합니다. 아래는 같은 작업의 수동 명령입니다.

압축을 푼 폴더에서 PowerShell을 열어 실행합니다. ADB 경로와 SERIAL을 자신의 환경에 맞게 바꾸세요.

```powershell
& 'C:\platform-tools\adb.exe' devices
py -3 release_patch.py install --adb 'C:\platform-tools\adb.exe' --serial SERIAL
```

성공 시 `INSTALLED_HASH_VERIFIED`가 나옵니다. 이미 같은 한글판이면 `ALREADY_INSTALLED_HASH_VERIFIED`가 나오며 폰을 바꾸지 않습니다. 설치 후 폰에서 게임을 직접 실행하세요.

설치기는 버전·리소스 해시를 확인하고 OBB와 CDN 두 파일만 PC의 `backups/pvz2-backup-*`에 백업합니다. PC에서 패치 결과를 검증한 뒤 폰에 적용하고 다시 해시를 확인합니다. 실패하면 변경한 리소스의 자동 복구를 시도합니다. USB가 끊긴 경우 재연결 후 아래 복구를 사용하세요. 백업 폴더는 보관하고 공유하지 마세요.

세이브·계정 파일, APK, 로그인, 구매, 보상, 레벨 진행은 다루지 않습니다. 게임 자체의 자동 저장 여부는 이 도구의 검증 범위가 아닙니다.

## 확인 / 설치 전 상태로 복구

```powershell
py -3 release_patch.py verify --adb 'C:\platform-tools\adb.exe' --serial SERIAL
py -3 release_patch.py restore --adb 'C:\platform-tools\adb.exe' --serial SERIAL --backup 'backups\pvz2-backup-실제폴더명'
```

복구는 해당 폰에서 만든 백업만 사용합니다. 다른 버전으로 업데이트됐거나 백업이 손상됐으면 거부합니다. 복구 실패 시 `install-result.json`과 백업을 보존하세요.

## 폰을 연결하지 않고 파일만 생성

```powershell
py -3 release_patch.py apply --obb '원본\main.1055.com.ea.game.pvz2_row.obb' --cdn '원본\LawnStrings-en-us.rton' --out '새출력폴더'
```

출력 폴더가 이미 있으면 거부합니다. 만들어진 전체 게임 리소스는 이 배포 ZIP에 넣지 마세요.

## 이번 베타의 범위

S24 Ultra에서 시작, 모드 선택, 기본 좀비 도감, 능력 카드의 한글 표시를 확인했습니다. 기본 좀비와 첫 3개 카드는 유지·재진입도 확인했습니다. 네 번째 ‘파워 잽’ 등 추가 카드의 첫 표시는 확인했지만, 30분 탐색은 사용자 직접 조작과 겹쳐 중단했습니다.

전투 전체·모든 메뉴·장시간 안정성·제작진 화면은 통과로 인증하지 않습니다. 제작진 화면은 이번 베타의 지원 범위에서 제외합니다. 이전 묶음에서 따로 처리했던 OBB 전용 문구 3개는 이 정확한 실기 통과 버전에 통합되지 않았습니다. 일부 이미지형 배너 문구는 영어로 남습니다. 새 CDN 다운로드나 게임 업데이트 뒤에는 적용 가능한 해시가 달라질 수 있습니다.

폰트·번역 내용을 새로 바꾼 버전이 아니라, 2026-09-11 실기 통과 후보와 바이트가 같은 버전입니다. 원본 및 출력 SHA256은 `manifest.json`, 묶음 내부 파일 해시는 `SHA256SUMS.txt`에 있습니다.

오류 제보 시 기종, 게임 버전, 실제 화면, 발생 순서, 설치 결과 JSON을 전달해 주세요. 세이브·계정·개인정보가 들어간 파일은 보내지 마세요.

## 구성과 고지

`obb.pvzdelta`, `cdn.pvzdelta`는 원본 참조 복사와 변경 바이트로 구성된 차분입니다. `release_patch.py`는 Python 표준 라이브러리만 사용하는 적용·설치 도구입니다. APK, ADB, 원본 또는 완성 OBB, 세이브는 동봉하지 않습니다.

추가 한글 글리프에는 Noto 계열 글꼴을 사용했습니다. SIL Open Font License 전문은 `NotoSans-OFL.txt`에 동봉합니다. 이 비공식 팬 패치는 EA/PopCap의 공식 제품이 아닙니다. 게임과 기존 게임 자산의 권리는 각 권리자에게 있습니다.
