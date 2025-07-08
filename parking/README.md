# 자율주차 시스템 (Autonomous Parking System)

이 문서는 성균관대학교 자동화연구실(AutomationLab)에서 개발한 자율주차 시스템에 대한 설명입니다.

## 📋 개요

이 시스템은 PYNQ-Z2 보드를 기반으로 한 자율주차 시스템으로, 초음파 센서와 모터 제어를 통해 자동으로 주차를 수행합니다. YOLO 기반 차선 인식과 DPU 가속을 지원하여 정확한 주차 제어가 가능합니다.

## 🏗️ 시스템 구조

```
parking/
├── main.py                      # 메인 실행 파일 (키보드 조작)
├── parking_system_controller.py # 주차 시스템 컨트롤러
├── motor_controller.py          # 모터 제어기
├── image_processor.py           # 이미지 처리 및 YOLO 추론
├── yolo_utils.py               # YOLO 유틸리티 함수
├── config.py                   # 설정 파일 (주소 매핑)
├── AutoLab_lib.py              # AutoLab 라이브러리
└── README_parking_system.md    # 이 문서
```

## 🚀 주요 기능

### 1. 자율주차 알고리즘
- **14단계 주차 프로세스**: 대기 → 초기전진 → 정지 → 좌회전 → 정지 → 우회전 → 후진 → 정렬 → 위치확인 → 수정 → 후진 → 완료정지 → 전진 → 완료
- **센서 기반 제어**: 5개 초음파 센서를 통한 실시간 거리 측정
- **안전한 정지 조건**: 센서 데이터 기반 안전 정지

### 2. 하드웨어 제어
- **모터 제어**: 6개 모터 독립 제어 (좌우 구동, 조향)
- **센서 제어**: 5개 초음파 센서 실시간 모니터링
- **SPI 통신**: 고속 데이터 통신

### 3. 컴퓨터 비전
- **YOLO 기반 차선 인식**: DPU 가속을 통한 실시간 차선 감지
- **Bird's Eye View 변환**: 원근 변환을 통한 도로 시야 확보
- **각도 계산**: 차선 중심점 기반 조향 각도 계산

### 4. 사용자 인터페이스
- **키보드 조작**: 실시간 키보드 입력 처리
- **상태 모니터링**: 실시간 주차 상태 및 센서 데이터 표시
- **비상 정지**: 안전한 비상 정지 기능

## 🎮 실행 방법

### 1. 기본 실행 (키보드 조작)
```bash
cd parking
python main.py
```

**키보드 조작법:**
- `SPACE`: 주차 시작/중지
- `R`: 시스템 리셋
- `E`: 비상 정지
- `Q`: 프로그램 종료
- `C`: 주차 설정 확인
- `S`: 센서 상태 확인

### 2. 프로그래밍 방식 사용

```python
from motor_controller import MotorController
from parking_system_controller import ParkingSystemController
from config import MOTOR_ADDRESSES, ULTRASONIC_ADDRESSES, ADDRESS_RANGE
from pynq import MMIO
from AutoLab_lib import init

# 하드웨어 초기화
init()

# 모터 초기화
motors = {}
for name, addr in MOTOR_ADDRESSES.items():
    motors[name] = MMIO(addr, ADDRESS_RANGE)

# 초음파 센서 초기화
ultrasonic_sensors = {}
for name, addr in ULTRASONIC_ADDRESSES.items():
    ultrasonic_sensors[name] = MMIO(addr, ADDRESS_RANGE)

# 컨트롤러 초기화
motor_controller = MotorController(motors)
motor_controller.init_motors()

parking_controller = ParkingSystemController(motor_controller, ultrasonic_sensors)

# 주차 시작
parking_controller.start_parking()

# 주차 사이클 실행
while parking_controller.is_parking_active:
    sensor_data = parking_controller.read_ultrasonic_sensors()
    parking_controller.update_sensor_data(sensor_data)
    parking_controller.execute_parking_cycle()
    time.sleep(0.1)
```

## ⚙️ 설정

### 하드웨어 주소 설정 (`config.py`)

```python
# 모터 주소 매핑
MOTOR_ADDRESSES = {
    'motor_0': 0x00A0000000,  # 우측 후방
    'motor_1': 0x00A0010000,  # 좌측 조향
    'motor_2': 0x00A0020000,  # 좌측 전방
    'motor_3': 0x00A0030000,  # 좌측 후방
    'motor_4': 0x00A0040000,  # 우측 전방
    'motor_5': 0x00A0050000   # 우측 조향
}

# 초음파 센서 주소 매핑
ULTRASONIC_ADDRESSES = {
    'ultrasonic_0': 0x00B0000000,  # 전방 우측
    'ultrasonic_1': 0x00B0010000,  # 중간 좌측
    'ultrasonic_2': 0x00B0020000,  # 중간 우측
    'ultrasonic_3': 0x00B0030000,  # 후방 좌측
    'ultrasonic_4': 0x00B0040000   # 후방 우측
}
```

### 주차 설정

```python
parking_config = {
    'forward_speed': 30,      # 전진 속도 (0-100)
    'backward_speed': 25,     # 후진 속도 (0-100)
    'steering_speed': 50,     # 조향 속도 (0-100)
    'left_turn_angle': -20,   # 좌회전 각도
    'right_turn_angle': 13,   # 우회전 각도
    'correction_angle': 15,   # 수정 조향 각도
    'stop_distance': 40,      # 정지 거리 (cm)
    'alignment_tolerance': 3, # 정렬 허용 오차 (cm)
    'correction_threshold': 10, # 수정 임계값 (cm)
    'straight_backward_duration': 0.3, # 정방향 후진 시간 (초)
    'correction_duration': 2.0, # 수정 시간 (초)
    'parking_stop_duration': 2.0, # 주차 완료 정지 시간 (초)
    'right_turn_duration': 1.5  # 우회전 시간 (초)
}
```

## 🔧 하드웨어 요구사항

### 필수 하드웨어
- **PYNQ-Z2 보드**: 메인 제어 보드
- **모터 6개**: 구동 및 조향용
- **초음파 센서 5개**: 거리 측정용
- **카메라**: 차선 인식용 (선택사항)

### 센서 배치
```
    [후방 좌측] [중간 좌측]
         ↓      ↓
    ┌─────────────────────┐
    │                     │
    │      차량 본체      │ 앞
    │                     │
    └─────────────────────┘
         ↑     ↑        ↑
    [후방 우측][중간 우측][전방 우측]
```

## 📊 센서 데이터 형식

```python
sensor_data = {
    "front_right": 50,    # 전방 우측 거리 (cm)
    "middle_left": 80,    # 중간 좌측 거리 (cm)
    "middle_right": 45,   # 중간 우측 거리 (cm)
    "rear_left": 90,      # 후방 좌측 거리 (cm)
    "rear_right": 40      # 후방 우측 거리 (cm)
}
```

## 🎯 주차 단계별 동작

| 단계 | 단계명 | 동작 | 센서 조건 |
|------|--------|------|-----------|
| 0 | 대기 | 시스템 대기 | - |
| 1 | 초기 전진 | 전진 | - |
| 2 | 첫 번째 정지 | 정지 | 전방 센서 감지 |
| 3 | 좌회전 전진 | 좌회전 + 전진 | - |
| 4 | 두 번째 정지 | 정지 | 중간 센서 감지 |
| 5 | 우회전 후진 | 우회전 + 후진 | - |
| 6 | 정방향 후진 | 직진 후진 | 시간 기반 |
| 7 | 차량 정렬 | 조향 조정 | 센서 기반 |
| 8 | 위치 확인 | 센서 체크 | 거리 측정 |
| 9 | 위치 수정 | 조향 수정 | 필요시 |
| 10 | 수정 후 후진 | 후진 | 시간 기반 |
| 11 | 주차 완료 정지 | 정지 | 시간 기반 |
| 12 | 최종 전진 | 전진 | 시간 기반 |
| 13 | 완료 | 시스템 정지 | - |

## 🛡️ 안전 기능

### 1. 비상 정지
```python
parking_controller.emergency_stop()
```

### 2. 센서 기반 안전 정지
- 거리 임계값 초과 시 자동 정지
- 센서 오류 시 안전 모드 진입

### 3. 모터 안전 제어
- 속도 제한 및 안전 범위 설정
- 급격한 방향 전환 방지

## 🔍 디버깅 및 모니터링

### 상태 확인
```python
status = parking_controller.get_status()
print(f"현재 단계: {status['phase']}")
print(f"상태 메시지: {status['status_message']}")
print(f"센서 거리: {status['sensor_distances']}")
```

### 로그 출력
```
🚗 주차 시스템 시작
📊 단계: INITIAL_FORWARD - 초기 전진 중...
✅ 센서 감지 완료!
🔄 단계 변경: FIRST_STOP
🎉 주차 완료!
```

## 🚨 주의사항

1. **하드웨어 의존성**: PYNQ-Z2 보드 및 관련 하드웨어 필요
2. **센서 보정**: 초음파 센서 정확도 확인 필요
3. **환경 조건**: 조명, 온도 등 환경 조건 고려
4. **안전성**: 실제 주행 전 충분한 테스트 필요
5. **법적 규정**: 지역의 자율주행 관련 법규 준수

## 📝 의존성

```bash
pip install pynq pynq-dpu opencv-python numpy keyboard spidev
```
