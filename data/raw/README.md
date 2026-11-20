# 실제 데이터 준비

원본 출처: [UCI SECOM (2008)](https://archive.ics.uci.edu/dataset/179/secom) (CC BY 4.0, 출처 표기).

1. `secom.data`와 `secom_labels.data`를 이 폴더(`data/raw/`)에 놓습니다.
2. `backend` 폴더에서 `python scripts/import_secom.py ../data/raw/secom.data ../data/raw/secom_labels.data`로 우선 **DRY RUN**을 확인합니다.
3. 검사 기록 1,567건 중 `sensor_001` 측정값이 존재하는 1,561건만 업로드 후보입니다.
4. Firestore 연결 후 같은 명령 끝에 `--confirm`을 붙여 업로드합니다.
5. `secom.data`와 `secom_labels.data`는 `.gitignore`에 의해 저장소에 업로드되지 않습니다.

시간열은 일정한 간격의 실시간 센서 스트림이 아니라 각 검사 기록의 타임스탬프입니다.
